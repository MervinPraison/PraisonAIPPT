"""Pixel-level visual audit — sample frames, compare to planned assets, optional vision LLM."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from praisonaippt.daily_single.display_sync import (
    MIN_ALIGNMENT,
    VISUAL_META,
    _meta_for,
    build_visual_timeline,
    parse_srt,
    score_cue_visual,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.image_selection import script_alignment, tokenise
from praisonaippt.segment_video.media import ffprobe_duration
from praisonaippt.daily_single.env import load_env
from praisonaippt.vision_describe import _GENERIC_PATTERNS, describe_frame, vision_model, vision_provider

DEFAULT_INTERVAL_SEC = 5.0
MIN_PIXEL_SIM = 0.42
MIN_PIXEL_SIM_VIDEO = 0.28
MIN_PIXEL_SIM_AVATAR = 0.15
MIN_TOPIC_ALIGNMENT = 0.35
GENERIC_BROLL_FILES = frozenset({"claudeai-launch.mp4"})
LAUNCH_CLIP_ON_TOPIC_IN_SEC = 5.8


def _vision_says_generic(
    vision: dict[str, Any] | None,
    spoken: str,
    planned_file: str,
) -> bool:
    """Trust gpt-4o-mini generic_broll only when description diverges from narration."""
    if not vision:
        return planned_file in GENERIC_BROLL_FILES
    desc = vision.get("description") or ""
    topics = " ".join(vision.get("topics") or [])
    vis_align = script_alignment(spoken, {
        "vision_description": desc,
        "relevance_reason": topics,
        "topic_relevance_score": 0.25 if vision.get("generic_broll") else 0.75,
    })
    if planned_file in GENERIC_BROLL_FILES:
        return vis_align < 0.4 or bool(_GENERIC_PATTERNS.search(desc))
    if vision.get("generic_broll") and vis_align < 0.35:
        return True
    return False


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def export_frame(mp4: Path, t_sec: float, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dur = ffprobe_duration(mp4)
    t = max(0.0, min(float(t_sec), max(0.0, dur - 0.5)))
    _run_ffmpeg([
        "ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(mp4.resolve()),
        "-frames:v", "1", "-q:v", "2", "-update", "1", str(dest),
    ])
    return dest


def _gray_array(image_path: Path, *, w: int = 320, h: int = 180) -> np.ndarray | None:
    if not image_path.is_file():
        return None
    cmd = [
        "ffmpeg", "-y", "-i", str(image_path.resolve()),
        "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        return None
    expected = w * h
    if len(proc.stdout) < expected:
        return None
    return np.frombuffer(proc.stdout[:expected], dtype=np.uint8).reshape(h, w)


def pixel_similarity(frame_a: Path, frame_b: Path) -> float:
    """Return 0–1 similarity (1 = identical grayscale downscale)."""
    a = _gray_array(frame_a)
    b = _gray_array(frame_b)
    if a is None or b is None:
        return 0.0
    mse = float(np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2))
    return round(max(0.0, 1.0 - mse / 65025.0), 3)


def reference_frame_for_asset(asset_path: Path, cache_dir: Path, *, at_sec: float | None = None) -> Path | None:
    """Build a reference JPEG for PNG or frame from MP4 (optional time offset)."""
    if not asset_path.is_file():
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = asset_path.name.replace(".", "_")
    if at_sec is not None:
        key = f"{key}-t{at_sec:.2f}"
    dest = cache_dir / f"ref-{key}.jpg"
    if dest.is_file() and dest.stat().st_mtime >= asset_path.stat().st_mtime:
        return dest
    suffix = asset_path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".webp"):
        _run_ffmpeg(["ffmpeg", "-y", "-i", str(asset_path.resolve()), "-frames:v", "1", "-q:v", "2", "-update", "1", str(dest)])
        return dest
    if suffix in (".mp4", ".mov", ".webm"):
        mid = at_sec if at_sec is not None else max(0.5, ffprobe_duration(asset_path) * 0.35)
        export_frame(asset_path, mid, dest)
        return dest
    return None


def _resolve_asset_path(project: DailySingleProject, filename: str) -> Path | None:
    if not filename or filename == "none":
        return None
    assets = project.assets_dir
    for candidate in (
        assets / "generated" / filename,
        assets / "images" / filename,
        assets / "videos" / filename,
        assets / filename,
    ):
        if candidate.is_file():
            return candidate
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    for beat in (beat_map.get("beats") or {}).values():
        for key in ("generated", "images", "clips"):
            for item in beat.get(key) or []:
                if filename in str(item.get("filename", "")):
                    p = Path(item["path"])
                    if p.is_file():
                        return p
    return None


def _spoken_at(cues: list[dict[str, Any]], t: float) -> str:
    for cue in cues:
        if cue["start_sec"] <= t < cue["end_sec"]:
            return cue["text"]
    if cues:
        return cues[-1]["text"]
    return ""


def _sample_times(duration: float, interval: float, windows: list[Any]) -> list[float]:
    cap = max(0.0, duration - 0.15)
    times: set[float] = set()
    t = interval / 2
    while t < cap:
        times.add(round(t, 2))
        t += interval
    for w in windows:
        mid = min((w.start_sec + w.end_sec) / 2, cap)
        if mid >= 0:
            times.add(round(mid, 2))
    return sorted(t for t in times if t <= cap)


def _pixel_threshold(planned_file: str, section: str) -> float:
    if "heygen" in planned_file.lower() or section == "bridge":
        return MIN_PIXEL_SIM_AVATAR
    if planned_file.lower().endswith(".mp4"):
        return MIN_PIXEL_SIM_VIDEO
    return MIN_PIXEL_SIM


def audit_sample(
    project: DailySingleProject,
    mp4: Path,
    t_sec: float,
    spoken: str,
    planned_file: str,
    section: str,
    frames_dir: Path,
    ref_cache: Path,
    *,
    use_vision: bool,
    window_start: float | None = None,
    window_end: float | None = None,
) -> dict[str, Any]:
    frame_path = frames_dir / f"frame-{t_sec:07.2f}.jpg"
    export_frame(mp4, t_sec, frame_path)

    asset_path = _resolve_asset_path(project, planned_file)
    ref_at: float | None = None
    if (
        planned_file == "canonical-scroll.mp4"
        and asset_path
        and window_start is not None
        and window_end is not None
    ):
        win_dur = max(0.1, window_end - window_start)
        frac = max(0.0, min(1.0, (t_sec - window_start) / win_dur))
        ref_at = frac * ffprobe_duration(asset_path)
    ref_path = reference_frame_for_asset(asset_path, ref_cache, at_sec=ref_at) if asset_path else None
    pixel_sim = pixel_similarity(frame_path, ref_path) if ref_path else 0.0
    threshold = _pixel_threshold(planned_file, section)

    meta = _meta_for(planned_file)
    planned_score = score_cue_visual(spoken, planned_file)
    vision: dict[str, Any] | None = None
    topic_alignment = planned_score
    generic_broll = planned_file in GENERIC_BROLL_FILES and section == "attention"

    if use_vision and vision_provider() not in ("", "off", "none", "false"):
        vision = describe_frame(frame_path, spoken)
        if vision:
            img = {
                "vision_description": vision.get("description", ""),
                "relevance_reason": " ".join(vision.get("topics") or ()),
                "topic_relevance_score": 0.85 if not vision.get("generic_broll") else 0.2,
            }
            topic_alignment = max(topic_alignment, script_alignment(spoken, img))
            generic_broll = _vision_says_generic(vision, spoken, planned_file)

    pixel_ok = pixel_sim >= threshold if ref_path else planned_score >= MIN_ALIGNMENT
    topic_ok = topic_alignment >= MIN_TOPIC_ALIGNMENT
    if ref_path and pixel_ok:
        ok = not generic_broll
    else:
        ok = pixel_ok and topic_ok and not generic_broll

    issues: list[str] = []
    if ref_path and not pixel_ok:
        issues.append(f"pixel_sim {pixel_sim:.2f} < {threshold:.2f} vs {planned_file}")
    elif not ref_path and not topic_ok:
        issues.append(f"topic_alignment {topic_alignment:.2f} < {MIN_TOPIC_ALIGNMENT}")
    elif not ref_path and not pixel_ok:
        issues.append(f"no reference asset for {planned_file}")
    if generic_broll:
        issues.append(f"generic/off-topic B-roll ({planned_file})")
        ok = False

    return {
        "t_sec": t_sec,
        "spoken": spoken[:200],
        "planned_file": planned_file,
        "section": section,
        "frame": str(frame_path.relative_to(project.root)),
        "pixel_similarity": pixel_sim,
        "pixel_threshold": threshold,
        "pixel_ok": pixel_ok,
        "topic_alignment": round(topic_alignment, 3),
        "topic_ok": topic_ok,
        "generic_broll": generic_broll,
        "vision": vision,
        "ok": ok,
        "issues": issues,
    }


def run_visual_audit(
    project: DailySingleProject,
    *,
    interval: float = DEFAULT_INTERVAL_SEC,
    use_vision: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Sample final.mp4 every `interval` seconds + at visual window midpoints."""
    mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final.mp4"
    if not mp4.is_file():
        raise FileNotFoundError("Missing merge/final.mp4 — run assemble-beats first")

    load_env()
    report_path = project.merge_dir / "visual_audit_report.json"
    if report_path.is_file() and not force:
        cached = json.loads(report_path.read_text(encoding="utf-8"))
        vision_on = use_vision and vision_provider() not in ("", "off", "none", "false")
        cached_vision = bool(cached.get("vision_samples"))
        if (
            cached.get("ok") is not None
            and cached.get("interval_sec") == interval
            and cached.get("vision_model") == vision_model()
            and cached_vision == vision_on
        ):
            return cached

    duration = ffprobe_duration(mp4)
    srt_path = project.merge_dir / "final.srt"
    srt_cues = parse_srt(srt_path) if srt_path.is_file() else []
    windows = build_visual_timeline(project)
    times = _sample_times(duration, interval, windows)

    frames_dir = project.merge_dir / "visual_audit_frames"
    ref_cache = project.merge_dir / "visual_audit_refs"
    samples: list[dict[str, Any]] = []

    for i, t in enumerate(times, 1):
        win = next((w for w in windows if w.start_sec <= t < w.end_sec), windows[-1] if windows else None)
        planned = win.file if win else "none"
        section = win.section if win else ""
        spoken = _spoken_at(srt_cues, t)
        samples.append(audit_sample(
            project, mp4, t, spoken, planned, section,
            frames_dir, ref_cache, use_vision=use_vision,
            window_start=win.start_sec if win else None,
            window_end=win.end_sec if win else None,
        ))
        if use_vision and i % 15 == 0:
            print(f"  audit-visual: {i}/{len(times)} frames (model={vision_model()})")

    fails = [s for s in samples if not s["ok"]]
    generic = [s for s in samples if s.get("generic_broll")]
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "video": str(mp4.relative_to(project.root)),
        "duration_sec": round(duration, 2),
        "interval_sec": interval,
        "vision_provider": vision_provider(),
        "vision_model": vision_model(),
        "vision_samples": sum(1 for s in samples if s.get("vision")),
        "samples_total": len(samples),
        "samples_pass": len(samples) - len(fails),
        "samples_fail": len(fails),
        "generic_broll_count": len(generic),
        "pass_rate": round((len(samples) - len(fails)) / max(1, len(samples)), 3),
        "ok": len(fails) == 0,
        "min_pixel_sim": MIN_PIXEL_SIM,
        "samples": samples,
        "failures": [{"t_sec": s["t_sec"], "issues": s["issues"], "planned_file": s["planned_file"]} for s in fails[:20]],
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def validate_visual_audit(project: DailySingleProject, *, force: bool = False) -> tuple[bool, dict[str, Any]]:
    """Run or load visual audit; fail on off-topic or low pixel match."""
    report_path = project.merge_dir / "visual_audit_report.json"
    if force or not report_path.is_file():
        report = run_visual_audit(project, force=True)
    else:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    ok = bool(report.get("ok"))
    issues = [
        f"t={f['t_sec']:.1f}s {f['planned_file']}: {', '.join(f['issues'])}"
        for f in report.get("failures") or []
    ]
    if report.get("generic_broll_count", 0) > 0 and ok:
        ok = False
        issues.append(f"{report['generic_broll_count']} generic B-roll samples detected")
    return ok, {**report, "issues": issues}

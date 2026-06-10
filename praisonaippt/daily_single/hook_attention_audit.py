"""Per-second validation for hook attention (first N seconds = canonical scroll)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from praisonaippt.daily_single.canonical_scroll import SCROLL_FILENAME, frame_motion, scroll_video_path
from praisonaippt.daily_single.hook_montage import build_hook_montage_plan, hook_attention_durations
from praisonaippt.daily_single.page_capture_quality import (
    frame_looks_like_browser_error,
    validate_scroll_asset,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.visual_audit import export_frame, pixel_similarity, reference_frame_for_asset
from praisonaippt.segment_video.media import ffprobe_duration

DEFAULT_SECONDS = 5
MIN_PIXEL_SIM = 0.22
MIN_MOTION = 0.008


def attention_sample_times(seconds: int = DEFAULT_SECONDS) -> list[float]:
    """One frame per second for the first `seconds` (0 .. seconds-1)."""
    return [float(i) for i in range(max(1, seconds))]


def run_hook_attention_audit(
    project: DailySingleProject,
    *,
    seconds: int = DEFAULT_SECONDS,
    use_vision: bool = False,
) -> dict:
    """Export one frame per second for hook attention; validate vs canonical-scroll."""
    mp4 = project.merge_dir / "final.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        raise FileNotFoundError("Missing merge/final.mp4 — run assemble-beats first")

    scroll = scroll_video_path(project)
    if not scroll:
        raise FileNotFoundError(f"Missing assets/videos/{SCROLL_FILENAME} — run record-canonical-scroll")

    scroll_ok, scroll_details = validate_scroll_asset(project, scroll)
    if not scroll_ok:
        raise RuntimeError(
            "canonical-scroll.mp4 failed content gate: "
            + "; ".join(scroll_details.get("issues") or [])
        )

    script_path = project.segment_script("00-hook")
    script = script_path.read_text(encoding="utf-8") if script_path.is_file() else ""
    tl_path = project.merge_dir / "timeline.json"
    hook_dur = ffprobe_duration(mp4)
    if tl_path.is_file():
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        hook_row = next((s for s in tl.get("segments") or [] if s.get("id") == "00-hook"), None)
        if hook_row:
            hook_dur = float(hook_row.get("duration_sec") or hook_dur)
    att_dur, _, _ = hook_attention_durations(
        hook_dur, script, motion_clip=bool(scroll),
    )
    check_sec = min(seconds, max(1, int(att_dur)))

    frames_dir = project.merge_dir / "qa" / "hook_attention_seconds"
    ref_cache = project.merge_dir / "visual_audit_refs"
    frames_dir.mkdir(parents=True, exist_ok=True)

    scroll_dur = ffprobe_duration(scroll)
    samples: list[dict] = []

    for t in attention_sample_times(check_sec):
        frame_out = frames_dir / f"hook-attention-{int(t):02d}s.jpg"
        export_frame(mp4, t, frame_out)
        ref_t = min(max(0.0, scroll_dur - 0.05), (t / max(0.1, check_sec)) * scroll_dur if scroll_dur > 0 else 0.0)
        ref_path = reference_frame_for_asset(scroll, ref_cache, at_sec=ref_t)
        pixel = pixel_similarity(frame_out, ref_path) if ref_path else 0.0
        spoken = ""
        srt = project.merge_dir / "final.srt"
        if srt.is_file():
            from praisonaippt.daily_single.display_sync import parse_srt
            for cue in parse_srt(srt):
                if cue["start_sec"] <= t < cue["end_sec"]:
                    spoken = cue["text"]
                    break

        ok = pixel >= MIN_PIXEL_SIM and not frame_looks_like_browser_error(frame_out)
        issues: list[str] = []
        if pixel < MIN_PIXEL_SIM:
            issues.append(f"pixel_sim {pixel:.2f} < {MIN_PIXEL_SIM}")
        if frame_looks_like_browser_error(frame_out):
            issues.append("frame looks like browser error page (not news content)")
        samples.append({
            "t_sec": t,
            "frame": str(frame_out.relative_to(project.root)),
            "ref_scroll_t_sec": round(ref_t, 2),
            "pixel_sim": round(pixel, 3),
            "spoken": spoken[:120],
            "ok": ok,
            "issues": issues,
        })

    motion_checks: list[dict] = []
    for i in range(len(samples) - 1):
        a = project.root / samples[i]["frame"]
        b = project.root / samples[i + 1]["frame"]
        delta = round(frame_motion(a, b), 4)
        moved = delta >= MIN_MOTION
        motion_checks.append({
            "from_sec": samples[i]["t_sec"],
            "to_sec": samples[i + 1]["t_sec"],
            "motion_delta": delta,
            "ok": moved,
        })
        if not moved:
            samples[i + 1]["ok"] = False
            samples[i + 1]["issues"] = list(samples[i + 1].get("issues") or []) + [
                f"no scroll/zoom motion {samples[i]['t_sec']:.0f}s→{samples[i+1]['t_sec']:.0f}s (delta={delta:.3f})"
            ]

    fails = [s for s in samples if not s["ok"]]
    motion_ok = all(m["ok"] for m in motion_checks) if motion_checks else False
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seconds_checked": check_sec,
        "planned_file": SCROLL_FILENAME,
        "samples_total": len(samples),
        "samples_pass": len(samples) - len(fails),
        "ok": len(fails) == 0 and motion_ok,
        "min_pixel_sim": MIN_PIXEL_SIM,
        "min_motion_delta": MIN_MOTION,
        "motion_checks": motion_checks,
        "motion_ok": motion_ok,
        "samples": samples,
        "frames_dir": str(frames_dir.relative_to(project.root)),
    }
    out = project.merge_dir / "qa" / "hook_attention_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    build_hook_montage_plan(project)
    return report

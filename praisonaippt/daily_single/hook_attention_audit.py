"""Hook QA — frame export (1s then 2s cadence), scroll/framing gates, spoken↔visual inline."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.canonical_scroll import SCROLL_FILENAME, frame_motion, scroll_video_path
from praisonaippt.daily_single.content_framing import measure_framing, validate_framing
from praisonaippt.daily_single.display_sync import build_visual_timeline, parse_srt, visual_at
from praisonaippt.daily_single.hook_montage import ATTENTION_MOTION_SEC, build_hook_montage_plan
from praisonaippt.daily_single.page_capture_quality import (
    frame_looks_like_browser_error,
    validate_scroll_asset,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.spoken_visual_sync import (
    validate_chart_inline,
    validate_hook_sample_inline,
    validate_srt_plain_language,
)
from praisonaippt.daily_single.visual_audit import export_frame, pixel_similarity, reference_frame_for_asset
from praisonaippt.segment_video.media import ffprobe_duration

DEFAULT_ATTENTION_SEC = 5
MIN_PIXEL_SIM = 0.22
MIN_MOTION = 0.008
ATTENTION_SAMPLE_INTERVAL = 1.0
HOOK_SAMPLE_INTERVAL = 2.0


def attention_sample_times(seconds: int = DEFAULT_ATTENTION_SEC) -> list[float]:
    """One frame per second for the first `seconds` (0 .. seconds-1)."""
    return [float(i) for i in range(max(1, seconds))]


def hook_audit_sample_times(hook_dur: float, *, attention_sec: float = ATTENTION_MOTION_SEC) -> list[float]:
    """1 Hz for the first `attention_sec`, then every 2s until the hook ends."""
    times: list[float] = []
    t = 0.0
    while t < min(attention_sec, hook_dur) - 0.05:
        times.append(round(t, 2))
        t += ATTENTION_SAMPLE_INTERVAL
    t = attention_sec + ATTENTION_SAMPLE_INTERVAL
    while t < hook_dur - 0.05:
        times.append(round(t, 2))
        t += HOOK_SAMPLE_INTERVAL
    return times


def _spoken_at(cues: list[dict], t: float) -> str:
    for cue in cues:
        if cue["start_sec"] <= t < cue["end_sec"]:
            return cue["text"]
    return ""


def _frame_name(t: float) -> str:
    return f"hook-{int(round(t)):02d}s.jpg"


def run_hook_attention_audit(
    project: DailySingleProject,
    *,
    seconds: int = DEFAULT_ATTENTION_SEC,
    use_vision: bool = False,
) -> dict:
    """Export hook frames (1s/2s cadence), validate scroll, framing, spoken↔visual inline."""
    mp4 = project.merge_dir / "final.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        raise FileNotFoundError("Missing merge/final.mp4 — run assemble-beats first")

    try:
        beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        beat_map = {}
    skip_scroll = beat_map.get("variant") in ("trust-audit", "social-comparison")

    scroll = scroll_video_path(project)
    scroll_ok, scroll_details = True, {}
    if not skip_scroll:
        if not scroll:
            raise FileNotFoundError(f"Missing assets/videos/{SCROLL_FILENAME} — run record-canonical-scroll")
        scroll_ok, scroll_details = validate_scroll_asset(project, scroll)
        if not scroll_ok:
            raise RuntimeError(
                "canonical-scroll.mp4 failed content gate: "
                + "; ".join(scroll_details.get("issues") or [])
            )

    tl_path = project.merge_dir / "timeline.json"
    hook_dur = ffprobe_duration(mp4)
    hook_start = 0.0
    if tl_path.is_file():
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        hook_row = next((s for s in tl.get("segments") or [] if s.get("id") == "00-hook"), None)
        if hook_row:
            hook_dur = float(hook_row.get("duration_sec") or hook_dur)
            hook_start = float(hook_row.get("start_sec") or 0.0)

    attention_sec = min(float(seconds), ATTENTION_MOTION_SEC, hook_dur)
    sample_times = hook_audit_sample_times(hook_dur, attention_sec=attention_sec)

    frames_dir = project.merge_dir / "qa" / "hook_frames"
    ref_cache = project.merge_dir / "visual_audit_refs"
    frames_dir.mkdir(parents=True, exist_ok=True)

    windows = [w for w in build_visual_timeline(project) if w.beat == "00-hook"]
    cues: list[dict] = []
    srt = project.merge_dir / "final.srt"
    if srt.is_file():
        cues = parse_srt(srt)

    scroll_dur = ffprobe_duration(scroll) if scroll and scroll.is_file() else 0.0
    att_dur = min(attention_sec, hook_dur)
    montage_plan = build_hook_montage_plan(project)
    montage_cues = [c for c in (montage_plan.get("cues") or []) if c.get("ok")]
    hook_script = project.segment_script("00-hook")
    hook_script_text = hook_script.read_text(encoding="utf-8") if hook_script.is_file() else ""
    from praisonaippt.daily_single.hook_montage import attention_visual

    att_cue = attention_visual(project, montage_cues, script=hook_script_text) if skip_scroll else {}
    att_ref_path = Path(att_cue["path"]) if att_cue.get("path") else None
    samples: list[dict] = []

    for t in sample_times:
        frame_out = frames_dir / _frame_name(t)
        export_frame(mp4, hook_start + t, frame_out)
        vis = visual_at(windows, t)
        spoken = _spoken_at(cues, hook_start + t)
        if not spoken.strip() and vis and vis.section == "overview" and vis.script_fragment:
            spoken = vis.script_fragment

        in_attention = t < att_dur - 0.05
        ref_t = 0.0
        pixel = 0.0
        if in_attention and skip_scroll and att_ref_path and att_ref_path.is_file():
            att_clip_dur = ffprobe_duration(att_ref_path)
            ref_t = min(max(0.0, att_clip_dur - 0.05), t)
            ref_path = reference_frame_for_asset(att_ref_path, ref_cache, at_sec=ref_t)
            pixel = pixel_similarity(frame_out, ref_path) if ref_path else 0.0
        elif in_attention and scroll_dur > 0:
            ref_t = min(max(0.0, scroll_dur - 0.05), (t / max(0.1, att_dur)) * scroll_dur)
            ref_path = reference_frame_for_asset(scroll, ref_cache, at_sec=ref_t)
            pixel = pixel_similarity(frame_out, ref_path) if ref_path else 0.0

        inline_ok, alignment, inline_issues = validate_hook_sample_inline(spoken, vis)
        if vis and vis.section == "overview":
            chart_ok, chart_issues = True, []
        else:
            chart_ok, _, chart_issues = validate_chart_inline(spoken, vis.file if vis else "")
        plain_ok, plain_issues = validate_srt_plain_language(
            [{"start_sec": t, "end_sec": t + 1, "text": spoken}] if spoken else []
        )
        ok = inline_ok and chart_ok and plain_ok and not frame_looks_like_browser_error(frame_out)
        issues: list[str] = list(inline_issues) + list(chart_issues) + list(plain_issues)

        if in_attention and not skip_scroll:
            if pixel < MIN_PIXEL_SIM:
                ok = False
                issues.append(f"pixel_sim {pixel:.2f} < {MIN_PIXEL_SIM}")
            frame_metrics = measure_framing(frame_out)
            framing_ok, framing_issues = validate_framing(frame_metrics)
            if not framing_ok:
                ok = False
                issues.extend(framing_issues)
        elif in_attention:
            frame_metrics = measure_framing(frame_out)
        else:
            frame_metrics = measure_framing(frame_out)

        if frame_looks_like_browser_error(frame_out):
            ok = False
            issues.append("frame looks like browser error page (not news content)")

        samples.append({
            "t_sec": t,
            "frame": str(frame_out.relative_to(project.root)),
            "planned_file": vis.file if vis else "",
            "section": vis.section if vis else "",
            "script_fragment": (vis.script_fragment or "")[:80] if vis else "",
            "ref_scroll_t_sec": round(ref_t, 2) if in_attention else None,
            "pixel_sim": round(pixel, 3) if in_attention else None,
            "alignment": round(alignment, 3),
            "spoken_inline_ok": inline_ok,
            "chart_inline_ok": chart_ok,
            "plain_language_ok": plain_ok,
            "left_margin": frame_metrics.left_margin_ratio,
            "right_margin": frame_metrics.right_margin_ratio,
            "content_fill": frame_metrics.content_fill_ratio,
            "spoken": spoken[:120],
            "ok": ok,
            "issues": issues,
        })

    motion_checks: list[dict] = []
    att_samples = [s for s in samples if s["t_sec"] < att_dur - 0.05]
    if not skip_scroll:
        for i in range(len(att_samples) - 1):
            a = project.root / att_samples[i]["frame"]
            b = project.root / att_samples[i + 1]["frame"]
            delta = round(frame_motion(a, b), 4)
            moved = delta >= MIN_MOTION
            motion_checks.append({
                "from_sec": att_samples[i]["t_sec"],
                "to_sec": att_samples[i + 1]["t_sec"],
                "motion_delta": delta,
                "ok": moved,
            })
            if not moved:
                for s in samples:
                    if s["t_sec"] == att_samples[i + 1]["t_sec"]:
                        s["ok"] = False
                        s["issues"] = list(s.get("issues") or []) + [
                            f"no scroll/zoom motion {att_samples[i]['t_sec']:.0f}s→"
                            f"{att_samples[i + 1]['t_sec']:.0f}s (delta={delta:.3f})"
                        ]

    fails = [s for s in samples if not s["ok"]]
    inline_fails = [s for s in samples if not s.get("spoken_inline_ok")]
    chart_fails = [s for s in samples if not s.get("chart_inline_ok")]
    plain_fails = [s for s in samples if not s.get("plain_language_ok")]
    motion_ok = all(m["ok"] for m in motion_checks) if motion_checks else True
    overall_ok = len(fails) == 0 and motion_ok

    spoken_visual: dict[str, Any] = {}
    if srt.is_file():
        from praisonaippt.daily_single.spoken_visual_sync import validate_spoken_visual_sync

        try:
            sv = validate_spoken_visual_sync(project)
            spoken_visual = {
                "ok": sv.get("ok"),
                "charts_pass": sv.get("charts_pass"),
                "charts_total": sv.get("charts_total"),
                "coverage_pass": sv.get("coverage_pass"),
                "coverage_total": sv.get("coverage_total"),
                "plain_language_ok": sv.get("plain_language_ok"),
                "issues": (sv.get("issues") or [])[:8],
            }
        except FileNotFoundError:
            pass

    report = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hook_duration_sec": round(hook_dur, 2),
        "attention_sec": round(att_dur, 2),
        "sample_cadence": "1s for first 5s, then 2s until hook end",
        "seconds_checked": len(sample_times),
        "planned_file": att_cue.get("file") if skip_scroll else SCROLL_FILENAME,
        "skip_canonical_scroll": skip_scroll,
        "samples_total": len(samples),
        "samples_pass": len(samples) - len(fails),
        "spoken_inline_pass": len(samples) - len(inline_fails),
        "spoken_inline_fail": len(inline_fails),
        "chart_inline_pass": len(samples) - len(chart_fails),
        "chart_inline_fail": len(chart_fails),
        "plain_language_pass": len(samples) - len(plain_fails),
        "plain_language_fail": len(plain_fails),
        "ok": overall_ok,
        "min_pixel_sim": MIN_PIXEL_SIM,
        "min_motion_delta": MIN_MOTION,
        "motion_checks": motion_checks,
        "motion_ok": motion_ok,
        "spoken_visual": spoken_visual,
        "samples": samples,
        "frames_dir": str(frames_dir.relative_to(project.root)),
    }
    out = project.merge_dir / "qa" / "hook_attention_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    build_hook_montage_plan(project)
    return report

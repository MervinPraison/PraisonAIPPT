"""Hook montage clock — pictures must change when the words change (non-developer sync)."""
from __future__ import annotations

import json
from typing import Any

from praisonaippt.daily_single.cue_slide_sync import _parse_segment_srt
from praisonaippt.daily_single.display_sync import VisualWindow, build_visual_timeline, parse_srt
from praisonaippt.daily_single.hook_montage import (
    build_hook_montage_plan,
    hook_visual_windows,
    load_hook_montage_plan,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.media import ffprobe_duration

MAX_BRIDGE_OVERLAP_SEC = 0.35
MAX_OVERVIEW_DRIFT_SEC = 1.0
VIDEO_FIRST_BRIDGE_FILES = frozenset({
    "heygen.mp4",
    "canonical-scroll.mp4",
    "claudeai-launch.mp4",
    "demo-launch.mp4",
    "brand-bumper-1080p-hevc.mp4",
    "x-claudeai-launch.mp4",
    "x-claudeai-safeguards.mp4",
    "x-chrissgpt-minecraft.mp4",
    "x-chrissgpt-pokemon.mp4",
    "x-demo-deveshcodes-blackhole.mp4",
    "x-pootlepress-wp-theme.mp4",
    "x-trq212-edit-2064826394589442448.mp4",
    "x-trq212-edit-2064828193446740023.mp4",
})


def _hook_rows(project: DailySingleProject) -> list[tuple[float, float, str]]:
    seg_srt = project.segments_dir / "00-hook" / "segment.srt"
    if seg_srt.is_file():
        return _parse_segment_srt(seg_srt)
    merged = project.merge_dir / "final.srt"
    if not merged.is_file():
        return []
    cues = parse_srt(merged)
    tl = project.merge_dir / "timeline.json"
    t0 = 0.0
    if tl.is_file():
        for row in json.loads(tl.read_text(encoding="utf-8")).get("segments") or []:
            if row.get("id") == "00-hook":
                t0 = float(row.get("start_sec") or 0)
                break
    return [
        (float(c["start_sec"]) - t0, float(c["end_sec"]) - t0, c.get("text") or "")
        for c in cues
        if float(c["start_sec"]) >= t0 - 0.05
    ]


def validate_montage_clock(project: DailySingleProject) -> tuple[bool, list[str], dict[str, Any]]:
    """Fail when intro montage overlaps the bridge or drifts from spoken timing."""
    issues: list[str] = []
    try:
        beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        beat_map = {}
    variant = str(beat_map.get("variant") or "")
    min_cues = 4 if variant == "social-comparison" else 5

    plan = load_hook_montage_plan(project)
    ok_cues = [c for c in plan.get("cues") or [] if c.get("ok")]
    if len(ok_cues) < min_cues:
        issues.append(
            f"Hook montage needs {min_cues} pictures resolved — only {len(ok_cues)} are ready"
        )

    hook_script = project.segment_script("00-hook")
    script = hook_script.read_text(encoding="utf-8") if hook_script.is_file() else ""
    mp3 = project.segment_narration("00-hook")
    hook_dur = ffprobe_duration(mp3) if mp3.is_file() else 30.0

    build_hook_montage_plan(project)
    raw = hook_visual_windows(0.0, hook_dur, script, plan.get("cues") or [], project=project)
    overview: list[VisualWindow] = []
    bridge: list[VisualWindow] = []
    for item in raw:
        w = VisualWindow(
            float(item["start"]),
            float(item["end"]),
            item.get("beat", "00-hook"),
            item.get("visual", ""),
            item.get("file", ""),
            section=item.get("section", ""),
            script_fragment=item.get("script_fragment", ""),
        )
        if w.section == "overview":
            overview.append(w)
        elif w.section == "bridge":
            bridge.append(w)

    rows = _hook_rows(project)
    if len(rows) >= 3:
        overview_speech_end = rows[1][1]
        overview_visual_end = max((w.end_sec for w in overview), default=0.0)
        drift = overview_visual_end - overview_speech_end
        if drift > MAX_OVERVIEW_DRIFT_SEC:
            issues.append(
                f"Intro pictures run {drift:.1f}s past the spoken overview — "
                f"viewers hear 'Let's get started' while the wrong slide is still up"
            )
        bridge_start = rows[2][0]
        last_overview = max((w.end_sec for w in overview), default=0.0)
        if last_overview > bridge_start + MAX_BRIDGE_OVERLAP_SEC:
            issues.append(
                f"Last montage slide ends at {last_overview:.1f}s but bridge starts at "
                f"{bridge_start:.1f}s — overlap confuses the hand-off"
            )
        for w in bridge:
            if w.file not in VIDEO_FIRST_BRIDGE_FILES:
                issues.append(
                    f"After 'Let's get started' bridge should be motion or presenter — got {w.file}"
                )

    for c in plan.get("cues") or []:
        if not c.get("ok"):
            issues.append(f"Missing montage picture: {c.get('file', '?')}")
        fn = (c.get("file") or "").lower()
        if (
            fn.startswith("v2-")
            or "beat1-launch-summary" in fn
            or "inequality-ladder" in fn
            or "social-capture-reddit" in fn
            or "demo-scroll" in fn
            or "demo-pokemon" in fn
            or "demo-solar" in fn
            or (fn.endswith(".png") and fn not in ("linkedin-cintas-frame.png",))
        ):
            issues.append(
                f"Hook montage must not use programmatic slide {c.get('file')} — use video clips"
            )

    return len(issues) == 0, issues, {
        "overview_windows": len(overview),
        "resolved_cues": len(ok_cues),
        "hook_dur_sec": round(hook_dur, 2),
    }

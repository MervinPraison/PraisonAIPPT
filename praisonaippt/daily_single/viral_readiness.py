"""Composite viral-readiness gate — proof density, comparisons, hook motion."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.display_sync import (
    VisualWindow,
    build_visual_timeline,
    parse_srt,
    visual_at,
)
from praisonaippt.daily_single.engagement_audit import validate_engagement_assets
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.publish_quality_config import asset_tier, engagement_config
from praisonaippt.daily_single.slide_design_audit import validate_slide_design
from praisonaippt.daily_single.youtube_quality import validate_compelling_hook

COMPARISON_MARKERS = ("benchmark", "pricing", "compare", "table", "stat", "tier", "social-capture")


def _hook_has_motion(windows: list[VisualWindow], hook_end: float) -> bool:
    for w in windows:
        if w.start_sec >= hook_end:
            break
        if w.file.endswith(".mp4") and w.file not in ("heygen.mp4",):
            return True
    return False


def _proof_cue_count(project: DailySingleProject, windows: list[VisualWindow]) -> int:
    srt = project.merge_dir / "final.srt"
    if not srt.is_file():
        return 0
    count = 0
    for cue in parse_srt(srt):
        mid = (float(cue["start_sec"]) + float(cue["end_sec"])) / 2
        vis = visual_at(windows, mid)
        if not vis or vis.beat in ("00-hook", "99-outro"):
            continue
        tier = asset_tier(vis.file)
        if tier in ("motion", "social-capture", "chart", "gpt-image"):
            count += 1
    return count


def _comparison_beats(windows: list[VisualWindow]) -> set[str]:
    beats: set[str] = set()
    for w in windows:
        if w.beat in ("00-hook", "99-outro"):
            continue
        fn = w.file.lower()
        if any(m in fn for m in COMPARISON_MARKERS):
            beats.add(w.beat)
    return beats


def validate_viral_readiness(project: DailySingleProject) -> dict[str, Any]:
    cfg = engagement_config(project)
    slide = validate_slide_design(project)
    engage = validate_engagement_assets(project)
    issues: list[str] = list(slide.get("issues") or []) + list(engage.get("issues") or [])

    windows = build_visual_timeline(project)
    hook_script = project.segment_script("00-hook")
    hook_text = hook_script.read_text(encoding="utf-8") if hook_script.is_file() else ""
    hook_cues = split_caption_cues(hook_text)
    cue_map = [{"spoken": c} for c in hook_cues[:3]]
    hook_ok, hook_issues = validate_compelling_hook(cue_map)
    if not hook_ok:
        issues.extend([f"hook: {i}" for i in hook_issues])

    hook_end = 25.0
    tl_path = project.merge_dir / "timeline.json"
    if tl_path.is_file():
        for row in json.loads(tl_path.read_text(encoding="utf-8")).get("segments") or []:
            if row.get("id") == "00-hook":
                hook_end = float(row.get("duration_sec") or 25)
                break
    if not _hook_has_motion(windows, hook_end):
        issues.append("hook: no MP4 motion in first segment (scroll or demo clip required)")

    proof = _proof_cue_count(project, windows)
    min_proof = int(cfg.get("min_proof_cues", 6))
    if proof < min_proof:
        issues.append(f"proof density: {proof} cues with MP4/social/chart/gpt-image < {min_proof}")

    comp_beats = _comparison_beats(windows)
    min_comp = int(cfg.get("min_comparison_beats", 1))
    if len(comp_beats) < min_comp:
        issues.append(f"comparison beats: {len(comp_beats)} < {min_comp} required")

    hook_files = {w.file for w in windows if w.beat == "00-hook" and w.section != "bridge"}
    if len(hook_files) < 2:
        issues.append("hook: fewer than 2 distinct visuals in montage/attention")

    ok = len(issues) == 0 and slide.get("ok") and engage.get("ok")
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "proof_cue_count": proof,
        "comparison_beats": sorted(comp_beats),
        "hook_motion": _hook_has_motion(windows, hook_end),
        "hook_distinct_visuals": len(hook_files),
        "slide_design_ok": slide.get("ok"),
        "engagement_ok": engage.get("ok"),
        "thresholds": cfg,
        "issues": issues,
    }
    out = project.merge_dir / "viral_readiness_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

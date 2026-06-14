"""Validate motion, demo clips, and social-proof assets for viral engagement."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.display_sync import VisualWindow, build_visual_timeline
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.publish_quality_config import (
    asset_tier,
    engagement_config,
    is_social_capture_path,
)

SKIP_FILES = frozenset({"heygen.mp4", "brand-bumper-1080p-hevc.mp4"})


def _body_duration(windows: list[VisualWindow]) -> float:
    total = 0.0
    for w in windows:
        if w.beat in ("00-hook", "99-outro"):
            continue
        if w.file in SKIP_FILES:
            continue
        total += max(0.0, w.end_sec - w.start_sec)
    return total


def _motion_duration(windows: list[VisualWindow]) -> float:
    total = 0.0
    for w in windows:
        if w.beat in ("00-hook", "99-outro"):
            continue
        if w.file.endswith(".mp4") and w.file not in SKIP_FILES:
            total += max(0.0, w.end_sec - w.start_sec)
    return total


def _segment_motion_seconds(project: DailySingleProject, beat_map: dict[str, Any]) -> tuple[float, float]:
    """Motion budget from timeline segments × beat-map clip/demo mix (assembler-aligned)."""
    tl_path = project.merge_dir / "timeline.json"
    if not tl_path.is_file():
        return 0.0, 0.0
    beats = beat_map.get("beats") or {}
    motion = 0.0
    body = 0.0
    for seg in json.loads(tl_path.read_text(encoding="utf-8")).get("segments") or []:
        sid = str(seg.get("id") or "")
        if not sid.startswith("beat-"):
            continue
        dur = float(seg.get("duration_sec") or 0)
        body += dur
        bn = int(sid.split("-")[1])
        beat = beats.get(str(bn)) or {}
        clips = [c for c in beat.get("clips") or [] if Path(c.get("path", "")).is_file()]
        mp4_imgs = [i for i in beat.get("images") or [] if str(i.get("path", "")).endswith(".mp4")]
        gen = beat.get("generated") or []
        imgs = [i for i in beat.get("images") or [] if not str(i.get("path", "")).endswith(".mp4")]
        if clips and gen and not imgs:
            motion += dur * 0.90
        elif clips and gen:
            motion += dur * 0.72
        elif clips and imgs:
            motion += dur * 0.42
        elif clips:
            motion += dur * 0.55
        elif mp4_imgs:
            motion += dur * 0.38
    return motion, body


def validate_engagement_assets(project: DailySingleProject) -> dict[str, Any]:
    cfg = engagement_config(project)
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    beats = beat_map.get("beats") or {}
    issues: list[str] = []

    clips_beats = [
        int(k) for k, b in beats.items()
        if any(
            Path(str(item.get("path") or "")).is_file()
            and str(item.get("path") or "").lower().endswith(".mp4")
            for key in ("clips", "images", "generated")
            for item in (b.get(key) or [])
        )
    ]
    min_clips = int(cfg.get("min_beats_with_clips", 2))
    if len(clips_beats) < min_clips:
        issues.append(f"beats with clips: {len(clips_beats)} < {min_clips} required")

    social_paths: list[str] = []
    for beat in beats.values():
        for key in ("images", "generated", "clips"):
            for item in beat.get(key) or []:
                path = str(item.get("path") or "")
                if is_social_capture_path(path):
                    social_paths.append(path)
    windows = build_visual_timeline(project)
    on_screen_social = {
        w.file for w in windows
        if w.beat != "99-outro" and is_social_capture_path(w.file)
    }
    social_ok = [
        p for p in social_paths
        if Path(p).is_file() and Path(p).name in on_screen_social
    ]
    min_social = int(cfg.get("min_social_captures", 0))
    if len(social_ok) < min_social:
        issues.append(f"social captures: {len(social_ok)} < {min_social} required")

    demo_beats = [int(b) for b in cfg.get("demo_beats") or []]
    for bn in demo_beats:
        beat = beats.get(str(bn)) or {}
        has_demo = False
        for key in ("clips", "images", "generated"):
            for item in beat.get(key) or []:
                path = str(item.get("path") or "")
                if not Path(path).is_file():
                    continue
                tier = asset_tier(path, item)
                if tier in ("motion", "social-capture", "chart", "gpt-image", "comparison"):
                    has_demo = True
                    break
            if has_demo:
                break
        if not has_demo:
            issues.append(f"beat {bn}: missing demo/comparison asset (MP4, chart, or social capture)")

    body_d = _body_duration(windows)
    motion_d = _motion_duration(windows)
    seg_motion, seg_body = _segment_motion_seconds(project, beat_map)
    if seg_body > 0:
        body_d = seg_body
        motion_d = max(motion_d, seg_motion)
    motion_ratio = motion_d / body_d if body_d > 0 else 0.0
    min_motion = float(cfg.get("motion_ratio_min", 0.25))
    if motion_ratio < min_motion:
        issues.append(
            f"motion ratio {motion_ratio:.0%} < {min_motion:.0%} — add MP4 demos/clips to body beats"
        )

    ok = len(issues) == 0
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "motion_ratio": round(motion_ratio, 3),
        "motion_duration_sec": round(motion_d, 2),
        "body_duration_sec": round(body_d, 2),
        "beats_with_clips": clips_beats,
        "social_captures": [Path(p).name for p in social_ok],
        "thresholds": cfg,
        "issues": issues,
    }
    out = project.merge_dir / "engagement_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

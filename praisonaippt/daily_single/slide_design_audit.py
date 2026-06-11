"""Validate slide design tier — reject programmatic text_slide-heavy body beats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.display_sync import VisualWindow, build_visual_timeline
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.publish_quality_config import asset_tier, slide_design_config

SKIP_FILES = frozenset({"heygen.mp4", "canonical-scroll.mp4", "brand-bumper-1080p-hevc.mp4"})


def _body_windows(windows: list[VisualWindow]) -> list[VisualWindow]:
    out: list[VisualWindow] = []
    for w in windows:
        if w.beat in ("00-hook", "99-outro"):
            continue
        if w.file in SKIP_FILES or w.section == "bridge":
            continue
        if not w.file.endswith(".png"):
            continue
        if w.end_sec - w.start_sec < 0.5:
            continue
        out.append(w)
    return out


def validate_slide_design(project: DailySingleProject) -> dict[str, Any]:
    cfg = slide_design_config(project)
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    tier_by_file: dict[str, str] = {}
    for beat in (beat_map.get("beats") or {}).values():
        for key in ("images", "generated", "clips"):
            for item in beat.get(key) or []:
                path = str(item.get("path") or "")
                if path:
                    tier_by_file[Path(path).name] = asset_tier(path, item)

    windows = build_visual_timeline(project)
    body = _body_windows(windows)
    issues: list[str] = []
    tier_dur: dict[str, float] = {}
    total_dur = 0.0
    rows: list[dict[str, Any]] = []

    for w in body:
        dur = w.end_sec - w.start_sec
        tier = tier_by_file.get(w.file) or asset_tier(w.file)
        tier_dur[tier] = tier_dur.get(tier, 0.0) + dur
        total_dur += dur
        rows.append({
            "file": w.file,
            "beat": w.beat,
            "tier": tier,
            "duration_sec": round(dur, 2),
        })

    text_slide_ratio = tier_dur.get("text_slide", 0.0) / total_dur if total_dur else 0.0
    gpt_ratio = tier_dur.get("gpt-image", 0.0) / total_dur if total_dur else 0.0
    max_text = float(cfg.get("text_slide_max_body_ratio", 0.55))
    min_gpt = float(cfg.get("min_gpt_image_ratio", 0.25))

    if text_slide_ratio > max_text:
        issues.append(
            f"text_slide tier {text_slide_ratio:.0%} of body PNG time > {max_text:.0%} max — "
            "use gpt-image or social captures"
        )
    if gpt_ratio < min_gpt and total_dur > 30:
        issues.append(
            f"gpt-image tier {gpt_ratio:.0%} < {min_gpt:.0%} min — slides look programmatic"
        )

    ok = len(issues) == 0
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "text_slide_body_ratio": round(text_slide_ratio, 3),
        "gpt_image_body_ratio": round(gpt_ratio, 3),
        "body_png_duration_sec": round(total_dur, 2),
        "tier_durations": {k: round(v, 2) for k, v in tier_dur.items()},
        "thresholds": cfg,
        "windows": rows[:40],
        "issues": issues,
    }
    out = project.merge_dir / "slide_design_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

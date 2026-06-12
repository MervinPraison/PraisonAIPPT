"""Hook montage validators — June cross-check for daily_single."""
from __future__ import annotations

import json
from typing import Any

from praisonaippt.daily_single.display_sync import HOOK_MONTAGE_MIN_ALIGNMENT, VisualWindow, build_visual_timeline
from praisonaippt.daily_single.hook_montage import load_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject

from praisonaippt.daily_single.publish_quality_config import beat_map_variant

MIN_MONTAGE_CUES = 5


def _min_montage_cues(project: DailySingleProject) -> int:
    if beat_map_variant(project) == "social-comparison":
        return 4
    return MIN_MONTAGE_CUES


def _overview_windows(windows: list[VisualWindow]) -> list[VisualWindow]:
    return [w for w in windows if w.beat == "00-hook" and w.section == "overview"]


def _min_distinct_visuals(project: DailySingleProject, files: set[str]) -> int:
    mp4 = sum(1 for f in files if f.endswith(".mp4"))
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        if bm.get("asset_policy") == "video-first-local" and mp4 >= 3:
            return 4
    except (OSError, json.JSONDecodeError):
        pass
    return MIN_MONTAGE_CUES


def validate_hook_montage(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    plan = load_hook_montage_plan(project)
    windows = build_visual_timeline(project)
    overview = _overview_windows(windows)
    issues: list[str] = []

    min_cues = _min_montage_cues(project)
    ok_cues = [c for c in plan.get("cues") or [] if c.get("ok")]
    if len(ok_cues) < min_cues:
        issues.append(f"montage plan has {len(ok_cues)} assets (need {min_cues})")
    if len(overview) < min_cues:
        issues.append(f"timeline has {len(overview)} overview windows (need {min_cues})")

    files = {w.file for w in overview}
    need_distinct = _min_distinct_visuals(project, files)
    if len(files) < need_distinct:
        issues.append(f"only {len(files)} distinct overview visuals (need {need_distinct})")
    if overview and all(w.file == "claudeai-launch.mp4" for w in overview):
        issues.append("overview uses launch B-roll only — montage missing")

    if beat_map_variant(project) != "social-comparison":
        launch_only = [w for w in overview if w.file == "claudeai-launch.mp4"]
        if launch_only:
            issues.append(f"{len(launch_only)} overview windows still on launch B-roll")

    missing_paths = [c["file"] for c in ok_cues if not c.get("path")]
    if missing_paths:
        issues.append(f"missing asset paths: {', '.join(missing_paths[:3])}")

    report = {
        "ok": len(issues) == 0,
        "issues": issues,
        "min_cues": _min_montage_cues(project),
        "plan_cues": len(ok_cues),
        "overview_windows": len(overview),
        "distinct_files": sorted(files),
        "min_alignment": HOOK_MONTAGE_MIN_ALIGNMENT,
        "cues": plan.get("cues") or [],
    }
    return len(issues) == 0, report

"""Hook montage validators — June cross-check for daily_single."""
from __future__ import annotations

from typing import Any

from praisonaippt.daily_single.display_sync import HOOK_MONTAGE_MIN_ALIGNMENT, VisualWindow, build_visual_timeline
from praisonaippt.daily_single.hook_montage import load_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject

MIN_MONTAGE_CUES = 5


def _overview_windows(windows: list[VisualWindow]) -> list[VisualWindow]:
    return [w for w in windows if w.beat == "00-hook" and w.section == "overview"]


def validate_hook_montage(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    plan = load_hook_montage_plan(project)
    windows = build_visual_timeline(project)
    overview = _overview_windows(windows)
    issues: list[str] = []

    ok_cues = [c for c in plan.get("cues") or [] if c.get("ok")]
    if len(ok_cues) < MIN_MONTAGE_CUES:
        issues.append(f"montage plan has {len(ok_cues)} assets (need {MIN_MONTAGE_CUES})")
    if len(overview) < MIN_MONTAGE_CUES:
        issues.append(f"timeline has {len(overview)} overview windows (need {MIN_MONTAGE_CUES})")

    files = {w.file for w in overview}
    if len(files) < MIN_MONTAGE_CUES:
        issues.append(f"only {len(files)} distinct overview visuals")
    if overview and all(w.file == "claudeai-launch.mp4" for w in overview):
        issues.append("overview uses launch B-roll only — montage missing")

    launch_only = [w for w in overview if w.file == "claudeai-launch.mp4"]
    if launch_only:
        issues.append(f"{len(launch_only)} overview windows still on launch B-roll")

    missing_paths = [c["file"] for c in ok_cues if not c.get("path")]
    if missing_paths:
        issues.append(f"missing asset paths: {', '.join(missing_paths[:3])}")

    report = {
        "ok": len(issues) == 0,
        "issues": issues,
        "min_cues": MIN_MONTAGE_CUES,
        "plan_cues": len(ok_cues),
        "overview_windows": len(overview),
        "distinct_files": sorted(files),
        "min_alignment": HOOK_MONTAGE_MIN_ALIGNMENT,
        "cues": plan.get("cues") or [],
    }
    return len(issues) == 0, report

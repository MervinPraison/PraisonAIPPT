"""s23 — clip trim bounds and source cut suggestions."""
from __future__ import annotations

from praisonaippt.daily_single.clip_trim_audit import validate_clip_trims
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s23_clip_trim_range(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx=None,
) -> StageReport:
    report = validate_clip_trims(project)
    checks = [
        CheckResult(
            id="clip_trim_bounds",
            ok=bool(report["ok"]),
            severity="info" if report["ok"] else "error",
            message="; ".join(report.get("issues") or []) or "clip trim ranges OK",
        )
    ]
    return StageReport(
        id="s23-clip-trim-range",
        ok=bool(report["ok"]),
        required=required,
        when=when,
        checks=checks,
        details=report,
    )

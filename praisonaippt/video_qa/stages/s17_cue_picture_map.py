"""Stage s17 — cue-to-picture map (safeguard beat and similar)."""
from __future__ import annotations

from praisonaippt.daily_single.cue_map_audit import validate_cue_picture_map
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s17_cue_picture_map(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_assemble",
    ctx: SuiteContext | None = None,
) -> StageReport:
    ok, issues, details = validate_cue_picture_map(project)
    checks = [
        CheckResult(
            id=f"cue_map_{i}",
            ok=False,
            severity="error" if required else "warn",
            message=msg,
        )
        for i, msg in enumerate(issues)
    ]
    if ok:
        checks.append(CheckResult(
            id="cue_picture_map",
            ok=True,
            severity="info",
            message="Every safeguard cue has a matching on-screen picture",
        ))
    return StageReport(
        id="s17-cue-picture-map",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details=details,
    )

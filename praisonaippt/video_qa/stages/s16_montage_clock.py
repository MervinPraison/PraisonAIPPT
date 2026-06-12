"""Stage s16 — hook montage clock (pictures change when words change)."""
from __future__ import annotations

from praisonaippt.daily_single.montage_clock_audit import validate_montage_clock
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s16_montage_clock(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_assemble",
    ctx: SuiteContext | None = None,
) -> StageReport:
    ok, issues, details = validate_montage_clock(project)
    checks = [
        CheckResult(
            id=f"montage_{i}",
            ok=False,
            severity="error" if required else "warn",
            message=msg,
        )
        for i, msg in enumerate(issues)
    ]
    if ok:
        checks.append(CheckResult(
            id="montage_clock",
            ok=True,
            severity="info",
            message="Hook montage timing matches spoken overview and bridge",
        ))
    return StageReport(
        id="s16-montage-clock",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details=details,
    )

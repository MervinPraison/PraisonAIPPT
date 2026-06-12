"""Stage s19 — chart script contract (name charts in plain words before they appear)."""
from __future__ import annotations

from praisonaippt.daily_single.chart_script_audit import validate_chart_script_contract
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s19_chart_script(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    ok, issues, details = validate_chart_script_contract(project)
    checks = [
        CheckResult(
            id=f"chart_script_{i}",
            ok=False,
            severity="error" if required else "warn",
            message=msg,
        )
        for i, msg in enumerate(issues)
    ]
    if ok:
        checks.append(CheckResult(
            id="chart_script_contract",
            ok=True,
            severity="info",
            message="Scripts name charts and tables in plain language",
        ))
    return StageReport(
        id="s19-chart-script",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details=details,
    )

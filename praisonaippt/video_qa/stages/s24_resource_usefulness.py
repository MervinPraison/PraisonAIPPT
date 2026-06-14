"""s24 — related resource informational usefulness vs main video topic."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.resource_usefulness_audit import validate_resource_usefulness
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s24_resource_usefulness(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx=None,
) -> StageReport:
    report = validate_resource_usefulness(project)
    checks = [
        CheckResult(
            id="resource_usefulness",
            ok=bool(report["ok"]),
            severity="info" if report["ok"] else "error",
            message="; ".join(report.get("issues") or []) or "resource catalog usefulness OK",
        )
    ]
    return StageReport(
        id="s24-resource-usefulness",
        ok=bool(report["ok"]),
        required=required,
        when=when,
        checks=checks,
        details=report,
    )

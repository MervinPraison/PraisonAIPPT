"""Stage s15 — viral readiness composite gate."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.viral_readiness import validate_viral_readiness
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s15_viral_readiness(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    report = validate_viral_readiness(project)
    ok = bool(report.get("ok"))
    checks = [
        CheckResult(
            id="viral_readiness",
            ok=ok,
            severity="error" if required and not ok else ("warn" if not ok else "info"),
            message=(
                f"viral readiness OK (proof {report.get('proof_cue_count', 0)} cues)"
                if ok
                else "; ".join((report.get("issues") or [])[:3])
            ),
        )
    ]
    return StageReport(id="s15-viral-readiness", ok=ok or not required, required=required, when=when, checks=checks, details=report)

"""Stage s14 — engagement / motion asset gate."""
from __future__ import annotations

from praisonaippt.daily_single.engagement_audit import validate_engagement_assets
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s14_engagement(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    report = validate_engagement_assets(project)
    ok = bool(report.get("ok"))
    checks = [
        CheckResult(
            id="engagement",
            ok=ok,
            severity="error" if required and not ok else ("warn" if not ok else "info"),
            message=(
                f"engagement OK (motion {report.get('motion_ratio', 0):.0%}, "
                f"clips beats {len(report.get('beats_with_clips') or [])})"
                if ok
                else "; ".join(report.get("issues") or [])[:200]
            ),
        )
    ]
    return StageReport(id="s14-engagement", ok=ok or not required, required=required, when=when, checks=checks, details=report)

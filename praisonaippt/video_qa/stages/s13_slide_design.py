"""Stage s13 — slide design tier gate."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.slide_design_audit import validate_slide_design
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s13_slide_design(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    report = validate_slide_design(project)
    ok = bool(report.get("ok"))
    checks = [
        CheckResult(
            id="slide_design",
            ok=ok,
            severity="error" if required and not ok else ("warn" if not ok else "info"),
            message=(
                f"slide design OK (gpt {report.get('gpt_image_body_ratio', 0):.0%}, "
                f"text_slide {report.get('text_slide_body_ratio', 0):.0%})"
                if ok
                else "; ".join(report.get("issues") or [])[:200]
            ),
        )
    ]
    return StageReport(id="s13-slide-design", ok=ok or not required, required=required, when=when, checks=checks, details=report)

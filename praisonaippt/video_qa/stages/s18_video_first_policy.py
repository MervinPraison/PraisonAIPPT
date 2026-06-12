"""Stage s18 — video-first policy (local clips, plain language, no mythos slides)."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.video_first_audit import validate_video_first_policy
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s18_video_first_policy(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    ok, issues, details = validate_video_first_policy(project)
    if details.get("skipped"):
        return StageReport(
            id="s18-video-first-policy",
            ok=True,
            required=False,
            when=when,
            checks=[CheckResult(
                id="video_first_skip",
                ok=True,
                severity="info",
                message="Not a video-first build — policy check skipped",
            )],
            details=details,
        )
    checks = [
        CheckResult(
            id=f"video_first_{i}",
            ok=False,
            severity="error" if required else "warn",
            message=msg,
        )
        for i, msg in enumerate(issues)
    ]
    if ok:
        checks.append(CheckResult(
            id="video_first_policy",
            ok=True,
            severity="info",
            message="Video-first assets and plain-language scripts OK",
        ))
    return StageReport(
        id="s18-video-first-policy",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details=details,
    )

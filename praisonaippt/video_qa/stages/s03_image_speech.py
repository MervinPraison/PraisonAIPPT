"""Stage s03 — image vs speech (post display sync, cached per suite)."""
from __future__ import annotations

from praisonaippt.daily_single.display_sync import MIN_ALIGNMENT, validate_display_sync
from praisonaippt.daily_single.spoken_visual_sync import validate_spoken_visual_sync
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s03_image_speech(
    project: DailySingleProject,
    *,
    phase: str = "post_render",
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []

    if phase == "pre_metadata":
        checks.append(CheckResult(
            id="pre_build",
            ok=True,
            severity="info",
            message="pre-build metadata pass — run post_render after assemble",
        ))
        return StageReport(id="s03-image-speech", ok=True, required=False, when=when, checks=checks, details={"phase": phase})

    report = ctx.get_display_sync() if ctx else validate_display_sync(project)

    ok = bool(report.get("ok"))
    checks.append(CheckResult(
        id="display_sync",
        ok=ok,
        severity="error" if required else "warn",
        message=f"{report.get('cues_pass', 0)}/{report.get('cues_total', 0)} cues aligned",
        details={"min_alignment": report.get("min_alignment", MIN_ALIGNMENT)},
    ))
    fail_count = int(report.get("cues_fail") or 0)
    if fail_count:
        checks.append(CheckResult(
            id="cues_fail",
            ok=False,
            severity="error" if required else "warn",
            message=f"{fail_count} cue(s) below alignment threshold",
        ))

    spoken = validate_spoken_visual_sync(project)
    spoken_ok = bool(spoken.get("ok"))
    checks.append(CheckResult(
        id="spoken_visual_sync",
        ok=spoken_ok,
        severity="error" if required else "warn",
        message=(
            f"montage {spoken.get('montage_fragments_pass', 0)}/"
            f"{spoken.get('montage_fragments_total', 0)}, "
            f"windows {spoken.get('windows_pass', 0)}/{spoken.get('windows_total', 0)} inline"
        ),
        details={"issues": (spoken.get("issues") or [])[:5]},
    ))
    ok = ok and spoken_ok

    return StageReport(
        id="s03-image-speech",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"phase": phase},
    )

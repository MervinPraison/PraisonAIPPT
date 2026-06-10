"""Stage s09 — on-screen text vs spoken (via cached display sync)."""
from __future__ import annotations

from praisonaippt.daily_single.display_sync import validate_display_sync
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s09_on_screen_text(
    project: DailySingleProject,
    *,
    min_alignment: float = 0.35,
    required: bool = False,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    report = ctx.get_display_sync() if ctx else validate_display_sync(project)
    checks: list[CheckResult] = []
    weak: list[dict] = []

    for row in report.get("cue_map") or []:
        align = float(row.get("alignment") or 0)
        spoken = str(row.get("spoken") or "")
        if len(spoken.split()) >= 6 and align < min_alignment:
            weak.append(row)
        if str(row.get("file", "")).endswith(".png") and align < min_alignment:
            checks.append(CheckResult(
                id=f"png_cue_{row.get('cue')}",
                ok=False,
                severity="warn",
                message=f"PNG cue {row.get('cue')} alignment {align:.2f}",
            ))

    ok = len(weak) == 0
    checks.append(CheckResult(
        id="on_screen",
        ok=ok,
        severity="warn" if not required else ("error" if not ok else "info"),
        message=(
            f"on-screen text OK ({report.get('cues_total', 0)} cues)"
            if ok else f"{len(weak)} cue(s) below alignment {min_alignment}"
        ),
        details={"weak_count": len(weak)},
    ))

    return StageReport(
        id="s09-on-screen-text",
        ok=ok or not required,
        required=required,
        when=when,
        checks=checks,
        details={"weak_count": len(weak)},
    )

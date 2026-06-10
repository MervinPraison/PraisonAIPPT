"""Stage s00 — bookend gate before assemble."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s00_bookends(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_assemble",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []
    for label in ("00-hook", "99-outro"):
        script = project.segment_script(label)
        narration = project.segment_narration(label)
        heygen = project.segments_dir / label / "heygen.mp4"
        checks.append(CheckResult(
            id=f"{label}_script",
            ok=script.is_file(),
            severity="error" if required else "warn",
            message=f"{label} script present" if script.is_file() else f"missing {label}/script.md",
        ))
        checks.append(CheckResult(
            id=f"{label}_narration",
            ok=narration.is_file(),
            severity="error" if required else "warn",
            message=f"{label} narration present" if narration.is_file() else f"missing {label}/narration.mp3",
        ))
        checks.append(CheckResult(
            id=f"{label}_heygen",
            ok=heygen.is_file(),
            severity="error" if required else "warn",
            message=f"{label} heygen.mp4 present" if heygen.is_file() else f"missing {label}/heygen.mp4 — run bookend-media",
        ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(id="s00-bookends", ok=ok, required=required, when=when, checks=checks)

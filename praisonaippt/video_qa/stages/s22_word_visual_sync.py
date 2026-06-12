"""Stage s22 — word-level Whisper timings vs on-screen frames (VLM when needed)."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.word_visual_sync import validate_word_visual_sync
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s22_word_visual_sync(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "post_build",
    use_vlm: bool = True,
    **_: object,
) -> StageReport:
    report = validate_word_visual_sync(project, use_vlm=use_vlm)
    if report.get("skipped"):
        msg = str(report.get("error", "skipped"))
        stage_ok = not required
        return StageReport(
            id="s22-word-visual-sync",
            ok=stage_ok,
            required=required,
            when=when,
            checks=[CheckResult(
                id="skipped",
                ok=stage_ok,
                severity="error" if required else "info",
                message=msg,
            )],
            skipped=True,
        )
    ok = bool(report.get("ok"))
    checks = [
        CheckResult(
            id="word_samples",
            ok=ok,
            severity="error" if required else "warn",
            message=(
                f"{report.get('samples_pass', 0)}/{report.get('samples_total', 0)} word samples aligned "
                f"({report.get('vlm_calls', 0)} VLM checks)"
            ),
            details={"issues": (report.get("issues") or [])[:5]},
        ),
    ]
    if report.get("error"):
        checks.append(CheckResult(
            id="whisper_words",
            ok=False,
            severity="error" if required else "warn",
            message=str(report["error"]),
        ))
        ok = False
    return StageReport(
        id="s22-word-visual-sync",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"report": str(project.merge_dir / "word_visual_sync_report.json")},
    )

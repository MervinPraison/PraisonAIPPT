"""Stage s12 — hook attention seconds + error-page rejection (post-build)."""
from __future__ import annotations

from praisonaippt.daily_single.hook_attention_audit import run_hook_attention_audit
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s12_hook_attention(
    project: DailySingleProject,
    *,
    seconds: int = 5,
    required: bool = True,
    when: str = "post_build",
    ctx=None,
) -> StageReport:
    checks: list[CheckResult] = []
    try:
        report = run_hook_attention_audit(project, seconds=seconds)
    except FileNotFoundError as exc:
        checks.append(CheckResult(
            id="hook_attention",
            ok=False,
            severity="error" if required else "warn",
            message=str(exc)[:200],
        ))
        return StageReport(id="s12-hook-attention", ok=False, required=required, when=when, checks=checks)
    except RuntimeError as exc:
        checks.append(CheckResult(
            id="scroll_content",
            ok=False,
            severity="error" if required else "warn",
            message=str(exc)[:200],
        ))
        return StageReport(id="s12-hook-attention", ok=False, required=required, when=when, checks=checks)

    ok = bool(report.get("ok"))
    checks.append(CheckResult(
        id="hook_attention",
        ok=ok,
        severity="error" if required else "warn",
        message=(
            f"{report.get('samples_pass', 0)}/{report.get('samples_total', 0)} second-frames, "
            f"motion={report.get('motion_ok')}"
        ),
        details={"frames_dir": report.get("frames_dir"), "issues": [
            i for s in (report.get("samples") or []) for i in (s.get("issues") or [])
        ][:5]},
    ))
    return StageReport(
        id="s12-hook-attention",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details=report,
    )

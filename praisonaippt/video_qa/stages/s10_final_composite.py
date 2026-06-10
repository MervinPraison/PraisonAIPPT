"""Stage s10 — final composite (visual audit + sync idempotency + validate-all)."""
from __future__ import annotations

import os

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.sync_validation import run_sync_suite
from praisonaippt.daily_single.validation import validate_all
from praisonaippt.daily_single.visual_audit import run_visual_audit, validate_visual_audit
from praisonaippt.video_qa.adapters import load_protocol, mirror_legacy_report
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext
from praisonaippt.video_qa.degradation import qa_offline_mode


def run_s10_final_composite(
    project: DailySingleProject,
    *,
    sync_runs: int = 3,
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []
    protocol = load_protocol(project)
    va_cfg = protocol.get("visual_audit") or {}
    va_enabled = bool(va_cfg.get("enabled", True))
    use_vision = va_enabled and not qa_offline_mode() and bool(os.environ.get("OPENAI_API_KEY"))

    if va_enabled:
        run_visual_audit(
            project,
            interval=float(va_cfg.get("interval_sec", 5.0)),
            use_vision=use_vision,
            force=False,
        )
        ok_va, va_report = validate_visual_audit(project)
        va_legacy = project.merge_dir / "visual_audit_report.json"
        mirror_legacy_report(project, "s10-final-composite", va_legacy)
        checks.append(CheckResult(
            id="visual_audit",
            ok=ok_va,
            severity="error" if required else "warn",
            message=(
                f"visual audit {va_report.get('samples_pass', '?')}/"
                f"{va_report.get('samples_total', '?')}"
            ),
            details={"vision": va_report.get("vision_model", "off")},
        ))
    else:
        checks.append(CheckResult(
            id="visual_audit",
            ok=True,
            severity="info",
            message="visual audit disabled in protocol",
        ))

    sync_report = run_sync_suite(project, runs=max(1, sync_runs))
    sync_legacy = project.merge_dir / "sync_validation_report.json"
    mirror_legacy_report(project, "s10-final-composite", sync_legacy)
    checks.append(CheckResult(
        id="sync_suite",
        ok=bool(sync_report.get("ok")),
        severity="error" if required else "warn",
        message=f"sync {sync_report.get('runs')} runs idempotent={sync_report.get('idempotent')}",
        details={"summary": sync_report.get("summary")},
    ))

    ok_all, all_report = validate_all(project)
    all_legacy = project.root / "validation_report.json"
    mirror_legacy_report(project, "s10-final-composite", all_legacy)
    checks.append(CheckResult(
        id="validate_all",
        ok=ok_all,
        severity="error" if required else "warn",
        message="validate-all PASS" if ok_all else "; ".join(all_report.get("issues") or [])[:200],
    ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(
        id="s10-final-composite",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"sync_runs": sync_runs, "vision_enabled": use_vision},
    )

"""s21 — beat-map policy (banned assets, LinkedIn placement, clip diversity)."""
from __future__ import annotations

from praisonaippt.daily_single.beat_map_audit import validate_beat_map_policy
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s21_beat_map_policy(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx=None,
) -> StageReport:
    report = validate_beat_map_policy(project)
    checks = [
        CheckResult(
            id="beat_map_policy",
            ok=bool(report["ok"]),
            severity="info" if report["ok"] else "error",
            message="; ".join(report.get("issues") or []) or "beat-map policy OK",
        )
    ]
    return StageReport(
        id="s21-beat-map-policy",
        ok=bool(report["ok"]),
        required=required,
        when=when,
        checks=checks,
        details=report,
    )

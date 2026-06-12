"""QA suite runner — per-stage isolation and summary rollup."""
from __future__ import annotations

from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.adapters import export_vlm_timeline, load_protocol, write_stage_report, write_summary
from praisonaippt.video_qa.base import CheckResult, StageReport, SuiteReport
from praisonaippt.video_qa.config import DEFAULT_QA_STAGES
from praisonaippt.video_qa.context import SuiteContext
from praisonaippt.video_qa.degradation import detect_degradation, qa_offline_mode, stage_should_skip
from praisonaippt.video_qa.registry import run_registered_stage


def _stage_configs(protocol: dict[str, Any], when: str | None) -> list[dict[str, Any]]:
    qa = protocol.get("video_qa") or {}
    stages = qa.get("stages") or DEFAULT_QA_STAGES
    if when and when != "all":
        stages = [s for s in stages if s.get("when") == when]
    return stages


def _stage_key(cfg: dict[str, Any]) -> str:
    sid = str(cfg.get("id", ""))
    phase = cfg.get("phase")
    return f"{sid}:{phase}" if phase else sid


def _apply_degradation(report: StageReport, degradation: dict[str, Any]) -> StageReport:
    if report.degraded:
        degradation["whisper"] = degradation.get("whisper") or "missing_timestamps"
    return report


def _persist_stage(
    project: DailySingleProject,
    report: StageReport,
    *,
    phase: str | None,
) -> None:
    write_stage_report(project, report.id, report.to_dict(), phase=phase)


def run_stage(
    project: DailySingleProject,
    stage_id: str,
    *,
    phase: str | None = None,
    continue_on_fail: bool = True,
) -> StageReport:
    protocol = load_protocol(project)
    degradation = detect_degradation(project)
    ctx = SuiteContext.from_protocol(project, protocol, degradation)
    stages = _stage_configs(protocol, None)
    cfg = next((s for s in stages if s.get("id") == stage_id), {"id": stage_id})
    if phase:
        cfg = {**cfg, "phase": phase}
    elif cfg.get("phase"):
        phase = str(cfg.get("phase"))

    skip, reason = stage_should_skip(cfg, degradation)
    if skip:
        required = bool(cfg.get("required", True))
        report = StageReport(
            id=stage_id,
            ok=not required,
            required=required,
            when=str(cfg.get("when", "all")),
            skipped=True,
            checks=[CheckResult(
                id="skipped",
                ok=not required,
                severity="error" if required else "info",
                message=reason or "skipped",
            )],
            details={"skip_reason": reason, "stage_key": _stage_key(cfg)},
        )
        _persist_stage(project, report, phase=phase)
        return report

    try:
        report = run_registered_stage(stage_id, project, cfg, ctx=ctx)
    except Exception as exc:
        report = StageReport(
            id=stage_id,
            ok=False,
            required=bool(cfg.get("required", True)),
            when=str(cfg.get("when", "all")),
            checks=[],
            details={"exception": str(exc), "stage_key": _stage_key(cfg)},
        )
        _persist_stage(project, report, phase=phase)
        if not continue_on_fail:
            raise
        return report

    report = _apply_degradation(report, degradation)
    report.details["stage_key"] = _stage_key(cfg)
    _persist_stage(project, report, phase=phase)
    return report


def run_suite(
    project: DailySingleProject,
    *,
    when: str = "all",
    stages: list[str] | None = None,
    continue_on_fail: bool = True,
) -> SuiteReport:
    protocol = load_protocol(project)
    degradation = detect_degradation(project)
    ctx = SuiteContext.from_protocol(project, protocol, degradation)
    profile = protocol.get("profile") or "daily_single"
    configs = _stage_configs(protocol, when)

    if stages:
        configs = [c for c in configs if c.get("id") in stages]

    suite = SuiteReport(profile=profile, when=when, degradation=degradation)
    for cfg in configs:
        sid = str(cfg.get("id", ""))
        phase = cfg.get("phase")
        phase_str = str(phase) if phase else None
        skip, reason = stage_should_skip(cfg, degradation)
        if skip:
            required = bool(cfg.get("required", True))
            report = StageReport(
                id=sid,
                ok=not required,
                required=required,
                when=str(cfg.get("when", "all")),
                skipped=True,
                checks=[CheckResult(
                    id="skipped",
                    ok=not required,
                    severity="error" if required else "info",
                    message=reason or "skipped",
                )],
                details={"skip_reason": reason, "phase": phase, "stage_key": _stage_key(cfg)},
            )
            _persist_stage(project, report, phase=phase_str)
            suite.stages.append(report)
            continue
        try:
            report = run_registered_stage(sid, project, cfg, ctx=ctx)
        except Exception as exc:
            report = StageReport(
                id=sid,
                ok=False,
                required=bool(cfg.get("required", True)),
                when=str(cfg.get("when", "all")),
                details={"exception": str(exc), "phase": phase, "stage_key": _stage_key(cfg)},
            )
            _persist_stage(project, report, phase=phase_str)
            suite.stages.append(report)
            if not continue_on_fail:
                break
            continue
        report = _apply_degradation(report, degradation)
        report.details["stage_key"] = _stage_key(cfg)
        _persist_stage(project, report, phase=phase_str)
        suite.stages.append(report)

    from praisonaippt.daily_single.spoken_visual_gates import PHASE_GATES, run_phase_gates

    gate_whens = [when] if when != "all" else list(PHASE_GATES.keys())
    for gate_when in gate_whens:
        if gate_when not in PHASE_GATES:
            continue
        use_vlm = degradation.get("vlm") != "offline" and not qa_offline_mode()
        gate_ok, gate_detail = run_phase_gates(project, gate_when, use_vlm=use_vlm)
        suite.stages.append(StageReport(
            id=f"sdk-phase-gates-{gate_when}",
            ok=gate_ok,
            required=True,
            when=gate_when,
            checks=[CheckResult(
                id="phase_gates",
                ok=gate_ok,
                severity="error" if not gate_ok else "info",
                message=f"SDK A/V phase gates ({gate_when})",
                details=gate_detail,
            )],
        ))

    if when in ("post_build", "all"):
        export_vlm_timeline(project)

    write_summary(project, suite.to_dict())
    return suite

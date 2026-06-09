"""Run protocol-configured validation suite."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from ..project import SegmentVideoProject
from .base import SuiteReport, ValidatorReport
from .validators import REGISTRY


def default_validator_ids() -> list[dict]:
    return [
        {"id": "tools", "required": True},
        {"id": "protocol_stages", "required": False},
        {"id": "artifacts", "required": True},
        {"id": "hook_montage", "required": True},
        {"id": "script_policy", "required": True},
        {"id": "image_audit", "required": True, "run_fresh": True},
        {"id": "segment_sync", "required": True},
        {"id": "audio_loudness", "required": True},
        {"id": "merge_output", "required": True},
        {"id": "coverage", "required": False},
        {"id": "manual_assets", "required": False},
        {"id": "required_assets", "required": True, "fetch_canonical": True},
        {"id": "hook_speech_sync", "required": False},
        {"id": "display_sync", "required": True, "fetch_canonical": True},
    ]


def run_validation_suite(
    project: SegmentVideoProject,
    *,
    log: Callable[[str], None] | None = None,
    strict: bool = False,
) -> SuiteReport:
    """Execute all validators listed in protocol.validation_suite."""
    emit = log or (lambda _: None)
    protocol = project.load_protocol()
    cfg = protocol.get("validation_suite") or {}
    entries = cfg.get("validators") or default_validator_ids()

    suite = SuiteReport(schema_version=int(cfg.get("schema_version", 1)))
    required_failed = False

    for entry in entries:
        vid = entry.get("id")
        if not vid or vid not in REGISTRY:
            suite.validators.append(ValidatorReport(
                id=str(vid),
                ok=False,
                required=bool(entry.get("required", True)),
                checks=[],
            ))
            emit(f"  [FAIL] unknown validator: {vid}")
            required_failed = True
            continue

        fn = REGISTRY[vid]
        report = fn(project, protocol)
        report.required = bool(entry.get("required", report.required))
        suite.validators.append(report)

        mark = "OK" if report.ok else ("FAIL" if report.required else "WARN")
        n_bad = sum(1 for c in report.checks if not c.ok)
        emit(f"  [{mark}] {vid}: {n_bad} issue(s)")
        for check in report.checks:
            if not check.ok:
                emit(f"      - [{check.severity}] {check.message}")

        if report.required and not report.ok:
            required_failed = True

    suite.ok = not required_failed
    if strict and any(not v.ok for v in suite.validators):
        suite.ok = False

    return suite


def write_validation_report(project: SegmentVideoProject, suite: SuiteReport) -> Path:
    out = project.root / "validation_report.json"
    out.write_text(json.dumps(suite.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out

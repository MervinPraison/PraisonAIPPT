"""validate-all stage — run full protocol validation suite."""
from __future__ import annotations

from typing import Callable

from ..project import SegmentVideoProject
from ..validation.suite import run_validation_suite, write_validation_report


def run_validate_all(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
    strict: bool = False,
) -> int:
    emit = log or print
    emit("validate-all: running protocol validation suite…")
    suite = run_validation_suite(project, log=emit, strict=strict)
    out = write_validation_report(project, suite)
    summary = suite.to_dict()["summary"]
    emit(
        f"validate-all → {out} "
        f"({'PASS' if suite.ok else 'FAIL'}) "
        f"{summary.get('validators_passed')}/{summary.get('validators_run')} validators, "
        f"{summary.get('errors')} errors, {summary.get('warnings')} warnings"
    )
    if summary.get("failed_required"):
        emit(f"  failed required: {', '.join(summary['failed_required'])}")
    return 0 if suite.ok else 1

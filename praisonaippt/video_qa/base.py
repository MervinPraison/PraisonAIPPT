"""Shared QA report types."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warn", "info", "skip"]


@dataclass
class CheckResult:
    id: str
    ok: bool
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageReport:
    id: str
    ok: bool
    required: bool
    when: str
    checks: list[CheckResult] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    degraded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "id": self.id,
            "ok": self.ok,
            "required": self.required,
            "when": self.when,
            "skipped": self.skipped,
            "degraded": self.degraded,
            "checks": [c.to_dict() for c in self.checks],
            "details": self.details,
        }


@dataclass
class SuiteReport:
    schema_version: int = 1
    ok: bool = True
    profile: str = "daily_single"
    when: str = "all"
    stages: list[StageReport] = field(default_factory=list)
    degradation: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        errors = sum(
            1 for s in self.stages for c in s.checks if not c.ok and c.severity == "error"
        )
        warns = sum(
            1 for s in self.stages for c in s.checks if not c.ok and c.severity == "warn"
        )
        failed_required = [s.id for s in self.stages if s.required and not s.ok and not s.skipped]
        self.summary = {
            "stages_run": len(self.stages),
            "stages_passed": sum(1 for s in self.stages if s.ok or s.skipped),
            "errors": errors,
            "warnings": warns,
            "failed_required": failed_required,
        }
        self.ok = len(failed_required) == 0
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "profile": self.profile,
            "when": self.when,
            "degradation": self.degradation,
            "summary": self.summary,
            "stages": [s.to_dict() for s in self.stages],
        }

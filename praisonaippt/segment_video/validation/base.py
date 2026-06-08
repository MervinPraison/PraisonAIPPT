"""Validation suite types — protocol-driven, modular checks."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warn", "info"]


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
class ValidatorReport:
    id: str
    ok: bool
    required: bool
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ok": self.ok,
            "required": self.required,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass
class SuiteReport:
    schema_version: int = 1
    ok: bool = True
    validators: list[ValidatorReport] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        errors = sum(
            1 for v in self.validators for c in v.checks if not c.ok and c.severity == "error"
        )
        warns = sum(
            1 for v in self.validators for c in v.checks if not c.ok and c.severity == "warn"
        )
        failed_required = [v.id for v in self.validators if v.required and not v.ok]
        self.summary = {
            "validators_run": len(self.validators),
            "validators_passed": sum(1 for v in self.validators if v.ok),
            "errors": errors,
            "warnings": warns,
            "failed_required": failed_required,
        }
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "summary": self.summary,
            "validators": [v.to_dict() for v in self.validators],
        }

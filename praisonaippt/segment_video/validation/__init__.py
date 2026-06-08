"""Protocol-driven validation suite for segment-video projects."""

from .base import CheckResult, SuiteReport, ValidatorReport
from .suite import run_validation_suite, write_validation_report
from .validators import REGISTRY

__all__ = [
    "CheckResult",
    "REGISTRY",
    "SuiteReport",
    "ValidatorReport",
    "run_validation_suite",
    "write_validation_report",
]

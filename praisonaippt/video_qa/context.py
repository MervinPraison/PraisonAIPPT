"""Shared state for a QA suite run (cache + config)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.adapters import mirror_legacy_report


@dataclass
class SuiteContext:
    project: DailySingleProject
    protocol: dict[str, Any]
    degradation: dict[str, Any]
    display_sync: dict[str, Any] | None = None
    qa_cfg: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_protocol(cls, project: DailySingleProject, protocol: dict[str, Any], degradation: dict[str, Any]) -> SuiteContext:
        qa = protocol.get("video_qa") or {}
        return cls(project=project, protocol=protocol, degradation=degradation, qa_cfg=qa)

    def min_transcript_overlap(self) -> float:
        return float(self.qa_cfg.get("min_transcript_overlap", 0.35))

    def min_coverage_assets(self) -> int:
        return int(self.qa_cfg.get("min_coverage_assets_per_beat", 1))

    def get_display_sync(self) -> dict[str, Any]:
        if self.display_sync is not None:
            return self.display_sync
        from praisonaippt.daily_single.display_sync import validate_display_sync

        self.display_sync = validate_display_sync(self.project)
        legacy = self.project.merge_dir / "display_sync_report.json"
        mirror_legacy_report(self.project, "display_sync", legacy)
        return self.display_sync

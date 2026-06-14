"""Tests for on-screen table/chart claim vs actual pixels."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from praisonaippt.daily_single.visual_claim_audit import validate_visual_claims
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.display_sync import VisualWindow


def _project(tmp_path: Path) -> DailySingleProject:
    root = tmp_path / "p"
    research = tmp_path / "r"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    merge = root / "merge"
    merge.mkdir()
    (merge / "final.srt").write_text(
        "1\n00:01:08,190 --> 00:01:18,190\n"
        "On screen you see the routing table: when a prompt trips a safeguard.\n",
        encoding="utf-8",
    )
    (merge / "final.mp4").write_bytes(b"\x00")
    return DailySingleProject.from_root(root)


def test_routing_table_claim_on_safeguards_clip_fails(tmp_path: Path):
    project = _project(tmp_path)
    windows = [
        VisualWindow(68.0, 78.0, "beat-02", "safeguards", "x-claudeai-safeguards.mp4"),
    ]
    with patch(
        "praisonaippt.daily_single.visual_claim_audit.build_visual_timeline",
        return_value=windows,
    ), patch(
        "praisonaippt.daily_single.visual_claim_audit.describe_frame_cached",
        return_value={"description": "woman presenter speaking in office"},
    ), patch(
        "praisonaippt.daily_single.visual_claim_audit.export_frame",
    ):
        report = validate_visual_claims(project, use_vlm=True)
    assert not report["ok"]
    assert report["issues"]

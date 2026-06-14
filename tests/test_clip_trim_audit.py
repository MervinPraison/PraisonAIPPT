"""Tests for clip trim-range QA."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from praisonaippt.daily_single.clip_trim_audit import (
    suggested_trim_for_source,
    validate_clip_trims,
)
from praisonaippt.daily_single.project import DailySingleProject


def _project(tmp_path: Path, beat_map: dict) -> DailySingleProject:
    root = tmp_path / "p"
    research = tmp_path / "r"
    research.mkdir()
    root.mkdir()
    beat_path = root / "research" / "beat-map-v2.json"
    beat_path.parent.mkdir(parents=True)
    beat_path.write_text(json.dumps(beat_map), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "t",
            "create_news_research": str(research),
            "beat_map": str(beat_path),
        }),
        encoding="utf-8",
    )
    return DailySingleProject.from_root(root)


def test_suggested_trim_from_shell_map():
    trim = suggested_trim_for_source(
        local_file="research/reference-videos/social/youtube-jono-flight-sim.mp4",
        notes="Physics flight sim (~04:48)",
        duration=600.0,
    )
    assert trim["in_sec"] == 45.0
    assert trim["out_sec"] == 59.0


def test_invalid_beat_map_trim_fails(tmp_path: Path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"x" * 100)
    project = _project(tmp_path, {
        "beats": {
            "6": {
                "clips": [{
                    "filename": "clip.mp4",
                    "path": str(clip),
                    "in_sec": 0,
                    "out_sec": 30,
                }],
            },
        },
    })
    with patch("praisonaippt.daily_single.clip_trim_audit.ffprobe_duration", return_value=10.0), patch(
        "praisonaippt.daily_single.clip_trim_audit.build_hook_montage_plan",
        return_value={"cues": []},
    ):
        report = validate_clip_trims(project)
    assert not report["ok"]
    assert any("exceeds file duration" in i for i in report["issues"])

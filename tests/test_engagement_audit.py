"""Tests for engagement asset validation helpers."""
import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.engagement_audit import (
    _body_duration,
    _motion_duration,
    validate_engagement_assets,
)
from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.project import DailySingleProject


def _window(beat: str, file: str, start: float, end: float) -> VisualWindow:
    return VisualWindow(
        start_sec=start,
        end_sec=end,
        beat=beat,
        visual=file,
        file=file,
        section="main",
    )


def test_body_duration_skips_hook_outro_and_heygen():
    wins = [
        _window("00-hook", "a.png", 0, 10),
        _window("beat-3", "demo.mp4", 10, 20),
        _window("99-outro", "b.png", 20, 25),
        _window("beat-4", "heygen.mp4", 25, 30),
    ]
    assert _body_duration(wins) == pytest.approx(10.0)


def test_motion_duration_counts_mp4_body_only():
    wins = [
        _window("beat-3", "clip.mp4", 0, 5),
        _window("beat-4", "slide.png", 5, 10),
        _window("99-outro", "out.mp4", 10, 15),
    ]
    assert _motion_duration(wins) == pytest.approx(5.0)


def test_validate_engagement_assets_writes_report(tmp_path: Path):
    root = tmp_path / "proj"
    merge = root / "merge"
    research = tmp_path / "research"
    research.mkdir(parents=True)
    beat_map = research / "beat-map.json"
    beat_map.write_text(
        """{"variant":"default","beats":{"3":{"clips":[{"path":"x.mp4"}],"images":[]}}}""",
        encoding="utf-8",
    )
    root.mkdir(parents=True)
    merge.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(research),
            "beat_map": str(beat_map),
        }),
        encoding="utf-8",
    )
    (merge / "timeline.json").write_text(
        '{"segments":[{"id":"beat-3","duration_sec":10}]}',
        encoding="utf-8",
    )
    project = DailySingleProject.from_root(root)
    report = validate_engagement_assets(project)
    assert report["schema_version"] == 1
    assert (merge / "engagement_report.json").is_file()
    assert "beats with clips" in " ".join(report.get("issues") or [])

"""Tests for viral-readiness composite gate."""
import json
from pathlib import Path

from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.viral_readiness import (
    _comparison_beats,
    _hook_has_motion,
    validate_viral_readiness,
)
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


def test_hook_has_motion_detects_mp4():
    wins = [_window("00-hook", "scroll.mp4", 0, 5), _window("00-hook", "a.png", 5, 10)]
    assert _hook_has_motion(wins, 10.0) is True
    assert _hook_has_motion([_window("00-hook", "a.png", 0, 5)], 5.0) is False


def test_comparison_beats_from_filenames():
    wins = [
        _window("beat-4", "beat4-stat-overlay.png", 0, 5),
        _window("beat-5", "plain.png", 5, 10),
    ]
    assert "beat-4" in _comparison_beats(wins)


def test_validate_viral_readiness_writes_report(tmp_path: Path):
    root = tmp_path / "proj"
    merge = root / "merge"
    research = tmp_path / "research"
    research.mkdir(parents=True)
    beat_map = research / "beat-map.json"
    beat_map.write_text('{"variant":"default","beats":{}}', encoding="utf-8")
    root.mkdir(parents=True)
    merge.mkdir(parents=True)
    (root / "segments" / "00-hook").mkdir(parents=True)
    (root / "segments" / "00-hook" / "script.md").write_text(
        "Hook line one.\nHook line two.",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(research),
            "beat_map": str(beat_map),
        }),
        encoding="utf-8",
    )
    (merge / "timeline.json").write_text('{"segments":[]}', encoding="utf-8")
    project = DailySingleProject.from_root(root)
    report = validate_viral_readiness(project)
    assert report["schema_version"] == 1
    assert (merge / "viral_readiness_report.json").is_file()
    assert report.get("ok") is False

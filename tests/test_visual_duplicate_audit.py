"""Tests for assembled-video duplicate clip gate."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.visual_duplicate_audit import validate_visual_duplicates


def _project(tmp_path: Path, beat_map: dict) -> DailySingleProject:
    root = tmp_path / "proj"
    (root / "segments" / "00-hook").mkdir(parents=True)
    (root / "segments" / "00-hook" / "script.md").write_text("Hook script.", encoding="utf-8")
    (root / "merge").mkdir(parents=True)
    research = tmp_path / "research"
    research.mkdir()
    (research / "video-understanding").mkdir(parents=True)
    bm = research / "video-understanding" / "beat-map.json"
    bm.write_text(json.dumps(beat_map), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test-social",
            "create_news_research": str(research),
            "beat_map": str(bm),
        }),
        encoding="utf-8",
    )
    tl = {
        "segments": [
            {"id": "00-hook", "start_sec": 0.0, "duration_sec": 20.0},
            {"id": "beat-01", "start_sec": 20.0, "duration_sec": 20.0},
            {"id": "beat-05", "start_sec": 40.0, "duration_sec": 20.0},
        ]
    }
    (root / "merge" / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    return DailySingleProject.from_root(root)


def test_flags_hook_clip_in_late_body(tmp_path: Path, monkeypatch):
    launch = "x-claudeai-launch.mp4"

    def fake_timeline(_project):
        from praisonaippt.daily_single.display_sync import VisualWindow

        return [
            VisualWindow(0, 8, "00-hook", "clip", launch, "attention"),
            VisualWindow(20, 35, "beat-01", "clip", launch),
            VisualWindow(40, 55, "beat-05", "clip", launch),
        ]

    def fake_hook_plan(_project):
        return {
            "cues": [{"file": launch, "ok": True, "path": f"/x/{launch}", "beat": 1}],
        }

    monkeypatch.setattr(
        "praisonaippt.daily_single.visual_duplicate_audit.build_visual_timeline",
        fake_timeline,
    )
    monkeypatch.setattr(
        "praisonaippt.daily_single.visual_duplicate_audit.build_hook_montage_plan",
        fake_hook_plan,
    )

    project = _project(tmp_path, {
        "variant": "social-comparison",
        "asset_policy": "video-first-local",
        "beats": {"1": {"clips": [], "images": [], "generated": []}},
    })
    report = validate_visual_duplicates(project)
    assert not report["ok"]
    assert any("beat-05" in i for i in report["issues"])


def test_allows_hook_plus_beat01_only(tmp_path: Path, monkeypatch):
    launch = "x-claudeai-launch.mp4"

    def fake_timeline(_project):
        from praisonaippt.daily_single.display_sync import VisualWindow

        return [
            VisualWindow(0, 8, "00-hook", "clip", launch, "attention"),
            VisualWindow(20, 35, "beat-01", "clip", launch),
        ]

    def fake_hook_plan(_project):
        return {
            "cues": [{"file": launch, "ok": True, "path": f"/x/{launch}", "beat": 1}],
        }

    monkeypatch.setattr(
        "praisonaippt.daily_single.visual_duplicate_audit.build_visual_timeline",
        fake_timeline,
    )
    monkeypatch.setattr(
        "praisonaippt.daily_single.visual_duplicate_audit.build_hook_montage_plan",
        fake_hook_plan,
    )

    project = _project(tmp_path, {
        "variant": "social-comparison",
        "asset_policy": "video-first-local",
        "beats": {"1": {"clips": [], "images": [], "generated": []}},
    })
    report = validate_visual_duplicates(project)
    assert report["ok"]

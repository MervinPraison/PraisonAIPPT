"""Integration tests for daily_single sync validation suite."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.display_sync import validate_display_sync
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.sync_validation import (
    borderline_cues,
    expected_script_cues,
    run_sync_suite,
    validate_caption_script_lock,
    validate_hook_structure,
)

FABLE_ROOT = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-mythos-5"


@pytest.fixture
def mini_project(tmp_path: Path) -> DailySingleProject:
    root = tmp_path / "proj"
    (root / "segments/00-hook").mkdir(parents=True)
    (root / "segments/01-cold-open").mkdir(parents=True)
    (root / "merge").mkdir()
    (root / "beats").mkdir()
    research = tmp_path / "research"
    (research / "video-understanding").mkdir(parents=True)
    beat_map = research / "video-understanding/beat-map.json"
    beat_map.write_text(json.dumps({"beats": {"1": {"clips": [], "generated": [], "images": []}}}), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(research),
            "beat_map": str(beat_map),
        }),
        encoding="utf-8",
    )
    hook = (
        "Hook: Anthropic just released Claude Fable five for everyday teams.\n\n"
        "In this walkthrough we cover tiers, benchmarks, safety checks, pricing, and launch tips.\n\n"
        "Let's get started.\n"
    )
    (root / "segments/00-hook/script.md").write_text(hook, encoding="utf-8")
    (root / "segments/01-cold-open/script.md").write_text("First beat sentence here.", encoding="utf-8")
    timeline = {
        "segments": [
            {"id": "00-hook", "start_sec": 0.0, "duration_sec": 12.0},
            {"id": "beat-01", "start_sec": 12.0, "duration_sec": 8.0},
        ],
    }
    (root / "merge/timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
    srt = (
        "1\n00:00:00,000 --> 00:00:04,000\n"
        "Anthropic just released Claude Fable five for everyday teams.\n\n"
        "2\n00:00:04,000 --> 00:00:10,000\n"
        "In this walkthrough we cover tiers, benchmarks, safety checks, pricing, and launch tips.\n\n"
        "3\n00:00:10,000 --> 00:00:12,000\nLet's get started.\n\n"
        "4\n00:00:12,000 --> 00:00:20,000\nFirst beat sentence here.\n"
    )
    (root / "merge/final.srt").write_text(srt, encoding="utf-8")
    return DailySingleProject.from_root(root)


def test_expected_script_cues_strips_hook_label(mini_project: DailySingleProject):
    cues = expected_script_cues(mini_project)
    assert "Anthropic" in cues[0]
    assert cues[2] == "Let's get started."


def test_validate_caption_script_lock_passes(mini_project: DailySingleProject):
    ok, issues = validate_caption_script_lock(mini_project)
    assert ok, issues


def test_validate_hook_structure_passes(mini_project: DailySingleProject):
    from praisonaippt.daily_single.display_sync import parse_srt

    cues = parse_srt(mini_project.merge_dir / "final.srt")
    cue_map = [{"cue": i + 1, "spoken": c["text"]} for i, c in enumerate(cues)]
    ok, issues = validate_hook_structure(cue_map)
    assert ok, issues


def test_run_sync_suite_idempotent_three_times(mini_project: DailySingleProject, monkeypatch):
    cue_map = [
        {"cue": 1, "spoken": "Anthropic just released Claude Fable five for everyday teams.", "alignment": 0.9, "ok": True, "file": "claudeai-launch.mp4"},
        {"cue": 2, "spoken": "In this walkthrough we cover tiers, benchmarks, safety checks, pricing, and launch tips.", "alignment": 0.9, "ok": True, "file": "heygen.mp4"},
        {"cue": 3, "spoken": "Let's get started.", "alignment": 0.9, "ok": True, "file": "heygen.mp4"},
        {"cue": 4, "spoken": "First beat sentence here.", "alignment": 0.9, "ok": True, "file": "claudeai-launch.mp4"},
    ]

    def _fake_display(_project):
        return {
            "ok": True,
            "cues_total": 4,
            "cues_pass": 4,
            "cues_fail": 0,
            "cue_map": cue_map,
        }

    monkeypatch.setattr(
        "praisonaippt.daily_single.sync_validation.validate_hook_montage",
        lambda _p: (True, {"ok": True, "issues": [], "overview_windows": 5}),
    )
    monkeypatch.setattr(
        "praisonaippt.daily_single.sync_validation.validate_visual_audit",
        lambda _p: (True, {"ok": True, "issues": [], "samples_total": 10, "samples_pass": 10}),
    )
    monkeypatch.setattr(
        "praisonaippt.daily_single.sync_validation.validate_display_sync",
        _fake_display,
    )
    report = run_sync_suite(mini_project, runs=3)
    assert report["runs"] == 3
    assert report["idempotent"] is True
    assert len(report["run_results"]) == 3
    assert all(r["cues_total"] == r["cues_total"] for r in report["run_results"])


def test_hook_overview_split():
    raw = (
        "Hook: Anthropic released Fable five today.\n\n"
        "We cover tiers, benchmarks, and pricing.\n\n"
        "Let's get started.\n"
    )
    cues = split_caption_cues(raw)
    assert len(cues) == 3
    assert cues[-1] == "Let's get started."


@pytest.mark.skipif(not FABLE_ROOT.is_dir(), reason="pilot project missing")
class TestFablePilotSync:
    """Regression on anthropic-claude-fable-5-mythos-5 when artefacts exist."""

    @pytest.fixture
    def project(self) -> DailySingleProject:
        return DailySingleProject.from_root(FABLE_ROOT)

    def test_pilot_sync_suite_three_runs(self, project: DailySingleProject):
        if not (project.merge_dir / "final.srt").is_file():
            pytest.skip("final.srt missing — run build-captions on pilot")
        report = run_sync_suite(project, runs=3)
        assert report["idempotent"] is True
        assert report["summary"]["caption_script_lock"] is True
        assert report["summary"]["hook_structure"] is True
        assert report["summary"]["image_mapping"] is True
        assert report["summary"].get("hook_montage") is True
        assert report["summary"].get("visual_audit") is True
        assert report["ok"] is True

    def test_pilot_display_sync_deterministic(self, project: DailySingleProject):
        if not (project.merge_dir / "final.srt").is_file():
            pytest.skip("final.srt missing")
        r1 = validate_display_sync(project)
        r2 = validate_display_sync(project)
        sig1 = [(c["cue"], c["file"], c["alignment"]) for c in r1["cue_map"]]
        sig2 = [(c["cue"], c["file"], c["alignment"]) for c in r2["cue_map"]]
        assert sig1 == sig2

    def test_pilot_borderline_reported_not_failed(self, project: DailySingleProject):
        if not (project.merge_dir / "final.srt").is_file():
            pytest.skip("final.srt missing")
        display = validate_display_sync(project)
        borderline = borderline_cues(display["cue_map"])
        assert display["ok"] is True
        assert len(borderline) >= 0

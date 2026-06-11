"""Tier-0 tests for praisonaippt.video_qa (no network, no API keys)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.config import DEFAULT_QA_STAGES
from praisonaippt.video_qa.degradation import detect_degradation, stage_should_skip
from praisonaippt.video_qa.registry import list_stages
from praisonaippt.video_qa.runner import run_stage, run_suite
from praisonaippt.video_qa.stages.s04_knowledge import run_s04_knowledge
from praisonaippt.video_qa.stages.s05_transcript import run_s05_transcript
from praisonaippt.video_qa.stages.s06_coverage import run_s06_coverage


@pytest.fixture
def mini_project(tmp_path: Path) -> DailySingleProject:
    root = tmp_path / "proj"
    research = tmp_path / "research"
    (research / "video-understanding").mkdir(parents=True)
    beat_map = research / "video-understanding/beat-map.json"
    beats = {
        str(i): {"generated": [{"filename": f"beat{i}.png"}], "images": [], "clips": []}
        for i in range(1, 11)
    }
    beat_map.write_text(json.dumps({"beats": beats}), encoding="utf-8")
    (research / "video-handoff.json").write_text(json.dumps({"images": [], "videos": []}), encoding="utf-8")
    (research / "video-script.md").write_text("# Script\n\n" + ("Beat section.\n\n" * 12), encoding="utf-8")

    root.mkdir(parents=True)
    (root / "merge").mkdir()
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(research),
            "beat_map": str(beat_map),
        }),
        encoding="utf-8",
    )

    from praisonaippt.daily_single.protocol import SEGMENT_ORDER

    for seg_id, seg_dir, _ in SEGMENT_ORDER:
        folder = seg_dir or seg_id
        path = root / "segments" / folder
        path.mkdir(parents=True, exist_ok=True)
        (path / "script.md").write_text(f"Script for {seg_id}. One sentence here.", encoding="utf-8")

    return DailySingleProject.from_root(root)


def test_list_stages_includes_core():
    stages = list_stages()
    assert len(stages) == 16
    assert "s00-bookends" in stages


def test_default_qa_stages_have_ids():
    assert all(s.get("id") for s in DEFAULT_QA_STAGES)


def test_s04_knowledge_passes_mini(mini_project: DailySingleProject):
    report = run_s04_knowledge(mini_project)
    assert report.ok
    assert report.id == "s04-knowledge"


def test_s06_coverage_passes_with_beat_assets(mini_project: DailySingleProject):
    report = run_s06_coverage(mini_project, phase="post_scripts")
    assert report.id == "s06-coverage"


def test_s05_transcript_warns_without_narration(mini_project: DailySingleProject):
    report = run_s05_transcript(mini_project, phase="post_vo")
    assert not report.ok
    assert any("vo" in c.id for c in report.checks)


def test_s05_post_vo_checks_narration_only(mini_project: DailySingleProject):
    for seg_id, seg_dir, _ in __import__(
        "praisonaippt.daily_single.protocol", fromlist=["SEGMENT_ORDER"]
    ).SEGMENT_ORDER:
        folder = seg_dir or seg_id
        seg = mini_project.segments_dir / folder
        (seg / "narration.mp3").write_bytes(b"\x00" * 50)
    report = run_s05_transcript(mini_project, phase="post_vo")
    assert report.ok


def test_s05_transcript_fails_without_timestamps(mini_project: DailySingleProject):
    for seg_id, seg_dir, _ in __import__(
        "praisonaippt.daily_single.protocol", fromlist=["SEGMENT_ORDER"]
    ).SEGMENT_ORDER:
        folder = seg_dir or seg_id
        seg = mini_project.segments_dir / folder
        (seg / "narration.mp3").write_bytes(b"\x00" * 50)
    report = run_s05_transcript(mini_project, phase="post_captions")
    assert not report.ok


def test_s05_transcript_passes_with_whisper(mini_project: DailySingleProject):
    seg = mini_project.segments_dir / "01-cold-open"
    script = seg / "script.md"
    text = script.read_text(encoding="utf-8")
    (seg / "narration.mp3").write_bytes(b"\x00" * 100)
    (seg / "timestamps.json").write_text(
        json.dumps({
            "text": text,
            "segments": [{"id": 0, "start": 0.0, "end": 2.0, "text": text}],
            "words": [],
        }),
        encoding="utf-8",
    )
    report = run_s05_transcript(mini_project, phase="post_captions")
    beat_check = next(c for c in report.checks if c.id == "beat-01_overlap")
    assert beat_check.ok


def test_stage_skip_when_final_mp4_missing(mini_project: DailySingleProject):
    degradation = detect_degradation(mini_project)
    skip, reason = stage_should_skip(
        {"id": "s10-final-composite", "when": "post_build"},
        degradation,
    )
    assert skip
    assert reason == "missing_final_mp4"


def test_run_suite_pre_build_writes_summary(mini_project: DailySingleProject):
    suite = run_suite(mini_project, when="pre_build")
    summary_path = mini_project.merge_dir / "qa" / "summary.json"
    assert summary_path.is_file()
    assert suite.summary["stages_run"] >= 1


def test_vlm_cache_roundtrip(tmp_path: Path):
    from praisonaippt.video_qa.vlm_cache import frame_key, load_cached, save_cached

    qa = tmp_path / "qa"
    key = frame_key(b"frame-bytes", "gpt-4o-mini", "spoken text")
    save_cached(qa, key, {"description": "test", "topics": []})
    loaded = load_cached(qa, key)
    assert loaded is not None
    assert loaded["description"] == "test"


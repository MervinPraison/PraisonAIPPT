"""AV pillar gates — audio, Whisper words, visuals at each pipeline phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from praisonaippt.daily_single.pipeline import PIPELINE_AV_ORDER
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.spoken_visual_gates import (
    PHASE_GATES,
    run_phase_gates,
    validate_post_assemble_av,
    validate_pre_build_av,
    validate_segment_audio,
    validate_whisper_word_timings,
)


def test_phase_gates_cover_av_order():
    assert set(PHASE_GATES) >= {
        "pre_build",
        "post_vo",
        "post_bookends",
        "pre_assemble",
        "post_assemble",
        "post_captions",
        "post_build",
    }
    assert PIPELINE_AV_ORDER[-1] == "spoken_visual_map"


def test_pre_build_av_requires_scripts(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    bm = root / "research" / "beat-map-v2.json"
    bm.parent.mkdir(parents=True)
    bm.write_text(json.dumps({"variant": "default", "beats": {}}), encoding="utf-8")
    project = DailySingleProject.from_root(root)
    with patch("praisonaippt.daily_single.media_sync.validate_media_inventory", return_value=(True, {})):
        ok, detail = validate_pre_build_av(project)
    assert not ok
    assert detail["missing_scripts"]


def test_post_vo_runs_three_pillar_gates(tmp_path: Path):
    root = tmp_path / "proj"
    seg = root / "segments" / "01-cold-open"
    seg.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (root / "research").mkdir(exist_ok=True)
    (root / "research" / "beat-map-v2.json").write_text("{}", encoding="utf-8")
    (seg / "narration.mp3").write_bytes(b"\x00" * 200)
    words = [{"word": f"w{i}", "start": i * 0.2, "end": i * 0.2 + 0.15} for i in range(12)]
    (seg / "timestamps.json").write_text(json.dumps({
        "text": " ".join(w["word"] for w in words),
        "source": "openai-whisper",
        "words": words,
        "segments": [],
    }), encoding="utf-8")
    project = DailySingleProject.from_root(root)
    with patch("praisonaippt.daily_single.captions._ensure_transcript"):
        ok, detail = run_phase_gates(project, "post_vo")
    names = {g["name"] for g in detail["gates"]}
    assert names == {
        "_gate_transcribe_vo",
        "validate_whisper_word_timings",
        "validate_segment_audio",
    }


def test_post_bookends_requires_hook_outro_audio(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    project = DailySingleProject.from_root(root)
    from praisonaippt.daily_single.spoken_visual_gates import validate_post_bookends_av

    ok, detail = validate_post_bookends_av(project)
    assert not ok
    assert len(detail["bookends"]) == 2


def test_build_pipeline_includes_post_bookends_gate():
    from praisonaippt.daily_single.pipeline import BUILD_PIPELINE

    ids = [s.id for s in BUILD_PIPELINE]
    assert ids.index("bookend-media") < ids.index("validate-av-post_bookends")
    assert ids.index("validate-av-post_bookends") < ids.index("validate-qa-pre_assemble")


def test_publish_gate_includes_post_assemble_and_post_captions():
    from praisonaippt.daily_single.pipeline import PUBLISH_GATE

    gate_ids = [s.id for s in PUBLISH_GATE]
    assert "validate-av-post_assemble" in gate_ids
    assert "validate-av-post_captions" in gate_ids
    assert gate_ids.index("build-captions") < gate_ids.index("validate-av-post_assemble")
    assert gate_ids.index("validate-av-post_assemble") < gate_ids.index("validate-av-post_captions")
    assert gate_ids.index("validate-av-post_captions") < gate_ids.index("pytest")


@pytest.mark.skipif(
    not Path("examples/videos/anthropic-claude-fable-5-social-comparison/merge/final.mp4").is_file(),
    reason="social-comparison pilot not built",
)
def test_post_assemble_on_built_project():
    project = DailySingleProject.from_root(
        "examples/videos/anthropic-claude-fable-5-social-comparison",
    )
    ok, detail = validate_post_assemble_av(project)
    assert detail["visual_windows"] >= 10
    assert detail["pillar"]["words"] is True or not ok


def test_build_timeline_from_narration(tmp_path: Path):
    from praisonaippt.daily_single.timeline import build_timeline_from_narration

    root = tmp_path / "proj"
    seg = root / "segments" / "01-cold-open"
    seg.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (seg / "narration.mp3").write_bytes(b"\x00" * 200)
    project = DailySingleProject.from_root(root)
    with patch("praisonaippt.daily_single.timeline.ffprobe_duration", return_value=12.5):
        payload = build_timeline_from_narration(project)
    assert payload["source"] == "narration_preview"
    assert payload["segments"][0]["id"] == "00-hook" or payload["segments"][0]["id"] == "beat-01"


def test_run_suite_post_assemble_includes_phase_gates(tmp_path: Path):
    from praisonaippt.video_qa.runner import run_suite

    root = tmp_path / "proj"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (root / "merge").mkdir()
    project = DailySingleProject.from_root(root)
    suite = run_suite(project, when="post_assemble", continue_on_fail=True)
    assert any(s.id == "sdk-phase-gates-post_assemble" for s in suite.stages)

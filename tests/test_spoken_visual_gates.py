"""Tests for SDK spoken↔visual phase gates."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.spoken_visual_gates import (
    PIPELINE_AV_ORDER,
    validate_pre_assemble_readiness,
    validate_whisper_word_timings,
)


def test_pipeline_av_order_contract():
    assert PIPELINE_AV_ORDER[0] == "video_first_assets"
    assert "whisper_word_timings" in PIPELINE_AV_ORDER
    assert PIPELINE_AV_ORDER[-1] == "spoken_visual_map"


def test_whisper_rejects_proportional_timestamps(tmp_path):
    root = tmp_path / "proj"
    seg = root / "segments" / "01-cold-open"
    seg.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "video-understanding").mkdir(parents=True)
    (tmp_path / "research" / "video-understanding" / "beat-map.json").write_text("{}", encoding="utf-8")
    (seg / "narration.mp3").write_bytes(b"\x00")
    (seg / "timestamps.json").write_text(json.dumps({
        "text": "hello world test clip",
        "duration": 1.0,
        "source": "proportional",
        "words": [{"word": "hello", "start": 0, "end": 0.5}],
        "segments": [],
    }), encoding="utf-8")

    from praisonaippt.daily_single.project import DailySingleProject

    project = DailySingleProject.from_root(root)
    ok, detail = validate_whisper_word_timings(project, min_words=2)
    assert not ok
    assert detail["segments"][0]["ok"] is False


def test_pre_assemble_requires_segment_files(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "video-understanding").mkdir(parents=True)
    (tmp_path / "research" / "video-understanding" / "beat-map.json").write_text("{}", encoding="utf-8")

    from praisonaippt.daily_single.project import DailySingleProject

    project = DailySingleProject.from_root(root)
    ok, detail = validate_pre_assemble_readiness(project)
    assert not ok
    assert detail["missing"]

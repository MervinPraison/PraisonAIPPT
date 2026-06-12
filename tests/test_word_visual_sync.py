"""Tests for word-level Whisper ↔ visual sync."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.word_visual_sync import (
    GlobalWord,
    build_global_word_timeline,
    spoken_context_around,
    validate_word_visual_sync,
    words_in_window,
)


def test_spoken_context_around():
    words = [
        GlobalWord("Stripe", 0.0, 0.4, "beat-03"),
        GlobalWord("moved", 0.4, 0.7, "beat-03"),
        GlobalWord("fifty", 0.7, 1.0, "beat-03"),
        GlobalWord("million", 1.0, 1.3, "beat-03"),
    ]
    ctx = spoken_context_around(words, 2, radius=2)
    assert "Stripe" in ctx
    assert "million" in ctx


def test_words_in_window():
    words = [
        GlobalWord("a", 1.0, 1.2, "x"),
        GlobalWord("b", 2.0, 2.2, "x"),
        GlobalWord("c", 5.0, 5.2, "x"),
    ]
    hits = words_in_window(words, 1.5, 3.0)
    assert len(hits) == 1
    assert hits[0].word == "b"


def test_validate_word_visual_sync_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAISONAIPPT_QA_OFFLINE", "1")
    root = tmp_path / "proj"
    merge = root / "merge"
    segs = root / "segments" / "03-engineers-care"
    merge.mkdir(parents=True)
    segs.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(tmp_path / "research"),
        }),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "video-understanding").mkdir(parents=True)
    (tmp_path / "research" / "video-understanding" / "beat-map.json").write_text("{}", encoding="utf-8")

    (merge / "timeline.json").write_text(json.dumps({
        "segments": [{"id": "beat-03", "start_sec": 10.0, "duration_sec": 5.0}],
    }), encoding="utf-8")
    (segs / "timestamps.json").write_text(json.dumps({
        "text": "Stripe moved code",
        "duration": 3.0,
        "words": [
            {"word": "Stripe", "start": 0.0, "end": 0.5},
            {"word": "moved", "start": 0.5, "end": 1.0},
            {"word": "code", "start": 1.0, "end": 1.5},
        ],
        "segments": [],
    }), encoding="utf-8")
    (merge / "final.mp4").write_bytes(b"\x00")

    from praisonaippt.daily_single.project import DailySingleProject

    project = DailySingleProject.from_root(root)
    windows = [
        VisualWindow(10.0, 15.0, "beat-03", "stripe", "beat3-stripe-card.png"),
    ]
    with patch("praisonaippt.daily_single.word_visual_sync.build_visual_timeline", return_value=windows):
        with patch("praisonaippt.daily_single.word_visual_sync.export_frame"):
            report = validate_word_visual_sync(project, use_vlm=False)
    assert report["samples_total"] >= 1
    assert report["whisper_words_total"] == 3


def test_validate_word_visual_sync_fails_without_final_mp4(tmp_path):
    root = tmp_path / "proj"
    merge = root / "merge"
    segs = root / "segments" / "03-engineers-care"
    merge.mkdir(parents=True)
    segs.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"slug": "test", "create_news_research": str(tmp_path / "research")}),
        encoding="utf-8",
    )
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "video-understanding").mkdir(parents=True)
    (tmp_path / "research" / "video-understanding" / "beat-map.json").write_text("{}", encoding="utf-8")
    (merge / "timeline.json").write_text(json.dumps({
        "segments": [{"id": "beat-03", "start_sec": 10.0, "duration_sec": 5.0}],
    }), encoding="utf-8")
    (segs / "timestamps.json").write_text(json.dumps({
        "text": "Stripe moved code",
        "words": [{"word": "Stripe", "start": 0.0, "end": 0.5}],
        "segments": [],
    }), encoding="utf-8")

    from praisonaippt.daily_single.project import DailySingleProject

    project = DailySingleProject.from_root(root)
    report = validate_word_visual_sync(project, use_vlm=True)
    assert not report["ok"]
    assert report.get("skipped")
    assert "final.mp4" in str(report.get("error", ""))

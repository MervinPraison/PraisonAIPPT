"""Tests for align, timeline resolver, image selection."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.segment_video.align import align_cues_to_transcript, match_fragment_to_segments
from praisonaippt.segment_video.image_selection import build_cue_plan, is_relevant_image
from praisonaippt.segment_video.timeline import resolve_at_time
from praisonaippt.transcript_loader import TranscriptData, WhisperSegment, WhisperWord


def _transcript():
    return TranscriptData(
        duration=20.0,
        text="NVIDIA Nemotron deploy via Hugging Face",
        segments=[
            WhisperSegment(0, 0.0, 10.0, "NVIDIA Nemotron 3 Ultra sparse MoE"),
            WhisperSegment(1, 10.0, 20.0, "Deploy via Hugging Face NIM vLLM"),
        ],
        words=[
            WhisperWord("NVIDIA", 0.1, 0.5),
            WhisperWord("Nemotron", 0.5, 1.0),
            WhisperWord("Deploy", 10.2, 10.8),
            WhisperWord("Hugging", 11.0, 11.5),
        ],
    )


def test_match_fragment_finds_second_span():
    data = _transcript()
    span = match_fragment_to_segments("Deploy via Hugging Face", data, min_start=9.0)
    assert span is not None
    assert span[0] >= 9.0


def test_align_cues_segment_pair(tmp_path: Path):
    """When cue count matches Whisper segments, pair by index (no overlap at 0)."""
    ts = tmp_path / "timestamps.json"
    ts.write_text(json.dumps({
        "duration": 22.72,
        "segments": [
            {"id": 0, "start": 0.0, "end": 11.36, "text": "First half"},
            {"id": 1, "start": 11.36, "end": 22.72, "text": "Second half"},
        ],
    }))
    cues = [
        {"script_fragment": "First half", "file": "a.png"},
        {"script_fragment": "Second half", "file": "b.png"},
    ]
    timings = align_cues_to_transcript(cues, ts, total_duration=22.72)
    assert timings[0]["audio_start_sec"] == 0.0
    assert timings[1]["audio_start_sec"] == 11.36
    assert timings[0]["match_method"] == "segment_pair"


def test_align_cues_produces_timings(tmp_path: Path):
    ts = tmp_path / "timestamps.json"
    data = _transcript()
    ts.write_text(json.dumps({
        "duration": data.duration,
        "segments": [{"id": s.id, "start": s.start, "end": s.end, "text": s.text} for s in data.segments],
        "words": [{"word": w.word, "start": w.start, "end": w.end} for w in data.words],
    }))
    cues = [
        {"script_fragment": "NVIDIA Nemotron 3 Ultra", "file": "a.png"},
        {"script_fragment": "Deploy via Hugging Face", "file": "b.png"},
    ]
    timings = align_cues_to_transcript(cues, ts, total_duration=20.0)
    assert len(timings) == 2
    assert timings[1]["audio_start_sec"] >= 9.0


def test_resolve_at_time():
    tl = {
        "cues": [
            {"start_sec": 0, "end_sec": 10, "notes": "first", "jpeg_rel": "a.jpg", "words": []},
            {"start_sec": 10, "end_sec": 20, "notes": "second", "jpeg_rel": "b.jpg", "words": []},
        ],
        "srt_cues": [{"start_sec": 0, "end_sec": 10, "text": "first caption"}],
    }
    r = resolve_at_time(tl, 5)
    assert r["slide_index"] == 0
    r2 = resolve_at_time(tl, 15)
    assert r2["slide_index"] == 1


def test_hook_clauses():
    script = (
        "June 2026 stacked fifteen engineering moves: Nemotron 3 Ultra, Gemma 4 twelve billion, "
        "seven Microsoft MAI models. Here is what changed."
    )
    from praisonaippt.segment_video.image_audit import hook_clauses
    parts = hook_clauses(script)
    assert len(parts) == 3
    assert "Nemotron" in parts[0]
    rules = {
        "min_topic_relevance": 0.7,
        "require_topic_relevance_label": "relevant",
        "min_script_alignment": 0.35,
        "max_cues_per_segment": 2,
        "multi_cue_requires_sentences": 1,
        "no_fallback_to_marginal": True,
    }
    images = [
        {"filename": "a.png", "topic_relevance_label": "marginal", "topic_relevance_score": 0.1,
         "vision_description": "unrelated"},
    ]
    cues, rejected = build_cue_plan("Short script.", images, rules)
    assert len(cues) == 0
    assert len(rejected) >= 1

"""Tests for audio_align."""

import re
from unittest.mock import patch

from praisonaippt.audio_align import (
    _SILENCE_RE,
    emphasis_score,
    merge_boundaries,
    segment_gaps_from_data,
    write_word_srt,
)
from praisonaippt.transcript_loader import WhisperWord, load_whisper_json, WhisperSegment, TranscriptData


def test_silence_regex():
    log = "silence_start: 4.54\nsilence_end: 5.58"
    pairs = _SILENCE_RE.findall(log)
    assert ("start", "4.54") in pairs


def test_emphasis_score():
    assert emphasis_score(0.2, 0.1) == 2.0
    assert emphasis_score(0.0, 0.0) == 1.0


def test_merge_boundaries():
    seg = [(4.0, 4.54)]
    sil = [(4.02, 4.52)]
    merged = merge_boundaries(seg, sil, tolerance=0.15)
    assert len(merged) >= 1


def test_segment_gaps():
    data = TranscriptData(
        duration=10,
        text="",
        segments=[
            WhisperSegment(0, 0, 4, "a"),
            WhisperSegment(1, 4.5, 7, "b"),
        ],
    )
    gaps = segment_gaps_from_data(data)
    assert gaps == [(4.0, 4.5)]


def test_write_word_srt(tmp_path):
    words = [
        WhisperWord("Hello", 0.0, 0.5),
        WhisperWord("world", 0.5, 1.0),
    ]
    out = tmp_path / "w.srt"
    write_word_srt(words, out, refine_onset=False)
    text = out.read_text()
    assert "Hello" in text
    assert "world" in text
    assert text.count("-->") == 2


@patch("praisonaippt.audio_align._run_ffmpeg")
def test_detect_silences_mock(mock_ff):
    from praisonaippt.audio_align import detect_silences

    mock_ff.return_value = "silence_start: 1.0\nsilence_end: 1.5\n"
    gaps = detect_silences("fake.mp3")
    assert gaps == [(1.0, 1.5)]

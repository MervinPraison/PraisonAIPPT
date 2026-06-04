"""Tests for transcript_loader."""

from pathlib import Path

import pytest

from praisonaippt.transcript_loader import (
    load_whisper_json,
    segments_to_verses,
    wall_clock_duration,
    normalise_text,
    build_title_verse,
)

JSON = Path(__file__).resolve().parent.parent / "examples" / "short-script-50590_timestamps.json"


@pytest.fixture
def transcript():
    if not JSON.is_file():
        pytest.skip("50590 transcript fixture missing")
    return load_whisper_json(JSON)


def test_load_whisper_json(transcript):
    assert len(transcript.segments) == 15
    assert transcript.duration > 56
    assert len(transcript.words) > 50


def test_normalise_claude():
    assert "Claude" in normalise_text("Clawed agents")


def test_wall_clock_includes_gaps(transcript):
    segs = {s.id: s for s in transcript.segments}
    dur = wall_clock_duration(segs[1], segs[4])
    assert dur > 10


def test_thematic_verses_count(transcript):
    verses, ts = segments_to_verses(transcript, mode="thematic")
    assert len(verses) == 7
    assert len(ts) == 9
    assert all(v.get("notes") for v in verses)
    assert all(v.get("duration_sec") for v in verses)


def test_thematic_headline_has_notes(transcript):
    verses, _ = segments_to_verses(transcript, mode="thematic")
    headlines = [v for v in verses if v.get("slide_type") == "avatar_headline"]
    assert headlines
    for v in headlines:
        assert v.get("notes")


def test_full_mode_skips_standalone_seg1(transcript):
    verses, _ = segments_to_verses(transcript, mode="full")
    assert len(verses) == 14
    first = verses[0]
    assert "dreaming" in first.get("notes", "").lower() or first.get("audio_start_sec") == 0.0


def test_title_verse():
    v = build_title_verse("Title", "Sub", duration_sec=3.0)
    assert v["slide_type"] == "title_only"
    assert v["duration_sec"] == 3.0


def test_media_variants():
    from praisonaippt.transcript_loader import MEDIA_VARIANTS, apply_media_variant, build_deck_yaml, load_whisper_json

    data = load_whisper_json(Path(__file__).resolve().parent.parent / "examples" / "short-script-50590_timestamps.json")
    base = build_deck_yaml(data, mode="thematic")
    for name in MEDIA_VARIANTS:
        deck = apply_media_variant(base, name)
        verses = deck["sections"][0]["verses"]
        has_av = any("avatar_video_path" in v for v in verses)
        has_mp3 = any("audio_path" in v for v in verses)
        mode = deck["video_export"]["narration_mode"]
        if name == "audio-only":
            assert not has_av and has_mp3 and mode == "audio_file"
        elif name == "video-audio-heygen":
            assert has_av and not has_mp3 and mode == "avatar"
        elif name == "slides-silent":
            assert not has_av and not has_mp3 and mode == "fixed"


def test_post_roll_on_last_slide(transcript):
    verses, ts = segments_to_verses(transcript, mode="thematic", post_roll_sec=0.31)
    assert ts[-1] > 56

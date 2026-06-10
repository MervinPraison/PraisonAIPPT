"""Tests for editor label stripping before TTS."""
from praisonaippt.segment_video.script_text import narration_text_for_tts


def test_hook_label_stripped():
    raw = "Hook: Anthropic shipped Mythos-class to everyday builders."
    assert narration_text_for_tts(raw) == "Anthropic shipped Mythos-class to everyday builders."


def test_beat_label_stripped():
    raw = "Beat 3 — Why engineers care\n\nLong-horizon work matters."
    out = narration_text_for_tts(raw)
    assert out.startswith("Long-horizon")
    assert "Beat" not in out.split("\n")[0]


def test_visual_cue_stripped():
    raw = "Hook: Hello\n\n[VISUAL: launch clip]\n\nWorld."
    out = narration_text_for_tts(raw)
    assert "[VISUAL" not in out
    assert "Hello" in out
    assert "World" in out

"""Tests for script-driven caption cues."""
from praisonaippt.daily_single.captions import split_caption_cues


def test_split_strips_hook_label():
    raw = "Hook: Anthropic put Mythos-class weights in builders' hands."
    cues = split_caption_cues(raw)
    assert len(cues) == 1
    assert cues[0].startswith("Anthropic")
    assert "Hook" not in cues[0]


def test_one_cue_per_sentence():
    raw = "First sentence. Second sentence. Third."
    assert len(split_caption_cues(raw)) == 3

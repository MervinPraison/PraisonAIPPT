"""Cue-aligned slide timing tests."""
from pathlib import Path

from praisonaippt.daily_single.cue_slide_sync import BEAT6_CUE_IMAGES, beat6_cue_windows, find_image


def test_beat6_cue_image_order():
    assert BEAT6_CUE_IMAGES[1] == ("bio-aav",)
    assert BEAT6_CUE_IMAGES[2] == ("distillation",)


def test_beat6_cue_windows_from_segment_srt():
    images = [
        {"path": "/x/gpt-image-safeguard-fallback.png", "filename": "gpt-image-safeguard-fallback.png"},
        {"path": "/x/bio-aav-chart.png", "filename": "bio-aav-chart.png"},
        {"path": "/x/distillation-safeguard.png", "filename": "distillation-safeguard.png"},
        {"path": "/x/cyber-classifier.png", "filename": "cyber-classifier.png"},
        {"path": "/x/jailbreak-resistance.png", "filename": "jailbreak-resistance.png"},
    ]
    srt = Path("examples/videos/anthropic-claude-fable-5-mythos-5/segments/06-safeguards/segment.srt")
    if not srt.is_file():
        return
    wins = beat6_cue_windows(161.7, 40.8, images, srt)
    assert len(wins) >= 4
    assert wins[1].file == "bio-aav-chart.png"
    assert wins[2].file == "distillation-safeguard.png"
    assert wins[1].end_sec <= wins[2].start_sec + 0.01


def test_find_image_bio_aav():
    images = [{"path": "/a/bio-aav-chart.png", "filename": "bio-aav-chart.png"}]
    assert find_image(images, "bio-aav") is not None

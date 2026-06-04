"""Tests for automatic avatar framing calibration."""

from pathlib import Path

import pytest

from praisonaippt.avatar_calibrate import (
    AvatarFramingResult,
    CalibrationConfig,
    calibrate_avatar_framing,
    collect_avatar_seek_samples,
    merge_framing_into_slide_style,
    maybe_auto_calibrate_deck,
)

PKG = Path(__file__).resolve().parent.parent
HEYGEN = PKG / "examples" / "heygen-article-50590.mp4"


def test_collect_avatar_seek_samples():
    data = {
        "sections": [
            {
                "verses": [
                    {"avatar_video_path": "a.mp4", "audio_start_sec": 4.54},
                    {"avatar_video_path": "a.mp4", "audio_start_sec": 18.2},
                ]
            }
        ]
    }
    samples = collect_avatar_seek_samples(data)
    assert "a.mp4" in samples
    assert len(samples["a.mp4"]) <= 3
    assert 0.5 in samples["a.mp4"]


def test_maybe_auto_calibrate_skipped_when_disabled():
    data = {"slide_style": {"layouts": {"pip": {"crop_x_ratio": 0.5}}}}
    out = maybe_auto_calibrate_deck(data)
    assert "_avatar_calibration" not in out


def test_merge_framing_into_slide_style():
    style = merge_framing_into_slide_style(
        {},
        AvatarFramingResult("v.mp4", 0.52, 0.06, 1.45, 0.04, [0.5]),
    )
    assert style["layouts"]["pip"]["crop_x_ratio"] == 0.52


@pytest.mark.skipif(not HEYGEN.is_file(), reason="HeyGen sample video missing")
def test_calibrate_avatar_framing_finds_crop_x():
    cfg = CalibrationConfig(method="balance", crop_x_window=(0.50, 0.56))
    result = calibrate_avatar_framing(
        str(HEYGEN),
        seek_secs=[6.0],
        config=cfg,
    )
    assert 0.50 <= result.crop_x_ratio <= 0.56
    assert result.balance_score < 0.25

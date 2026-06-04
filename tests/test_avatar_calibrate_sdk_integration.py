"""Integration: calibration SDK → merged YAML → compositor head centred."""

from pathlib import Path

import pytest
import yaml

from praisonaippt.avatar_calibrate import (
    calibrate_deck_avatars,
    maybe_auto_calibrate_deck,
    pip_probe_size_px,
)
from praisonaippt.pip_face_measure import centring_advice, measure_pip_video

PKG = Path(__file__).resolve().parent.parent
HEYGEN_VIDEO = PKG / "examples" / "heygen-article-50590.mp4"
HEYGEN_DECK = PKG / "examples" / "heygen-50590-content.yaml"
CENTRE_SYMMETRY_LIMIT = 0.22
CENTRE_OFFSET_X_LIMIT = 0.05
MARGIN_LR_DELTA_LIMIT = 0.08


@pytest.mark.skipif(not HEYGEN_VIDEO.is_file(), reason="HeyGen sample video missing")
@pytest.mark.skipif(not HEYGEN_DECK.is_file(), reason="HeyGen content YAML missing")
def test_sdk_pipeline_calibrates_and_centres_head_in_compositor(tmp_path):
    """SDK sweep + auto-merge must yield |pip_face_balance| <= limit at Dreaming seek."""
    data = yaml.safe_load(HEYGEN_DECK.read_text(encoding="utf-8"))
    data["_source_file"] = str(HEYGEN_DECK.resolve())

    results = calibrate_deck_avatars(data, source_file=data["_source_file"], force=True)
    assert results
    primary = next(iter(results.values()))
    assert primary.balance_score < CENTRE_SYMMETRY_LIMIT
    assert 0.50 <= primary.crop_x_ratio <= 0.56
    assert primary.crop_x_ratio >= 0.53, "face-centred calibration should raise crop_x above balance-only ~0.505"

    merged = maybe_auto_calibrate_deck(data, source_file=data["_source_file"])
    pip_layout = merged["slide_style"]["layouts"]["pip"]
    crop_x = pip_layout["crop_x_ratio"]
    crop_y = float(pip_layout.get("crop_y_ratio", 0.03))
    zoom = float(pip_layout.get("zoom_ratio", 1.45))
    assert 0.50 <= crop_x <= 0.56
    pw, ph = pip_probe_size_px(merged["slide_style"])

    metrics, _ = measure_pip_video(
        str(HEYGEN_VIDEO),
        seek_sec=6.0,
        crop_x=crop_x,
        crop_y=crop_y,
        zoom=zoom,
        width=pw,
        height=ph,
        shape="circle",
    )
    assert metrics.face_fx is not None, "face detector required for centring SDK check"
    assert abs(metrics.centre_offset_x) <= CENTRE_OFFSET_X_LIMIT, (
        f"validation offset_x={metrics.centre_offset_x:+.3f} (crop_x={crop_x})"
    )
    lr = metrics.margin_lr_delta
    assert lr is not None and abs(lr) <= MARGIN_LR_DELTA_LIMIT, (
        f"L/R margin asymmetry {lr:+.3f} (want L≈R on diagram)"
    )
    advice = centring_advice(metrics)
    assert advice.is_centred or abs(metrics.centre_offset_x) <= CENTRE_OFFSET_X_LIMIT

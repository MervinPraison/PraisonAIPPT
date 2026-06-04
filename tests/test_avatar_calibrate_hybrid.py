"""Hybrid avatar calibration (face detect seed + anchored balance)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from praisonaippt.avatar_calibrate import (
    CalibrationConfig,
    _anchored_score,
    _effective_detector,
    calibrate_avatar_framing,
    pip_probe_size_px,
)
from praisonaippt.face_detect import FaceCentre
from praisonaippt.ffmpeg_composer import face_x_to_crop_x_ratio

PKG = Path(__file__).resolve().parent.parent
HEYGEN = PKG / "examples" / "heygen-article-50590.mp4"


def test_face_x_to_crop_x_ratio_centre_face():
    # Face at horizontal centre → crop_x 0.5
    assert abs(face_x_to_crop_x_ratio(0.5, 1280, 720, 460, 460, zoom_ratio=1.45) - 0.5) < 0.02


def test_anchored_score_prefers_preferred_crop_x():
    cfg = CalibrationConfig(crop_x_preferred=0.53, anchor_weight=0.15)
    at_pref = _anchored_score(0.05, 0.53, cfg)
    at_low = _anchored_score(0.05, 0.42, cfg)
    assert at_pref < at_low


def test_effective_detector_from_method():
    assert _effective_detector(CalibrationConfig(method="yolo")) == "yolo"
    assert _effective_detector(CalibrationConfig(method="mediapipe")) == "mediapipe"
    assert _effective_detector(CalibrationConfig(method="hybrid", detector="auto")) == "auto"


def test_calibration_config_defaults():
    cfg = CalibrationConfig.from_dict({"method": "hybrid", "crop_x_preferred": 0.53})
    assert cfg.crop_x_window == (0.50, 0.56)
    assert cfg.method == "hybrid"


def test_pip_probe_size_from_style():
    style = {"layouts": {"pip": {"width_ratio": 0.24}}}
    w, h = pip_probe_size_px(style, slide_w_px=1920)
    assert w == h == 461


def test_fixed_method_uses_preferred():
    cfg = CalibrationConfig(method="fixed", crop_x_preferred=0.53)
    if not HEYGEN.is_file():
        pytest.skip("HeyGen sample video missing")
    result = calibrate_avatar_framing(
        str(HEYGEN), seek_secs=[6.0], config=cfg,
    )
    assert result.crop_x_ratio == 0.53
    assert result.method == "fixed"


@pytest.mark.skipif(not HEYGEN.is_file(), reason="HeyGen sample video missing")
def test_hybrid_mock_face_near_preferred():
    cfg = CalibrationConfig(
        method="hybrid",
        crop_x_preferred=0.53,
        crop_x_window=(0.50, 0.56),
        anchor_weight=0.15,
    )
    centre = FaceCentre(fx=0.52, fy=0.35, confidence=0.9, detector="mediapipe")

    with patch("praisonaippt.face_detect.detect_face_centre", return_value=centre):
        result = calibrate_avatar_framing(
            str(HEYGEN), seek_secs=[6.0], config=cfg,
        )
    assert 0.50 <= result.crop_x_ratio <= 0.56
    assert abs(result.crop_x_ratio - 0.53) < abs(result.crop_x_ratio - 0.42)
    assert result.detector == "mediapipe"


@pytest.mark.skipif(not HEYGEN.is_file(), reason="HeyGen sample video missing")
def test_hybrid_integration_near_preferred():
    pytest.importorskip("mediapipe")
    cfg = CalibrationConfig(method="hybrid", crop_x_preferred=0.53)
    result = calibrate_avatar_framing(str(HEYGEN), seek_secs=[6.0], config=cfg)
    assert 0.50 <= result.crop_x_ratio <= 0.56
    assert result.balance_score < 0.25

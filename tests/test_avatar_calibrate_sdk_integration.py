"""Integration: calibration SDK → merged YAML → compositor head centred."""

from pathlib import Path

import pytest
import yaml

from praisonaippt.avatar_calibrate import (
    calibrate_deck_avatars,
    maybe_auto_calibrate_deck,
    pip_probe_size_px,
)
from praisonaippt.ffmpeg_composer import OverlaySpec, pip_face_balance, render_slide_segment
from praisonaippt.pip_face_measure import measure_pip_video

PKG = Path(__file__).resolve().parent.parent
HEYGEN_VIDEO = PKG / "examples" / "heygen-article-50590.mp4"
HEYGEN_DECK = PKG / "examples" / "heygen-50590-content.yaml"
SLIDE_BASE = PKG / "examples" / "slide_images" / "slide-003.jpg"

HEAD_BALANCE_LIMIT = 0.12
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
    crop_x = merged["slide_style"]["layouts"]["pip"]["crop_x_ratio"]
    assert 0.50 <= crop_x <= 0.56
    pw, ph = pip_probe_size_px(merged["slide_style"])

    import subprocess

    base = tmp_path / "base.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(SLIDE_BASE), str(base),
        ],
        check=True,
    )
    seg = tmp_path / "seg.mp4"
    ov = OverlaySpec(
        path=str(HEYGEN_VIDEO),
        x=1366,
        y=55,
        width=pw,
        height=ph,
        is_video=True,
        fit="cover",
        shape="circle",
        crop_x_ratio=crop_x,
        crop_y_ratio=0.06,
        zoom_ratio=1.45,
        video_start_sec=6.0,
    )
    render_slide_segment(str(base), 1.0, str(seg), width=1920, height=1080, overlays=[ov])
    frame = tmp_path / "frame.png"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(seg), "-vframes", "1", str(frame)],
        check=True,
    )
    from PIL import Image

    pip = Image.open(frame).crop((1366, 55, 1366 + pw, 55 + ph))
    balance = pip_face_balance(pip)
    assert abs(balance) <= HEAD_BALANCE_LIMIT, (
        f"SDK crop_x={crop_x} still off-centre at compositor (balance={balance:+.3f})"
    )

    metrics, _ = measure_pip_video(
        str(HEYGEN_VIDEO),
        seek_sec=6.0,
        crop_x=crop_x,
        crop_y=float(merged["slide_style"]["layouts"]["pip"].get("crop_y_ratio", 0.03)),
        zoom=1.45,
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

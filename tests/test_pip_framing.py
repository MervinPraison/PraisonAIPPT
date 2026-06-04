"""PiP face framing validation (HeyGen source + compositor path)."""

from pathlib import Path

import pytest

from praisonaippt.ffmpeg_composer import OverlaySpec, pip_face_balance, render_slide_segment

PKG = Path(__file__).resolve().parent.parent
HEYGEN_VIDEO = PKG / "examples" / "heygen-article-50590.mp4"
SLIDE_BASE = PKG / "examples" / "slide_images" / "slide-003.jpg"

PIP_BALANCE_TOLERANCE = 0.20


def _heygen_crop_x() -> float:
    if not HEYGEN_VIDEO.is_file():
        return 0.53
    from praisonaippt.avatar_calibrate import CalibrationConfig, calibrate_avatar_framing

    cfg = CalibrationConfig(method="hybrid", crop_x_preferred=0.53)
    return calibrate_avatar_framing(
        str(HEYGEN_VIDEO), seek_secs=[6.0], config=cfg,
    ).crop_x_ratio


@pytest.mark.skipif(not HEYGEN_VIDEO.is_file(), reason="HeyGen sample video missing")
def test_heygen_pip_face_centred_in_compositor(tmp_path):
    """Avatar face should be near horizontal centre in circle PiP (video export path)."""
    base_png = tmp_path / "base.png"
    import subprocess

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(SLIDE_BASE), str(base_png),
        ],
        check=True,
    )
    from praisonaippt.avatar_calibrate import pip_probe_size_px

    pw, ph = pip_probe_size_px({"layouts": {"pip": {"width_ratio": 0.24}}})
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
        crop_x_ratio=_heygen_crop_x(),
        crop_y_ratio=0.03,
        zoom_ratio=1.45,
        video_start_sec=6.0,
    )
    render_slide_segment(str(base_png), 1.0, str(seg), width=1920, height=1080, overlays=[ov])
    frame = tmp_path / "frame.png"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(seg), "-vframes", "1", str(frame)],
        check=True,
    )
    from PIL import Image

    pip = Image.open(frame).crop((1366, 55, 1366 + pw, 55 + ph))
    balance = pip_face_balance(pip)
    assert abs(balance) <= PIP_BALANCE_TOLERANCE, (
        f"PiP face balance {balance:+.3f} outside ±{PIP_BALANCE_TOLERANCE}; "
        f"tune layouts.pip.crop_x_ratio (lower → face right, higher → face left)"
    )


def test_manifest_uses_pip_crop_x_from_slide_style():
    import yaml
    from pptx import Presentation

    from praisonaippt.video_exporter import VideoOptions, build_video_manifest

    yaml_path = PKG / "examples" / "heygen-50590-video-visual-mp3.yaml"
    if not yaml_path.is_file():
        pytest.skip("variant yaml missing")
    with yaml_path.open() as f:
        data = yaml.safe_load(f)
    pptx = PKG / "examples" / "heygen-50590-video-visual-mp3.pptx"
    if not pptx.is_file():
        pytest.skip("pptx missing")
    data["_source_file"] = str(yaml_path.resolve())
    opts = VideoOptions.from_dict(data.get("video_export"), deck=data)
    entries = build_video_manifest(data, Presentation(str(pptx)), opts, source_file=data["_source_file"])
    exec_entry = next(e for e in entries if e.slide_type == "deck_exec_summary")
    assert 0.50 <= exec_entry.avatar_crop_x_ratio <= 0.56

"""Tests for PiP face centre measurement."""

from pathlib import Path

from PIL import Image

from praisonaippt.pip_face_measure import (
    PipFaceMetrics,
    _circle_margins_for_bbox,
    centring_advice,
    default_validation_image_path,
    face_centre_symmetry_score,
    save_pip_validation_diagram,
)


def test_circle_margins_symmetric_bbox():
    left, right, top, bottom = _circle_margins_for_bbox(0.4, 0.4, 0.6, 0.6)
    assert left > 0 and right > 0
    assert abs(left - right) < 0.05
    assert abs(top - bottom) < 0.05


def test_centred_face_offsets():
    m = PipFaceMetrics(
        face_fx=0.5, face_fy=0.45, centre_offset_x=0.0, centre_offset_y=-0.05,
        balance=0.02, margin_left=0.1, margin_right=0.1, margin_top=0.15, margin_bottom=0.12,
    )
    assert m.is_centred


def test_centring_advice_face_right_suggests_higher_crop_x():
    m = PipFaceMetrics(
        face_fx=0.57, face_fy=0.62, centre_offset_x=0.07, centre_offset_y=0.12,
        balance=-0.13, margin_left=0.25, margin_right=0.11, margin_top=0.34, margin_bottom=0.10,
        face_xmin=0.38, face_ymin=0.32, face_xmax=0.66, face_ymax=0.68,
    )
    advice = centring_advice(m)
    assert not advice.is_centred
    assert advice.crop_x_delta > 0
    assert advice.crop_y_delta < 0
    assert "increase crop_x" in advice.summary


def test_face_centre_symmetry_score_lower_when_balanced_margins():
    off = PipFaceMetrics(
        face_fx=0.57, face_fy=0.62, centre_offset_x=0.07, centre_offset_y=0.12,
        balance=-0.13, margin_left=0.25, margin_right=0.11, margin_top=0.34, margin_bottom=0.10,
    )
    centred = PipFaceMetrics(
        face_fx=0.50, face_fy=0.48, centre_offset_x=0.01, centre_offset_y=-0.02,
        balance=0.01, margin_left=0.12, margin_right=0.11, margin_top=0.14, margin_bottom=0.13,
    )
    assert face_centre_symmetry_score(centred) < face_centre_symmetry_score(off)


def test_default_validation_image_path():
    p = default_validation_image_path("/tmp/probe_0.50_0.505.png")
    assert p.name == "probe_0.50_0.505_pip_validation.png"


def test_save_pip_validation_diagram(tmp_path):
    probe = tmp_path / "probe.png"
    Image.new("RGBA", (120, 120), (40, 40, 40, 255)).save(probe)
    metrics = PipFaceMetrics(
        face_fx=0.52,
        face_fy=0.48,
        centre_offset_x=0.02,
        centre_offset_y=-0.02,
        balance=0.01,
        margin_left=0.08,
        margin_right=0.10,
        margin_top=0.12,
        margin_bottom=0.11,
        detector="test",
        face_xmin=0.38,
        face_ymin=0.32,
        face_xmax=0.66,
        face_ymax=0.68,
    )
    out = tmp_path / "diagram.png"
    saved = save_pip_validation_diagram(probe, metrics, out)
    assert saved.is_file()
    assert saved.stat().st_size > 500
    with Image.open(saved) as im:
        assert im.size[1] == 120 + 56

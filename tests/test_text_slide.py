"""Tests for progressive text slides."""
from pathlib import Path

from praisonaippt.daily_single.text_slide import render_point_slide, slide_specs, visual_meta_from_specs


def test_render_point_slide_writes_png(tmp_path: Path):
    dest = tmp_path / "slide.png"
    render_point_slide(dest, headline="Test headline", bullets=["One", "Two"], step=1, total=3)
    assert dest.is_file()
    assert dest.stat().st_size > 1000


def test_beat01_single_professional_slide():
    points = slide_specs()["beat-01-rest"]
    assert len(points) == 1
    assert points[0]["file"] == "beat1-launch-summary.png"
    assert len(points[0]["bullets"]) == 3


def test_single_slide_no_step_badge(tmp_path: Path):
    dest = tmp_path / "one.png"
    render_point_slide(
        dest,
        headline="One professional slide",
        bullets=["Point A", "Point B"],
        show_steps=False,
    )
    assert dest.is_file()


def test_visual_meta_from_specs():
    meta = visual_meta_from_specs()
    assert "beat1-launch-summary.png" in meta
    assert "outro-cta.png" in meta

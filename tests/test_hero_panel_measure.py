"""Tests for hero panel measurement and validation diagrams (parity with pip_face_measure)."""

from pathlib import Path
from unittest.mock import patch

from PIL import Image

from praisonaippt.hero_panel_measure import (
    HeroPanelMetrics,
    default_hero_validation_image_path,
    format_hero_panel_measure_report,
    panel_clearance_score,
    placement_advice,
    save_hero_panel_validation_diagram,
    _edge_clearances,
    _overlap_ratio,
)
from praisonaippt.text_region_detect import TextRegion

PKG = Path(__file__).resolve().parent.parent
IMG = PKG / "assets" / "background_alt.jpg"


def test_overlap_ratio_empty_obstacles():
    panel = (40, 40, 400, 200)
    assert _overlap_ratio(panel, []) == 0.0


def test_overlap_ratio_half_cover():
    panel = (0, 0, 100, 100)
    obs = [(50, 0, 150, 100)]
    assert abs(_overlap_ratio(panel, obs) - 0.5) < 0.01


def test_edge_clearances_no_obstacles():
    panel = (100, 80, 500, 300)
    cl, cr, ct, cb = _edge_clearances(panel, [])
    assert cl == 100 and cr > 1000


def test_clear_panel_metrics():
    m = HeroPanelMetrics(
        anchor="top_right",
        panel_left=1200, panel_top=40, panel_width=400, panel_height=180,
        overlap_ratio=0.02,
        clearance_left=80, clearance_right=120, clearance_top=30, clearance_bottom=200,
        score=0.05, confidence=0.9, region_count=3, detector="test",
    )
    assert m.is_clear
    advice = placement_advice(m)
    assert advice.is_clear


def test_panel_clearance_score_lower_when_clear():
    clear = HeroPanelMetrics(
        anchor="top_left", panel_left=40, panel_top=40, panel_width=400, panel_height=180,
        overlap_ratio=0.01,
        clearance_left=40, clearance_right=200, clearance_top=40, clearance_bottom=300,
        score=0.04, confidence=0.95, region_count=2, detector="test",
    )
    bad = HeroPanelMetrics(
        anchor="bottom_right", panel_left=1400, panel_top=800, panel_width=400, panel_height=180,
        overlap_ratio=0.35,
        clearance_left=5, clearance_right=5, clearance_top=5, clearance_bottom=5,
        score=2.0, confidence=0.3, region_count=40, detector="test", pip_overlap=True,
    )
    assert panel_clearance_score(clear) < panel_clearance_score(bad)


def test_default_hero_validation_image_path():
    p = default_hero_validation_image_path("/tmp/hero.jpg")
    assert p.name == "hero_hero_panel_validation.png"


def test_save_hero_panel_validation_diagram(tmp_path):
    img = tmp_path / "hero.jpg"
    Image.new("RGB", (640, 360), (30, 30, 30)).save(img)
    metrics = HeroPanelMetrics(
        anchor="top_left",
        panel_left=40, panel_top=40, panel_width=320, panel_height=120,
        overlap_ratio=0.0,
        clearance_left=40, clearance_right=500, clearance_top=40, clearance_bottom=400,
        score=0.01, confidence=0.95, region_count=0, detector="test",
    )
    style = {"layouts": {"avatar_media_3": {"hero_layout": "full_bleed"}, "pip": {"width_ratio": 0.2}}}
    data = {"slide_size": "widescreen"}
    verse = {
        "slide_type": "avatar_media_3",
        "headline": "Test",
        "media_fit": "contain",
        "text_panel": {"anchor": "top_left", "width_ratio": 0.36, "height_in": 0.9},
    }
    out = tmp_path / "diagram.png"
    saved = save_hero_panel_validation_diagram(
        img, metrics, out, style=style, data=data, verse=verse,
    )
    assert saved.is_file()
    assert saved.stat().st_size > 800
    with Image.open(saved) as im:
        assert im.size[1] == 1080 + 56


def test_format_hero_panel_measure_report():
    m = HeroPanelMetrics(
        anchor="top_right",
        panel_left=1200, panel_top=40, panel_width=400, panel_height=180,
        overlap_ratio=0.02,
        clearance_left=80, clearance_right=120, clearance_top=30, clearance_bottom=200,
        score=0.05, confidence=0.9, region_count=3, detector="east",
    )
    text = format_hero_panel_measure_report(m)
    assert "Hero text panel measurement" in text
    assert "clearances px" in text


@patch("praisonaippt.hero_panel_measure.detect_text_regions")
@patch("praisonaippt.hero_panel_measure.calibrate_hero_panel")
def test_measure_hero_panel_image(mock_cal, mock_det, tmp_path):
    from praisonaippt.hero_panel_calibrate import HeroPanelResult
    from praisonaippt.hero_panel_measure import measure_hero_panel_image

    img = tmp_path / "shot.jpg"
    Image.new("RGB", (800, 450), (40, 40, 40)).save(img)
    mock_det.return_value = [TextRegion(0.1, 0.1, 0.3, 0.2, 0.8, "test")]
    mock_cal.return_value = HeroPanelResult(
        media_path="shot.jpg", anchor="top_left", score=0.1,
        confidence=0.85, detector="test", region_count=1,
    )
    style = {"layouts": {"avatar_media_3": {"hero_layout": "full_bleed"}, "pip": {"width_ratio": 0.2}}}
    data = {"slide_size": "widescreen"}
    verse = {
        "slide_type": "avatar_media_3",
        "headline": "Hi",
        "media_path": str(img),
        "media_fit": "contain",
        "text_panel": {"anchor": "auto", "width_ratio": 0.36, "height_in": 0.9},
    }
    metrics, result = measure_hero_panel_image(img, style=style, data=data, verse=verse)
    assert result.anchor == "top_left"
    assert metrics.panel_width > 0

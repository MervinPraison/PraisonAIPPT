"""Tests for hero text panel auto-placement."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pptx import Presentation

from praisonaippt.avatar_layouts import _verse_text_panel_cfg
from praisonaippt.exceptions import SchemaError
from praisonaippt.hero_panel_calibrate import (
    HeroTextConfig,
    calibrate_hero_panel,
    map_regions_to_slide_px,
    maybe_auto_place_hero_text_deck,
    score_anchor,
)
from praisonaippt.text_region_detect import TextRegion
from praisonaippt.yaml_validate import validate_deck_options, validate_verse_options

PKG = Path(__file__).resolve().parent.parent
IMG = PKG / "assets" / "background_alt.jpg"


def test_schema_accepts_anchor_auto():
    validate_verse_options(
        {"slide_type": "avatar_media_3", "text_panel": {"anchor": "auto"}},
        "sections[0].verses[0]",
    )


def test_schema_rejects_invalid_anchor():
    with pytest.raises(SchemaError, match="anchor"):
        validate_verse_options(
            {"slide_type": "avatar_media_3", "text_panel": {"anchor": "middle"}},
            "sections[0].verses[0]",
        )


def test_hero_text_placement_block_validates():
    validate_deck_options({
        "hero_text_placement": {
            "auto": True,
            "method": "hybrid",
            "detector": "auto",
            "preferred_anchor": "top_right",
            "fallback_anchor": "top_left",
        },
    })


def test_verse_text_panel_cfg_resolves_auto_anchor():
    style = {"layouts": {"avatar_media_3": {"text_anchor": "top_left"}}}
    verse = {"text_panel": {"anchor": "auto"}, "_hero_panel_anchor": "bottom_left"}
    cfg = _verse_text_panel_cfg(style, verse, "avatar_media_3")
    assert cfg["anchor"] == "bottom_left"


def test_map_regions_contain_letterbox():
    regions = [TextRegion(0.1, 0.1, 0.4, 0.2, 0.9, "test")]
    boxes = map_regions_to_slide_px(
        regions, img_w=1200, img_h=800,
        slide_w_in=13.33, slide_h_in=7.5, media_fit="contain",
    )
    assert len(boxes) == 1
    x0, y0, x1, y1 = boxes[0]
    assert x0 >= 0 and y1 <= 1080


def test_score_anchor_rejects_pip_overlap():
    panel = {"x": 1500, "y": 750, "width": 350, "height": 280}
    pip = {"x": 1600, "y": 800, "width": 280, "height": 280}
    cfg = HeroTextConfig(preferred_anchor="top_right")
    assert score_anchor(panel, [], pip, anchor="bottom_right", cfg=cfg) is None


def test_score_anchor_prefers_low_overlap():
    panel = {"x": 40, "y": 40, "width": 400, "height": 200}
    obstacles = [(500, 200, 900, 400)]
    pip = {"x": 1600, "y": 800, "width": 280, "height": 280}
    cfg = HeroTextConfig(preferred_anchor="top_left")
    good = score_anchor(panel, obstacles, pip, anchor="top_left", cfg=cfg)
    bad_panel = {"x": 520, "y": 210, "width": 350, "height": 180}
    bad = score_anchor(bad_panel, obstacles, pip, anchor="top_left", cfg=cfg)
    assert good is not None
    assert bad is None or good < bad


@patch("praisonaippt.hero_panel_calibrate.detect_text_regions")
def test_calibrate_hero_panel_picks_anchor(mock_detect):
    mock_detect.return_value = [
        TextRegion(0.05, 0.05, 0.55, 0.35, 0.9, "mser"),
    ]
    if not IMG.is_file():
        pytest.skip("fixture image missing")
    verse = {
        "slide_type": "avatar_media_3",
        "headline": "Dreaming",
        "subheader": "Agents",
        "media_path": str(IMG.relative_to(PKG)),
        "media_fit": "contain",
        "text_panel": {"anchor": "auto", "width_ratio": 0.36, "height_in": 0.95},
    }
    style = {
        "layouts": {
            "avatar_media_3": {
                "hero_layout": "full_bleed",
                "panel_width_ratio": 0.36,
                "panel_margin_in": 0.34,
                "text_pip_gap_in": 0.14,
                "pip_width_ratio": 0.15,
                "pip_margin_in": 0.32,
            },
            "pip": {"width_ratio": 0.2, "shape": "circle"},
        },
    }
    data = {"slide_size": "widescreen", "slide_style": style}
    result = calibrate_hero_panel(
        verse, style=style, data=data, source_file=str(PKG), cfg=HeroTextConfig(),
    )
    assert result.anchor in {
        "top_left", "top_right", "bottom_left", "bottom_right", "top", "bottom",
    }
    assert result.confidence >= 0.0


@patch("praisonaippt.hero_panel_calibrate.calibrate_deck_hero_panels")
def test_maybe_auto_place_sets_verse_anchor(mock_cal):
    from praisonaippt.hero_panel_calibrate import HeroPanelResult

    mock_cal.return_value = {
        "slide_images/x.jpg": HeroPanelResult(
            media_path="slide_images/x.jpg",
            anchor="top_right",
            score=0.1,
            confidence=0.8,
            detector="mser",
        ),
    }
    data = {
        "hero_text_placement": {"auto": True},
        "sections": [{
            "verses": [{
                "slide_type": "avatar_media_3",
                "media_path": "slide_images/x.jpg",
                "text_panel": {"anchor": "auto"},
            }],
        }],
    }
    out = maybe_auto_place_hero_text_deck(data, source_file=str(PKG))
    verse = out["sections"][0]["verses"][0]
    assert verse["_hero_panel_anchor"] == "top_right"


def test_panel_px_all_anchors_distinct():
    from praisonaippt.hero_panel_calibrate import _panel_px

    prs = Presentation()
    style = {
        "layouts": {
            "avatar_media_3": {
                "hero_layout": "full_bleed",
                "panel_width_ratio": 0.36,
                "panel_margin_in": 0.34,
            },
            "pip": {"width_ratio": 0.2},
        },
    }
    verse = {
        "headline": "Test",
        "subheader": "Sub",
        "text_panel": {"anchor": "auto", "width_ratio": 0.36, "height_in": 0.9},
    }
    anchors = ["top_left", "top_right", "bottom_left", "bottom_right", "top", "bottom"]
    boxes = [_panel_px(prs, style, verse, a) for a in anchors]
    assert len({(b["x"], b["y"]) for b in boxes}) >= 4


def test_calibration_presentation_respects_slide_size():
    from praisonaippt.hero_panel_calibrate import calibration_presentation

    prs = calibration_presentation({"slide_size": "standard"})
    assert abs(prs.slide_width.inches - 10.0) < 0.01


def test_maybe_auto_place_skipped_when_disabled():
    data = {"hero_text_placement": {"auto": False}, "sections": []}
    out = maybe_auto_place_hero_text_deck(data)
    assert out is data


@patch("praisonaippt.hero_panel_calibrate.detect_text_regions")
def test_calibrate_fallback_when_all_rejected(mock_detect):
    mock_detect.return_value = [
        TextRegion(0.35, 0.35, 0.65, 0.55, 0.9, "test"),
    ] * 20
    from pptx import Presentation
    from praisonaippt.hero_panel_calibrate import calibration_presentation

    style = {
        "layouts": {
            "avatar_media_3": {"hero_layout": "full_bleed", "panel_margin_in": 0.34},
            "pip": {"width_ratio": 0.2},
        },
    }
    verse = {
        "headline": "X",
        "media_path": "missing.jpg",
        "text_panel": {"anchor": "auto"},
    }
    result = calibrate_hero_panel(
        verse, style=style, data={"slide_size": "widescreen"},
        cfg=HeroTextConfig(fallback_anchor="top_left"),
    )
    assert result.anchor == "top_left"
    assert result.confidence == 0.0

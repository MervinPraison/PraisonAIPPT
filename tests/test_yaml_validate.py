"""Tests for deck YAML option validation (slide_style, video_export, verse enums)."""

import logging
from pathlib import Path

import pytest
import yaml

from praisonaippt.exceptions import SchemaError
from praisonaippt.schema import validate_verses
from praisonaippt.yaml_validate import (
    validate_deck_options,
    validate_slide_style,
    validate_video_export,
    validate_verse_options,
)

PKG = Path(__file__).resolve().parent.parent
HEYGEN_CONTENT = PKG / "examples" / "heygen-50590-content.yaml"
AVATAR_GALLERY = PKG / "examples" / "avatar_layouts.yaml"
DECK_GALLERY = PKG / "examples" / "deck_template_gallery.yaml"


def test_heygen_content_yaml_passes_validation():
    data = yaml.safe_load(HEYGEN_CONTENT.read_text(encoding="utf-8"))
    validate_verses(data)


def test_avatar_gallery_yaml_passes_validation():
    data = yaml.safe_load(AVATAR_GALLERY.read_text(encoding="utf-8"))
    validate_verses(data)


def test_deck_gallery_yaml_passes_validation():
    data = yaml.safe_load(DECK_GALLERY.read_text(encoding="utf-8"))
    validate_verses(data)


def test_invalid_narration_mode_raises():
    with pytest.raises(SchemaError, match="narration_mode"):
        validate_verses({
            "sections": [{
                "verses": [{
                    "text": "x",
                    "narration_mode": "karaoke",
                }],
            }],
        })


def test_invalid_video_export_preset_raises():
    with pytest.raises(SchemaError, match="preset"):
        validate_video_export({"preset": "ultra"})


def test_invalid_color_scheme_raises():
    with pytest.raises(SchemaError, match="color_scheme"):
        validate_verse_options(
            {"text": "t", "color_scheme": "not_a_preset"},
            "sections[0].verses[0]",
        )


def test_invalid_pip_shape_in_slide_style_raises():
    with pytest.raises(SchemaError, match="shape"):
        validate_slide_style({
            "layouts": {"pip": {"shape": "hexagon"}},
        })


def test_invalid_slide_size_preset_raises():
    with pytest.raises(SchemaError, match="slide_size"):
        validate_deck_options({"slide_size": "ultrawide"})


def test_table_empty_row_raises():
    with pytest.raises(SchemaError, match="table_rows"):
        validate_verses({
            "sections": [{
                "verses": [{
                    "slide_type": "table",
                    "table_rows": [["H1", "H2"], []],
                }],
            }],
        })


def test_invalid_list_type_raises():
    with pytest.raises(SchemaError, match="list_type"):
        validate_verses({
            "sections": [{
                "verses": [{
                    "text": "a",
                    "list_type": "dashes",
                }],
            }],
        })


def test_unknown_layout_key_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="praisonaippt.schema"):
        validate_slide_style({
            "layouts": {"pip": {"width_ratio": 0.2, "not_a_real_key": 1}},
        })
    assert any("not_a_real_key" in rec.message for rec in caplog.records)


def test_dark_table_slide_style_passes():
    validate_verses({
        "slide_style": {
            "background_color": "#000000",
            "layouts": {
                "table": {
                    "header_fill": "#2563EB",
                    "row_fill": "#1F2937",
                    "min_font_pt": 11,
                },
                "pip": {"width_ratio": 0.2, "shape": "circle"},
            },
        },
        "sections": [{
            "verses": [{
                "slide_type": "table",
                "table_rows": [["A", "B"], ["1", "2"]],
                "avatar_video_path": "examples/heygen-article-50590.mp4",
            }],
        }],
    })

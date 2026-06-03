"""Layout SDK defaults and helpers (inches in layouts.*, pt in typography.*)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from pptx.util import Inches, Length

LAYOUT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "title": {
        "margin_in": 0.6,
        "title_top_in": 2.5,
        "subtitle_gap_in": 0.25,
        "custom_subtitle_min_len": 40,
    },
    "section": {
        "margin_in": 0.6,
        "subtitle_dim_factor": 0.76,
    },
    "verse": {
        "margin_in": 0.6,
        "ref_top_in": 0.3,
        "ref_height_in": 0.7,
        "ref_height_large_in": 0.95,
        "body_gap_in": 0.15,
        "leading_title_top_in": 0.35,
        "leading_title_ref_gap_in": 0.2,
        "bottom_ref_top_in": 6.0,
        "bottom_ref_height_in": 0.7,
        "default_body_height_in": 4.5,
        "no_ref_body_top_in": 1.5,
        "no_ref_body_height_in": 3.8,
        "bottom_margin_in": 0.15,
        "extra_ref_reserve_in": 1.32,
    },
    "list": {
        "margin_in": 0.6,
        "list_top_in": 0.35,
        "list_bottom_margin_in": 0.4,
        "list_bottom_reserve_in": 6.0,
        "ref_gap_in": 0.12,
        "ref_bottom_offset_in": 0.35,
    },
    "image": {
        "margin_in": 0.35,
        "caption_height_in": 0.9,
    },
    "hebrew_rename": {
        "row_y_in": [1.15, 4.05],
        "box_height_in": 1.35,
        "reference_width_in": 10.0,
        "left_x_factor": 0.35,
        "right_x_factor": 5.15,
        "box_width_factor": 4.2,
        "caption_height_in": 0.85,
        "caption_bottom_in": 0.45,
        "caption_margin_in": 0.5,
    },
    "title_only": {
        "margin_in": 0.6,
    },
    "two_column": {
        "margin_in": 0.6,
        "top_in": 0.9,
        "column_gap_in": 0.4,
        "bottom_reserve_in": 0.5,
    },
    "comparison": {
        "margin_in": 0.6,
        "top_in": 0.75,
        "heading_height_in": 0.55,
        "column_gap_in": 0.4,
        "body_top_gap_in": 0.12,
        "bottom_reserve_in": 0.5,
    },
    "big_number": {
        "margin_in": 0.6,
    },
    "quote": {
        "margin_in": 0.8,
        "top_in": 2.0,
    },
    "picture_text": {
        "margin_in": 0.35,
        "column_gap_in": 0.35,
        "image_width_ratio": 0.48,
    },
    "table": {
        "margin_in": 0.6,
        "top_in": 0.75,
    },
    "avatar_only": {},
    "media_only": {},
    "avatar_media_1": {
        "media_width_ratio": 0.50,
        "gap_in": 0,
    },
    "avatar_media_2": {
        "media_width_ratio": 0.40,
        "gap_in": 0,
    },
    "avatar_media_3": {
        "pip_width_ratio": 0.18,
        "pip_margin_in": 0.35,
    },
    "avatar_name_card": {
        "panel_width_ratio": 0.42,
        "panel_height_in": 1.35,
        "panel_margin_in": 0.35,
    },
    "avatar_headline": {
        "panel_width_ratio": 0.42,
        "panel_height_in": 1.1,
        "panel_margin_in": 0.35,
    },
    "avatar_quote": {
        "quote_bg_color": "#1E3A5F",
        "pip_width_ratio": 0.16,
        "pip_margin_in": 0.35,
        "top_in": 1.8,
    },
    "avatar_border": {
        "border_inset_in": 0.25,
        "border_width_pt": 8,
        "border_color": "#1E3A5F",
    },
    "media_border": {
        "border_inset_in": 0.25,
        "border_width_pt": 8,
        "border_color": "#1E3A5F",
    },
    "avatar_media_border_1": {
        "media_width_ratio": 0.60,
        "inner_gap_in": 0.15,
        "inner_radius_in": 0.12,
        "border_inset_in": 0.25,
        "border_width_pt": 8,
        "border_color": "#1E3A5F",
    },
    "avatar_media_border_2": {
        "media_width_ratio": 0.40,
        "inner_gap_in": 0.15,
        "inner_radius_in": 0.12,
        "border_inset_in": 0.25,
        "border_width_pt": 8,
        "border_color": "#1E3A5F",
    },
    "avatar_media_border_3": {
        "pip_width_ratio": 0.18,
        "pip_margin_in": 0.35,
        "border_inset_in": 0.25,
        "border_width_pt": 8,
        "border_color": "#1E3A5F",
    },
}

TYPOGRAPHY_DEFAULTS: Dict[str, Any] = {
    "title_size_pt": 44,
    "subtitle_size_pt": 28,
    "section_title_size_pt": 44,
    "section_subtitle_size_pt": 24,
    "body_size_pt": 32,
    "reference_size_pt": 28,
    "reference_size_small_pt": 24,
    "reference_size_list_top_pt": 26,
    "reference_size_list_bottom_pt": 22,
    "reference_size_bottom_pt": 22,
    "leading_title_size_pt": 38,
    "annotation_size_pt": 46,
    "list_ref_top_pt": 26,
    "list_ref_bottom_pt": 22,
    "caption_ref_size_pt": 22,
    "caption_body_size_pt": 18,
    "big_number_size_pt": 120,
    "big_number_label_size_pt": 32,
    "quote_size_pt": 36,
    "comparison_heading_size_pt": 28,
}


def layout_in(style: dict, kind: str, key: str, default: Any = None) -> Any:
    """Read a layout token in inches (or other scalar) from slide_style.layouts."""
    if default is None and kind in LAYOUT_DEFAULTS and key in LAYOUT_DEFAULTS[kind]:
        default = LAYOUT_DEFAULTS[kind][key]
    layouts = (style or {}).get("layouts") or {}
    block = layouts.get(kind) or {}
    val = block.get(key, default)
    return default if val is None else val


def typography_pt(style: dict, key: str, default: Any = None) -> Any:
    """Read a typography token in pt from slide_style.typography."""
    if default is None and key in TYPOGRAPHY_DEFAULTS:
        default = TYPOGRAPHY_DEFAULTS[key]
    typography = (style or {}).get("typography") or {}
    val = typography.get(key, default)
    return default if val is None else val


def split_max_length_default(style: dict) -> int:
    """Deck-level default for verse text splitting."""
    raw = (style or {}).get("split_max_length", 200)
    try:
        return max(int(raw), 50)
    except (TypeError, ValueError):
        return 200


def title_custom_threshold(style: dict) -> int:
    return int(layout_in(style, "title", "custom_subtitle_min_len", 40))


def content_width_inches(prs, style: dict, kind: str, default_margin_in: Optional[float] = None) -> float:
    """Content width in inches; verse/list cap at 9.0 on widescreen unless overridden."""
    margin_in = layout_in(
        style, kind, "margin_in", default_margin_in if default_margin_in is not None else 0.6
    )
    fixed = layout_in(style, kind, "content_width_in", None)
    if fixed is not None:
        return float(fixed)
    slide_w_in = prs.slide_width.inches
    natural = slide_w_in - 2 * float(margin_in)
    if kind in ("verse", "list"):
        return min(9.0, natural)
    return natural


def content_box(
    prs, style: dict, kind: str, default_margin_in: Optional[float] = None
) -> Tuple[Length, Length, float, float]:
    """Return (left, width, width_in, margin_in) centred on the slide."""
    margin_in = float(
        layout_in(
            style, kind, "margin_in", default_margin_in if default_margin_in is not None else 0.6
        )
    )
    width_in = content_width_inches(prs, style, kind, margin_in)
    left_in = (prs.slide_width.inches - width_in) / 2
    return Inches(left_in), Inches(width_in), width_in, margin_in


def body_font_size(style: dict, verse: dict) -> int:
    """verse.font_size > typography.body_size_pt > 32."""
    if verse.get("font_size") is not None:
        return int(verse["font_size"])
    return int(typography_pt(style, "body_size_pt", 32))

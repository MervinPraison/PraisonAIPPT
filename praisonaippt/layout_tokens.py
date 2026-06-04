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
        "bottom_in": 0.35,
        "ref_gap_in": 0.15,
        "min_font_pt": 11,
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
        "pip_width_ratio": 0.14,
        "pip_margin_in": 0.45,
    },
    "avatar_name_card": {
        "panel_width_ratio": 0.42,
        "panel_margin_in": 0.35,
        "name_pill_height_in": 0.72,
        "title_pill_height_in": 0.55,
        "pill_gap_in": 0.12,
        "pill_radius_in": 0.08,
    },
    "avatar_headline": {
        "panel_margin_in": 0.75,
        "pip_width_ratio": 0.14,
        "pip_margin_in": 0.45,
    },
    "avatar_headline_full": {
        "panel_width_ratio": 0.48,
        "panel_height_in": 1.45,
        "panel_margin_in": 0.35,
    },
    "avatar_intro": {},
    "avatar_outro": {
        "diamond_size_in": 1.85,
    },
    "avatar_quote": {
        "quote_bg_color": "#1E3A5F",
        "pip_width_ratio": 0.14,
        "pip_margin_in": 0.45,
        "margin_in": 0.75,
        "top_in": 1.4,
    },
    "pip": {
        "width_ratio": 0.20,
        "margin_in": 0.38,
        "text_gap_in": 0.35,
        "shape": "circle",
        "crop_y_ratio": 0.06,
        "zoom_ratio": 1.45,
        "border_color": "#FFFFFF",
        "border_width_pt": 2.5,
    },
    "list": {
        "margin_in": 0.75,
        "list_bottom_margin_in": 1.0,
        "ref_gap_in": 0.18,
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
    "deck_title_split": {
        "margin_in": 0.75,
        "avatar_width_ratio": 0.5,
        "avatar_shape": "rect",
        "color_scheme": "sales_blue",
    },
    "deck_exec_summary": {
        "margin_in": 0.65,
        "pip_position": "top_right",
        "pip_width_ratio": 0.12,
        "columns_top_in": 2.05,
        "column_gap_in": 0.35,
        "color_scheme": "exec_grey",
    },
    "deck_split_performance": {
        "margin_in": 0.65,
        "left_width_ratio": 0.45,
        "left_bg_color": "#4338CA",
        "avatar_height_in": 3.0,
        "avatar_shape": "rect",
        "color_scheme": "split_blue",
    },
    "deck_region_grid": {
        "margin_in": 0.65,
        "pip_position": "bottom_left",
        "pip_width_ratio": 0.14,
        "grid_top_in": 1.55,
        "color_scheme": "region_navy",
    },
    "deck_product_columns": {
        "margin_in": 0.65,
        "pip_position": "top_right",
        "pip_width_ratio": 0.12,
        "columns_top_in": 1.85,
        "column_gap_in": 0.25,
        "color_scheme": "product_lavender",
    },
    "deck_channel_analysis": {
        "margin_in": 0.65,
        "left_width_ratio": 0.45,
        "avatar_height_in": 3.0,
        "avatar_shape": "rect",
        "badge_width_in": 0.95,
        "badge_height_in": 0.55,
        "color_scheme": "channel_violet",
    },
    "deck_customer_segments": {
        "margin_in": 0.65,
        "pip_position": "top_right",
        "pip_width_ratio": 0.12,
        "columns_top_in": 1.55,
        "column_gap_in": 0.35,
        "color_scheme": "segments_sky",
    },
    "deck_thank_you": {
        "margin_in": 0.75,
        "avatar_width_ratio": 0.5,
        "avatar_shape": "rect",
        "color_scheme": "thank_you_blue",
    },
    "deck_agenda": {
        "margin_in": 0.65,
        "agenda_columns": 2,
        "list_top_in": 1.35,
        "row_height_in": 0.52,
        "badge_width_in": 0.42,
        "column_gap_in": 0.55,
        "color_scheme": "agenda_periwinkle",
    },
    "deck_intro_split": {
        "margin_in": 0.65,
        "top_height_ratio": 0.45,
        "title_width_ratio": 0.38,
        "media_fit": "cover",
        "color_scheme": "intro_grey",
    },
    "deck_opportunity_cards": {
        "margin_in": 0.65,
        "columns_top_in": 1.25,
        "column_gap_in": 0.3,
        "image_height_in": 1.35,
        "color_scheme": "opportunity_grey",
    },
    "deck_forecast_split": {
        "margin_in": 0.65,
        "top_height_ratio": 0.45,
        "items_top_in": 1.15,
        "column_gap_in": 0.35,
        "media_fit": "cover",
        "color_scheme": "forecast_grey",
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
    reserve = pip_reserve_inches(style, slide_w_in)
    if reserve and kind == "list":
        natural = slide_w_in - float(margin_in) - reserve
    elif reserve:
        natural = slide_w_in - 2 * float(margin_in) - reserve
    else:
        natural = slide_w_in - 2 * float(margin_in)
    if kind in ("verse", "list"):
        return min(9.0, max(natural, 5.0))
    return max(natural, 4.5)


def _pip_enabled(style: dict) -> bool:
    if (style or {}).get("avatar_pip"):
        return True
    pip = ((style or {}).get("layouts") or {}).get("pip")
    return isinstance(pip, dict) and bool(pip)


def pip_size_inches(style: dict, slide_w_in: float) -> float:
    if not _pip_enabled(style):
        return 0.0
    ratio = float(layout_in(style, "pip", "width_ratio", 0.14))
    return slide_w_in * ratio


def pip_reserve_inches(style: dict, slide_w_in: float) -> float:
    """Horizontal space to keep clear for the bottom-right avatar PiP."""
    if not _pip_enabled(style):
        return 0.0
    gap = float(layout_in(style, "pip", "text_gap_in", 0.35))
    margin = float(layout_in(style, "pip", "margin_in", 0.45))
    return pip_size_inches(style, slide_w_in) + margin + gap


def pip_top_inches(style: dict, slide_h_in: float, slide_w_in: float) -> float:
    """Top edge (inches) of the PiP region — content should stay above this."""
    if not _pip_enabled(style):
        return slide_h_in
    margin = float(layout_in(style, "pip", "margin_in", 0.45))
    return slide_h_in - pip_size_inches(style, slide_w_in) - margin


def content_box(
    prs, style: dict, kind: str, default_margin_in: Optional[float] = None
) -> Tuple[Length, Length, float, float]:
    """Return (left, width, width_in, margin_in) centred on the slide (PiP-aware)."""
    margin_in = float(
        layout_in(
            style, kind, "margin_in", default_margin_in if default_margin_in is not None else 0.6
        )
    )
    slide_w_in = prs.slide_width.inches
    width_in = content_width_inches(prs, style, kind, margin_in)
    reserve = pip_reserve_inches(style, slide_w_in)
    if reserve:
        usable_w = slide_w_in - reserve
        left_in = max(margin_in, (usable_w - width_in) / 2.0)
    else:
        left_in = (slide_w_in - width_in) / 2.0
    return Inches(left_in), Inches(width_in), width_in, margin_in


def body_font_size(style: dict, verse: dict) -> int:
    """verse.font_size > typography.body_size_pt > 32."""
    if verse.get("font_size") is not None:
        return int(verse["font_size"])
    return int(typography_pt(style, "body_size_pt", 32))

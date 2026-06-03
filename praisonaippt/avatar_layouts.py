"""Avatar and media layout slides (speaking-head video + media regions)."""

from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from .layout_tokens import content_box, layout_in, typography_pt
from .utils import resolve_asset_path

AVATAR_SLIDE_TYPES = (
    "avatar_only",
    "media_only",
    "avatar_media_1",
    "avatar_media_2",
    "avatar_media_3",
    "avatar_name_card",
    "avatar_headline",
    "avatar_quote",
    "avatar_border",
    "media_border",
    "avatar_media_border_1",
    "avatar_media_border_2",
    "avatar_media_border_3",
)

_BORDER_KINDS = frozenset({
    "avatar_border",
    "media_border",
    "avatar_media_border_1",
    "avatar_media_border_2",
    "avatar_media_border_3",
})

_SPLIT_KINDS = frozenset({
    "avatar_media_1",
    "avatar_media_2",
    "avatar_media_border_1",
    "avatar_media_border_2",
})

_PIP_KINDS = frozenset({
    "avatar_media_3",
    "avatar_media_border_3",
    "avatar_quote",
})

_VIDEO_EXTS = {".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4", ".webm": "video/webm"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"}

_GREY_POSTER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

_AVATAR_GREY = RGBColor(0xB8, 0xB8, 0xB8)
_MEDIA_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_PANEL_NAVY = RGBColor(0x1E, 0x3A, 0x5F)


@dataclass(frozen=True)
class RegionBox:
    left_in: float
    top_in: float
    width_in: float
    height_in: float
    rounded: bool = False
    corner_radius_in: float = 0.12


def _hex_rgb(hex_color: str) -> RGBColor:
    h = (hex_color or "#1E3A5F").lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _border_inset(style: dict, kind: str) -> float:
    return float(layout_in(style, kind, "border_inset_in", layout_in(style, "avatar_border", "border_inset_in", 0.25)))


def _content_area(prs, style: dict, kind: str) -> Tuple[float, float, float, float]:
    """Return (left_in, top_in, width_in, height_in) for inner content."""
    sw, sh = prs.slide_width.inches, prs.slide_height.inches
    if kind in _BORDER_KINDS:
        inset = _border_inset(style, kind)
        return inset, inset, sw - 2 * inset, sh - 2 * inset
    return 0.0, 0.0, sw, sh


def _split_boxes(
    cx: float, cy: float, cw: float, ch: float, media_ratio: float, gap_in: float
) -> Tuple[RegionBox, RegionBox]:
    gap = max(gap_in, 0.0)
    usable = cw - gap
    media_w = usable * media_ratio
    avatar_w = usable - media_w
    media = RegionBox(cx, cy, media_w, ch)
    avatar = RegionBox(cx + media_w + gap, cy, avatar_w, ch)
    return media, avatar


def _pip_box(cx: float, cy: float, cw: float, ch: float, style: dict, kind: str) -> RegionBox:
    ratio = float(layout_in(style, kind, "pip_width_ratio", 0.18))
    margin = float(layout_in(style, kind, "pip_margin_in", 0.35))
    size = cw * ratio
    return RegionBox(cx + cw - size - margin, cy + ch - size - margin, size, size)


def _text_panel_box(prs, style: dict, kind: str, position: str) -> RegionBox:
    cx, cy, cw, ch = _content_area(prs, style, kind)
    margin = float(layout_in(style, kind, "panel_margin_in", 0.35))
    pw = cw * float(layout_in(style, kind, "panel_width_ratio", 0.42))
    ph = float(layout_in(style, kind, "panel_height_in", 1.2))
    if position == "top":
        return RegionBox(cx + margin, cy + margin, pw, ph)
    return RegionBox(cx + margin, cy + ch - ph - margin, pw, ph)


def _slide_regions(prs, kind: str, style: dict) -> Dict[str, Optional[RegionBox]]:
    cx, cy, cw, ch = _content_area(prs, style, kind)
    full = RegionBox(cx, cy, cw, ch)
    regions: Dict[str, Optional[RegionBox]] = {
        "media": None,
        "avatar": None,
        "text_panel": None,
    }

    if kind == "avatar_only":
        regions["avatar"] = full
    elif kind == "media_only":
        regions["media"] = full
    elif kind in _SPLIT_KINDS:
        ratio = float(layout_in(style, kind, "media_width_ratio", 0.5))
        gap = float(layout_in(style, kind, "gap_in", layout_in(style, kind, "inner_gap_in", 0)))
        rounded = kind.startswith("avatar_media_border")
        radius = float(layout_in(style, kind, "inner_radius_in", 0.12))
        media, avatar = _split_boxes(cx, cy, cw, ch, ratio, gap)
        regions["media"] = RegionBox(
            media.left_in, media.top_in, media.width_in, media.height_in, rounded, radius
        )
        regions["avatar"] = RegionBox(
            avatar.left_in, avatar.top_in, avatar.width_in, avatar.height_in, rounded, radius
        )
    elif kind in _PIP_KINDS:
        regions["media"] = full if kind != "avatar_quote" else None
        regions["avatar"] = _pip_box(cx, cy, cw, ch, style, kind)
    elif kind == "avatar_name_card":
        regions["avatar"] = full
        regions["text_panel"] = _text_panel_box(prs, style, kind, "bottom")
    elif kind == "avatar_headline":
        regions["avatar"] = full
        regions["text_panel"] = _text_panel_box(prs, style, kind, "top")
    elif kind == "avatar_border":
        regions["avatar"] = full
    elif kind == "media_border":
        regions["media"] = full
    return regions


def _poster_bytes(poster_path: Optional[str], source_file: Optional[str]) -> io.BytesIO:
    if poster_path:
        resolved = resolve_asset_path(poster_path, source_file=source_file)
        path = resolved if resolved else poster_path
        if path and os.path.isfile(path):
            with open(path, "rb") as fh:
                return io.BytesIO(fh.read())
    return io.BytesIO(_GREY_POSTER_PNG)


def _is_video_path(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in _VIDEO_EXTS


def _video_mime(path: str) -> str:
    return _VIDEO_EXTS.get(os.path.splitext(path)[1].lower(), "video/unknown")


def _box_lengths(box: RegionBox):
    return Inches(box.left_in), Inches(box.top_in), Inches(box.width_in), Inches(box.height_in)


def _draw_filled_rect(slide, box: RegionBox, rgb: RGBColor, rounded: bool = False) -> None:
    left, top, width, height = _box_lengths(box)
    if rounded:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        try:
            short_in = min(box.width_in, box.height_in)
            adj = min(0.5, max(0.02, box.corner_radius_in / short_in)) if short_in > 0 else 0.08
            shape.adjustments[0] = adj
        except (IndexError, AttributeError):
            pass
    else:
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb
    shape.line.fill.background()


def _place_empty_region(slide, box: RegionBox, zone: str) -> None:
    colour = _MEDIA_WHITE if zone == "media" else _AVATAR_GREY
    _draw_filled_rect(slide, box, colour, rounded=box.rounded)


def _fit_movie_in_box(slide, movie_path: str, poster: io.BytesIO, box: RegionBox, mime: str) -> None:
    left, top, width, height = _box_lengths(box)
    slide.shapes.add_movie(
        movie_path,
        left,
        top,
        width,
        height,
        poster_frame_image=poster,
        mime_type=mime,
    )


def _place_picture_in_box(slide, path: str, box: RegionBox, fit: str) -> None:
    from .core import _fit_picture_in_box

    left, top, width, height = _box_lengths(box)
    fit = (fit or "contain").lower()
    if fit == "fill":
        slide.shapes.add_picture(path, left, top, width=width, height=height)
        return
    pic = slide.shapes.add_picture(path, left, top, width=width)
    _fit_picture_in_box(pic, left, top, width, height, fit if fit in ("contain", "cover") else "contain")


def _place_media_in_box(
    slide,
    box: RegionBox,
    media_path: Optional[str],
    *,
    fit: str = "contain",
    poster_path: Optional[str] = None,
    source_file: Optional[str] = None,
) -> None:
    if not media_path:
        _place_empty_region(slide, box, "media")
        return
    resolved = resolve_asset_path(media_path, source_file=source_file)
    path = resolved if resolved else media_path
    if not path or not os.path.isfile(path):
        print(f"Warning: Media not found: {media_path}")
        _place_empty_region(slide, box, "media")
        return
    if _is_video_path(path):
        poster = _poster_bytes(poster_path, source_file)
        _fit_movie_in_box(slide, path, poster, box, _video_mime(path))
    else:
        _place_picture_in_box(slide, path, box, fit)


def _place_avatar_in_box(
    slide,
    box: RegionBox,
    avatar_path: Optional[str],
    *,
    poster_path: Optional[str] = None,
    source_file: Optional[str] = None,
) -> None:
    if not avatar_path:
        _place_empty_region(slide, box, "avatar")
        return
    resolved = resolve_asset_path(avatar_path, source_file=source_file)
    path = resolved if resolved else avatar_path
    if not path or not os.path.isfile(path):
        print(f"Warning: Avatar video not found: {avatar_path}")
        _place_empty_region(slide, box, "avatar")
        return
    poster = _poster_bytes(poster_path, source_file)
    _fit_movie_in_box(slide, path, poster, box, _video_mime(path))


def _draw_border_frame(slide, prs, style: dict, kind: str) -> None:
    inset = _border_inset(style, kind)
    colour = _hex_rgb(str(layout_in(style, kind, "border_color", "#1E3A5F")))
    width_pt = float(layout_in(style, kind, "border_width_pt", 8))
    sw, sh = prs.slide_width.inches, prs.slide_height.inches
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(inset),
        Inches(inset),
        Inches(sw - 2 * inset),
        Inches(sh - 2 * inset),
    )
    shape.fill.background()
    shape.line.color.rgb = colour
    shape.line.width = Pt(width_pt)


def _panel_colour(style: dict) -> RGBColor:
    raw = (style or {}).get("avatar_panel_color")
    return _hex_rgb(raw) if raw else _PANEL_NAVY


def _add_text_panel(slide, box: RegionBox, headline: str, subheader: str, style: dict, theme: dict) -> None:
    from .core import _write_body_paragraph

    _draw_filled_rect(slide, box, _panel_colour(style))
    left, top, width, height = _box_lengths(box)
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(12)
    tf.margin_top = tf.margin_bottom = Pt(8)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    head_pt = int(typography_pt(style, "title_size_pt", 44) * 0.75)
    sub_pt = int(typography_pt(style, "subtitle_size_pt", 28) * 0.85)
    panel_theme = dict(theme)
    panel_theme["body"] = RGBColor(0xFF, 0xFF, 0xFF)
    p = tf.paragraphs[0]
    _write_body_paragraph(p, headline, head_pt, panel_theme, style=style, alignment=PP_ALIGN.LEFT)
    if subheader:
        p2 = tf.add_paragraph()
        _write_body_paragraph(p2, subheader, sub_pt, panel_theme, style=style, alignment=PP_ALIGN.LEFT)


def _render_avatar_quote(slide, prs, verse: dict, style: dict, regions: dict, theme: dict) -> None:
    from .core import _resolve_alignment, _write_body_paragraph

    bg = str(layout_in(style, "avatar_quote", "quote_bg_color", "#1E3A5F"))
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _hex_rgb(bg)
    quote_pt = int(verse.get("font_size") or typography_pt(style, "quote_size_pt", 36))
    left, width, _, _ = content_box(prs, style, "avatar_quote")
    top_in = float(layout_in(style, "avatar_quote", "top_in", 1.8))
    body_h_in = prs.slide_height.inches - top_in - 1.5
    align = _resolve_alignment(verse.get("alignment", "center"))
    tb = slide.shapes.add_textbox(left, Inches(top_in), width, Inches(body_h_in * 0.72))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    quote_theme = dict(theme)
    quote_theme["body"] = RGBColor(0xFF, 0xFF, 0xFF)
    quote_theme["reference"] = RGBColor(0xDD, 0xDD, 0xDD)
    _write_body_paragraph(tf.paragraphs[0], verse["text"], quote_pt, quote_theme, style=style, alignment=align)
    ref_str = (verse.get("reference") or "").strip()
    if ref_str:
        ref_pt = int(typography_pt(style, "reference_size_pt", 28))
        ref_y = top_in + body_h_in * 0.76
        rt = slide.shapes.add_textbox(left, Inches(ref_y), width, Inches(0.65))
        rp = rt.text_frame.paragraphs[0]
        rp.text = ref_str
        rp.alignment = align
        rp.font.size = Pt(ref_pt)
        rp.font.italic = True
        rp.font.color.rgb = quote_theme["reference"]
        if theme.get("font_name"):
            rp.font.name = theme["font_name"]


def render_avatar_slide(prs, kind: str, verse: dict, style=None, *, source_file: Optional[str] = None):
    """Build one avatar layout slide."""
    from .core import _apply_slide_background, _resolve_theme

    style = dict(style or {})
    if source_file:
        style["_source_file"] = source_file
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    if kind != "avatar_quote":
        _apply_slide_background(slide, style, prs)
    theme = _resolve_theme(style)
    regions = _slide_regions(prs, kind, style)

    media_box = regions.get("media")
    avatar_box = regions.get("avatar")
    media_fit = verse.get("media_fit", "contain")

    if kind == "avatar_quote":
        _render_avatar_quote(slide, prs, verse, style, regions, theme)
        if avatar_box:
            _place_avatar_in_box(
                slide,
                avatar_box,
                verse.get("avatar_video_path"),
                poster_path=verse.get("avatar_poster_path"),
                source_file=source_file,
            )
        return slide

    if media_box and kind in _SPLIT_KINDS and media_box.rounded:
        _place_empty_region(slide, media_box, "media")
    if avatar_box and kind in _SPLIT_KINDS and avatar_box.rounded:
        _place_empty_region(slide, avatar_box, "avatar")

    if media_box:
        _place_media_in_box(
            slide,
            media_box,
            verse.get("media_path"),
            fit=media_fit,
            poster_path=verse.get("media_poster_path"),
            source_file=source_file,
        )
    if avatar_box:
        _place_avatar_in_box(
            slide,
            avatar_box,
            verse.get("avatar_video_path"),
            poster_path=verse.get("avatar_poster_path"),
            source_file=source_file,
        )

    panel = regions.get("text_panel")
    if panel:
        _add_text_panel(
            slide,
            panel,
            str(verse.get("headline", "")),
            str(verse.get("subheader") or ""),
            style,
            theme,
        )

    if kind in _BORDER_KINDS:
        _draw_border_frame(slide, prs, style, kind)
    return slide

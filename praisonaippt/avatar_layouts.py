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

from .layout_tokens import layout_in, typography_pt
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
    ratio_raw = layout_in(style, kind, "pip_width_ratio", None)
    margin_raw = layout_in(style, kind, "pip_margin_in", None)
    ratio = float(ratio_raw if ratio_raw is not None else layout_in(style, "pip", "width_ratio", 0.14))
    margin = float(margin_raw if margin_raw is not None else layout_in(style, "pip", "margin_in", 0.45))
    size = cw * ratio
    shape = str(layout_in(style, "pip", "shape", "circle")).lower()
    rounded = shape in ("circle", "round", "rounded")
    radius = size / 2 if shape == "circle" else float(layout_in(style, "pip", "corner_radius_in", 0.12))
    return RegionBox(
        cx + cw - size - margin,
        cy + ch - size - margin,
        size,
        size,
        rounded=rounded,
        corner_radius_in=radius,
    )


def export_floating_pip_box(prs, style: dict) -> RegionBox:
    """Bottom-right PiP box used for avatar overlays on any slide type."""
    cx, cy, cw, ch = 0.0, 0.0, prs.slide_width.inches, prs.slide_height.inches
    return _pip_box(cx, cy, cw, ch, style, "pip")


def _content_beside_pip(
    cx: float, cy: float, cw: float, ch: float, pip: RegionBox, margin: float
) -> RegionBox:
    """Text area that leaves the bottom-right PiP corner clear."""
    text_w = max(cw - pip.width_in - 2 * margin, 1.0)
    text_h = max(ch - 2 * margin, 1.0)
    return RegionBox(cx + margin, cy + margin, text_w, text_h)


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
        ratio = float(layout_in(style, kind, "media_width_ratio"))
        gap_raw = layout_in(style, kind, "gap_in")
        if gap_raw is None:
            gap_raw = layout_in(style, kind, "inner_gap_in")
        gap = float(gap_raw or 0)
        rounded = kind.startswith("avatar_media_border")
        radius_raw = layout_in(style, kind, "inner_radius_in") if rounded else 0
        radius = float(radius_raw or 0.12) if rounded else 0.0
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
        pip = _pip_box(cx, cy, cw, ch, style, kind)
        regions["avatar"] = pip
        margin = float(layout_in(style, kind, "panel_margin_in", 0.6))
        regions["text_panel"] = _content_beside_pip(cx, cy, cw, ch, pip, margin)
    elif kind == "avatar_border":
        regions["avatar"] = full
    elif kind == "media_border":
        regions["media"] = full
    return regions


def export_slide_regions(prs, kind: str, style: dict) -> Dict[str, Optional[RegionBox]]:
    """Public wrapper for layout region geometry (inches on slide)."""
    return _slide_regions(prs, kind, style)


def region_box_to_pixels(
    box: RegionBox,
    slide_width_in: float,
    slide_height_in: float,
    out_width: int,
    out_height: int,
) -> Dict[str, int]:
    """Map inch region box to output pixel coordinates."""
    pad_x, pad_y, cw, ch = letterbox_content_rect(
        slide_width_in, slide_height_in, out_width, out_height,
    )
    sx = cw / slide_width_in
    sy = ch / slide_height_in
    return {
        "x": pad_x + int(round(box.left_in * sx)),
        "y": pad_y + int(round(box.top_in * sy)),
        "width": max(1, int(round(box.width_in * sx))),
        "height": max(1, int(round(box.height_in * sy))),
    }


def letterbox_content_rect(
    slide_width_in: float,
    slide_height_in: float,
    out_width: int,
    out_height: int,
) -> Tuple[int, int, int, int]:
    """Return pad_x, pad_y, content_w, content_h for letterboxed slide in output frame."""
    slide_aspect = slide_width_in / slide_height_in
    out_aspect = out_width / out_height
    if slide_aspect > out_aspect:
        content_w = out_width
        content_h = max(1, int(round(out_width / slide_aspect)))
        pad_x, pad_y = 0, (out_height - content_h) // 2
    else:
        content_h = out_height
        content_w = max(1, int(round(out_height * slide_aspect)))
        pad_x, pad_y = (out_width - content_w) // 2, 0
    return pad_x, pad_y, content_w, content_h


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


def _draw_pip_frame(slide, box: RegionBox, style: dict) -> None:
    """White ring around the avatar PiP (circle or rounded rect)."""
    left, top, width, height = _box_lengths(box)
    shape_kind = str(layout_in(style, "pip", "shape", "circle")).lower()
    if shape_kind == "circle":
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    else:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        try:
            shape.adjustments[0] = 0.18
        except (IndexError, AttributeError):
            pass
    shape.fill.background()
    border = str(layout_in(style, "pip", "border_color", "#FFFFFF"))
    shape.line.color.rgb = _hex_rgb(border)
    shape.line.width = Pt(float(layout_in(style, "pip", "border_width_pt", 2.5)))


def _place_avatar_in_box(
    slide,
    box: RegionBox,
    avatar_path: Optional[str],
    *,
    poster_path: Optional[str] = None,
    source_file: Optional[str] = None,
    style: Optional[dict] = None,
    draw_frame: bool = True,
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
    if draw_frame and box.rounded:
        _draw_pip_frame(slide, box, style or {})


def place_floating_avatar_pip(
    slide,
    verse: dict,
    style: dict,
    *,
    prs,
    source_file: Optional[str] = None,
) -> None:
    """Avatar PiP on standard slides — drawn last so it floats above the slide."""
    path = verse.get("avatar_video_path")
    if not path:
        return
    style = dict(style or {})
    if source_file:
        style["_source_file"] = source_file
    box = export_floating_pip_box(prs, style)
    _place_avatar_in_box(
        slide,
        box,
        path,
        poster_path=verse.get("avatar_poster_path"),
        source_file=source_file,
        style=style,
        draw_frame=True,
    )


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


def _format_subheader_lines(subheader: str) -> list[str]:
    parts = [s.strip() for s in subheader.replace(" · ", "·").split("·") if s.strip()]
    if len(parts) <= 1:
        return [subheader.strip()] if subheader.strip() else []
    return [f"•  {part}" for part in parts]


def _headline_font_sizes(style: dict, headline: str, subheader: str) -> tuple[int, int]:
    sub_len = len(subheader or "")
    head_pt = int(typography_pt(style, "title_size_pt", 44) * 0.78)
    if len(headline) > 48:
        head_pt = max(head_pt - 6, 28)
    if sub_len > 140:
        sub_pt = 18
    elif sub_len > 90:
        sub_pt = 20
    elif sub_len > 55:
        sub_pt = 22
    else:
        sub_pt = int(typography_pt(style, "body_size_pt", 32) * 0.72)
    return head_pt, sub_pt


def _add_headline_content(
    slide, box: RegionBox, headline: str, subheader: str, style: dict, theme: dict
) -> None:
    from .core import _write_body_paragraph

    left, top, width, height = _box_lengths(box)
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = tf.margin_right = Pt(10)
    tf.margin_top = tf.margin_bottom = Pt(6)
    tf.vertical_anchor = MSO_ANCHOR.TOP

    head_pt, sub_pt = _headline_font_sizes(style, headline, subheader)
    head_theme = dict(theme)
    head_theme["body"] = theme.get("title") or theme.get("body")
    sub_theme = dict(theme)
    sub_theme["body"] = theme.get("subtitle") or theme.get("reference") or theme.get("body")

    p = tf.paragraphs[0]
    _write_body_paragraph(p, headline, head_pt, head_theme, style=style, alignment=PP_ALIGN.LEFT)
    p.space_after = Pt(12)

    for line in _format_subheader_lines(subheader):
        para = tf.add_paragraph()
        _write_body_paragraph(para, line, sub_pt, sub_theme, style=style, alignment=PP_ALIGN.LEFT)
        para.space_after = Pt(8)


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

    pip = regions.get("avatar")
    cx, cy, cw, ch = _content_area(prs, style, "avatar_quote")
    margin = float(layout_in(style, "avatar_quote", "margin_in", 0.6))
    pip_w = pip.width_in if pip else 0.0
    pip_top = pip.top_in if pip else ch
    text_w_in = max(cw - pip_w - 2 * margin, 4.0)
    left_in = cx + margin

    quote_pt = int(verse.get("font_size") or typography_pt(style, "quote_size_pt", 36))
    top_in = float(layout_in(style, "avatar_quote", "top_in", 1.6))
    available_h = max(pip_top - top_in - 0.35, 2.0)
    align = _resolve_alignment(verse.get("alignment", "center"))

    quote_h = available_h * 0.62
    tb = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(text_w_in), Inches(quote_h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(12)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    quote_theme = dict(theme)
    quote_theme["body"] = RGBColor(0xFF, 0xFF, 0xFF)
    quote_theme["reference"] = RGBColor(0xDD, 0xDD, 0xDD)
    _write_body_paragraph(tf.paragraphs[0], verse["text"], quote_pt, quote_theme, style=style, alignment=align)

    ref_str = (verse.get("reference") or "").strip()
    if ref_str:
        ref_pt = int(typography_pt(style, "reference_size_pt", 24))
        ref_top = top_in + quote_h + 0.15
        ref_h = max(min(available_h - quote_h - 0.2, 1.1), 0.55)
        rt = slide.shapes.add_textbox(Inches(left_in), Inches(ref_top), Inches(text_w_in), Inches(ref_h))
        tf_ref = rt.text_frame
        tf_ref.word_wrap = True
        tf_ref.vertical_anchor = MSO_ANCHOR.TOP
        rp = tf_ref.paragraphs[0]
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
                style=style,
            )
        _stamp_slide_type_note(slide, kind, verse)
        return slide

    if kind == "avatar_headline":
        panel = regions.get("text_panel")
        if panel:
            _add_headline_content(
                slide,
                panel,
                str(verse.get("headline", "")),
                str(verse.get("subheader") or ""),
                style,
                theme,
            )
        if avatar_box:
            _place_avatar_in_box(
                slide,
                avatar_box,
                verse.get("avatar_video_path"),
                poster_path=verse.get("avatar_poster_path"),
                source_file=source_file,
                style=style,
            )
        _stamp_slide_type_note(slide, kind, verse)
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
            style=style,
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
    _stamp_slide_type_note(slide, kind, verse)
    return slide


def _stamp_slide_type_note(slide, kind: str, verse: dict) -> None:
    """Store layout kind in speaker notes for list-slides (hidden from normal notes)."""
    try:
        notes = (verse.get("notes") or "").strip()
        meta = f"slide_type: {kind}"
        frame = slide.notes_slide.notes_text_frame
        if notes:
            if meta not in notes:
                frame.text = f"{notes}\n{meta}"
        else:
            frame.text = meta
    except Exception:
        pass

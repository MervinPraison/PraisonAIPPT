"""Protocol-based slide renderer registry."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Protocol, runtime_checkable

from .exceptions import SchemaError

logger = logging.getLogger(__name__)


@runtime_checkable
class SlideRenderer(Protocol):
    """Render one verse dict to zero or more slides."""

    kind: str

    def validate(self, verse: dict, path: str) -> None:
        ...

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        ...


_REGISTRY: Dict[str, SlideRenderer] = {}


def register_renderer(renderer: SlideRenderer) -> None:
    """Register or replace a slide renderer by ``renderer.kind``."""
    _REGISTRY[renderer.kind] = renderer


def get_renderer(kind: str) -> Optional[SlideRenderer]:
    return _REGISTRY.get(kind)


def list_renderers() -> list[str]:
    return sorted(_REGISTRY.keys())


def resolve_renderer(verse: dict) -> SlideRenderer:
    """slide_type (if registered) → list_type → verse."""
    slide_type = verse.get("slide_type")
    if slide_type:
        renderer = _REGISTRY.get(str(slide_type))
        if renderer is None:
            raise SchemaError(f"Unknown slide_type {slide_type!r}")
        return renderer
    list_type = verse.get("list_type")
    if list_type in ("bullet", "numbered"):
        return _REGISTRY["list"]
    return _REGISTRY["verse"]


def validate_verse(verse: dict, path: str) -> None:
    resolve_renderer(verse).validate(verse, path)


def _apply_notes(slide, verse: dict) -> None:
    from .core import _apply_speaker_notes

    _apply_speaker_notes(slide, verse.get("notes"))


def _finish_slide(
    slide, verse: dict, style: dict, prs, *, source_file: Optional[str] = None,
) -> None:
    _apply_notes(slide, verse)
    if not verse.get("avatar_video_path"):
        return
    st = verse.get("slide_type")
    from .avatar_layouts import AVATAR_SLIDE_TYPES, place_floating_avatar_pip
    from .deck_slides import DECK_SLIDE_TYPES

    if st in AVATAR_SLIDE_TYPES or st in DECK_SLIDE_TYPES:
        return
    place_floating_avatar_pip(slide, verse, style, prs=prs, source_file=source_file)


def _column_texts(verse: dict) -> tuple:
    """Parse two column texts from ``columns`` or ``left``/``right`` keys."""
    cols = verse.get("columns")
    if isinstance(cols, list) and len(cols) >= 2:
        left = cols[0].get("text", "") if isinstance(cols[0], dict) else str(cols[0])
        right = cols[1].get("text", "") if isinstance(cols[1], dict) else str(cols[1])
        left_hl = cols[0].get("highlights") if isinstance(cols[0], dict) else None
        right_hl = cols[1].get("highlights") if isinstance(cols[1], dict) else None
        return left, right, left_hl, right_hl
    return verse.get("left", ""), verse.get("right", ""), None, None


def _table_rows(verse: dict) -> List[List[str]]:
    raw = verse.get("table_rows") or verse.get("rows")
    if not raw:
        return []
    rows = []
    for row in raw:
        if isinstance(row, list):
            rows.append([str(c) for c in row])
        elif isinstance(row, dict):
            rows.append([str(v) for v in row.values()])
        else:
            rows.append([str(row)])
    return rows


class ImageRenderer:
    kind = "image"

    def validate(self, verse: dict, path: str) -> None:
        if not verse.get("image_path"):
            raise SchemaError(f"{path} with slide_type 'image' requires 'image_path'")
        fit = verse.get("image_fit")
        if fit is not None and fit not in ("contain", "cover", "fill"):
            raise SchemaError(f"{path}.image_fit must be 'contain', 'cover', or 'fill'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .core import add_image_slide

        slide = add_image_slide(
            prs,
            verse["image_path"],
            style=style,
            reference=verse.get("reference"),
            caption=verse.get("text"),
            image_fit=verse.get("image_fit", "contain"),
            source_file=source_file,
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class HebrewRenameRenderer:
    kind = "hebrew_rename"

    def validate(self, verse: dict, path: str) -> None:
        if not verse.get("hebrew_rows"):
            raise SchemaError(f"{path} with slide_type 'hebrew_rename' requires 'hebrew_rows'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .core import add_hebrew_rename_slide

        slide = add_hebrew_rename_slide(
            prs,
            verse["hebrew_rows"],
            style=style,
            font_size=verse.get("hebrew_font_size"),
            reference=verse.get("reference"),
            caption=verse.get("text"),
            highlight_color=verse.get("hebrew_highlight_color"),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class ListRenderer:
    kind = "list"

    def validate(self, verse: dict, path: str) -> None:
        if "reference" not in verse and "text" not in verse:
            raise SchemaError(f"{path} must have 'reference' or 'text'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_list_slide

        list_type = verse.get("list_type")
        items = [line.strip() for line in verse.get("text", "").split("\n") if line.strip()]
        slide = add_list_slide(
            prs,
            items,
            verse.get("reference"),
            list_type=list_type,
            font_size=body_font_size(style, verse),
            alignment=verse.get("alignment", style.get("alignment", "left")),
            style=style,
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class TitleOnlyRenderer:
    kind = "title_only"

    def validate(self, verse: dict, path: str) -> None:
        if not (verse.get("text") or verse.get("reference")):
            raise SchemaError(f"{path} with slide_type 'title_only' requires 'text' or 'reference'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .core import add_title_only_slide

        slide = add_title_only_slide(
            prs,
            verse.get("text") or verse.get("reference") or "",
            subtitle=verse.get("reference") if verse.get("text") else None,
            style=style,
            font_size=verse.get("font_size") or verse.get("reference_font_size"),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class TwoColumnRenderer:
    kind = "two_column"

    def validate(self, verse: dict, path: str) -> None:
        cols = verse.get("columns")
        if isinstance(cols, list) and len(cols) >= 2:
            return
        if verse.get("left") is not None or verse.get("right") is not None:
            return
        raise SchemaError(f"{path} with slide_type 'two_column' requires 'columns' (2+) or 'left'/'right'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_two_column_slide

        left, right, left_hl, right_hl = _column_texts(verse)
        slide = add_two_column_slide(
            prs, left, right, style=style,
            font_size=body_font_size(style, verse),
            alignment=verse.get("alignment", style.get("alignment", "left")),
            left_highlights=left_hl, right_highlights=right_hl,
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class ComparisonRenderer:
    kind = "comparison"

    def validate(self, verse: dict, path: str) -> None:
        cols = verse.get("columns")
        if not isinstance(cols, list) or len(cols) < 2:
            raise SchemaError(f"{path} with slide_type 'comparison' requires 'columns' with at least 2 entries")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_comparison_slide

        slide = add_comparison_slide(
            prs,
            verse["columns"],
            style=style,
            font_size=body_font_size(style, verse),
            alignment=verse.get("alignment", style.get("alignment", "left")),
            reference=verse.get("reference"),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class BigNumberRenderer:
    kind = "big_number"

    def validate(self, verse: dict, path: str) -> None:
        if not str(verse.get("number", "")).strip() and not str(verse.get("text", "")).strip():
            raise SchemaError(f"{path} with slide_type 'big_number' requires 'number'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .core import add_big_number_slide

        slide = add_big_number_slide(
            prs,
            str(verse.get("number", verse.get("text", ""))),
            verse.get("label", ""),
            style=style,
            reference=verse.get("reference"),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class QuoteRenderer:
    kind = "quote"

    def validate(self, verse: dict, path: str) -> None:
        if not verse.get("text"):
            raise SchemaError(f"{path} with slide_type 'quote' requires 'text'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_quote_slide

        slide = add_quote_slide(
            prs,
            verse["text"],
            style=style,
            reference=verse.get("reference"),
            font_size=verse.get("font_size") or body_font_size(style, verse),
            alignment=verse.get("alignment", "center"),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class PictureTextRenderer:
    kind = "picture_text"

    def validate(self, verse: dict, path: str) -> None:
        if not verse.get("image_path"):
            raise SchemaError(f"{path} with slide_type 'picture_text' requires 'image_path'")
        if not verse.get("text"):
            raise SchemaError(f"{path} with slide_type 'picture_text' requires 'text'")
        fit = verse.get("image_fit")
        if fit is not None and fit not in ("contain", "cover", "fill"):
            raise SchemaError(f"{path}.image_fit must be 'contain', 'cover', or 'fill'")
        side = verse.get("image_side")
        if side is not None and side not in ("left", "right"):
            raise SchemaError(f"{path}.image_side must be 'left' or 'right'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_picture_text_slide

        slide = add_picture_text_slide(
            prs,
            verse["image_path"],
            verse["text"],
            style=style,
            image_side=verse.get("image_side", "left"),
            image_fit=verse.get("image_fit", "contain"),
            font_size=body_font_size(style, verse),
            alignment=verse.get("alignment", style.get("alignment", "left")),
            source_file=source_file,
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class TableRenderer:
    kind = "table"

    def validate(self, verse: dict, path: str) -> None:
        if not _table_rows(verse):
            raise SchemaError(f"{path} with slide_type 'table' requires 'table_rows' or 'rows'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size
        from .core import add_table_slide

        slide = add_table_slide(
            prs,
            _table_rows(verse),
            style=style,
            font_size=body_font_size(style, verse),
            header_row=verse.get("header_row", True),
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class VerseRenderer:
    kind = "verse"

    def validate(self, verse: dict, path: str) -> None:
        if "reference" not in verse and "text" not in verse:
            raise SchemaError(f"{path} must have 'reference' or 'text'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .layout_tokens import body_font_size, split_max_length_default
        from .core import add_verse_slide
        from .utils import split_long_text

        highlights = verse.get("highlights")
        large_text = verse.get("large_text")
        alignment = verse.get("alignment", style.get("alignment", "left"))
        font_size = body_font_size(style, verse)
        max_len = int(verse.get("split_max_length") or split_max_length_default(style))
        parts = split_long_text(verse.get("text", ""), max_length=max(max_len, 50))
        notes = verse.get("notes")

        for i, part in enumerate(parts):
            slide = add_verse_slide(
                prs,
                part,
                verse.get("reference"),
                None,
                highlights,
                large_text,
                alignment=alignment,
                font_size=font_size,
                style=style,
                reference_font_size=verse.get("reference_font_size"),
                reference_position=verse.get("reference_position"),
                leading_title=(verse.get("leading_title") if i == 0 else None),
                text_below_reference=(verse.get("text_below_reference") if i == 0 else None),
                text_below_reference_highlights=(
                    verse.get("text_below_reference_highlights") if i == 0 else None
                ),
                text_below_reference_large_text=(
                    verse.get("text_below_reference_large_text") if i == 0 else None
                ),
            )
            if i == 0 and notes:
                _finish_slide(slide, verse, style, prs, source_file=source_file)


class AvatarKindRenderer:
    """Factory renderer for avatar layout slide types."""

    _MEDIA_REQUIRED = frozenset({"media_only", "media_border"})
    _HEADLINE_REQUIRED = frozenset({
        "avatar_name_card",
        "avatar_headline",
        "avatar_headline_full",
    })

    def __init__(self, kind: str) -> None:
        self.kind = kind

    def validate(self, verse: dict, path: str) -> None:
        if self.kind in self._MEDIA_REQUIRED and not verse.get("media_path"):
            raise SchemaError(f"{path} with slide_type {self.kind!r} requires 'media_path'")
        if self.kind in self._HEADLINE_REQUIRED and not verse.get("headline"):
            raise SchemaError(f"{path} with slide_type {self.kind!r} requires 'headline'")
        if self.kind == "avatar_quote" and not verse.get("text"):
            raise SchemaError(f"{path} with slide_type 'avatar_quote' requires 'text'")
        fit = verse.get("media_fit")
        if fit is not None and fit not in ("contain", "cover", "fill"):
            raise SchemaError(f"{path}.media_fit must be 'contain', 'cover', or 'fill'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .avatar_layouts import render_avatar_slide

        slide = render_avatar_slide(
            prs, self.kind, verse, style=style, source_file=source_file
        )
        _finish_slide(slide, verse, style, prs, source_file=source_file)


class DeckKindRenderer:
    """HeyGen-style designed deck layouts."""

    def __init__(self, kind: str) -> None:
        self.kind = kind

    def validate(self, verse: dict, path: str) -> None:
        def _require_list(key: str, alt: Optional[str] = None) -> list:
            raw = verse.get(key) if alt is None else (verse.get(key) or verse.get(alt))
            if not isinstance(raw, list) or not raw:
                keys = f"{key!r}" if alt is None else f"{key!r} or {alt!r}"
                raise SchemaError(f"{path} with slide_type {self.kind!r} requires {keys}")
            return raw

        def _warn_truncated(items: list, limit: int, label: str) -> None:
            if len(items) > limit:
                logger.warning(
                    "%s with slide_type %r has %d %s; only first %d are rendered",
                    path, self.kind, len(items), label, limit,
                )

        if self.kind == "deck_exec_summary":
            items = _require_list("items")
            _warn_truncated(items, 3, "items")
        elif self.kind == "deck_region_grid":
            data = verse.get("cells") or verse.get("columns")
            if not isinstance(data, list) or not data:
                raise SchemaError(
                    f"{path} with slide_type {self.kind!r} requires 'cells' or 'columns'"
                )
            _warn_truncated(data, 4, "cells")
        elif self.kind in ("deck_product_columns", "deck_customer_segments"):
            key = "columns"
            cols = _require_list(key)
            limit = 4 if self.kind == "deck_product_columns" else 3
            _warn_truncated(cols, limit, "columns")
        elif self.kind in ("deck_split_performance", "deck_channel_analysis"):
            rows = _require_list("rows")
            for i, row in enumerate(rows):
                if not isinstance(row, (dict, str)):
                    raise SchemaError(
                        f"{path} rows[{i}] must be a mapping or string, got {type(row).__name__}"
                    )
        elif self.kind == "deck_agenda":
            _require_list("items", "agenda")
        elif self.kind == "deck_opportunity_cards":
            cards = _require_list("columns", "items")
            _warn_truncated(cards, 3, "columns")
        elif self.kind == "deck_forecast_split":
            items = _require_list("items")
            _warn_truncated(items, 3, "items")
        elif not (verse.get("text") or verse.get("headline")):
            raise SchemaError(f"{path} with slide_type {self.kind!r} requires 'text' or 'headline'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .deck_slides import render_deck_slide

        slide = render_deck_slide(prs, self.kind, verse, deck_style=style, source_file=source_file)
        _apply_notes(slide, verse)


def _register_builtins() -> None:
    from .avatar_layouts import AVATAR_SLIDE_TYPES
    from .deck_slides import DECK_SLIDE_TYPES

    renderers = [
        ImageRenderer(),
        HebrewRenameRenderer(),
        ListRenderer(),
        TitleOnlyRenderer(),
        TwoColumnRenderer(),
        ComparisonRenderer(),
        BigNumberRenderer(),
        QuoteRenderer(),
        PictureTextRenderer(),
        TableRenderer(),
        VerseRenderer(),
    ]
    renderers.extend(AvatarKindRenderer(kind) for kind in AVATAR_SLIDE_TYPES)
    renderers.extend(DeckKindRenderer(kind) for kind in DECK_SLIDE_TYPES)
    for renderer in renderers:
        register_renderer(renderer)


_register_builtins()

"""Protocol-based slide renderer registry."""

from __future__ import annotations

from typing import Dict, Optional, Protocol, runtime_checkable

from .exceptions import SchemaError


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

        add_image_slide(
            prs,
            verse["image_path"],
            style=style,
            reference=verse.get("reference"),
            caption=verse.get("text"),
            image_fit=verse.get("image_fit", "contain"),
            source_file=source_file,
        )


class HebrewRenameRenderer:
    kind = "hebrew_rename"

    def validate(self, verse: dict, path: str) -> None:
        if not verse.get("hebrew_rows"):
            raise SchemaError(f"{path} with slide_type 'hebrew_rename' requires 'hebrew_rows'")

    def render(self, prs, verse: dict, style: dict, *, source_file: Optional[str] = None) -> None:
        from .core import add_hebrew_rename_slide

        add_hebrew_rename_slide(
            prs,
            verse["hebrew_rows"],
            style=style,
            font_size=verse.get("hebrew_font_size"),
            reference=verse.get("reference"),
            caption=verse.get("text"),
            highlight_color=verse.get("hebrew_highlight_color"),
        )


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
        add_list_slide(
            prs,
            items,
            verse.get("reference"),
            list_type=list_type,
            font_size=body_font_size(style, verse),
            alignment=verse.get("alignment", style.get("alignment", "left")),
            style=style,
        )


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

        for i, part in enumerate(parts):
            add_verse_slide(
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


def _register_builtins() -> None:
    for renderer in (
        ImageRenderer(),
        HebrewRenameRenderer(),
        ListRenderer(),
        VerseRenderer(),
    ):
        register_renderer(renderer)


_register_builtins()

"""Shared highlight phrase normalisation for deck text export."""

from __future__ import annotations

import re
from html import escape
from typing import List, Optional, Tuple

# Match praisonaippt/core.py named highlight colours (as CSS hex).
NAMED_CSS = {
    "orange": "#FF8C00",
    "yellow": "#FFD700",
    "gold": "#FFD700",
    "#ffd700": "#FFD700",
    "#fde68a": "#FDE68A",
    "red": "#DC3232",
    "green": "#32B432",
    "blue": "#1E64DC",
    "white": "#FFFFFF",
    "cyan": "#00C8C8",
    "purple": "#9632C8",
}


def normalise_phrases(highlights: list | None) -> List[Tuple[str, Optional[str]]]:
    """Return ``(phrase, colour_hint)`` pairs from YAML highlight entries."""
    out: List[Tuple[str, Optional[str]]] = []
    if not highlights:
        return out
    for item in highlights:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            colour = item.get("color")
            if text:
                out.append((text, str(colour) if colour is not None else None))
        elif isinstance(item, str) and item.strip():
            out.append((item.strip(), None))
    return out


def resolve_highlight_hex(color_hint: object | None, default_hex: str = "#FFD700") -> str:
    """Resolve YAML highlight colour to a CSS hex string."""
    if color_hint is None or color_hint == "":
        return default_hex
    raw = str(color_hint).strip()
    lower = raw.lower()
    if lower in NAMED_CSS:
        return NAMED_CSS[lower]
    if raw.startswith("#") and len(raw) in (4, 7):
        return raw
    stripped = raw.lstrip("#")
    if len(stripped) == 6:
        try:
            int(stripped, 16)
            return f"#{stripped.upper()}"
        except ValueError:
            pass
    return default_hex


def deck_default_highlight_hex(slide_style: dict | None) -> str:
    """Default highlight colour from deck ``slide_style`` (matches PPT dark/light decks)."""
    style = slide_style or {}
    if style.get("highlight_color"):
        return resolve_highlight_hex(style["highlight_color"])
    if style.get("background_image") or style.get("background_color"):
        return "#FFD700"
    return "#FF8C00"


def apply_colored_highlights(
    text: str,
    highlights: list | None,
    *,
    fmt: str = "markdown",
    default_hex: str = "#FFD700",
) -> str:
    """Apply phrase highlights for markdown (**bold**) or HTML (coloured background)."""
    items = normalise_phrases(highlights)
    if not items or not text:
        return text

    if fmt == "html":
        text = escape(text)

    for phrase, colour_hint in sorted({(p, c) for p, c in items}, key=lambda x: len(x[0]), reverse=True):
        hex_color = resolve_highlight_hex(colour_hint, default_hex)
        match_phrase = escape(phrase) if fmt == "html" else phrase
        pattern = re.compile(re.escape(match_phrase), re.IGNORECASE)

        if fmt == "html":
            def _repl(match: re.Match[str], color=hex_color) -> str:
                return (
                    f'<span style="background-color:{color}; font-weight:bold">'
                    f"{match.group(0)}</span>"
                )
        else:

            def _repl(match: re.Match[str]) -> str:
                return f"**{match.group(0)}**"

        text = pattern.sub(_repl, text, count=1)
    return text


def apply_markdown_highlights(
    text: str,
    highlights: list | None,
    default_hex: str = "#FFD700",
) -> str:
    """Wrap highlight phrases in ``**bold**``."""
    return apply_colored_highlights(
        text, highlights, fmt="markdown", default_hex=default_hex,
    )


def apply_html_highlights(
    text: str,
    highlights: list | None,
    default_hex: str = "#FFD700",
) -> str:
    """Wrap highlight phrases in coloured ``<span>`` backgrounds for Google Docs import."""
    return apply_colored_highlights(
        text, highlights, fmt="html", default_hex=default_hex,
    )

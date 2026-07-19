"""Convert validated PraisonAIPPT deck dicts to HTML for Google Docs import."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable, List

from .highlights import apply_html_highlights, deck_default_highlight_hex
from .markdown import _render_verse_entry as _render_md_entry, _strip


def _make_highlight_fn(default_hex: str, enabled: bool) -> Callable[[str, list | None], str]:
    if not enabled:
        return lambda text, _: escape(text)

    def _apply(text: str, highlights: list | None) -> str:
        return apply_html_highlights(text, highlights, default_hex=default_hex)

    return _apply


def _section_heading_html(section_name: str, verses: list) -> str:
    name = _strip(section_name)
    if not name:
        return ""
    if not verses:
        return f"<h1>{escape(name)}</h1>"
    return f"<h2>{escape(name)}</h2>"


def _blockquote_html(body_html: str, reference: str = "") -> str:
    if not body_html:
        return ""
    ref = _strip(reference)
    parts = [f"<blockquote><p>&ldquo;{body_html}&rdquo;</p>"]
    if ref:
        parts.append(f"<p>&mdash; {escape(ref)}</p>")
    parts.append("</blockquote>")
    return "".join(parts)


def _render_verse_html(verse: dict, *, highlight_fn: Callable[[str, list | None], str]) -> str:
    text = _strip(verse.get("text"))
    ref = _strip(verse.get("reference"))
    below = _strip(verse.get("text_below_reference"))
    if not text and not below and not ref:
        return ""
    parts: List[str] = []
    leading = _strip(verse.get("leading_title"))
    if leading:
        parts.append(f"<h3>{escape(leading)}</h3>")
    if text:
        body = highlight_fn(text, verse.get("highlights"))
        parts.append(_blockquote_html(body, ref))
    elif ref:
        parts.append(f"<h3>{escape(ref)}</h3>")
    if below:
        below_body = highlight_fn(below, verse.get("text_below_reference_highlights"))
        parts.append(_blockquote_html(below_body))
    return "\n".join(parts)


def _render_verse_entry_html(
    verse: dict,
    *,
    highlight_fn: Callable[[str, list | None], str],
) -> str:
    if not isinstance(verse, dict):
        return ""

    from ..slide_renderers import resolve_renderer

    try:
        kind = resolve_renderer(verse).kind
    except Exception:
        kind = _strip(verse.get("slide_type")) or "verse"

    if kind in ("verse", "hebrew_rename", "quote", "avatar_quote"):
        return _render_verse_html(verse, highlight_fn=highlight_fn)

    md = _render_md_entry(verse, highlights=True)
    if not md:
        return ""

    chunks: List[str] = []
    for block in md.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            chunks.append(f"<h3>{escape(block[4:])}</h3>")
        elif block.startswith("## "):
            chunks.append(f"<h2>{escape(block[3:])}</h2>")
        elif block.startswith("- ") or (block and block[0].isdigit()):
            lis = []
            for item in block.splitlines():
                item = item.lstrip("-0123456789. ").strip().replace("**", "")
                lis.append(f"<li>{escape(item)}</li>")
            chunks.append("<ul>" + "".join(lis) + "</ul>")
        elif block.startswith("> "):
            lines = [ln[2:] for ln in block.splitlines()]
            body = " ".join(lines).strip('"').replace("**", "")
            chunks.append(f"<blockquote><p>{escape(body)}</p></blockquote>")
        else:
            chunks.append(f"<p>{escape(block.replace('**', ''))}</p>")
    return "\n".join(chunks)


def deck_to_html(
    data: dict,
    *,
    highlights: bool = True,
    separators: bool = True,
    include_title: bool = True,
) -> str:
    """Render deck as HTML with PPT-style coloured highlight backgrounds."""
    default_hex = deck_default_highlight_hex(data.get("slide_style"))
    highlight_fn = _make_highlight_fn(default_hex, highlights)

    blocks: List[str] = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'></head><body>",
    ]

    if include_title:
        title = _strip(data.get("presentation_title"))
        if title:
            blocks.append(f"<h1><strong>{escape(title)}</strong></h1>")
        subtitle = _strip(data.get("presentation_subtitle"))
        if subtitle:
            blocks.append(f"<p>{escape(subtitle)}</p>")

    sections = data.get("sections") or []
    prev_section_had_verses = False

    for section in sections:
        if not isinstance(section, dict):
            continue
        section_name = _strip(section.get("section"))
        verses = section.get("verses") or []

        if separators and prev_section_had_verses:
            blocks.append("<hr/>")

        heading = _section_heading_html(section_name, verses)
        if heading:
            blocks.append(heading)

        section_parts: List[str] = []
        for verse in verses:
            rendered = _render_verse_entry_html(verse, highlight_fn=highlight_fn)
            if rendered:
                section_parts.append(rendered)

        if section_parts:
            blocks.append("\n".join(section_parts))
            prev_section_had_verses = True
        else:
            prev_section_had_verses = False

    blocks.append("</body></html>")
    return "\n".join(blocks) + "\n"


def write_deck_html(
    data: dict,
    output_path: str | Path,
    **kwargs,
) -> Path:
    """Write ``deck_to_html`` output to ``output_path``."""
    path = Path(output_path)
    path.write_text(deck_to_html(data, **kwargs), encoding="utf-8")
    return path

"""Convert validated PraisonAIPPT deck dicts to plain Markdown."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from ..slide_renderers import _column_texts, _table_rows, resolve_renderer
from .highlights import apply_markdown_highlights, deck_default_highlight_hex


class _HighlightDefaults:
    hex: str = "#FFD700"


def _hl(text: str, highlights: list | None) -> str:
    return apply_markdown_highlights(text, highlights, default_hex=_HighlightDefaults.hex)


def _strip(text: object) -> str:
    return str(text or "").strip()


def _section_heading(section_name: str, verses: list) -> str:
    name = _strip(section_name)
    if not name:
        return ""
    if not verses:
        return f"# {name}"
    return f"## {name}"


def _blockquote_lines(text: str, reference: str = "") -> List[str]:
    body = _strip(text)
    if not body:
        return []
    lines = [f'> "{body}"']
    ref = _strip(reference)
    if ref:
        lines.append(f"> — {ref}")
    return lines


def _markdown_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalised = [list(r) + [""] * (width - len(r)) for r in rows]
    header = normalised[0]
    sep = ["---"] * width
    body = normalised[1:] if len(normalised) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _render_list(verse: dict, *, highlights: bool) -> str:
    ref = _strip(verse.get("reference"))
    raw = _strip(verse.get("text"))
    if not raw:
        return ""
    items = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if not items:
        return ""
    hl = verse.get("highlights") if highlights else None
    numbered = verse.get("list_type") == "numbered"
    parts: List[str] = []
    if ref:
        parts.append(f"### {ref}")
    for i, item in enumerate(items, 1):
        item_text = _hl(item, hl) if highlights else item
        parts.append(f"{i}. {item_text}" if numbered else f"- {item_text}")
    return "\n\n".join(parts)


def _render_comparison(verse: dict, *, highlights: bool) -> str:
    cols = verse.get("columns")
    if not isinstance(cols, list) or len(cols) < 2:
        return ""
    rows: List[List[str]] = [["", ""]]
    for col in cols[:2]:
        if isinstance(col, dict):
            heading = _strip(col.get("heading") or col.get("title") or "Column")
            text = _strip(col.get("text"))
            if highlights:
                text = _hl(text, col.get("highlights"))
            rows.append([heading, text])
        else:
            rows.append(["Column", _strip(col)])
    ref = _strip(verse.get("reference"))
    table = _markdown_table(rows)
    if ref:
        return f"### {ref}\n\n{table}".strip()
    return table


def _render_two_column(verse: dict, *, highlights: bool) -> str:
    left, right, left_hl, right_hl = _column_texts(verse)
    left = _strip(left)
    right = _strip(right)
    if not left and not right:
        return ""
    if highlights:
        left = _hl(left, left_hl)
        right = _hl(right, right_hl)
    ref = _strip(verse.get("reference"))
    parts = []
    if ref:
        parts.append(f"### {ref}")
    if left:
        parts.append(f"**Left**\n\n{left}")
    if right:
        parts.append(f"**Right**\n\n{right}")
    return "\n\n".join(parts)


def _render_table(verse: dict) -> str:
    rows = _table_rows(verse)
    if not rows:
        return ""
    ref = _strip(verse.get("reference"))
    table = _markdown_table(rows)
    if ref:
        return f"### {ref}\n\n{table}"
    return table


def _render_image_like(verse: dict) -> str:
    path = _strip(verse.get("image_path") or verse.get("media_path"))
    ref = _strip(verse.get("reference"))
    caption = _strip(verse.get("text"))
    if not path and not caption:
        return ""
    parts: List[str] = []
    if path:
        alt = ref or Path(path).stem
        parts.append(f"![{alt}]({path})")
    if caption:
        parts.append(caption)
    if ref and not path:
        parts.append(f"### {ref}")
    return "\n\n".join(parts)


def _render_big_number(verse: dict) -> str:
    number = _strip(verse.get("number"))
    label = _strip(verse.get("label"))
    ref = _strip(verse.get("reference"))
    if not number and not label:
        return ""
    parts = []
    if number:
        parts.append(f"## {number}")
    if label:
        parts.append(label)
    if ref:
        parts.append(f"— {ref}")
    return "\n\n".join(parts)


def _render_title_only(verse: dict) -> str:
    title = _strip(verse.get("text"))
    subtitle = _strip(verse.get("reference"))
    if not title and not subtitle:
        return ""
    parts = []
    if title:
        parts.append(f"### {title}")
    if subtitle:
        parts.append(subtitle)
    return "\n\n".join(parts)


def _render_quote(verse: dict, *, highlights: bool) -> str:
    text = _strip(verse.get("text"))
    ref = _strip(verse.get("reference"))
    if not text:
        return ""
    if highlights:
        text = _hl(text, verse.get("highlights"))
    return "\n".join(_blockquote_lines(text, ref))


def _render_verse(verse: dict, *, highlights: bool) -> str:
    text = _strip(verse.get("text"))
    ref = _strip(verse.get("reference"))
    below = _strip(verse.get("text_below_reference"))
    if not text and not below and not ref:
        return ""
    parts: List[str] = []
    leading = _strip(verse.get("leading_title"))
    if leading:
        parts.append(f"### {leading}")
    if text:
        body = _hl(text, verse.get("highlights")) if highlights else text
        parts.append("\n".join(_blockquote_lines(body, ref)))
    elif ref:
        parts.append(f"### {ref}")
    if below:
        below_body = (
            _hl(below, verse.get("text_below_reference_highlights"))
            if highlights
            else below
        )
        parts.append("\n".join(_blockquote_lines(below_body)))
    return "\n\n".join(parts)


def _render_generic_fallback(verse: dict, kind: str, *, highlights: bool) -> str:
    headline = _strip(verse.get("headline") or verse.get("leading_title"))
    text = _strip(verse.get("text"))
    ref = _strip(verse.get("reference"))
    parts: List[str] = []
    if headline:
        parts.append(f"### {headline}")
    elif ref:
        parts.append(f"### {ref}")
    if kind and kind not in ("verse", "list"):
        parts.append(f"*{kind}*")
    if text:
        body = _hl(text, verse.get("highlights")) if highlights else text
        parts.append(body)
    image = _render_image_like(verse)
    if image:
        parts.append(image)
    items = verse.get("items")
    if isinstance(items, list) and items:
        bullets = []
        for item in items:
            if isinstance(item, dict):
                line = _strip(item.get("text") or item.get("title") or item.get("heading"))
            else:
                line = _strip(item)
            if line:
                bullets.append(f"- {line}")
        if bullets:
            parts.append("\n".join(bullets))
    return "\n\n".join(p for p in parts if p)


def _render_verse_entry(verse: dict, *, highlights: bool) -> str:
    if not isinstance(verse, dict):
        return ""
    try:
        kind = resolve_renderer(verse).kind
    except Exception:
        kind = _strip(verse.get("slide_type")) or "verse"

    if kind == "list":
        return _render_list(verse, highlights=highlights)
    if kind == "comparison":
        return _render_comparison(verse, highlights=highlights)
    if kind == "two_column":
        return _render_two_column(verse, highlights=highlights)
    if kind == "table":
        return _render_table(verse)
    if kind in ("image", "media_only", "media_border"):
        return _render_image_like(verse)
    if kind == "picture_text":
        img = _render_image_like(verse)
        txt = _strip(verse.get("text"))
        return "\n\n".join(p for p in (img, txt) if p)
    if kind == "big_number":
        return _render_big_number(verse)
    if kind == "title_only":
        return _render_title_only(verse)
    if kind in ("quote", "avatar_quote"):
        return _render_quote(verse, highlights=highlights)
    if kind in ("verse", "hebrew_rename"):
        return _render_verse(verse, highlights=highlights)
    if _strip(verse.get("text")) or _strip(verse.get("reference")):
        rendered = _render_verse(verse, highlights=highlights)
        if rendered:
            return rendered
    return _render_generic_fallback(verse, kind, highlights=highlights)


def deck_to_markdown(
    data: dict,
    *,
    highlights: bool = True,
    separators: bool = True,
    include_title: bool = True,
) -> str:
    """Render a validated deck dict as plain Markdown."""
    _HighlightDefaults.hex = deck_default_highlight_hex(data.get("slide_style"))
    blocks: List[str] = []

    if include_title:
        title = _strip(data.get("presentation_title"))
        if title:
            blocks.append(f"# **{title}**")
        subtitle = _strip(data.get("presentation_subtitle"))
        if subtitle:
            blocks.append(subtitle)

    sections = data.get("sections") or []
    prev_section_had_verses = False

    for section in sections:
        if not isinstance(section, dict):
            continue
        section_name = _strip(section.get("section"))
        verses = section.get("verses") or []

        if separators and prev_section_had_verses and blocks:
            blocks.append("---")

        heading = _section_heading(section_name, verses)
        if heading:
            blocks.append(heading)

        section_parts: List[str] = []
        for verse in verses:
            rendered = _render_verse_entry(verse, highlights=highlights)
            if rendered:
                section_parts.append(rendered)

        if section_parts:
            blocks.append("\n\n".join(section_parts))
            prev_section_had_verses = True
        else:
            prev_section_had_verses = False

    return "\n\n".join(blocks).strip() + "\n"


def write_deck_markdown(
    data: dict,
    output_path: str | Path,
    **kwargs,
) -> Path:
    """Write ``deck_to_markdown`` output to ``output_path``."""
    path = Path(output_path)
    path.write_text(deck_to_markdown(data, **kwargs), encoding="utf-8")
    return path

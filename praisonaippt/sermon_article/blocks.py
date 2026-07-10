"""Gutenberg HTML block builders — shared across all article builders."""
from __future__ import annotations

import re

from .config import GOLD, GREEN


def highlight(text: str, phrases: list, color: str = GREEN) -> str:
    for ph in sorted({p for p in phrases if p}, key=len, reverse=True):
        if isinstance(ph, dict):
            ph = ph.get("text", "")
        if not ph:
            continue
        text = re.sub(
            re.escape(str(ph)),
            f'<mark style="background-color:{color}"><strong>{ph}</strong></mark>',
            text,
            count=1,
            flags=re.I,
        )
    return text


def apply_highlights(text: str, highlights: list | None) -> str:
    if not highlights:
        return text
    for h in highlights:
        if isinstance(h, dict):
            c = (h.get("color") or "").lower()
            color = GOLD if c in ("#ffd700", "gold", "#fde68a") else GREEN
            t = h.get("text", "")
            if t:
                text = highlight(text, [t], color)
        elif isinstance(h, str):
            text = highlight(text, [h], GREEN)
    return text


def block(tag: str, inner: str, attrs: str = "") -> str:
    if attrs:
        return f"<!-- wp:{tag} {attrs} -->\n{inner}\n<!-- /wp:{tag} -->"
    return f"<!-- wp:{tag} -->\n{inner}\n<!-- /wp:{tag} -->"


def h3(title: str) -> str:
    return block("heading", f'<h3 class="wp-block-heading">{title}</h3>', '{"level":3}')


def h2(title: str) -> str:
    return block("heading", f'<h2 class="wp-block-heading">{title}</h2>')


def paragraph(text: str) -> str:
    return block("paragraph", f"<p>{text}</p>")


def quote(text: str) -> str:
    return block("quote", f'<blockquote class="wp-block-quote"><p>{text}</p></blockquote>')


def separator() -> str:
    return block("separator", '<hr class="wp-block-separator has-alpha-channel-opacity"/>')


def bullet_list(items: list[str]) -> str:
    lis = "".join(f"<li>{i}</li>" for i in items)
    return block("list", f'<ul class="wp-block-list">{lis}</ul>')


def ordered_list(items: list[str]) -> str:
    lis = "".join(f"<li>{i}</li>" for i in items)
    return block("list", f'<ol class="wp-block-list">{lis}</ol>', '{"ordered":true}')


def table(headers: list[str], rows: list[tuple]) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return block(
        "table",
        f'<figure class="wp-block-table"><table style="width:100%">'
        f"<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></figure>",
    )


def verse_block(ref: str, text: str, highlights: list | None = None) -> str:
    body = apply_highlights(text.strip().strip('"'), highlights or [])
    cite = ref.strip() if ref else ""
    quote_body = f'<em>"{body}"</em>' + (f" — <strong>{cite}</strong>" if cite and re.search(r"\d+:\d+", cite) else "")
    # Split long scripture into ≤380-char blockquote chunks (structure audit max para 450)
    if len(re.sub(r"<[^>]+>", "", quote_body)) > 380:
        plain = re.sub(r"<[^>]+>", "", body)
        words = plain.split()
        chunks: list[str] = []
        buf: list[str] = []
        clen = 0
        for w in words:
            if clen + len(w) + 1 > 380 and buf:
                chunks.append(" ".join(buf))
                buf, clen = [], 0
            buf.append(w)
            clen += len(w) + 1
        if buf:
            chunks.append(" ".join(buf))
        quotes = [quote(f'<em>"{apply_highlights(c, highlights or [])}"</em>') for c in chunks]
        cite_p = paragraph(f"<strong>{cite}</strong>") if cite and re.search(r"\d+:\d+", cite) else ""
        return "\n".join([p for p in [cite_p, *quotes] if p])
    if cite and re.search(r"\d+:\d+", cite):
        return f"{paragraph(f'<strong>{cite}</strong>')}\n{quote(quote_body)}"
    if cite:
        return f"{paragraph(f'<strong>{cite}</strong>')}\n{quote(f'<em>{body}</em>')}"
    if re.search(r"\d+:\d+", text):
        return f"{paragraph(f'<strong>{text.strip()}</strong>')}\n{quote(f'<em>{body}</em>')}"
    return quote(f"<em>{body}</em>")


def highlight_key() -> str:
    return quote(
        "🎨 <strong>Highlight key:</strong> 🟩 = grace / apart-from-works truth · "
        "🟨 = the precious gift · <strong>bold</strong> = key terms"
    )


def footer(topic: str) -> str:
    return paragraph(
        f"<em>🎧 Scripture-based study on {topic}. "
        "If it strengthened you, share it with someone who needs this truth today. 💛</em>"
    )


def takeaway_section(bullets: list[str]) -> str:
    return "\n\n".join([separator(), h2("🎯 The Takeaway"), ordered_list(bullets), separator()])

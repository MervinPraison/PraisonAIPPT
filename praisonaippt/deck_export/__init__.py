"""Deck export helpers (Markdown and future formats)."""

from .markdown import deck_to_markdown, write_deck_markdown
from .html import deck_to_html, write_deck_html

__all__ = [
    "deck_to_markdown",
    "write_deck_markdown",
    "deck_to_html",
    "write_deck_html",
    "deck_to_docx",
    "write_deck_docx",
]


def deck_to_docx(*args, **kwargs):
    from .docx import deck_to_docx as _fn

    return _fn(*args, **kwargs)


def write_deck_docx(*args, **kwargs):
    from .docx import write_deck_docx as _fn

    return _fn(*args, **kwargs)

"""Lightweight schema validation for the verses dict.

Only top-level keys and section/verse mandatory fields are enforced strictly.
Unknown keys produce warnings (via :mod:`logging`) so misspellings such as
``slide_styles`` instead of ``slide_style`` are surfaced without breaking
forward-compatibility for new keys added by callers.
"""

from __future__ import annotations

import difflib
import logging
from typing import Any, Dict, Iterable

from .exceptions import SchemaError

logger = logging.getLogger(__name__)


_TOP_LEVEL_KEYS = {
    "presentation_title",
    "presentation_subtitle",
    "sections",
    "slide_style",
    "slide_size",
    "auto_upload_gdrive",
    # implementation/extension hooks
    "_source",
}

_SECTION_KEYS = {"section", "section_subtitle", "verses"}

_VERSE_KEYS = {
    "reference",
    "text",
    "highlights",
    "large_text",
    "list_type",
    "alignment",
    "font_size",
    "reference_font_size",
    "leading_title",
    "split_max_length",
    "slide_type",
    "image_path",
    "text_below_reference",
    "text_below_reference_highlights",
    "text_below_reference_large_text",
}


def _warn_unknown(actual: Iterable[str], allowed: set, where: str) -> None:
    for key in actual:
        if key in allowed:
            continue
        suggestion = difflib.get_close_matches(key, allowed, n=1)
        hint = f" (did you mean '{suggestion[0]}'?)" if suggestion else ""
        logger.warning("Unknown key %r in %s%s", key, where, hint)


def validate_verses(data: Any) -> Dict[str, Any]:
    """Validate the top-level verses dictionary.

    Returns the same dict on success (mutating only to add the default
    ``sections`` list when missing, matching the existing loader contract).
    Raises :class:`SchemaError` on hard violations.
    """
    if not isinstance(data, dict):
        raise SchemaError("Verses data must be a mapping/dictionary at the top level")

    _warn_unknown(data.keys(), _TOP_LEVEL_KEYS, "top-level")

    sections = data.get("sections")
    if sections is None:
        data["sections"] = []
        sections = data["sections"]
    if not isinstance(sections, list):
        raise SchemaError("'sections' must be a list")

    for s_idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise SchemaError(f"sections[{s_idx}] must be a mapping")
        _warn_unknown(section.keys(), _SECTION_KEYS, f"sections[{s_idx}]")

        verses = section.get("verses", []) or []
        if not isinstance(verses, list):
            raise SchemaError(f"sections[{s_idx}].verses must be a list")

        for v_idx, verse in enumerate(verses):
            if not isinstance(verse, dict):
                raise SchemaError(
                    f"sections[{s_idx}].verses[{v_idx}] must be a mapping"
                )
            _warn_unknown(
                verse.keys(),
                _VERSE_KEYS,
                f"sections[{s_idx}].verses[{v_idx}]",
            )
            # 'reference' or 'text' is required (text can be empty for title-only slides)
            if "reference" not in verse and "text" not in verse:
                raise SchemaError(
                    f"sections[{s_idx}].verses[{v_idx}] must have 'reference' or 'text'"
                )

    return data

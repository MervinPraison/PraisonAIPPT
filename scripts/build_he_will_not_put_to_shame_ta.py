#!/usr/bin/env python3
"""Build examples/he_will_not_put_to_shame_ta.yaml from NKJV deck + TAOVBSI (local tamil-ov.json)."""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LYRICAL_SRC = Path.home() / "praisonai-lyrical-video" / "src"
sys.path.insert(0, str(LYRICAL_SRC))

from praisonai_lyrical_video.bible import tamil_verse  # noqa: E402
from praisonai_lyrical_video.scripture_books import parse_reference, ScriptureBookError  # noqa: E402

EN_PATH = ROOT / "examples" / "he_will_not_put_to_shame.yaml"
TA_HINTS_PATH = ROOT / "examples" / "he_will_not_put_to_shame_tamil.yaml"
OUT_PATH = ROOT / "examples" / "he_will_not_put_to_shame_ta.yaml"

_CITATION_TAIL = re.compile(r"\s*\([^)]+\)\s*$")
_VERSE_START = re.compile(r"^(\d+)")


def strip_translation(ref: str) -> str:
    return _CITATION_TAIL.sub("", ref.strip())


def ta_lookup_key(ref: str) -> str | None:
    try:
        parsed = parse_reference(strip_translation(ref))
    except ScriptureBookError:
        return None
    verse = _VERSE_START.match(parsed.verse.strip())
    if not verse:
        return None
    return f"{parsed.book.tamil} {parsed.chapter}:{verse.group(1)}"


def load_tamil_hint_index() -> dict[str, dict]:
    if not TA_HINTS_PATH.is_file():
        return {}
    data = yaml.safe_load(TA_HINTS_PATH.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for section in data.get("sections") or []:
        for verse in section.get("verses") or []:
            ref = verse.get("reference") or ""
            key = ta_lookup_key(ref.replace("–", "-"))
            if key:
                index[key] = verse
    return index


def tamil_reference(ref_en: str) -> str | None:
    key_base = strip_translation(ref_en)
    try:
        parsed = parse_reference(key_base)
    except ScriptureBookError:
        return None
    verse = _VERSE_START.match(parsed.verse.strip())
    if not verse:
        return None
    return f"{parsed.book.tamil} {parsed.chapter}:{verse.group(1)} (TAOVBSI)"


def tamil_text_for(ref_en: str, hint: dict | None) -> str | None:
    if hint and (hint.get("text") or "").strip():
        return hint["text"].strip()
    key_base = strip_translation(ref_en)
    try:
        parsed = parse_reference(key_base)
        v = int(_VERSE_START.match(parsed.verse.strip()).group(1))
        return tamil_verse(parsed.book, parsed.chapter, v).strip()
    except (ScriptureBookError, AttributeError, ValueError):
        return None


def map_highlights_ta(verse_en: dict, hint: dict | None) -> list | None:
    if hint and hint.get("highlights"):
        out = copy.deepcopy(hint["highlights"])
        en_hl = verse_en.get("highlights") or []
        for item in en_hl:
            if isinstance(item, dict) and item.get("color"):
                # Romans 10:17: green on "faith comes" → green on Tamil faith phrase
                if item.get("text") == "faith comes" and out:
                    for i, h in enumerate(out):
                        if isinstance(h, str) and "விசுவாசம்" in h:
                            out[i] = {"text": h, "color": item["color"]}
                            break
        return out
    return None


def enrich_verse(verse: dict, hints: dict[str, dict]) -> dict:
    ref = verse.get("reference") or ""
    if not ref or not (verse.get("text") or "").strip():
        return verse
    key = ta_lookup_key(ref)
    hint = hints.get(key) if key else None
    ref_ta = tamil_reference(ref)
    text_ta = tamil_text_for(ref, hint)
    if not ref_ta or not text_ta:
        return verse
    out = copy.deepcopy(verse)
    out["reference_ta"] = ref_ta
    out["text_ta"] = text_ta
    hl_ta = map_highlights_ta(verse, hint)
    if hl_ta:
        out["highlights_ta"] = hl_ta
    return out


def main() -> None:
    en = yaml.safe_load(EN_PATH.read_text(encoding="utf-8"))
    hints = load_tamil_hint_index()
    deck = copy.deepcopy(en)
    deck["presentation_title"] = "He will not put to shame / அவன் வெட்கப்படுவதில்லை"
    deck["presentation_subtitle"] = "NKJV + TAOVBSI"
    style = dict(deck.get("slide_style") or {})
    style.setdefault("font_name", "Palatino")
    style["tamil_font_name"] = "Tamil MN"
    deck["slide_style"] = style

    for section in deck.get("sections") or []:
        verses = []
        for verse in section.get("verses") or []:
            verses.append(enrich_verse(verse, hints))
        section["verses"] = verses

    header = (
        "# Bilingual deck: English body + TAOVBSI Tamil below each verse (reference_ta / text_ta).\n"
        "# Regenerate: python scripts/build_he_will_not_put_to_shame_ta.py\n"
    )
    OUT_PATH.write_text(
        header + yaml.dump(deck, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

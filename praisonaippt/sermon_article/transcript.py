"""Transcript parsing helpers."""
from __future__ import annotations

import re

BANNER = re.compile(
    r"^(how many of you|shall we all|amen[!]?|tell the person|it's going to be a great day|"
    r"i believe that|say the person|can anyone remember|do you remember|ok,? so)",
    re.I,
)

RAW_PASTE = re.compile(
    r"\b(how many of you|tell the person next|shall we all read|amen\?)\b",
    re.I,
)


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def filter_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out: list[str] = []
    for s in parts:
        s = s.strip()
        if len(s) < 25 or BANNER.match(s):
            continue
        s = re.sub(r"\bamen\b", "", s, flags=re.I).strip()
        if len(s) < 25:
            continue
        # Split run-on clauses when punctuation is sparse
        if len(s) > 900:
            for chunk in re.split(r"(?<=[;])\s+|(?<=\bso)\s+|(?<=\bBut)\s+", s):
                chunk = chunk.strip()
                if len(chunk) >= 25:
                    out.append(chunk)
        else:
            out.append(s)
    return out


def has_raw_paste(html_or_text: str) -> bool:
    return bool(RAW_PASTE.search(html_or_text))

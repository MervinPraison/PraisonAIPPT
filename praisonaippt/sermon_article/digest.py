"""Condense transcript sentences into scannable intro + bullet lists."""
from __future__ import annotations

import re

MAX_INTRO_CHARS = 320
MAX_BULLET_CHARS = 160
MAX_PARAGRAPH_CHARS = 420

FILLER = re.compile(
    r"(tell the person next to you|shall we all read|can anyone say|everyone tell|"
    r"again tell|amen[!?]?|how many of you|it's going to be a great day|"
    r"just know,?\s*we are here|okay,?\s*the third thing|don't worry|"
    r"we are going to see|shall we read|okay,?\s*let'?s|again we are going|"
    r"how much you were jumping|do you remember the message)",
    re.I,
)

JUNK_BULLET = re.compile(
    r"^(we are going|okay|shall we|let's|so when you see|it's all in the same|"
    r"jesus said,|jesus christ said,|men are like)",
    re.I,
)


def _clean(text: str) -> str:
    text = FILLER.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(so|okay|now|then|and)\s+", "", text, flags=re.I)
    return text


def _shorten(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def _bold_terms(text: str) -> str:
    for term in (
        "100%", "full restoration", "zōē", "zoe", "righteousness", "grace",
        "faith", "heir", "stand still", "miracles", "free", "hear him",
        "apart from the law", "zero sickness", "shalom", "saved", "life",
    ):
        text = re.sub(re.escape(term), f"<strong>{term}</strong>", text, count=1, flags=re.I)
    return text


def sentences_to_bullets(sentences: list[str], *, max_items: int = 5) -> list[str]:
    """Turn transcript sentences into short bullet points — not raw paste."""
    bullets: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        s = _clean(s)
        if len(s) < 20 or s.lower() in seen or JUNK_BULLET.search(s):
            continue
        seen.add(s.lower())
        short = _shorten(s, MAX_BULLET_CHARS)
        if len(short) >= 20:
            bullets.append(_bold_terms(short))
        if len(bullets) >= max_items:
            break
    return bullets


def digest_intro(sentences: list[str]) -> str:
    """One short intro paragraph — condensed, not transcript dump."""
    usable = [_clean(s) for s in sentences if len(_clean(s)) >= 40]
    if not usable:
        return ""
    # Prefer sentences with teaching keywords over filler
    usable.sort(key=lambda x: -len(set(x.lower().split()) & {
        "god", "christ", "jesus", "restoration", "faith", "grace", "life", "heal",
        "righteous", "blessing", "gospel", "covenant", "miracle", "free",
    }))
    parts = [_shorten(usable[0], 180)]
    if len(usable) > 1 and len(parts[0]) < 200:
        extra = _shorten(usable[1], 140)
        if extra and extra not in parts[0]:
            parts.append(extra)
    intro = " ".join(parts)
    return _shorten(intro, MAX_INTRO_CHARS)


def digest_section(sentences: list[str], *, max_items: int | None = None) -> tuple[str, list[str]]:
    cap = max_items or min(5, max(3, len(sentences) // 3))
    intro = digest_intro(sentences[:4])
    bullets = sentences_to_bullets(sentences, max_items=cap)
    return intro, bullets

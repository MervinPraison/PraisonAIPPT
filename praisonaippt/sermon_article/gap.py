"""Transcript ↔ article gap analysis."""
from __future__ import annotations

import re
from pathlib import Path

from .builders import build_article
from .protocol import GapReport, SermonJob, SermonPack
from .transcript import RAW_PASTE, filter_sentences, has_raw_paste, word_count
from .validate import validate

GENERIC_TAKEAWAY = "Hear the word of Christ"


def gap_report(job: SermonJob, pack: SermonPack, html_path: Path | None = None) -> GapReport:
    tpath = job.transcript_path(pack.pack_dir)
    transcript = tpath.read_text(encoding="utf-8")
    tw = word_count(transcript)

    if html_path is None or not html_path.exists():
        html_path = job.draft_html_path(pack.draft_dir)

    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
    else:
        html = build_article(job, pack)

    hw = word_count(re.sub(r"<[^>]+>", " ", html))
    ratio = hw / tw if tw else 0.0

    val = validate(job, pack, html_path) if html_path.exists() else None
    yaml_missing = val.yaml_missing if val else []

    themes = _missing_themes(transcript, html)
    return GapReport(
        slug=job.slug,
        transcript_words=tw,
        article_words=hw,
        ratio=ratio,
        yaml_missing=yaml_missing,
        raw_transcript_paste=has_raw_paste(html),
        generic_takeaway=GENERIC_TAKEAWAY in html,
        missing_themes=themes,
    )


def _missing_themes(transcript: str, html: str) -> list[str]:
    """Heuristic: flag transcript keywords absent from article."""
    t_low = transcript.lower()
    h_low = re.sub(r"<[^>]+>", " ", html).lower()
    candidates: list[tuple[str, str]] = []
    for m in re.finditer(r"(?:read|shall we read)\s+([a-z]+ \d+(?:[:.]\d+)?)", t_low):
        candidates.append((m.group(1), m.group(1)))
    for phrase in ("stand still", "first adam", "last adam", "deuteronomy 28", "2 kings 3",
                   "holy communion", "heir of the world", "full restoration", "el shaddai"):
        if phrase in t_low:
            candidates.append((phrase, phrase))
    missing = []
    for label, needle in candidates[:12]:
        if needle not in h_low and label not in missing:
            missing.append(label)
    return missing[:5]

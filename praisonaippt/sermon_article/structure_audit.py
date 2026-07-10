"""Structural quality audit — blocks mechanical / raw-paste articles."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import DEFAULT_AGENT_DIR, MIN_WORD_RATIO
from .faithful import DIGEST_OVERRIDES
from .transcript_flow import FLOW_BY_SLUG
from .protocol import SermonJob, SermonPack
from .transcript import word_count

MAX_PARAGRAPH_CHARS = 450
MIN_H2_SECTIONS = 8
MIN_LIST_BLOCKS = 6
MIN_TABLE_COUNT = 1

TRANSCRIPT_FILLER = (
    "tell the person next to you",
    "shall we all read",
    "again tell",
    "everyone tell",
    "we are going to see",
    "shall we read",
    "jesus said, i have taken",
    "jesus christ said, i have taken",
)

TABLE_CUES = (
    "two trees", "world's way", "first adam", "last adam", "pharisee",
    "tax collector", "recap", "love of god", "love for god", "before and after",
    "law path", "faith path", "worldly", "god's way",
)


@dataclass
class StructureReport:
    slug: str
    ok: bool
    h2_count: int = 0
    table_count: int = 0
    max_paragraph_chars: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "ok": self.ok,
            "h2_count": self.h2_count,
            "table_count": self.table_count,
            "max_paragraph_chars": self.max_paragraph_chars,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _paragraph_lengths(html: str) -> list[int]:
    return [
        len(re.sub(r"<[^>]+>", "", m, flags=re.S).strip())
        for m in re.findall(r"<p>(.*?)</p>", html, re.S)
    ]


def _h2_titles(html: str) -> list[str]:
    return [
        re.sub(r"<[^>]+>", "", h, flags=re.S).strip()
        for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    ]


def audit_structure(
    job: SermonJob,
    pack: SermonPack,
    html_path: Path | None = None,
    *,
    agent_dir: Path = DEFAULT_AGENT_DIR,
) -> StructureReport:
    path = html_path or agent_dir / f"biblerevelation-{job.slug}.html"
    if not path.exists():
        return StructureReport(slug=job.slug, ok=False, errors=[f"HTML not found: {path}"])

    html = path.read_text(encoding="utf-8")
    errors: list[str] = []

    h2s = _h2_titles(html)
    h2_count = len(h2s)
    table_count = html.count("wp-block-table")
    list_count = html.count("wp-block-list")
    para_lens = _paragraph_lengths(html)
    max_para = max(para_lens, default=0)
    html_low = html.lower()

    if h2_count < MIN_H2_SECTIONS:
        errors.append(f"Only {h2_count} h2 sections — need ≥{MIN_H2_SECTIONS}")
    if any("Teaching Block" in t for t in h2s):
        errors.append("Generic 'Teaching Block' headings — use sermon-specific h2 titles")
    if max_para > MAX_PARAGRAPH_CHARS:
        errors.append(f"Paragraph too long ({max_para} chars) — condense to digest format")
    if list_count < MIN_LIST_BLOCKS:
        errors.append(f"Only {list_count} list blocks — need ≥{MIN_LIST_BLOCKS} for scannable digest")
    if table_count < MIN_TABLE_COUNT:
        errors.append(f"No tables — need ≥{MIN_TABLE_COUNT} comparison/summary table")
    if any(f in html_low for f in TRANSCRIPT_FILLER):
        errors.append("Raw spoken filler detected — condense to bullets/tables")
    if "Highlight key" not in html:
        errors.append("Missing highlight-key blockquote near top")
    if "Takeaway" not in html:
        errors.append("Missing Takeaway section")
    if "Scripture-based study" not in html and "Based on a Sunday message" not in html:
        errors.append("Missing closing footer paragraph")
    if "Scripture from the Slides" in html:
        errors.append("YAML appendix present — weave verses inline")

    transcript = job.transcript_path(pack.pack_dir).read_text(encoding="utf-8")
    t_low = transcript.lower()
    if any(cue in t_low for cue in TABLE_CUES) and table_count == 0:
        errors.append("Transcript teaches comparisons but article has no tables")

    tw = word_count(transcript)
    hw = word_count(re.sub(r"<[^>]+>", " ", html))
    ratio = hw / tw if tw else 0.0
    min_ratio = 0.30 if job.slug in DIGEST_OVERRIDES or job.slug in FLOW_BY_SLUG else MIN_WORD_RATIO
    if ratio < min_ratio:
        errors.append(f"Word ratio {ratio:.0%} below {min_ratio:.0%}")

    return StructureReport(
        slug=job.slug,
        ok=not errors,
        h2_count=h2_count,
        table_count=table_count,
        max_paragraph_chars=max_para,
        errors=errors,
    )

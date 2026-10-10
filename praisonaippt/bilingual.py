"""English + Tamil scripture on one slide: where the Tamil comes from.

Two sources, one rule — **YAML wins, the Tamil Bible fills the rest**:

1. ``text_ta`` / ``reference_ta`` written in the deck are used exactly as given
   (a tidied spelling, a different verse range, a pastor's choice).
2. Any scripture verse without ``text_ta`` is looked up in the local Tamil
   O.V. (TAOVBSI / TAMOVR) Bible by its English ``reference`` — or by
   ``reference_ta`` when that is set — ranges included (``Romans 10:6–12``).

Enable it in the deck::

    bilingual:
      language: ta          # the only language with a bundled lookup today
      version: TAOVBSI      # label shown after the Tamil reference
      source: auto          # auto = fetch missing verses; yaml = never fetch
      strict: false         # true = fail the build when a verse has no Tamil
      bible_path: ~/.praisonai/lyrical-video/tamil-ov.json   # optional

or on the command line with ``--bilingual ta``. A deck whose verses already
carry ``text_ta`` renders bilingually without the block (``source: yaml``).

``highlights_ta`` is never guessed: Tamil word order differs, so emphasis is
authored. The fill report lists verses whose English has highlights but whose
Tamil has none, and any ``highlights_ta`` phrase that is not in its text.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .bible_books import BibleBook, BookNotFound, lookup_book
from .exceptions import SchemaError

logger = logging.getLogger(__name__)

BIBLE_PATH_ENV = "PRAISONAI_TAMIL_BIBLE"
DEFAULT_BIBLE_PATHS = (
    Path.home() / ".praisonai" / "lyrical-video" / "tamil-ov.json",
    Path.home() / ".praisonaippt" / "tamil-ov.json",
)
SUPPORTED_LANGUAGES = ("ta",)
SOURCES = ("auto", "yaml")
SCRIPTURE_SLIDE_TYPES = (None, "", "verse")


class BibleLookupError(LookupError):
    """A reference that cannot be parsed or is not in the Tamil Bible."""


# --------------------------------------------------------------------------- config


@dataclass
class BilingualConfig:
    enabled: bool = False
    language: str = "ta"
    version: str = "TAOVBSI"
    source: str = "auto"
    strict: bool = False
    bible_path: Optional[str] = None

    @classmethod
    def from_deck(cls, data: dict) -> "BilingualConfig":
        raw = data.get("bilingual")
        if raw is None:
            # Legacy decks: Tamil written straight into the YAML.
            return cls(enabled=deck_has_tamil_text(data), source="yaml")
        if raw is False:
            return cls(enabled=False)
        if raw is True:
            return cls(enabled=True)
        if isinstance(raw, str):
            return cls(enabled=True, language=raw.strip().lower())
        if not isinstance(raw, dict):
            raise SchemaError("bilingual must be true/false, a language code, or a mapping")
        cfg = cls(
            enabled=bool(raw.get("enabled", True)),
            language=str(raw.get("language", "ta")).strip().lower(),
            version=str(raw.get("version", "TAOVBSI")).strip(),
            source=str(raw.get("source", "auto")).strip().lower(),
            strict=bool(raw.get("strict", False)),
            bible_path=raw.get("bible_path"),
        )
        return cfg

    def validate(self) -> None:
        if self.language not in SUPPORTED_LANGUAGES:
            raise SchemaError(
                f"bilingual.language {self.language!r} is not supported "
                f"(supported: {', '.join(SUPPORTED_LANGUAGES)})"
            )
        if self.source not in SOURCES:
            raise SchemaError(f"bilingual.source must be one of: {', '.join(SOURCES)}")


def validate_bilingual_block(raw: Any) -> None:
    """Schema hook for the top-level ``bilingual`` key."""
    if raw is None:
        return
    BilingualConfig.from_deck({"bilingual": raw}).validate()
    if isinstance(raw, dict):
        allowed = {"enabled", "language", "version", "source", "strict", "bible_path"}
        for key in raw:
            if key not in allowed:
                logger.warning("Unknown key %r in bilingual (allowed: %s)", key, ", ".join(sorted(allowed)))


def iter_scripture_verses(data: dict):
    """Yield ``(section, verse)`` for every verse rendered as a scripture slide."""
    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for verse in section.get("verses") or []:
            if isinstance(verse, dict) and verse.get("slide_type") in SCRIPTURE_SLIDE_TYPES:
                yield section, verse


def deck_has_tamil_text(data: dict) -> bool:
    return any((v.get("text_ta") or "").strip() for _, v in iter_scripture_verses(data))


# --------------------------------------------------------------------------- Bible


_CACHE: Dict[str, Dict[str, str]] = {}


def resolve_bible_path(configured: Optional[str] = None) -> Optional[Path]:
    """Deck ``bible_path`` > ``$PRAISONAI_TAMIL_BIBLE`` > the default locations."""
    for candidate in (configured, os.environ.get(BIBLE_PATH_ENV)):
        if candidate:
            return Path(candidate).expanduser()
    for path in DEFAULT_BIBLE_PATHS:
        if path.is_file():
            return path
    return None


def load_tamil_bible(path: Optional[str] = None) -> Dict[str, str]:
    """``{"<book index>:<chapter>:<verse>": text}`` — the format praisonai-lyrical-video writes."""
    dest = resolve_bible_path(path)
    if dest is None or not dest.is_file():
        where = dest or " or ".join(str(p) for p in DEFAULT_BIBLE_PATHS)
        raise BibleLookupError(
            f"Tamil Bible not found ({where}). Set {BIBLE_PATH_ENV} or bilingual.bible_path, "
            "or import it with: praisonai-lyrical-video bible-import"
        )
    key = str(dest.resolve())
    if key not in _CACHE:
        _CACHE[key] = json.loads(dest.read_text(encoding="utf-8"))
    return _CACHE[key]


# --------------------------------------------------------------------------- references

_VERSION_TAIL = re.compile(r"\s*\(([^)]*)\)\s*$")
_DASHES = re.compile(r"\s*[‐-―-]\s*")
_REF_RE = re.compile(r"^(?P<book>.+?)\s+(?P<spec>\d{1,3}(?::[\d\s,:a-c‐-―-]+)?)$")


@dataclass(frozen=True)
class ParsedRef:
    book: BibleBook
    verses: Tuple[Tuple[int, int], ...]   # (chapter, verse) in reading order; verse 0 = whole chapter
    spec: str                             # normalised "10:6-12" / "3:8-10, 12"
    version: Optional[str] = None


def _strip_letter(token: str) -> int:
    return int(re.sub(r"[^0-9]", "", token))


def parse_reference(reference: str) -> ParsedRef:
    """Parse ``Romans 10:6–12 (NKJV)``, ``ரோமர் 10:17``, ``Malachi 3:8–3:10``, ``Psalm 23``."""
    ref = (reference or "").strip()
    version = None
    tail = _VERSION_TAIL.search(ref)
    if tail:
        version = tail.group(1).strip() or None
        ref = ref[: tail.start()].strip()
    match = _REF_RE.match(ref)
    if not match:
        raise BibleLookupError(f"cannot read reference {reference!r}")
    try:
        book = lookup_book(match.group("book"))
    except BookNotFound as exc:
        raise BibleLookupError(str(exc)) from exc
    spec = _DASHES.sub("-", match.group("spec").strip())
    verses: List[Tuple[int, int]] = []
    chapter: Optional[int] = None
    for part in [p.strip() for p in spec.split(",") if p.strip()]:
        start, _, end = part.partition("-")
        if ":" in start:
            c, v = start.split(":", 1)
            chapter, first = int(c), _strip_letter(v)
        elif chapter is None:            # "Psalm 23" — whole chapter
            chapter, first = int(start), 0
        else:
            first = _strip_letter(start)
        if not end:
            verses.append((chapter, first))
            continue
        if ":" in end:
            c2, v2 = end.split(":", 1)
            end_ch, last = int(c2), _strip_letter(v2)
        else:
            end_ch, last = chapter, _strip_letter(end)
        if (end_ch, last) < (chapter, first):
            raise BibleLookupError(f"backwards range in {reference!r}")
        verses.append((chapter, first))
        verses.append((end_ch, -last))   # negative verse = "through here"
        chapter = end_ch
    spec = re.sub(r"\s*,\s*", ", ", spec)
    spec = re.sub(r"\b(\d+):(\d+[a-c]?)-\1:(\d+)", r"\1:\2-\3", spec)
    return ParsedRef(book=book, verses=tuple(verses), spec=spec, version=version)


def _expand(parsed: ParsedRef, bible: Dict[str, str]) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    items = list(parsed.verses)
    i = 0
    b = parsed.book.index
    while i < len(items):
        ch, v = items[i]
        nxt = items[i + 1] if i + 1 < len(items) else None
        if nxt is not None and nxt[1] < 0:
            end_ch, last = nxt[0], -nxt[1]
            c, cur = ch, v
            while (c, cur) <= (end_ch, last):
                if f"{b}:{c}:{cur}" in bible:
                    out.append((c, cur))
                    cur += 1
                elif c < end_ch:
                    c, cur = c + 1, 1
                else:
                    raise BibleLookupError(f"no verse {parsed.book.english} {c}:{cur} in the Tamil Bible")
            i += 2
            continue
        if v == 0:
            cur = 1
            while f"{b}:{ch}:{cur}" in bible:
                out.append((ch, cur))
                cur += 1
            if cur == 1:
                raise BibleLookupError(f"no chapter {parsed.book.english} {ch} in the Tamil Bible")
        else:
            out.append((ch, v))
        i += 1
    return out


def tamil_text(reference: str, bible: Dict[str, str]) -> str:
    """The full TAOVBSI text for a reference (verses joined with a space)."""
    parsed = parse_reference(reference)
    texts = []
    for ch, v in _expand(parsed, bible):
        text = bible.get(f"{parsed.book.index}:{ch}:{v}")
        if not text:
            raise BibleLookupError(f"no verse {parsed.book.english} {ch}:{v} in the Tamil Bible")
        texts.append(text.strip())
    return " ".join(texts)


def tamil_reference(reference: str, version: Optional[str] = "TAOVBSI") -> str:
    """``Romans 10:6–12 (NKJV)`` → ``ரோமர் 10:6-12 (TAOVBSI)``."""
    parsed = parse_reference(reference)
    label = f"{parsed.book.tamil} {parsed.spec}"
    return f"{label} ({version})" if version else label


# --------------------------------------------------------------------------- fill


@dataclass
class FillReport:
    from_bible: List[str] = field(default_factory=list)
    from_yaml: List[str] = field(default_factory=list)
    missing: List[Tuple[str, str]] = field(default_factory=list)
    highlight_not_found: List[Tuple[str, str]] = field(default_factory=list)
    highlights_missing: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.highlight_not_found

    def summary(self) -> str:
        total = len(self.from_bible) + len(self.from_yaml) + len(self.missing)
        lines = [
            f"Bilingual: {total} scripture slides — {len(self.from_bible)} from the Tamil Bible, "
            f"{len(self.from_yaml)} from YAML, {len(self.missing)} without Tamil"
        ]
        for ref, why in self.missing:
            lines.append(f"  ✗ {ref}: {why}")
        for ref, phrase in self.highlight_not_found:
            lines.append(f"  ✗ {ref}: highlights_ta {phrase!r} is not in the Tamil text")
        if self.highlights_missing:
            lines.append("  · English highlights but no highlights_ta: " + ", ".join(self.highlights_missing))
        return "\n".join(lines)


def _highlight_texts(items) -> List[str]:
    out = []
    for item in items or []:
        text = item if isinstance(item, str) else (item or {}).get("text")
        if text:
            out.append(str(text))
    return out


def fill_tamil(data: dict, config: Optional[BilingualConfig] = None) -> FillReport:
    """Fill ``text_ta`` / ``reference_ta`` in place and report what happened."""
    config = config or BilingualConfig.from_deck(data)
    report = FillReport()
    if not config.enabled:
        return report
    config.validate()
    bible: Optional[Dict[str, str]] = None
    bible_error: Optional[str] = None
    if config.source == "auto":
        try:
            bible = load_tamil_bible(config.bible_path)
        except BibleLookupError as exc:
            bible_error = str(exc)

    for _, verse in iter_scripture_verses(data):
        ref = str(verse.get("reference") or "").strip()
        label = ref or (verse.get("text") or "")[:30]
        if verse.get("bilingual") is False:
            report.skipped.append(label)
            continue
        if (verse.get("text_ta") or "").strip():
            report.from_yaml.append(label)
            if not (verse.get("reference_ta") or "").strip() and ref:
                try:
                    verse["reference_ta"] = tamil_reference(ref, config.version)
                except BibleLookupError:
                    pass
        elif config.source == "yaml":
            report.missing.append((label, "no text_ta in YAML (bilingual.source: yaml)"))
            continue
        elif bible is None:
            report.missing.append((label, bible_error or "Tamil Bible unavailable"))
            continue
        else:
            lookup = (verse.get("reference_ta") or "").strip() or ref
            try:
                verse["text_ta"] = tamil_text(lookup, bible)
                if not (verse.get("reference_ta") or "").strip():
                    verse["reference_ta"] = tamil_reference(ref, config.version)
                report.from_bible.append(label)
            except BibleLookupError as exc:
                report.missing.append((label, str(exc)))
                continue

        text_ta = verse.get("text_ta") or ""
        for phrase in _highlight_texts(verse.get("highlights_ta")):
            if phrase not in text_ta:
                report.highlight_not_found.append((label, phrase))
        if verse.get("highlights") and not verse.get("highlights_ta"):
            report.highlights_missing.append(label)

    if config.strict and not report.ok:
        raise SchemaError(report.summary())
    return report


def prepare_bilingual_deck(data: dict) -> Tuple[dict, Optional[FillReport]]:
    """Return a copy of ``data`` with Tamil filled in, or ``data`` unchanged when not bilingual."""
    config = BilingualConfig.from_deck(data)
    if not config.enabled:
        return data, None
    out = dict(data)
    out["sections"] = copy.deepcopy(data.get("sections") or [])
    report = fill_tamil(out, config)
    out["_bilingual"] = {"language": config.language, "version": config.version}
    return out, report


def freeze_bilingual(data: dict) -> Tuple[dict, FillReport]:
    """Deck dict with every looked-up Tamil verse written in — for a portable YAML."""
    out, report = prepare_bilingual_deck(data)
    if report is None:
        config = BilingualConfig(enabled=True)
        out = dict(data)
        out["sections"] = copy.deepcopy(data.get("sections") or [])
        report = fill_tamil(out, config)
    out = {k: v for k, v in out.items() if not str(k).startswith("_")}
    if isinstance(out.get("bilingual"), dict):
        out["bilingual"] = {**out["bilingual"], "source": "yaml"}
    else:
        out["bilingual"] = {"language": "ta", "source": "yaml"}
    return out, report


def is_bilingual_deck(data: dict) -> bool:
    return bool(data.get("_bilingual")) or BilingualConfig.from_deck(data).enabled

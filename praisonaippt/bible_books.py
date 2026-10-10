"""The 66-book Protestant canon with Tamil (O.V./BSI) book names.

Order is canonical (Genesis = 0 … Revelation = 65); the Tamil Bible JSON
(``tamil-ov.json``) keys verses as ``"<book index>:<chapter>:<verse>"`` in this
same order. Tamil spellings and abbreviations match praisonai-lyrical-video's
``scripture_books.BOOKS`` so both tools resolve the same names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BibleBook:
    index: int
    english: str
    tamil: str
    abbreviations: tuple = ()


_BOOK_ROWS = (
    ('Genesis', 'ஆதியாகமம்', ('ஆதி', 'ஆகா')),
    ('Exodus', 'யாத்திராகமம்', ('யாத்',)),
    ('Leviticus', 'லேவியராகமம்', ()),
    ('Numbers', 'எண்ணாகமம்', ('எண்',)),
    ('Deuteronomy', 'உபாகமம்', ('உபா',)),
    ('Joshua', 'யோசுவா', ('யோசு',)),
    ('Judges', 'நியாயாதிபதிகள்', ('நியா',)),
    ('Ruth', 'ரூத்', ('ரூத்து',)),
    ('1 Samuel', '1 சாமுவேல்', ('1 சாமு', '1 சாம')),
    ('2 Samuel', '2 சாமுவேல்', ('2 சாமு', '2 சாம')),
    ('1 Kings', '1 இராஜாக்கள்', ('1 இராஜ', '1 இராஜாதிகள்', '1 இரா')),
    ('2 Kings', '2 இராஜாக்கள்', ('2 இராஜ', '2 இராஜாதிகள்', '2 இரா')),
    ('1 Chronicles', '1 நாளாகமம்', ('1 நாளா',)),
    ('2 Chronicles', '2 நாளாகமம்', ('2 நாளா',)),
    ('Ezra', 'எஸ்றா', ()),
    ('Nehemiah', 'நெகேமியா', ('நெகே',)),
    ('Esther', 'எஸ்தேர்', ()),
    ('Job', 'யோபு', ()),
    ('Psalms', 'சங்கீதம்', ('சங்', 'சங்கீத')),
    ('Proverbs', 'நீதிமொழிகள்', ('நீதி',)),
    ('Ecclesiastes', 'பிரசங்கி', ()),
    ('Song of Solomon', 'உன்னதப்பாட்டு', ()),
    ('Isaiah', 'ஏசாயா', ('ஏசா',)),
    ('Jeremiah', 'எரேமியா', ('எரே',)),
    ('Lamentations', 'புலம்பல்', ('புலம்', 'புல')),
    ('Ezekiel', 'எசேக்கியேல்', ('எசேக்', 'எசே', 'ஏசே')),
    ('Daniel', 'தானியேல்', ('தானி',)),
    ('Hosea', 'ஓசியா', ('ஓசி',)),
    ('Joel', 'யோவேல்', ('யோவே',)),
    ('Amos', 'ஆமோஸ்', ()),
    ('Obadiah', 'ஒபதியா', ()),
    ('Jonah', 'யோனா', ()),
    ('Micah', 'மீகா', ()),
    ('Nahum', 'நாகூம்', ('நாகூ',)),
    ('Habakkuk', 'ஆபகூக்', ('ஆப',)),
    ('Zephaniah', 'செப்பனியா', ('செப்',)),
    ('Haggai', 'ஆகாய்', ()),
    ('Zechariah', 'சகரியா', ('சக',)),
    ('Malachi', 'மல்கியா', ('மல்',)),
    ('Matthew', 'மத்தேயு', ('மத்',)),
    ('Mark', 'மாற்கு', ('மாற்',)),
    ('Luke', 'லூக்கா', ('லூக்',)),
    ('John', 'யோவான்', ('யோவா', 'யோ')),
    ('Acts', 'அப்போஸ்தலர்', ('அப்போ', 'அப்', 'அப்போஸ்தலருடைய நடபடிகள்')),
    ('Romans', 'ரோமர்', ('ரோம', 'ரோ')),
    ('1 Corinthians', '1 கொரிந்தியர்', ('1 கொரி',)),
    ('2 Corinthians', '2 கொரிந்தியர்', ('2 கொரி',)),
    ('Galatians', 'கலாத்தியர்', ('கலா',)),
    ('Ephesians', 'எபேசியர்', ('எபே',)),
    ('Philippians', 'பிலிப்பியர்', ('பிலி',)),
    ('Colossians', 'கொலோசெயர்', ('கொலோ',)),
    ('1 Thessalonians', '1 தெசலோனிக்கேயர்', ('1 தெச',)),
    ('2 Thessalonians', '2 தெசலோனிக்கேயர்', ('2 தெச',)),
    ('1 Timothy', '1 தீமோத்தேயு', ('1 தீம', '1 தீமோ', '1 தீ')),
    ('2 Timothy', '2 தீமோத்தேயு', ('2 தீம', '2 தீமோ', '2 தீ')),
    ('Titus', 'தீத்து', ()),
    ('Philemon', 'பிலேமோன்', ()),
    ('Hebrews', 'எபிரெயர்', ('எபி',)),
    ('James', 'யாக்கோபு', ('யாக்',)),
    ('1 Peter', '1 பேதுரு', ('1 பேது', '1 பே')),
    ('2 Peter', '2 பேதுரு', ('2 பேது', '2 பே')),
    ('1 John', '1 யோவான்', ('1 யோ',)),
    ('2 John', '2 யோவான்', ()),
    ('3 John', '3 யோவான்', ()),
    ('Jude', 'யூதா', ()),
    ('Revelation', 'வெளிப்படுத்தின விசேஷம்', ('வெளி', 'வெளிப்படுத்தல்', 'வெளிப்படுத்துதல்')),
)

BOOKS: tuple = tuple(
    BibleBook(i, english, tamil, tuple(abbr)) for i, (english, tamil, abbr) in enumerate(_BOOK_ROWS)
)

# English forms the canonical names and unique-prefix rule do not cover.
_ENGLISH_ALIASES = {
    "psalm": "Psalms", "ps": "Psalms", "pss": "Psalms",
    "song of songs": "Song of Solomon", "canticles": "Song of Solomon", "sos": "Song of Solomon",
    "revelations": "Revelation", "the revelation": "Revelation",
    "mt": "Matthew", "mk": "Mark", "mr": "Mark", "lk": "Luke", "jn": "John", "jhn": "John",
    "phil": "Philippians", "php": "Philippians", "phlm": "Philemon", "philem": "Philemon",
    "jas": "James", "jud": "Jude", "jdg": "Judges", "judg": "Judges",
    "ezk": "Ezekiel", "eze": "Ezekiel", "jer": "Jeremiah", "jl": "Joel",
    "nah": "Nahum", "hab": "Habakkuk", "zeph": "Zephaniah", "zech": "Zechariah",
    "hag": "Haggai", "mal": "Malachi", "dt": "Deuteronomy", "deut": "Deuteronomy",
}


def _key(name: str) -> str:
    return re.sub(r"\s+", " ", name.replace(".", " ")).strip().lower()


def _numbered(name: str) -> str:
    """'I John' / 'First John' / '1John' → '1 john'."""
    k = _key(name)
    k = re.sub(r"^(i{1,3})\s+", lambda m: f"{len(m.group(1))} ", k)
    k = re.sub(r"^(first|second|third)\s+", lambda m: {"first": "1 ", "second": "2 ", "third": "3 "}[m.group(1)], k)
    return re.sub(r"^([123])(?=[^\s\d])", r"\1 ", k)


_EXACT: dict = {}
for _b in BOOKS:
    for _name in (_b.english, _b.tamil, *_b.abbreviations):
        _EXACT[_key(_name)] = _b
for _alias, _english in _ENGLISH_ALIASES.items():
    _EXACT[_alias] = next(b for b in BOOKS if b.english == _english)


class BookNotFound(ValueError):
    """A book token that does not resolve to exactly one book."""


def lookup_book(name: str) -> BibleBook:
    """Resolve an English, Tamil or abbreviated book name (``Rom``, ``1 Cor``, ``ரோமர்``)."""
    key = _numbered(name)
    if key in _EXACT:
        return _EXACT[key]
    if len(key.replace(" ", "")) >= 3:
        hits = [b for b in BOOKS if b.english.lower().startswith(key)]
        if len(hits) == 1:
            return hits[0]
    raise BookNotFound(f"unknown Bible book: {name!r}")


def find_book(name: str) -> Optional[BibleBook]:
    try:
        return lookup_book(name)
    except BookNotFound:
        return None

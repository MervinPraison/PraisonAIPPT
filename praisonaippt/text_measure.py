"""Measure wrapped text so slides can be fitted before PowerPoint ever sees them.

python-pptx cannot ask PowerPoint how tall a text frame will be, so layouts
that must never overflow (bilingual cards) wrap words here. When the font file
is installed it is measured with Pillow; otherwise per-script average widths
calibrated on the Noto faces are used (deliberately on the wide side, so an
estimate errs towards splitting rather than clipping).
"""

from __future__ import annotations

import functools
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")

# Average advance per character, in em, when no font file is available.
# Measured over the he_will_not_put_to_shame verses: Noto Serif 0.47,
# Palatino 0.44, Noto Serif Tamil 0.68, Tamil MN 0.64, Tamil Sangam MN 0.54.
_FALLBACK_EM = {"latin": 0.50, "tamil": 0.70, "space": 0.26}
# Line pitch at 100% spacing, in em (ascent + descent + gap of the face).
_FALLBACK_LINE_EM = {"latin": 1.36, "tamil": 1.56}


def is_tamil(text: str) -> bool:
    return bool(TAMIL_RE.search(text or ""))


def _font_dirs() -> List[Path]:
    home = Path.home()
    dirs = [home / "Library" / "Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"), home / ".fonts", home / ".local/share/fonts",
            Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
    if sys.platform.startswith("win"):
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs += [Path(windir) / "Fonts", home / "AppData/Local/Microsoft/Windows/Fonts"]
    extra = os.environ.get("PRAISONAIPPT_FONT_DIRS")
    if extra:
        dirs = [Path(p).expanduser() for p in extra.split(os.pathsep)] + dirs
    return [d for d in dirs if d.is_dir()]


_STYLE_WORDS = ("regular", "variable", "vf", "book", "roman", "medium", "light", "bold", "italic", "semibold", "thin", "black")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


@functools.lru_cache(maxsize=64)
def find_font_file(family: str) -> Optional[str]:
    """Best regular-weight file for a family name (``Noto Serif Tamil``), or None."""
    if not family:
        return None
    want = _norm(family)
    best: Tuple[int, Optional[str]] = (99, None)
    for directory in _font_dirs():
        for path in directory.rglob("*"):
            if path.suffix.lower() not in (".ttf", ".otf", ".ttc"):
                continue
            stem = _norm(path.stem.split("[")[0])
            if not stem.startswith(want):
                continue
            rest = stem[len(want):]
            if rest and not rest.startswith(_STYLE_WORDS):
                continue          # "Noto Serif" must not match "Noto Serif Tamil"
            rank = 0 if rest in ("", "regular") else 1 if "[" in path.stem or rest == "variable" else 5
            if "bold" in rest or "italic" in rest:
                rank = 50
            if rank < best[0]:
                best = (rank, str(path))
    return best[1]


class TextMeasurer:
    """Width of text at a point size, for one font family."""

    def __init__(self, family: Optional[str], script: str = "latin"):
        self.family = family or ""
        self.script = script
        self._font = None
        self.line_em = _FALLBACK_LINE_EM[script]
        path = find_font_file(self.family)
        if path:
            try:
                from PIL import ImageFont

                self._font = ImageFont.truetype(path, 100)
                self.line_em = max(self.line_em if script == "tamil" else 1.2, self._line_em(path))
            except Exception:
                self._font = None

    @staticmethod
    def _line_em(path: str) -> float:
        try:
            from fontTools.ttLib import TTFont

            font = TTFont(path, fontNumber=0, lazy=True)
            hhea, upm = font["hhea"], font["head"].unitsPerEm
            return (hhea.ascent - hhea.descent + max(hhea.lineGap, 0)) / upm
        except Exception:
            return 1.36

    @property
    def measured(self) -> bool:
        return self._font is not None

    def width_pt(self, text: str, size_pt: float) -> float:
        if self._font is not None:
            return self._font.getlength(text) / 100.0 * size_pt
        em = 0.0
        for ch in text:
            if ch.isspace():
                em += _FALLBACK_EM["space"]
            elif TAMIL_RE.match(ch):
                em += _FALLBACK_EM["tamil"]
            else:
                em += _FALLBACK_EM["latin"]
        return em * size_pt

    def wrap(self, text: str, width_pt: float, size_pt: float) -> List[str]:
        """Greedy word wrap, as PowerPoint does; over-long words break across lines."""
        lines: List[str] = []
        space = self.width_pt(" ", size_pt)
        for para in (text or "").split("\n"):
            current, current_w = "", 0.0
            for word in para.split():
                w = self.width_pt(word, size_pt)
                if not current:
                    current, current_w = word, w
                elif current_w + space + w <= width_pt:
                    current, current_w = f"{current} {word}", current_w + space + w
                else:
                    lines.append(current)
                    current, current_w = word, w
                while current_w > width_pt and len(current) > 1:   # one word wider than the box
                    lines.append(current)
                    current_w -= width_pt
            lines.append(current)
        return lines or [""]

    def line_height_pt(self, size_pt: float, spacing: float = 1.0) -> float:
        return size_pt * self.line_em * spacing

    def height_pt(self, text: str, width_pt: float, size_pt: float, spacing: float = 1.0) -> float:
        return len(self.wrap(text, width_pt, size_pt)) * self.line_height_pt(size_pt, spacing)


# ----------------------------------------------------------------- splitting

_STRONG = re.compile(r"[.!?;:]['\"”’)]*\s+")
_WEAK = re.compile(r",['\"”’)]*\s+")


def _protected(text: str, phrases: Iterable[str]) -> List[Tuple[int, int]]:
    spans = []
    low = text.lower()
    for phrase in phrases:
        p = (phrase or "").lower()
        if not p:
            continue
        start = 0
        while (i := low.find(p, start)) != -1:
            spans.append((i, i + len(p)))
            start = i + len(p)
    return spans


def split_balanced(text: str, parts: int, keep_together: Iterable[str] = ()) -> List[str]:
    """Split ``text`` into ``parts`` pieces of similar length at clause breaks.

    Prefers ``. ! ? ; :`` over ``,`` over a plain space, and never breaks inside
    a highlighted phrase, so a highlight is not cut across two slides.
    """
    text = (text or "").strip()
    if parts <= 1 or not text:
        return [text]
    spans = _protected(text, keep_together)

    def ok(pos: int) -> bool:
        return not any(s < pos < e for s, e in spans)

    candidates = {}
    for m in re.finditer(r"\s+", text):
        if ok(m.start()):
            candidates[m.end()] = 2.0
    for m in _WEAK.finditer(text):
        if ok(m.start()):
            candidates[m.end()] = 1.0
    for m in _STRONG.finditer(text):
        if ok(m.start()):
            candidates[m.end()] = 0.0
    if not candidates:
        return [text]
    n = len(text)
    cuts: List[int] = []
    last = 0
    for k in range(1, parts):
        ideal = n * k / parts
        best = min(
            (pos for pos in candidates if pos > last + 1 and pos < n - 1),
            key=lambda pos: abs(pos - ideal) / n + 0.05 * candidates[pos],
            default=None,
        )
        if best is None:
            break
        cuts.append(best)
        last = best
    pieces, prev = [], 0
    for cut in cuts + [n]:
        piece = text[prev:cut].strip()
        if piece:
            pieces.append(piece)
        prev = cut
    return pieces

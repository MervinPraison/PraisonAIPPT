"""Load PPT YAML decks."""
from __future__ import annotations

from pathlib import Path

import yaml


def load_deck(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def deck_verses(path: Path) -> list[dict]:
    data = load_deck(path)
    out: list[dict] = []
    for sec in data.get("sections", []):
        for v in sec.get("verses", []):
            ref = (v.get("reference") or "").strip()
            text = (v.get("text") or "").strip()
            if text:
                out.append({
                    "section": (sec.get("section") or "").strip(),
                    "ref": ref,
                    "text": text,
                    "highlights": v.get("highlights") or [],
                    "leading_title": (v.get("leading_title") or "").strip(),
                })
    return out


def presentation_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("presentation_title:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return path.stem

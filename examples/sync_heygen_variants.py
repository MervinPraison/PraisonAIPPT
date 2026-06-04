#!/usr/bin/env python3
"""Copy slide content from master YAML to all media variant decks."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

import yaml

from praisonaippt.transcript_loader import MEDIA_VARIANTS, apply_media_variant, write_deck_yaml

MASTER = ROOT / "heygen-50590-content.yaml"


def main() -> None:
    base = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
    for name in MEDIA_VARIANTS:
        deck = apply_media_variant(base, name)
        out = ROOT / f"heygen-50590-{name}.yaml"
        write_deck_yaml(deck, out)
        print(f"✓ {out.name}")


if __name__ == "__main__":
    main()

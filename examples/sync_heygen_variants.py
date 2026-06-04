#!/usr/bin/env python3
"""Copy slide content from master YAML to all media variant decks."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from praisonaippt.variant_sync import sync_variants_from_master

MASTER = ROOT / "heygen-50590-content.yaml"


def main() -> None:
    for path in sync_variants_from_master(MASTER, ROOT, prefix="heygen-50590"):
        print(f"✓ {path.name}")


if __name__ == "__main__":
    main()

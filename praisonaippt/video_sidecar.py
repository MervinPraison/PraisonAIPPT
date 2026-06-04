"""Load deck YAML/JSON sidecar next to a PPTX for standalone video export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .loader import load_deck_mapping
from .schema import validate_verses


def load_deck_sidecar(pptx_path: str) -> Optional[Dict[str, Any]]:
    """Load ``deck.yaml`` / ``deck.json`` with the same stem as the PPTX."""
    stem = Path(pptx_path)
    for ext in (".yaml", ".yml", ".json"):
        sidecar = stem.with_suffix(ext)
        if not sidecar.is_file():
            continue
        try:
            data = load_deck_mapping(sidecar)
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        data = validate_verses(data)
        data["_source_file"] = str(sidecar.resolve())
        return data
    return None

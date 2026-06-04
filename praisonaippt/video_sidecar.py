"""Load deck YAML/JSON sidecar next to a PPTX for standalone video export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import validate_verses


def load_deck_sidecar(pptx_path: str) -> Optional[Dict[str, Any]]:
    """Load ``deck.yaml`` / ``deck.json`` with the same stem as the PPTX."""
    stem = Path(pptx_path)
    for ext in (".yaml", ".yml", ".json"):
        sidecar = stem.with_suffix(ext)
        if not sidecar.is_file():
            continue
        if ext == ".json":
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        else:
            import yaml
            data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
        data = validate_verses(data)
        data["_source_file"] = str(sidecar.resolve())
        return data
    return None

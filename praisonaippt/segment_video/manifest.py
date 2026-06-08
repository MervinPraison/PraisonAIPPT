from __future__ import annotations

import json
from pathlib import Path


def load_manifest(project_root: Path) -> dict:
    return json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))


def save_manifest(project_root: Path, manifest: dict) -> None:
    (project_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

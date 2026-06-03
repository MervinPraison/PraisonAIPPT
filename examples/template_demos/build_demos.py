#!/usr/bin/env python3
"""Build examples/template_demos/{template}.yaml and .pptx for every built-in theme."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DEMO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from praisonaippt.template_resolver import list_templates, resolve_template_style  # noqa: E402

SHOWCASE_IMAGE = DEMO_DIR / "assets" / "showcase-diagram.png"


def _write_showcase_png(path: Path, width: int = 640, height: int = 360) -> None:
    """Checkerboard PNG so contain / cover / fill are visually distinct on dark themes."""
    import struct
    import zlib

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    gold = (255, 215, 0)
    blue = (102, 179, 255)
    cell = 40
    rows = b""
    for y in range(height):
        rows += b"\x00"
        for x in range(width):
            rows += bytes(gold if ((x // cell) + (y // cell)) % 2 else blue)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(rows, 9))
        + _chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def _ensure_showcase_image() -> None:
    # Always refresh so gallery edits to the generator stay in sync.
    _write_showcase_png(SHOWCASE_IMAGE)


def _settings_lines(name: str) -> str:
    resolved = resolve_template_style(name)
    lines: list[str] = []
    if resolved.get("slide_size"):
        lines.append(f"slide_size: {resolved['slide_size']}")
    ss = resolved.get("slide_style") or {}
    for key in sorted(ss):
        if key in ("layouts", "typography", "_source_file"):
            continue
        lines.append(f"{key}: {ss[key]}")
    if not lines:
        lines.append("(inherits parent template only — run praisonaippt template {name})")
    return "\n".join(lines)


def _build_deck(name: str, description: str, showcase: dict) -> dict:
    settings = _settings_lines(name)
    intro = {
        "section": name,
        "section_subtitle": description or "",
        "verses": [
            {
                "reference": f"template: {name}",
                "text": settings,
                "list_type": "bullet",
                "font_size": 18,
                "alignment": "left",
            }
        ],
    }
    return {
        "template": name,
        "presentation_title": name,
        "presentation_subtitle": "Theme gallery demo",
        "sections": [intro] + list(showcase.get("sections") or []),
    }


def main() -> int:
    _ensure_showcase_image()
    showcase = yaml.safe_load((DEMO_DIR / "_showcase.yaml").read_text(encoding="utf-8"))
    meta = {e["name"]: e.get("description", "") for e in list_templates()}

    for name in sorted(meta):
        deck = _build_deck(name, meta[name], showcase)
        yaml_path = DEMO_DIR / f"{name}.yaml"
        yaml_path.write_text(
            yaml.dump(deck, sort_keys=False, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
        pptx_path = DEMO_DIR / f"{name}.pptx"
        from praisonaippt import load_verses_from_file
        from praisonaippt.core import create_presentation

        data = load_verses_from_file(str(yaml_path))
        create_presentation(data, output_file=str(pptx_path))
        print(f"✓ {yaml_path.name} → {pptx_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

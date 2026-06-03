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
        "section": "This template",
        "verses": [
            {
                "reference": f"template: {name}",
                "leading_title": description or name,
                "text": settings,
                "font_size": 20,
                "alignment": "left",
            }
        ],
    }
    return {
        "template": name,
        "presentation_title": f"Template showcase — {name}",
        "presentation_subtitle": description or f"Built-in theme: {name}",
        "sections": [intro] + list(showcase.get("sections") or []),
    }


def main() -> int:
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

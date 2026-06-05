"""Optional vision-LLM anchor suggestion for hero text panels."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .text_panel_anchors import HERO_PANEL_ANCHORS

_VALID_ANCHORS = HERO_PANEL_ANCHORS


def _vision_provider() -> str:
    return (os.environ.get("PRAISONAIPPT_VISION_PROVIDER") or "off").lower().strip()


def _parse_anchor_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    anchor = str(raw.get("anchor", "")).lower().strip()
    if anchor not in _VALID_ANCHORS:
        return None
    alts = [str(a).lower() for a in (raw.get("alternates") or []) if str(a).lower() in _VALID_ANCHORS]
    conf = float(raw.get("confidence") or 0.55)
    return {"anchor": anchor, "confidence": conf, "alternates": alts}


def _openai_suggest(image_path: Path, headline: str, pip_rect: dict) -> Optional[Dict[str, Any]]:
    try:
        import base64
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI()
    b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
    prompt = (
        "You place a headline panel on a product screenshot slide. "
        f"Headline: {headline!r}. PiP avatar occupies bottom-right at normalised rect {pip_rect}. "
        "Return JSON only: {\"anchor\": \"top_left|top_right|bottom_left|bottom_right|top|bottom\", "
        "\"confidence\": 0.0-1.0, \"alternates\": [\"...\"]}. "
        "Pick the anchor where a navy text panel avoids UI text and the PiP."
    )
    resp = client.chat.completions.create(
        model=os.environ.get("PRAISONAIPPT_VISION_MODEL", "gpt-4o-mini"),
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        max_tokens=120,
    )
    text = resp.choices[0].message.content or ""
    return _parse_anchor_json(text)


def _anthropic_suggest(image_path: Path, headline: str, pip_rect: dict) -> Optional[Dict[str, Any]]:
    try:
        import base64
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
    media_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    prompt = (
        "You place a headline panel on a product screenshot slide. "
        f"Headline: {headline!r}. PiP avatar bottom-right rect (normalised): {pip_rect}. "
        "Reply with JSON only: anchor (one of top_left, top_right, bottom_left, bottom_right, top, bottom), "
        "confidence 0-1, alternates array."
    )
    msg = client.messages.create(
        model=os.environ.get("PRAISONAIPPT_VISION_MODEL", "claude-3-5-haiku-latest"),
        max_tokens=120,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    text = msg.content[0].text if msg.content else ""
    return _parse_anchor_json(text)


def suggest_panel_anchor(
    image_path: str | Path,
    headline: str,
    pip_rect_norm: dict,
) -> Optional[Dict[str, Any]]:
    """Suggest panel anchor via vision LLM when env keys are set."""
    provider = _vision_provider()
    if provider in ("", "off", "none", "false"):
        return None

    path = Path(image_path)
    if not path.is_file():
        return None

    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        return _anthropic_suggest(path, headline, pip_rect_norm)

    if provider in ("openai", "auto"):
        if not os.environ.get("OPENAI_API_KEY"):
            if provider == "auto" and os.environ.get("ANTHROPIC_API_KEY"):
                return _anthropic_suggest(path, headline, pip_rect_norm)
            return None
        return _openai_suggest(path, headline, pip_rect_norm)

    return None

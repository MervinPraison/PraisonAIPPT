"""Optional vision-LLM frame description for video visual audit."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_GENERIC_PATTERNS = re.compile(
    r"\b(vintage|antique|old map|historical map|insect|moth|butterfly|"
    r"noah'?s ark|engraving|illustration plate|stock footage|unrelated|"
    r"decorative|generic b-roll|nature documentary)\b",
    re.I,
)


def vision_provider() -> str:
    explicit = (os.environ.get("PRAISONAIPPT_VISION_PROVIDER") or "").lower().strip()
    if explicit and explicit not in ("auto",):
        return explicit
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if explicit == "auto" and os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "off"


def vision_model() -> str:
    return os.environ.get("PRAISONAIPPT_VISION_MODEL") or os.environ.get(
        "PRAISONAIPPT_VISION_DESCRIBE_MODEL", "gpt-4o-mini"
    )


def _parse_describe_json(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    desc = str(raw.get("description") or raw.get("summary") or "").strip()
    if not desc:
        return None
    topics = [str(t).lower() for t in (raw.get("topics") or []) if str(t).strip()]
    generic = bool(raw.get("generic_broll")) or bool(_GENERIC_PATTERNS.search(desc))
    return {
        "description": desc[:500],
        "topics": topics[:12],
        "generic_broll": generic,
        "confidence": float(raw.get("confidence") or 0.7),
    }


def _openai_describe(image_path: Path, spoken: str) -> dict[str, Any] | None:
    try:
        import base64
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI()
    b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
    suffix = image_path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    prompt = (
        "Describe this video frame for a sync audit. Spoken narration at this moment: "
        f"{spoken[:400]!r}. Return JSON only: "
        '{"description": "one sentence", "topics": ["keyword", ...], '
        '"generic_broll": true if vintage/stock/unrelated to AI product news, '
        '"confidence": 0.0-1.0}.'
    )
    resp = client.chat.completions.create(
        model=vision_model(),
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
        max_tokens=200,
    )
    return _parse_describe_json(resp.choices[0].message.content or "")


def _anthropic_describe(image_path: Path, spoken: str) -> dict[str, Any] | None:
    try:
        import base64
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
    suffix = image_path.suffix.lower()
    media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    prompt = (
        "Describe this video frame for sync audit. Spoken: "
        f"{spoken[:400]!r}. JSON only: description, topics array, generic_broll bool, confidence."
    )
    msg = client.messages.create(
        model=vision_model() if "claude" in vision_model() else "claude-3-5-haiku-latest",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    text = msg.content[0].text if msg.content else ""
    return _parse_describe_json(text)


def describe_frame(
    image_path: str | Path,
    spoken: str = "",
    *,
    force: bool = False,
) -> dict[str, Any] | None:
    """Describe a frame via vision LLM when provider and keys are configured."""
    provider = vision_provider()
    if not force and provider in ("", "off", "none", "false"):
        return None
    path = Path(image_path)
    if not path.is_file():
        return None
    if provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic_describe(path, spoken)
    if provider in ("openai", "auto", "anthropic") and os.environ.get("OPENAI_API_KEY"):
        return _openai_describe(path, spoken)
    if provider in ("auto", "anthropic") and os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic_describe(path, spoken)
    return None

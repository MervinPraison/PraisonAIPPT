"""Normalise editor scripts for TTS vs on-screen cues."""
from __future__ import annotations

import re

_HEADER_LINE = re.compile(
    r"^(?:Hook|Outro|Beat\s+\d+(?:\s*[—–-][^\n]*)?)\s*:?\s*(.*)$",
    re.IGNORECASE,
)


def strip_editor_cues(text: str) -> str:
    """Remove [VISUAL:…], (~Xs) timing hints, markdown table rows, and bold markers."""
    text = re.sub(r"\[VISUAL:[^\]]+\]", "", text)
    text = re.sub(r"\([^)]*~[^)]*\)", "", text)
    text = re.sub(r"^\|.+\|$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def narration_text_for_tts(script: str) -> str:
    """Strip stage labels (Hook:, Outro:, Beat N — …) before ElevenLabs."""
    text = script.strip()
    first, _, tail = text.partition("\n")
    m = _HEADER_LINE.match(first)
    if m:
        rest = m.group(1).strip()
        text = f"{rest}\n{tail}".strip() if rest else tail.strip()
    return strip_editor_cues(text)


def extract_beat_section(video_script: str, beat: int) -> str:
    """Pull narration body for beat N from create-news video-script.md."""
    m = re.search(rf"## Beat {beat}[^\n]*\n(.*?)(?=\n## |\Z)", video_script, re.DOTALL)
    if not m:
        return ""
    return strip_editor_cues(m.group(1))

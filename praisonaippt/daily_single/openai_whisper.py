"""OpenAI Whisper API — word-level timestamps for segment narration."""
from __future__ import annotations

import json
import os
from pathlib import Path


def whisper_provider() -> str:
    """openai | local | auto — auto tries OpenAI when OPENAI_API_KEY is set."""
    explicit = (os.environ.get("PRAISONAIPPT_WHISPER_PROVIDER") or "auto").lower().strip()
    if explicit in ("openai", "local"):
        return explicit
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "local"


def transcribe_mp3_openai(mp3: Path, ts: Path, *, model: str | None = None) -> bool:
    """Transcribe mp3 with OpenAI Whisper API; write timestamps.json. Returns True on success."""
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    try:
        from openai import OpenAI
    except ImportError:
        return False

    model = model or os.environ.get("PRAISONAIPPT_WHISPER_MODEL") or "whisper-1"
    client = OpenAI()
    with mp3.open("rb") as audio:
        resp = client.audio.transcriptions.create(
            model=model,
            file=audio,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
        )

    words: list[dict] = []
    segments: list[dict] = []
    top_words = [
        {"word": w.word, "start": float(w.start), "end": float(w.end)}
        for w in (getattr(resp, "words", None) or [])
    ]
    for i, seg in enumerate(getattr(resp, "segments", None) or []):
        seg_words = [
            {"word": w.word, "start": float(w.start), "end": float(w.end)}
            for w in (getattr(seg, "words", None) or [])
        ]
        if not seg_words and top_words:
            seg_start = float(seg.start)
            seg_end = float(seg.end)
            seg_words = [
                w for w in top_words
                if w["start"] >= seg_start - 0.05 and w["end"] <= seg_end + 0.05
            ]
        segments.append({
            "id": i,
            "start": float(seg.start),
            "end": float(seg.end),
            "text": str(getattr(seg, "text", "") or ""),
            "words": seg_words,
        })
    words = top_words or [
        w for seg in segments for w in (seg.get("words") or [])
    ]

    payload = {
        "text": str(getattr(resp, "text", "") or ""),
        "duration": float(segments[-1]["end"]) if segments else 0.0,
        "segments": segments,
        "words": words,
        "source": "openai-whisper",
    }
    ts.parent.mkdir(parents=True, exist_ok=True)
    ts.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True

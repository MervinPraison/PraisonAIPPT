"""Beat-01 views overlay duration from merged SRT or Whisper word timings."""
from __future__ import annotations

import re
from pathlib import Path

from praisonaippt.transcript_loader import load_whisper_json


def _normalise_word(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower())


def beat01_views_duration_sec(
    total: float,
    ts_path: Path | None = None,
    *,
    merged_srt: Path | None = None,
    t0: float = 0.0,
) -> float:
    """Duration of beat-01 views overlay — through first SRT cue or views stat in Whisper."""
    default = min(5.5, max(4.0, total * 0.32))
    if merged_srt and merged_srt.is_file():
        from praisonaippt.daily_single.display_sync import parse_srt

        cues = [
            c for c in parse_srt(merged_srt)
            if t0 <= float(c["start_sec"]) < t0 + total - 0.05
        ]
        if cues:
            first_end = float(cues[0]["end_sec"]) - t0
            return min(max(first_end, default * 0.55), total * 0.55)
    if not ts_path or not ts_path.is_file():
        return default
    data = load_whisper_json(ts_path)
    hit_end = 0.0
    for w in data.words or []:
        tok = _normalise_word(getattr(w, "word", "") or "")
        if tok in ("views", "million", "launch", "clip", "viral", "x"):
            hit_end = max(hit_end, w.end)
    if hit_end > 0:
        return min(max(hit_end + 0.25, default * 0.55), total * 0.55)
    if data.segments:
        return min(max(data.segments[0].end, default), total * 0.55)
    return default

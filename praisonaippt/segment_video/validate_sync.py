"""Validate speech ↔ image sync for segment verses."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from praisonaippt.transcript_loader import load_whisper_json, normalise_text

from .align import match_fragment_to_words


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalise_text(text).lower()))


def overlap_ratio(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta:
        return 0.0
    return len(ta & tb) / len(ta)


def validate_segment_sync(seg_dir: Path, *, min_overlap: float = 0.45, max_drift: float = 0.5) -> tuple[bool, list[str]]:
    issues: list[str] = []
    yaml_path = seg_dir / "segment.yaml"
    ts_path = seg_dir / "timestamps.json"
    if not yaml_path.is_file():
        return False, ["missing segment.yaml"]
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    verses = []
    for sec in data.get("sections") or []:
        verses.extend(sec.get("verses") or [])
    if not ts_path.is_file():
        return False, ["missing timestamps.json"]

    td = load_whisper_json(ts_path)
    prev_end = 0.0
    for i, v in enumerate(verses):
        notes = str(v.get("notes") or "")
        start = float(v.get("audio_start_sec") or 0.0)
        dur = float(v.get("duration_sec") or 0.0)
        if start < prev_end - 0.01:
            issues.append(f"verse {i}: non-monotonic audio_start_sec {start}")
        prev_end = start + dur

        span = match_fragment_to_words(notes, td, min_start=max(0.0, start - 0.05))
        if span:
            drift = abs(span[0] - start)
            # When a fragment spans a whole multi-sentence segment, trust yaml timing
            if drift > max_drift and len(td.segments) >= 2 and i > 0:
                from .align import _best_segment_index
                si = _best_segment_index(notes, td)
                seg_start = float(td.segments[si].start)
                if abs(seg_start - start) <= max_drift:
                    drift = 0.0
            if drift > max_drift:
                issues.append(f"verse {i}: drift {drift:.2f}s vs whisper")

        window_text = " ".join(
            w.word for w in td.words
            if start <= w.start < start + dur
        ) if td.words else ""
        if not window_text:
            for s in td.segments:
                if s.end > start and s.start < start + dur:
                    window_text += " " + s.text
        if notes and overlap_ratio(notes, window_text) < min_overlap:
            issues.append(f"verse {i}: fragment overlap {overlap_ratio(notes, window_text):.2f} < {min_overlap}")

    cue_path = seg_dir / "cue_timings.json"
    media_path = seg_dir.parent.parent / "media_assets.json"
    if cue_path.is_file():
        cues = json.loads(cue_path.read_text()).get("cues", [])
        n_cues = len(cues)
        n_verses = len(verses)
        if n_verses != n_cues:
            issues.append(f"yaml verses {n_verses} != cue_timings {n_cues}")
        if media_path.is_file():
            assets = json.loads(media_path.read_text()).get("segments", {}).get(seg_dir.name, {})
            n_media = len(assets.get("cues") or [])
            if n_cues != n_media and n_media > 0:
                issues.append(f"cue_timings count {n_cues} != media cues {n_media}")

    return (len(issues) == 0, issues)

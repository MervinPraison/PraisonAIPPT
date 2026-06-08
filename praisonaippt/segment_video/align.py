"""Align media cue script fragments to Whisper transcript timings."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.transcript_loader import TranscriptData, load_whisper_json, normalise_text


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalise_text(text).lower())


def _span_score(fragment_tokens: list[str], window_tokens: list[str]) -> float:
    if not fragment_tokens:
        return 0.0
    frag = set(fragment_tokens)
    win = set(window_tokens)
    return len(frag & win) / len(frag)


def match_fragment_to_segments(
    fragment: str,
    data: TranscriptData,
    *,
    min_score: float = 0.45,
    min_start: float = 0.0,
) -> tuple[float, float] | None:
    """Find best consecutive segment span matching fragment text."""
    frag_toks = _tokens(fragment)
    if not data.segments:
        return None
    best: tuple[float, float, float] | None = None
    segs = data.segments
    for i in range(len(segs)):
        if segs[i].start < min_start - 0.3:
            continue
        for j in range(i, min(i + 6, len(segs))):
            window = " ".join(s.text for s in segs[i : j + 1])
            score = _span_score(frag_toks, _tokens(window))
            if score < min_score:
                continue
            start = segs[i].start
            end = segs[j].end
            if start < min_start - 0.3:
                continue
            if best is None or score > best[2]:
                best = (start, end, score)
    if best is None:
        return None
    return (round(best[0], 3), round(best[1], 3))


def match_fragment_to_words(
    fragment: str,
    data: TranscriptData,
    *,
    min_start: float = 0.0,
) -> tuple[float, float] | None:
    if not data.words:
        return match_fragment_to_segments(fragment, data, min_start=min_start)
    frag_toks = _tokens(fragment)
    if not frag_toks:
        return None
    best_i = 0
    best_j = 0
    best_score = 0.0
    for i in range(len(data.words)):
        if data.words[i].start < min_start - 0.3:
            continue
        for j in range(i, min(i + 40, len(data.words))):
            window = " ".join(w.word for w in data.words[i : j + 1])
            score = _span_score(frag_toks, _tokens(window))
            if score > best_score:
                best_score = score
                best_i = i
                best_j = j
    if best_score < 0.35:
        return match_fragment_to_segments(fragment, data, min_start=min_start)
    start = data.words[best_i].start
    end = data.words[best_j].end
    return (round(start, 3), round(end, 3))


def align_cues_to_transcript(
    cues: list[dict],
    transcript_path: Path,
    *,
    total_duration: float | None = None,
    pad_sec: float = 0.15,
) -> list[dict]:
    """Return timing rows: audio_start_sec, duration_sec, script_fragment, cue_index."""
    data = load_whisper_json(transcript_path)
    timings: list[dict] = []
    min_start = 0.0

    # Fast path: one transcript segment per cue (common roundup shape)
    if len(cues) == len(data.segments) and len(cues) >= 2:
        for i, (cue, seg) in enumerate(zip(cues, data.segments)):
            start = max(min_start, float(seg.start))
            end = float(seg.end)
            dur = max(0.5, end - start)
            timings.append({
                "cue_index": i,
                "audio_start_sec": round(start, 2),
                "duration_sec": round(dur, 2),
                "script_fragment": str(cue.get("script_fragment") or seg.text),
                "file": cue.get("file"),
                "match_method": "segment_pair",
            })
            min_start = start + dur
        if total_duration and timings:
            last = timings[-1]
            end = last["audio_start_sec"] + last["duration_sec"]
            if end > total_duration + 0.05:
                scale = total_duration / end
                acc = 0.0
                for t in timings:
                    t["audio_start_sec"] = round(acc, 2)
                    t["duration_sec"] = max(0.35, round(float(t["duration_sec"]) * scale, 2))
                    acc += t["duration_sec"]
                timings[-1]["duration_sec"] = round(
                    max(0.35, total_duration - timings[-1]["audio_start_sec"]), 2
                )
            elif end < total_duration - 0.3:
                last["duration_sec"] = round(total_duration - last["audio_start_sec"], 2)
        return timings

    # Hook montage / roll-call: many cues, one Whisper segment — equal split only without words
    if len(cues) >= 2 and len(data.segments) == 1 and not data.words:
        total = total_duration or float(data.segments[0].end) or data.duration or 10.0
        seg_text = data.segments[0].text or ""
        roll_total = total
        lower = seg_text.lower()
        for marker in ("now we are going", "now we're going", "let's get started"):
            idx = lower.find(marker)
            if idx > 0:
                roll_total = total * (idx / len(seg_text))
                break
        weights = [max(1, len(_tokens(str(cue.get("script_fragment") or "")))) for cue in cues]
        wsum = sum(weights) or len(cues)
        acc = 0.0
        for i, cue in enumerate(cues):
            share = weights[i] / wsum
            dur = max(0.35, roll_total * share)
            if i == len(cues) - 1:
                dur = max(0.35, roll_total - acc)
            timings.append({
                "cue_index": i,
                "audio_start_sec": round(acc, 2),
                "duration_sec": round(dur, 2),
                "script_fragment": str(cue.get("script_fragment") or ""),
                "file": cue.get("file"),
                "match_method": "montage_weighted",
            })
            acc += dur
        if total > acc + 0.05 and timings:
            timings[-1]["duration_sec"] = round(
                timings[-1]["duration_sec"] + (total - acc), 2
            )
        return timings

    for i, cue in enumerate(cues):
        fragment = str(cue.get("script_fragment") or "")
        span = match_fragment_to_words(fragment, data, min_start=min_start)
        if span:
            start, end = span
            start = max(min_start, start - pad_sec * 0.5)
            end = min(data.duration or end, end + pad_sec)
            dur = max(0.5, end - start)
            method = "whisper"
        else:
            if timings:
                start = min_start
            else:
                start = 0.0
            dur = max(0.5, (data.duration or 10.0) / max(len(cues), 1))
            method = "fallback"
        timings.append({
            "cue_index": i,
            "audio_start_sec": round(start, 2),
            "duration_sec": round(dur, 2),
            "script_fragment": fragment,
            "file": cue.get("file"),
            "match_method": method,
        })
        min_start = start + dur

    # Hook montage: word-aligned starts, duration until next cue
    if len(cues) >= 2 and data.words and len(timings) == len(cues):
        total = total_duration or data.duration or timings[-1]["audio_start_sec"] + timings[-1]["duration_sec"]
        for i in range(len(timings)):
            start = timings[i]["audio_start_sec"]
            if i + 1 < len(timings):
                end = timings[i + 1]["audio_start_sec"]
            else:
                end = total
            timings[i]["duration_sec"] = round(max(0.35, end - start), 2)
            timings[i]["match_method"] = "whisper" if timings[i].get("match_method") == "whisper" else "hook_chain"

    if total_duration and timings:
        last = timings[-1]
        end = last["audio_start_sec"] + last["duration_sec"]
        if end > total_duration + 0.05:
            scale = total_duration / end
            acc = 0.0
            for t in timings:
                t["audio_start_sec"] = round(acc, 2)
                t["duration_sec"] = max(0.35, round(float(t["duration_sec"]) * scale, 2))
                acc += t["duration_sec"]
            timings[-1]["duration_sec"] = round(
                max(0.35, total_duration - timings[-1]["audio_start_sec"]), 2
            )
        elif end < total_duration - 0.3:
            last["duration_sec"] = round(total_duration - last["audio_start_sec"], 2)
    return timings


def load_cue_timings(seg_dir: Path) -> list[dict] | None:
    path = seg_dir / "cue_timings.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("cues", [])


def save_cue_timings(seg_dir: Path, cues: list[dict], *, transcript_path: str = "timestamps.json") -> Path:
    payload = {"schema_version": 1, "transcript_path": transcript_path, "cues": cues}
    path = seg_dir / "cue_timings.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

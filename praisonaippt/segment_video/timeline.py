"""Timeline model — build and resolve image/caption at time T."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.video_protocol import ResolvedEdgeTransition, effective_timeline_sec

from .align import load_cue_timings
from .media import ffprobe_duration


def parse_srt(text: str) -> list[dict]:
    blocks = re.split(r"\n\n+", text.strip())
    cues = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start_s, end_s = [x.strip() for x in lines[1].split("-->")]
        body = " ".join(lines[2:]).strip()
        cues.append({
            "start_sec": _srt_ts(start_s),
            "end_sec": _srt_ts(end_s),
            "text": body,
        })
    return cues


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def load_segment_yaml(seg_dir: Path) -> dict:
    path = seg_dir / "segment.yaml"
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def verses_from_yaml(data: dict) -> list[dict]:
    verses: list[dict] = []
    for sec in data.get("sections") or []:
        verses.extend(sec.get("verses") or [])
    return verses


def build_segment_timeline(seg_dir: Path, project_root: Path) -> dict:
    data = load_segment_yaml(seg_dir)
    verses = verses_from_yaml(data)
    cue_rows = load_cue_timings(seg_dir)
    if cue_rows and len(cue_rows) == len(verses):
        for i, row in enumerate(cue_rows):
            verses[i]["audio_start_sec"] = row.get("audio_start_sec", verses[i].get("audio_start_sec"))
            verses[i]["duration_sec"] = row.get("duration_sec", verses[i].get("duration_sec"))

    duration = 0.0
    mp4 = seg_dir / "segment.mp4"
    heygen = seg_dir / "heygen.mp4"
    if mp4.is_file():
        duration = ffprobe_duration(mp4)
    elif heygen.is_file():
        duration = ffprobe_duration(heygen)

    cues_out: list[dict] = []
    for i, v in enumerate(verses):
        start = float(v.get("audio_start_sec") or 0.0)
        dur = float(v.get("duration_sec") or 0.0)
        media = v.get("media_path") or ""
        jpeg = seg_dir / "slide_jpegs" / f"slide-{i + 1:03d}.jpg"
        frame_base = seg_dir / "slide_jpegs" / "mp4-frames" / f"mp4-slide-{i + 1:03d}"
        frames = {}
        for tag in ("start", "mid", "end"):
            p = Path(f"{frame_base}-{tag}.jpg")
            if p.is_file():
                frames[tag] = str(p.relative_to(project_root))
            elif tag == "start" and Path(f"{frame_base}.jpg").is_file():
                frames["start"] = str(Path(f"{frame_base}.jpg").relative_to(project_root))

        words: list[dict] = []
        ts_path = seg_dir / "timestamps.json"
        if ts_path.is_file():
            try:
                td = load_whisper_json(ts_path)
                words = [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in td.words
                    if start <= w.start < start + dur
                ]
            except Exception:
                pass

        cues_out.append({
            "cue_id": f"{seg_dir.name}-{i}",
            "verse_index": i,
            "start_sec": start,
            "end_sec": round(start + dur, 3),
            "audio_start_sec": start,
            "duration_sec": dur,
            "headline": v.get("headline"),
            "notes": v.get("notes"),
            "media_path": media,
            "jpeg_rel": str(jpeg.relative_to(project_root)) if jpeg.is_file() else None,
            "frames": frames,
            "words": words,
        })

    srt_cues = []
    srt = seg_dir / "segment.srt"
    if srt.is_file():
        srt_cues = parse_srt(srt.read_text(encoding="utf-8"))

    timeline = {
        "schema_version": 1,
        "dir": seg_dir.name,
        "duration_sec": round(duration, 3),
        "avatar_timeline": (data.get("video_export") or {}).get("avatar_timeline"),
        "slide_timestamps": data.get("slide_timestamps") or [],
        "cues": cues_out,
        "srt_cues": srt_cues,
    }
    out = seg_dir / "timeline.json"
    out.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    return timeline


def resolve_at_time(timeline: dict, t: float) -> dict:
    cues = timeline.get("cues") or []
    slide = None
    slide_index = 0
    for i, c in enumerate(cues):
        if c["start_sec"] <= t < c["end_sec"]:
            slide = c
            slide_index = i
            break
    if slide is None and cues:
        slide = cues[-1]
        slide_index = len(cues) - 1

    caption = None
    for j, c in enumerate(timeline.get("srt_cues") or []):
        if c["start_sec"] <= t < c["end_sec"]:
            caption = {**c, "cue_index": j}
            break

    word = None
    if slide:
        for k, w in enumerate(slide.get("words") or []):
            if w["start"] <= t < w["end"]:
                window = [x["word"] for x in (slide.get("words") or [])[max(0, k - 2) : k + 3]]
                word = {"active": w["word"], "index": k, "window": window}
                break

    return {
        "t": t,
        "slide_index": slide_index,
        "slide": slide,
        "caption": caption,
        "word": word,
    }


def build_project_timeline(project_root: Path, manifest: dict, protocol: dict) -> dict:
    segments_out = []
    durations = []
    for seg in manifest.get("segments", []):
        d = seg["dir"]
        seg_dir = project_root / "segments" / d
        tl_path = seg_dir / "timeline.json"
        if tl_path.is_file():
            tl = json.loads(tl_path.read_text(encoding="utf-8"))
            dur = float(tl.get("duration_sec") or 0)
        elif (seg_dir / "segment.mp4").is_file():
            dur = ffprobe_duration(seg_dir / "segment.mp4")
        else:
            dur = 0.0
        durations.append(dur)
        segments_out.append({"dir": d, "duration_sec": round(dur, 3)})

    mt = protocol.get("merge_transitions") or {}
    edges = []
    if mt.get("default") == "crossfade" and len(durations) > 1:
        edges = [
            ResolvedEdgeTransition(i + 1, "crossfade", float(mt.get("duration_sec", 0.3)), "merge")
            for i in range(len(durations) - 1)
        ]
    entries = [{"duration_sec": d} for d in durations]
    if edges:
        starts = effective_timeline_sec(entries, edges)
    else:
        starts = []
        acc = 0.0
        for d in durations:
            starts.append(round(acc, 3))
            acc += d

    for i, item in enumerate(segments_out):
        item["global_start_sec"] = round(starts[i] if i < len(starts) else 0.0, 3)

    total = sum(durations)
    if edges:
        total -= float(mt.get("duration_sec", 0.3)) * (len(durations) - 1)

    out = {
        "schema_version": 1,
        "segments": segments_out,
        "merge_edges": [{"after_index": e.after_slide, "type": e.type, "duration_sec": e.duration_sec} for e in edges],
        "total_duration_sec": round(total, 3),
    }
    (project_root / "merge" / "timeline.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out

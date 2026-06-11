"""Map Whisper word timings to on-screen slides (word-level sync gate)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.display_sync import _meta_for
from praisonaippt.daily_single.text_slide import slide_specs
from praisonaippt.transcript_loader import load_whisper_json


def _normalise_word(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower())


def words_in_range(data: Any, start: float, end: float) -> list[str]:
    out: list[str] = []
    for w in data.words or []:
        if w.end <= start or w.start >= end:
            continue
        token = _normalise_word(getattr(w, "word", "") or getattr(w, "text", ""))
        if token:
            out.append(token)
    if out:
        return out
    for seg in data.segments or []:
        if seg.end <= start or seg.start >= end:
            continue
        for token in _normalise_word(seg.text).split():
            if token:
                out.append(token)
    return out


def slide_topics_for_file(filename: str) -> set[str]:
    meta = _meta_for(filename)
    topics = set(meta.get("topics") or ())
    for group in slide_specs().values():
        for spec in group:
            if spec["file"] == filename:
                topics |= set(spec.get("topics") or ())
    return topics


def validate_segment_slide_words(
    project: DailySingleProject,
    seg_dir: str,
    *,
    slide_files: list[str],
    local_start: float,
    local_end: float,
    min_hits: int = 2,
) -> tuple[bool, dict[str, Any]]:
    """Whisper words spoken while slide is visible must hit slide topic tokens."""
    ts = project.segments_dir / seg_dir / "timestamps.json"
    if not ts.is_file():
        return False, {"error": f"missing {ts} — run build-captions with Whisper"}

    data = load_whisper_json(ts)
    spoken = words_in_range(data, local_start, local_end)
    spoken_set = set(spoken)
    rows: list[dict[str, Any]] = []
    ok = True

    for fn in slide_files:
        topics = slide_topics_for_file(fn)
        hits = sorted(spoken_set & topics)
        row_ok = len(hits) >= min_hits
        if not row_ok:
            ok = False
        rows.append({
            "file": fn,
            "word_hits": hits,
            "hit_count": len(hits),
            "min_hits": min_hits,
            "ok": row_ok,
            "spoken_sample": " ".join(spoken[:24]),
        })

    return ok, {"segment": seg_dir, "local_start": local_start, "local_end": local_end, "slides": rows}


from praisonaippt.daily_single.beat01_timing import beat01_views_duration_sec


def validate_beat01_slide_word_map(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Beat-01: views window + summary slide, or trust-audit v2 slideshow."""
    mp3 = project.segment_narration("01-cold-open")
    if not mp3.is_file():
        return False, {"error": "missing 01-cold-open narration"}

    from praisonaippt.segment_video.media import ffprobe_duration

    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    beat1 = (beat_map.get("beats") or {}).get("1") or {}
    images = beat1.get("images") or []
    if images and not beat1.get("generated"):
        total = ffprobe_duration(mp3)
        headline_d = total * 0.20
        first_ok, first_report = validate_segment_slide_words(
            project,
            "01-cold-open",
            slide_files=[Path(images[0]["path"]).name],
            local_start=0.0,
            local_end=headline_d,
            min_hits=2,
        )
        second_ok, second_report = validate_segment_slide_words(
            project,
            "01-cold-open",
            slide_files=[Path(images[1]["path"]).name if len(images) > 1 else Path(images[0]["path"]).name],
            local_start=headline_d,
            local_end=total,
            min_hits=2,
        )
        return first_ok and second_ok, {
            "views_window": first_report,
            "summary_window": second_report,
        }

    total = ffprobe_duration(mp3)
    ts = project.segments_dir / "01-cold-open" / "timestamps.json"
    merged = project.merge_dir / "final.srt"
    t0 = 0.0
    tl_path = project.merge_dir / "timeline.json"
    if tl_path.is_file():
        for row in json.loads(tl_path.read_text(encoding="utf-8")).get("segments") or []:
            if row.get("id") == "beat-01":
                t0 = float(row["start_sec"])
                break
    views_d = beat01_views_duration_sec(
        total, ts,
        merged_srt=merged if merged.is_file() else None,
        t0=t0,
    )
    views_ok, views_report = validate_segment_slide_words(
        project,
        "01-cold-open",
        slide_files=["beat1-views-overlay.png"],
        local_start=0.0,
        local_end=views_d,
        min_hits=1,
    )
    summary_ok, summary_report = validate_segment_slide_words(
        project,
        "01-cold-open",
        slide_files=["beat1-launch-summary.png"],
        local_start=views_d,
        local_end=total,
        min_hits=3,
    )
    return views_ok and summary_ok, {
        "views_window": views_report,
        "summary_window": summary_report,
    }

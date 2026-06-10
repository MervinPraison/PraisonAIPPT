"""Validate spoken narration matches slides/images on screen (talk-through check)."""
from __future__ import annotations

import json
from typing import Any

from praisonaippt.daily_single.display_sync import (
    HOOK_MONTAGE_MIN_ALIGNMENT,
    MIN_ALIGNMENT,
    VisualWindow,
    _meta_for,
    build_visual_timeline,
    parse_srt,
    score_cue_visual,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.image_selection import tokenise

MIN_WINDOW_ALIGNMENT = MIN_ALIGNMENT
FRAGMENT_MIN_HIT = 0.28
MIN_WINDOW_SEC = 0.75
SKIP_FILES = frozenset({"heygen.mp4", "none"})
FRAG_STOP = frozenset({"the", "a", "an", "and", "or", "that", "this", "in", "to", "of", "for"})


def _content_tokens(text: str) -> set[str]:
    return tokenise(text) - FRAG_STOP


def fragment_token_hit(fragment: str, spoken: str) -> float:
    frag = _content_tokens(fragment)
    if not frag:
        return 1.0
    spoken_tokens = _content_tokens(spoken)
    return len(frag & spoken_tokens) / len(frag)


def _overlaps(w: VisualWindow, cue: dict[str, Any]) -> bool:
    return w.start_sec < cue["end_sec"] and w.end_sec > cue["start_sec"]


def _cue_at_mid(cues: list[dict[str, Any]], t: float) -> dict[str, Any] | None:
    for cue in cues:
        if cue["start_sec"] <= t < cue["end_sec"]:
            return cue
    return None


def spoken_topic_overlap(spoken: str, visual_file: str) -> bool:
    meta = _meta_for(visual_file)
    topics = set(meta.get("topics") or ())
    blob = tokenise(str(meta.get("vision_description") or ""))
    spoken_tokens = tokenise(spoken)
    return bool(spoken_tokens & (topics | blob))


def validate_montage_fragments(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """Each hook overview flash must map a script fragment → spoken overview cue → slide."""
    overview_spoken = cues[1]["text"] if len(cues) >= 2 else ""
    rows: list[dict[str, Any]] = []
    fails = 0

    for w in [x for x in windows if x.beat == "00-hook" and x.section == "overview"]:
        frag = (w.script_fragment or "").strip()
        hit = fragment_token_hit(frag, overview_spoken)
        topic = score_cue_visual(frag or overview_spoken, w.file)
        frag_ok = hit >= FRAGMENT_MIN_HIT
        topic_ok = topic >= HOOK_MONTAGE_MIN_ALIGNMENT and spoken_topic_overlap(frag or overview_spoken, w.file)
        ok = frag_ok and topic_ok
        if not ok:
            fails += 1
        rows.append({
            "start_sec": round(w.start_sec, 2),
            "end_sec": round(w.end_sec, 2),
            "file": w.file,
            "script_fragment": frag,
            "fragment_in_overview": round(hit, 3),
            "topic_alignment": topic,
            "ok": ok,
        })

    return fails == 0, rows


def validate_visual_windows(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """While each slide/image is on screen, overlapping speech must describe it."""
    rows: list[dict[str, Any]] = []
    fails = 0

    for w in windows:
        if w.file in SKIP_FILES:
            continue
        if w.section == "bridge":
            continue
        dur = w.end_sec - w.start_sec
        if dur < MIN_WINDOW_SEC:
            continue

        mid = (w.start_sec + w.end_sec) / 2
        overlapping = [c for c in cues if _overlaps(w, c)]

        if w.section == "overview" and w.script_fragment:
            spoken = w.script_fragment
            threshold = HOOK_MONTAGE_MIN_ALIGNMENT
        else:
            overlapping = [c for c in cues if _overlaps(w, c)]
            primary = _cue_at_mid(cues, mid)
            if not primary and not overlapping:
                fails += 1
                rows.append({
                    "start_sec": round(w.start_sec, 2),
                    "end_sec": round(w.end_sec, 2),
                    "beat": w.beat,
                    "file": w.file,
                    "spoken": "",
                    "alignment": 0.0,
                    "ok": False,
                    "issue": "no spoken cue while slide visible",
                })
                continue
            if primary:
                spoken = primary["text"]
            else:
                spoken = max(
                    overlapping,
                    key=lambda c: score_cue_visual(c["text"], w.file),
                )["text"]
            threshold = MIN_WINDOW_ALIGNMENT

        score = score_cue_visual(spoken, w.file)
        ok = score >= threshold and spoken_topic_overlap(spoken, w.file)
        if not ok:
            fails += 1
        rows.append({
            "start_sec": round(w.start_sec, 2),
            "end_sec": round(w.end_sec, 2),
            "beat": w.beat,
            "section": w.section,
            "file": w.file,
            "spoken": spoken[:120],
            "alignment": score,
            "threshold": threshold,
            "ok": ok,
        })

    return fails == 0, rows


def validate_spoken_visual_sync(project: DailySingleProject) -> dict[str, Any]:
    srt_path = project.merge_dir / "final.srt"
    if not srt_path.is_file():
        raise FileNotFoundError(f"Missing {srt_path} — run build-captions first")

    cues = parse_srt(srt_path)
    windows = build_visual_timeline(project)
    montage_ok, montage_rows = validate_montage_fragments(windows, cues)
    windows_ok, window_rows = validate_visual_windows(windows, cues)
    montage_fails = sum(1 for r in montage_rows if not r["ok"])
    window_fails = sum(1 for r in window_rows if not r["ok"])

    issues: list[str] = []
    for row in montage_rows:
        if not row["ok"]:
            issues.append(
                f"hook montage {row['file']}: fragment not inline "
                f"(hit={row['fragment_in_overview']}, topic={row['topic_alignment']})"
            )
    for row in window_rows:
        if not row["ok"]:
            msg = row.get("issue") or (
                f"alignment {row['alignment']} < {row.get('threshold', MIN_WINDOW_ALIGNMENT)}"
            )
            issues.append(
                f"{row['beat']} {row['file']} @{row['start_sec']:.1f}s: {msg} — "
                f"\"{row.get('spoken', '')[:50]}\""
            )

    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": montage_ok and windows_ok,
        "montage_fragments_total": len(montage_rows),
        "montage_fragments_pass": len(montage_rows) - montage_fails,
        "montage_fragments_fail": montage_fails,
        "windows_total": len(window_rows),
        "windows_pass": len(window_rows) - window_fails,
        "windows_fail": window_fails,
        "min_window_alignment": MIN_WINDOW_ALIGNMENT,
        "hook_montage_min_alignment": HOOK_MONTAGE_MIN_ALIGNMENT,
        "montage": montage_rows,
        "windows": window_rows,
        "issues": issues[:20],
    }
    out = project.merge_dir / "spoken_visual_sync_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

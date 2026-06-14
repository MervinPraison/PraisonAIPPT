"""Clip trim-range QA — validate beat-map windows and suggest source in/out cuts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.hook_montage import build_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.media import ffprobe_duration

MIN_CLIP_SEC = 2.0
DEFAULT_SUGGEST_DUR = 14.0
TIME_HINT = re.compile(r"(?:~|at\s+)?(\d{1,2}):(\d{2})")
SEC_HINT = re.compile(r"(\d{1,3})\s*(?:–|-)\s*(\d{1,3})\s*s(?:ec)?", re.I)

# Mirrors scripts/download_comparison_clips.sh — source file → pre-bake trim on social master.
COMPARISON_SOURCE_TRIMS: dict[str, tuple[float, float]] = {
    "youtube-jono-flight-sim.mp4": (45.0, 14.0),
    "youtube-romanlogic-dayone.mp4": (25.0, 14.0),
    "youtube-bridgemind-one-shot.mp4": (90.0, 14.0),
    "youtube-mattvidpro-gpt55.mp4": (120.0, 14.0),
    "youtube-asapguide-opus-test.mp4": (30.0, 14.0),
    "youtube-ryan-doser-multi-demo.mp4": (120.0, 14.0),
    "youtube-coderabbit-review.mp4": (240.0, 14.0),
}


def _social_sources_path(project: DailySingleProject) -> Path:
    return project.root / "research" / "social-sources.json"


def _duration(path: Path) -> float | None:
    if not path.is_file():
        return None
    try:
        return float(ffprobe_duration(path))
    except (OSError, ValueError, TypeError):
        return None


def _parse_time_hint(notes: str) -> float | None:
    m = TIME_HINT.search(notes or "")
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m2 = SEC_HINT.search(notes or "")
    if m2:
        return float(m2.group(1))
    return None


def suggested_trim_for_source(
    *,
    local_file: str,
    notes: str = "",
    duration: float | None = None,
    window_sec: float = DEFAULT_SUGGEST_DUR,
) -> dict[str, float]:
    """Recommend in/out on the source master for editors collecting clips."""
    name = Path(local_file).name
    if name in COMPARISON_SOURCE_TRIMS:
        start, dur = COMPARISON_SOURCE_TRIMS[name]
        end = start + dur
        if duration and end > duration:
            end = duration
            start = max(0.0, end - dur)
        return {"in_sec": round(start, 2), "out_sec": round(end, 2), "duration_sec": round(end - start, 2)}

    hint = _parse_time_hint(notes)
    start = hint if hint is not None else 0.0
    if duration:
        start = min(start, max(0.0, duration - window_sec))
        end = min(start + window_sec, duration)
    else:
        end = start + window_sec
    return {"in_sec": round(start, 2), "out_sec": round(end, 2), "duration_sec": round(end - start, 2)}


def _beat_map_clips(project: DailySingleProject) -> list[dict[str, Any]]:
    if not project.beat_map_path.is_file():
        return []
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for beat_n, spec in (beat_map.get("beats") or {}).items():
        for clip in spec.get("clips") or []:
            if not str(clip.get("filename") or "").lower().endswith(".mp4"):
                continue
            row = dict(clip)
            row["beat"] = beat_n
            out.append(row)
    return out


def validate_clip_trims(project: DailySingleProject) -> dict[str, Any]:
    """Fail when beat-map or hook montage trims exceed file duration."""
    issues: list[str] = []
    rows: list[dict[str, Any]] = []
    fails = 0

    for clip in _beat_map_clips(project):
        path = Path(str(clip.get("path") or ""))
        fname = path.name or str(clip.get("filename") or "")
        in_s = float(clip.get("in_sec") or 0)
        out_s = float(clip.get("out_sec") or 0)
        dur = _duration(path)
        row_issues: list[str] = []

        if out_s <= in_s:
            row_issues.append(f"out_sec {out_s} must be > in_sec {in_s}")
        if (out_s - in_s) < MIN_CLIP_SEC:
            row_issues.append(f"window {(out_s - in_s):.1f}s shorter than {MIN_CLIP_SEC}s minimum")
        if dur is not None and out_s > dur + 0.05:
            row_issues.append(f"out_sec {out_s} exceeds file duration {dur:.1f}s")
        if dur is not None and in_s >= dur:
            row_issues.append(f"in_sec {in_s} starts past file end {dur:.1f}s")

        ok = not row_issues
        if not ok:
            fails += 1
            issues.extend(f"beat {clip.get('beat')} {fname}: {m}" for m in row_issues)

        rows.append({
            "kind": "beat_map",
            "beat": clip.get("beat"),
            "file": fname,
            "path": str(path),
            "in_sec": in_s,
            "out_sec": out_s,
            "file_duration_sec": dur,
            "ok": ok,
            "issues": row_issues,
        })

    plan = build_hook_montage_plan(project)
    for cue in plan.get("cues") or []:
        if not cue.get("ok"):
            continue
        path = Path(str(cue.get("path") or ""))
        if not path.name.lower().endswith(".mp4"):
            continue
        in_s = float(cue.get("in_sec") or 0)
        dur = _duration(path)
        min_window = 3.0
        row_issues: list[str] = []
        if dur is not None and in_s + min_window > dur:
            row_issues.append(f"hook in_sec {in_s} + {min_window}s exceeds duration {dur:.1f}s")
        ok = not row_issues
        if not ok:
            fails += 1
            issues.append(f"hook {path.name}: {row_issues[0]}")
        rows.append({
            "kind": "hook_montage",
            "file": path.name,
            "in_sec": in_s,
            "file_duration_sec": dur,
            "ok": ok,
            "issues": row_issues,
        })

    suggestions: list[dict[str, Any]] = []
    src_path = _social_sources_path(project)
    if src_path.is_file():
        catalog = json.loads(src_path.read_text(encoding="utf-8"))
        for entry in catalog.get("clips") or []:
            local = str(entry.get("local_file") or "")
            if not local:
                continue
            full = project.root / local
            dur = _duration(full)
            trim = suggested_trim_for_source(
                local_file=local,
                notes=str(entry.get("notes") or ""),
                duration=dur,
            )
            suggestions.append({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "local_file": local,
                "file_duration_sec": dur,
                "suggested_trim": trim,
                "notes": entry.get("notes"),
            })

    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": fails == 0,
        "clips_checked": len(rows),
        "clips_fail": fails,
        "issues": issues[:30],
        "rows": rows,
        "source_trim_suggestions": suggestions,
    }
    out = project.merge_dir / "clip_trim_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

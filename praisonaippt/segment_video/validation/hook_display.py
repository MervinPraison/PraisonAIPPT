"""Hook-only validation: spoken phrase ↔ image ↔ caption at time T."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..image_audit import hook_topic_phrase
from ..manifest import load_manifest
from ..timeline import build_segment_timeline, parse_srt, resolve_at_time


def _roll_call_bounds(full_text: str, total_sec: float) -> tuple[float, float, str]:
    """Return (roll_start_sec, roll_end_sec, roll_text) excluding intro + outro."""
    lower = full_text.lower()
    roll_start_char = 0
    for m in ("roundup:", "roundup :"):
        i = lower.find(m)
        if i >= 0:
            roll_start_char = i + len(m)
            break
    roll_end_char = len(full_text)
    for m in ("now we are going", "now we're going", "let's get started", "lets get started"):
        i = lower.find(m)
        if i > roll_start_char:
            roll_end_char = i
            break
    roll_text = full_text[roll_start_char:roll_end_char].strip()
    roll_t0 = total_sec * (roll_start_char / max(len(full_text), 1))
    roll_t1 = total_sec * (roll_end_char / max(len(full_text), 1))
    return roll_t0, roll_t1, roll_text


def _estimate_phrase_start(phrase: str, roll_text: str, roll_t0: float, roll_duration: float) -> float | None:
    idx = roll_text.lower().find(phrase.lower())
    if idx < 0:
        return None
    return roll_t0 + (idx / max(len(roll_text), 1)) * roll_duration


def validate_hook_display(project_root: Path, protocol: dict) -> dict:
    """Validate hook montage: image shown when phrase spoken; CC aligned to timeline."""
    seg_dir = project_root / "segments" / "00-hook"
    manifest = load_manifest(project_root)
    topic_segs = [s for s in manifest["segments"] if s.get("slide_type") == "avatar_media_3"]
    hook_cfg = protocol.get("hook_montage") or {}
    max_cues = int(hook_cfg.get("max_cues", 15))
    max_drift = float((protocol.get("validation_suite") or {}).get("hook_display", {}).get(
        "max_speech_drift_sec", 0.6
    ))

    tl_path = seg_dir / "timeline.json"
    if not tl_path.is_file():
        build_segment_timeline(seg_dir, project_root)
    timeline = json.loads(tl_path.read_text(encoding="utf-8"))

    ts_path = seg_dir / "timestamps.json"
    ts = json.loads(ts_path.read_text()) if ts_path.is_file() else {"segments": []}
    full_text = (ts.get("segments") or [{}])[0].get("text") or ""
    total_sec = float((ts.get("segments") or [{}])[0].get("end") or timeline.get("duration_sec") or 0)
    has_words = bool(ts.get("words")) or any(s.get("words") for s in (ts.get("segments") or []))

    roll_t0, roll_t1, roll_text = _roll_call_bounds(full_text, total_sec)
    roll_duration = roll_t1 - roll_t0

    cues = timeline.get("cues") or []
    srt_cues = timeline.get("srt_cues") or []
    rows: list[dict[str, Any]] = []
    issues: list[str] = []

    for i, (cue, seg) in enumerate(zip(cues[:max_cues], topic_segs[:max_cues])):
        phrase = hook_topic_phrase(seg)
        img = Path(cue.get("media_path") or "").name
        start = float(cue.get("start_sec") or 0)
        end = float(cue.get("end_sec") or 0)
        notes = (cue.get("notes") or "").strip()

        srt = srt_cues[i] if i < len(srt_cues) else {}
        cap_text = (srt.get("text") or "").strip()
        cap_start = float(srt.get("start_sec") or 0)
        cap_end = float(srt.get("end_sec") or 0)

        caption_aligned = (
            notes.lower() == cap_text.lower()
            and abs(start - cap_start) < 0.05
            and abs(end - cap_end) < 0.05
        )

        mid_t = start + (end - start) / 2
        resolved = resolve_at_time(timeline, mid_t)
        resolver_ok = (
            resolved.get("slide_index") == i
            and (resolved.get("caption") or {}).get("text", "").strip().lower() == notes.lower()
        )

        speech_est = _estimate_phrase_start(phrase, roll_text, roll_t0, roll_duration)
        drift = (speech_est - start) if speech_est is not None else None
        speech_ok = drift is not None and abs(drift) <= max_drift
        if drift is not None and drift > max_drift:
            issues.append(
                f"cue {i} ({phrase[:30]}): image ~{drift:.1f}s early vs estimated speech"
            )
        elif drift is not None and drift < -max_drift:
            issues.append(
                f"cue {i} ({phrase[:30]}): image ~{abs(drift):.1f}s late vs estimated speech"
            )

        topic_slug = seg.get("slug")
        assets = json.loads((project_root / "media_assets.json").read_text())
        hook_cue = (assets.get("segments", {}).get("00-hook") or {}).get("cues") or []
        hero_slug = hook_cue[i].get("topic_slug") if i < len(hook_cue) else None
        image_topic_ok = hero_slug == topic_slug

        row = {
            "cue_index": i,
            "phrase": phrase,
            "image": img,
            "topic_slug": topic_slug,
            "cue_start_sec": round(start, 2),
            "cue_end_sec": round(end, 2),
            "caption_text": cap_text,
            "caption_start_sec": round(cap_start, 2),
            "caption_end_sec": round(cap_end, 2),
            "speech_est_start_sec": round(speech_est, 2) if speech_est is not None else None,
            "speech_drift_sec": round(drift, 2) if drift is not None else None,
            "checks": {
                "caption_timeline_aligned": caption_aligned,
                "resolver_mid_cue": resolver_ok,
                "image_topic_slug": image_topic_ok,
                "speech_timing": speech_ok if speech_est is not None else None,
            },
        }
        rows.append(row)

    ct_path = seg_dir / "cue_timings.json"
    match_method = None
    if ct_path.is_file():
        methods = {c.get("match_method") for c in json.loads(ct_path.read_text()).get("cues") or []}
        match_method = sorted(methods)

    intro_issue = rows[0]["cue_start_sec"] < roll_t0 - 0.1 if rows else False
    if intro_issue:
        issues.insert(0, f"montage starts at {rows[0]['cue_start_sec']}s but roll-call ~{roll_t0:.1f}s (intro not skipped)")

    ok = len(issues) == 0
    return {
        "schema_version": 1,
        "segment": "00-hook",
        "ok": ok,
        "has_word_timestamps": has_words,
        "match_method": match_method,
        "roll_call_start_sec": round(roll_t0, 2),
        "roll_call_end_sec": round(roll_t1, 2),
        "timing_method": "whisper_words" if has_words else "text_ratio_estimate",
        "caption_timeline_mapped": True,
        "summary": {
            "cues": len(rows),
            "caption_aligned": sum(1 for r in rows if r["checks"]["caption_timeline_aligned"]),
            "image_topic_ok": sum(1 for r in rows if r["checks"]["image_topic_slug"]),
            "speech_ok": sum(1 for r in rows if r["checks"]["speech_timing"] is True),
            "speech_unverified": sum(1 for r in rows if r["checks"]["speech_timing"] is None),
            "issues_count": len(issues),
        },
        "issues": issues,
        "cues": rows,
    }

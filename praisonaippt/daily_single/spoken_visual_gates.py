"""Central spoken↔visual QA gates — video-first → audio → Whisper words → slide map.

Every pipeline phase calls into this module so verification cannot leak between steps.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from praisonaippt.daily_single.pipeline import PIPELINE_AV_ORDER  # re-export for tests/docs
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.transcript_loader import load_whisper_json

GateFn = Callable[[DailySingleProject], tuple[bool, dict[str, Any]]]


def _segment_path(project: DailySingleProject, seg_id: str, seg_folder: str | None) -> Path:
    return project.segments_dir / (seg_folder or seg_id)


def ensure_whisper_after_vo(project: DailySingleProject, *, force: bool = False) -> dict[str, Any]:
    """After synthesise-vo: transcribe each segment mp3 → timestamps.json (word-level)."""
    from praisonaippt.daily_single.captions import _ensure_transcript

    rows: list[dict[str, Any]] = []
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        seg_path = _segment_path(project, seg_id, seg_folder)
        mp3 = seg_path / "narration.mp3"
        ts = seg_path / "timestamps.json"
        if not mp3.is_file():
            rows.append({"segment": seg_id, "skipped": True, "reason": "no narration.mp3"})
            continue
        try:
            _ensure_transcript(mp3, ts, force=force)
        except Exception as exc:
            rows.append({"segment": seg_id, "error": str(exc)[:120], "exists": ts.is_file()})
            continue
        rows.append({"segment": seg_id, "timestamps": str(ts), "exists": ts.is_file()})
    out = {"segments": rows}
    report_path = project.merge_dir / "qa" / "post_vo_whisper.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def validate_whisper_word_timings(project: DailySingleProject, *, min_words: int = 8) -> tuple[bool, dict[str, Any]]:
    """Require real Whisper word arrays — block proportional/degraded captions early."""
    rows: list[dict[str, Any]] = []
    ok = True
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        seg_path = _segment_path(project, seg_id, seg_folder)
        mp3 = seg_path / "narration.mp3"
        ts = seg_path / "timestamps.json"
        if not mp3.is_file():
            continue
        if not ts.is_file():
            ok = False
            rows.append({"segment": seg_id, "ok": False, "error": "missing timestamps.json"})
            continue
        raw = json.loads(ts.read_text(encoding="utf-8"))
        source = str(raw.get("source") or "")
        data = load_whisper_json(ts)
        word_count = len(data.words or [])
        seg_ok = word_count >= min_words and source != "proportional"
        if not seg_ok:
            ok = False
        rows.append({
            "segment": seg_id,
            "ok": seg_ok,
            "word_count": word_count,
            "source": source or "local",
            "error": "" if seg_ok else "need OpenAI/local Whisper word timings (not proportional)",
        })
    return ok, {"segments": rows, "min_words": min_words}


def validate_pre_assemble_readiness(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Before assemble: scripts, VO, and Whisper word timings must exist per segment."""
    whisper_ok, whisper_detail = validate_whisper_word_timings(project)
    missing: list[str] = []
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        seg_path = _segment_path(project, seg_id, seg_folder)
        for name in ("script.md", "narration.mp3", "timestamps.json"):
            if not (seg_path / name).is_file():
                missing.append(f"{seg_id}/{name}")
    ok = whisper_ok and not missing
    return ok, {
        "whisper": whisper_detail,
        "missing": missing,
        "issues": missing + ([] if whisper_ok else ["Whisper word timings incomplete"]),
    }


def validate_assembled_prerequisites(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Before spoken↔visual gates: final mux + merged SRT + global word timeline."""
    from praisonaippt.daily_single.word_visual_sync import build_global_word_timeline

    issues: list[str] = []
    mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final.mp4"
    if not mp4.is_file():
        issues.append("missing merge/final.mp4 — run assemble-beats")
    srt = project.merge_dir / "final.srt"
    if not srt.is_file():
        issues.append("missing merge/final.srt — run build-captions after assemble")
    timeline = project.merge_dir / "timeline.json"
    if not timeline.is_file():
        issues.append("missing merge/timeline.json")
    words = build_global_word_timeline(project)
    if not words:
        issues.append("no global Whisper words — build-captions after assemble")
    return len(issues) == 0, {
        "final_mp4": str(mp4) if mp4.is_file() else None,
        "final_srt": str(srt) if srt.is_file() else None,
        "whisper_words": len(words),
        "issues": issues,
    }


def run_spoken_visual_map(project: DailySingleProject, *, use_vlm: bool = True) -> tuple[bool, dict[str, Any]]:
    """Full spoken↔visual map: SRT windows + Whisper word samples + VLM on final.mp4."""
    prereq_ok, prereq = validate_assembled_prerequisites(project)
    if not prereq_ok:
        return False, {"prerequisites": prereq, "error": "; ".join(prereq["issues"])}

    from praisonaippt.daily_single.spoken_visual_sync import validate_spoken_visual_sync

    report = validate_spoken_visual_sync(project)
    return bool(report.get("ok")), report


def refresh_publish_validators(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Re-run live gates for validate-all — never trust stale JSON alone."""
    from praisonaippt.daily_single.display_sync import validate_display_sync

    results: dict[str, Any] = {}
    ok = True

    mp4 = project.merge_dir / "final.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final-with-audio.mp4"
    srt = project.merge_dir / "final.srt"

    if srt.is_file():
        ds = validate_display_sync(project)
        results["display_sync"] = ds
        ok = ok and bool(ds.get("ok"))

    if mp4.is_file() and srt.is_file():
        sv_ok, sv = run_spoken_visual_map(project, use_vlm=True)
        results["spoken_visual"] = sv
        ok = ok and sv_ok

        from praisonaippt.video_qa.stages.s03_image_speech import run_s03_image_speech
        from praisonaippt.video_qa.stages.s22_word_visual_sync import run_s22_word_visual_sync

        s03 = run_s03_image_speech(project, required=True, when="post_build")
        results["s03_image_speech"] = {"ok": s03.ok, "id": s03.id}
        ok = ok and s03.ok

        s22 = run_s22_word_visual_sync(project, required=True, when="post_build")
        results["s22_word_visual"] = {"ok": s22.ok, "id": s22.id}
        ok = ok and s22.ok
    else:
        ok = False
        missing = []
        if not mp4.is_file():
            missing.append("merge/final.mp4")
        if not srt.is_file():
            missing.append("merge/final.srt")
        results["spoken_visual"] = {
            "ok": False,
            "skipped": True,
            "reason": "missing final mp4 or srt",
            "missing": missing,
        }

    return ok, results


def validate_segment_audio(project: DailySingleProject, *, min_duration: float = 0.5) -> tuple[bool, dict[str, Any]]:
    """Every segment narration.mp3 must exist and have audible duration."""
    import subprocess

    rows: list[dict[str, Any]] = []
    ok = True
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        mp3 = _segment_path(project, seg_id, seg_folder) / "narration.mp3"
        if not mp3.is_file():
            ok = False
            rows.append({"segment": seg_id, "ok": False, "error": "missing narration.mp3"})
            continue
        try:
            dur = float(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3)],
                text=True,
            ).strip())
        except (OSError, ValueError, subprocess.CalledProcessError):
            ok = False
            rows.append({"segment": seg_id, "ok": False, "error": "ffprobe failed"})
            continue
        seg_ok = dur >= min_duration
        ok = ok and seg_ok
        rows.append({"segment": seg_id, "ok": seg_ok, "duration_sec": round(dur, 2)})
    return ok, {"segments": rows, "min_duration": min_duration}


def validate_pre_build_av(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Scripts on disk + beat-map visuals exist (audio/words deferred until post_vo)."""
    from praisonaippt.daily_single.media_sync import validate_media_inventory

    missing_scripts: list[str] = []
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        script = _segment_path(project, seg_id, seg_folder) / "script.md"
        if not script.is_file():
            missing_scripts.append(f"{seg_id}/script.md")
    media_ok, media = validate_media_inventory(project)
    issues = list(missing_scripts)
    if not media_ok:
        issues.extend(str(i) for i in (media.get("issues") or [])[:10])
    ok = not issues
    return ok, {
        "pillar": {"audio": "deferred", "words": "deferred", "visuals": media_ok},
        "missing_scripts": missing_scripts,
        "media_inventory": media,
        "issues": issues,
    }


def ensure_pre_assemble_preview_artifacts(project: DailySingleProject) -> dict[str, Any]:
    """Build segment.srt + narration-based timeline so s16/s17 can run before assemble."""
    from praisonaippt.daily_single.captions import build_segment_captions
    from praisonaippt.daily_single.timeline import build_timeline_from_narration

    built_srt: list[str] = []
    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        seg_path = _segment_path(project, seg_id, seg_folder)
        if not (seg_path / "script.md").is_file() or not (seg_path / "narration.mp3").is_file():
            continue
        srt = seg_path / "segment.srt"
        if not srt.is_file():
            build_segment_captions(seg_path)
            built_srt.append(f"{seg_id}/segment.srt")
    timeline_path = project.merge_dir / "timeline.json"
    preview = not timeline_path.is_file() or json.loads(
        timeline_path.read_text(encoding="utf-8"),
    ).get("source") == "narration_preview"
    if preview:
        build_timeline_from_narration(project)
    return {"built_srt": built_srt, "timeline_preview": preview}


def validate_pre_assemble_av(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Audio + Whisper words + cue-to-picture map before mux."""
    from praisonaippt.daily_single.cue_map_audit import validate_cue_picture_map

    preview = ensure_pre_assemble_preview_artifacts(project)
    audio_ok, audio = validate_segment_audio(project)
    ready_ok, ready = validate_pre_assemble_readiness(project)
    cue_ok, cue_issues, cue_detail = validate_cue_picture_map(project)
    ok = audio_ok and ready_ok and cue_ok
    issues = list(ready.get("issues") or []) + list(cue_issues)
    return ok, {
        "pillar": {"audio": audio_ok, "words": ready_ok, "visuals": cue_ok},
        "preview": preview,
        "audio": audio,
        "readiness": ready,
        "cue_map": {"ok": cue_ok, "detail": cue_detail, "issues": cue_issues[:8]},
        "issues": issues[:15],
    }


def _final_mp4(project: DailySingleProject) -> Path | None:
    for name in ("final-with-audio.mp4", "final.mp4", "final-silent.mp4"):
        path = project.merge_dir / name
        if path.is_file():
            return path
    return None


def validate_post_assemble_av(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """After assemble: mux exists, segment audio+words still valid, visual timeline planned."""
    import subprocess

    from praisonaippt.daily_single.display_sync import build_visual_timeline

    issues: list[str] = []
    audio_ok, audio = validate_segment_audio(project)
    whisper_ok, whisper = validate_whisper_word_timings(project)
    mp4 = _final_mp4(project)
    mux_ok = mp4 is not None
    has_audio_track = False
    if mp4:
        try:
            has_audio_track = bool(subprocess.check_output(
                ["ffprobe", "-v", "error", "-select_streams", "a:0",
                 "-show_entries", "stream=codec_name",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
                text=True,
            ).strip())
        except (OSError, subprocess.CalledProcessError):
            has_audio_track = False
    else:
        issues.append("missing merge/final.mp4 — run assemble-beats")
    if mux_ok and not has_audio_track:
        issues.append("merge/final.mp4 has no audio track")
    tl = project.merge_dir / "timeline.json"
    if not tl.is_file():
        issues.append("missing merge/timeline.json")
    windows = build_visual_timeline(project) if tl.is_file() else []
    visual_ok = len(windows) >= 10
    if not visual_ok:
        issues.append(f"visual timeline too short ({len(windows)} windows)")
    ok = audio_ok and whisper_ok and mux_ok and has_audio_track and visual_ok
    return ok, {
        "pillar": {
            "audio": audio_ok and mux_ok and has_audio_track,
            "words": whisper_ok,
            "visuals": visual_ok,
        },
        "audio": audio,
        "whisper": whisper,
        "final_mp4": str(mp4) if mp4 else None,
        "visual_windows": len(windows),
        "issues": issues,
    }


def validate_post_bookends_av(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """After bookend-media: hook/outro narration exists; whisper on bookends when timestamps present."""
    import subprocess

    rows: list[dict[str, Any]] = []
    ok = True
    for label in ("00-hook", "99-outro"):
        mp3 = project.segment_narration(label)
        ts = project.segments_dir / label / "timestamps.json"
        row: dict[str, Any] = {"segment": label}
        if not mp3.is_file():
            ok = False
            row.update({"ok": False, "error": "missing narration.mp3"})
            rows.append(row)
            continue
        try:
            dur = float(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3)],
                text=True,
            ).strip())
        except (OSError, ValueError, subprocess.CalledProcessError):
            ok = False
            row.update({"ok": False, "error": "ffprobe failed"})
            rows.append(row)
            continue
        whisper_ok = True
        if ts.is_file():
            raw = json.loads(ts.read_text(encoding="utf-8"))
            data = load_whisper_json(ts)
            whisper_ok = len(data.words or []) >= 8 and str(raw.get("source") or "") != "proportional"
            if not whisper_ok:
                ok = False
        row.update({"ok": dur >= 0.5 and whisper_ok, "duration_sec": round(dur, 2), "whisper_ok": whisper_ok})
        rows.append(row)
    return ok, {
        "pillar": {"audio": ok, "words": ok, "visuals": "deferred until pre_assemble"},
        "bookends": rows,
        "issues": [r["error"] for r in rows if not r.get("ok") and r.get("error")],
    }


def validate_post_captions_av(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """After build-captions: merged SRT + global word timeline + cue display plan."""
    from praisonaippt.daily_single.display_sync import build_visual_timeline, validate_display_sync
    from praisonaippt.daily_single.word_visual_sync import build_global_word_timeline

    prereq_ok, prereq = validate_assembled_prerequisites(project)
    words = build_global_word_timeline(project)
    windows = build_visual_timeline(project)
    ds = validate_display_sync(project) if (project.merge_dir / "final.srt").is_file() else {"ok": False}
    visual_ok = bool(ds.get("ok")) and len(windows) >= 10
    words_ok = len(words) >= 50
    ok = prereq_ok and words_ok and visual_ok
    issues = list(prereq.get("issues") or [])
    if len(words) < 50:
        issues.append(f"global whisper words too few ({len(words)})")
    if not visual_ok:
        issues.append(
            f"display sync: {ds.get('cues_fail', '?')} cues below threshold "
            f"({ds.get('cues_pass', 0)}/{ds.get('cues_total', 0)})"
        )
    return ok, {
        "pillar": {
            "audio": prereq_ok,
            "words": words_ok,
            "visuals": visual_ok,
        },
        "prerequisites": prereq,
        "whisper_words": len(words),
        "visual_windows": len(windows),
        "display_sync": {"ok": ds.get("ok"), "cues_pass": ds.get("cues_pass"), "cues_total": ds.get("cues_total")},
        "issues": issues,
    }


def _gate_transcribe_vo(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    detail = ensure_whisper_after_vo(project)
    ok = True
    for row in detail.get("segments") or []:
        if row.get("error"):
            ok = False
        elif not row.get("skipped") and not row.get("exists", True):
            ok = False
    return ok, detail


# Phase → gate functions (SDK + video_qa stages delegate here).
PHASE_GATES: dict[str, tuple[GateFn, ...]] = {
    "pre_build": (validate_pre_build_av,),
    "post_vo": (_gate_transcribe_vo, validate_whisper_word_timings, validate_segment_audio),
    "post_bookends": (validate_post_bookends_av,),
    "pre_assemble": (validate_pre_assemble_av,),
    "post_assemble": (validate_post_assemble_av,),
    "post_captions": (validate_post_captions_av,),
    "post_build": (run_spoken_visual_map,),
}


def av_pillar_matrix(project: DailySingleProject) -> dict[str, Any]:
    """Summarise audio / words / visuals gate status for every pipeline phase."""
    phases = list(PHASE_GATES.keys())
    rows: list[dict[str, Any]] = []
    for phase in phases:
        ok, detail = run_phase_gates(project, phase)
        pillar = {}
        for gate in detail.get("gates") or []:
            report = gate.get("report") or {}
            if isinstance(report, dict) and "pillar" in report:
                pillar = report["pillar"]
                break
        rows.append({"phase": phase, "ok": ok, "pillar": pillar})
    return {"phases": rows, "av_order": list(PIPELINE_AV_ORDER)}


def run_phase_gates(project: DailySingleProject, when: str, **kwargs: Any) -> tuple[bool, dict[str, Any]]:
    """Run all gates registered for a pipeline ``when`` phase."""
    gates = PHASE_GATES.get(when, ())
    details: dict[str, Any] = {"when": when, "gates": []}
    ok = True
    for gate in gates:
        if gate is run_spoken_visual_map:
            gate_ok, report = run_spoken_visual_map(
                project, use_vlm=bool(kwargs.get("use_vlm", True))
            )
        else:
            gate_ok, report = gate(project)
        details["gates"].append({"name": gate.__name__, "ok": gate_ok, "report": report})
        ok = ok and gate_ok
    report_path = project.merge_dir / "qa" / f"av_pillars_{when}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps({"ok": ok, **details}, indent=2),
        encoding="utf-8",
    )
    return ok, details

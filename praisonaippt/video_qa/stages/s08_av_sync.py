"""Stage s08 — audio–visual sync (word-level + section boundaries)."""
from __future__ import annotations

import json

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.sync_validation import validate_hook_structure
from praisonaippt.segment_video.align import match_fragment_to_words
from praisonaippt.segment_video.media import ffprobe_duration
from praisonaippt.segment_video.script_text import narration_text_for_tts
from praisonaippt.segment_video.validate_sync import overlap_ratio
from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def _validate_section_boundaries(project: DailySingleProject, *, tol: float = 0.5) -> tuple[bool, list[str]]:
    timeline_path = project.merge_dir / "timeline.json"
    if not timeline_path.is_file():
        return False, ["missing merge/timeline.json"]
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for row in timeline.get("segments") or []:
        seg_id = row.get("id") or ""
        expected = float(row.get("duration_sec") or 0)
        if seg_id.startswith("beat-"):
            n = int(seg_id.split("-")[1])
            beat_mp4 = project.beats_dir / f"beat-{n:02d}.mp4"
            narr = None
            from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS
            seg_dir = BEAT_SEGMENT_DIRS.get(n)
            if seg_dir:
                narr = project.segment_narration(seg_dir)
            if beat_mp4.is_file():
                actual = ffprobe_duration(beat_mp4)
                if abs(actual - expected) > tol:
                    issues.append(f"{seg_id}: beat mp4 {actual:.2f}s vs timeline {expected:.2f}s")
            elif narr and narr.is_file():
                actual = ffprobe_duration(narr)
                if abs(actual - expected) > tol + 0.3:
                    issues.append(f"{seg_id}: narration {actual:.2f}s vs timeline {expected:.2f}s")
        elif seg_id in ("00-hook", "99-outro"):
            beat_mp4 = project.beats_dir / f"{seg_id}.mp4"
            media = beat_mp4 if beat_mp4.is_file() else project.segments_dir / seg_id / "heygen.mp4"
            if media.is_file() and expected > 0:
                actual = ffprobe_duration(media)
                slack = 1.0 if beat_mp4.is_file() else (3.0 if seg_id == "00-hook" else 1.0)
                if abs(actual - expected) > tol + slack:
                    issues.append(f"{seg_id} duration {actual:.2f}s vs timeline {expected:.2f}s")
    return len(issues) == 0, issues


def run_s08_av_sync(
    project: DailySingleProject,
    *,
    min_overlap: float = 0.35,
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    if ctx is not None:
        min_overlap = ctx.min_transcript_overlap()
        display = ctx.get_display_sync()
    else:
        from praisonaippt.daily_single.display_sync import validate_display_sync
        display = validate_display_sync(project)

    checks: list[CheckResult] = []
    ok_display = bool(display.get("ok"))
    checks.append(CheckResult(
        id="display_sync",
        ok=ok_display,
        severity="error" if required else "warn",
        message=f"display {display.get('cues_pass', 0)}/{display.get('cues_total', 0)} cues",
    ))

    cue_map = display.get("cue_map") or []
    hook_ok, hook_issues = validate_hook_structure(cue_map[:3] if len(cue_map) >= 3 else cue_map)
    checks.append(CheckResult(
        id="hook_structure",
        ok=hook_ok,
        severity="error" if required else "warn",
        message="hook structure PASS" if hook_ok else "; ".join(hook_issues[:2]),
    ))

    for seg_id, seg_folder, _beat in SEGMENT_ORDER:
        seg_path = project.segments_dir / (seg_folder or seg_id)
        ts_path = seg_path / "timestamps.json"
        script_path = seg_path / "script.md"
        if not script_path.is_file() or not ts_path.is_file():
            continue
        script_text = narration_text_for_tts(script_path.read_text(encoding="utf-8"))
        sentences = split_caption_cues(script_text)
        probe = sentences[0] if sentences else script_text[:120]
        td = load_whisper_json(ts_path)
        span = match_fragment_to_words(probe, td)
        spoken = td.text or " ".join(s.text for s in td.segments)
        ov = overlap_ratio(script_text, spoken)
        word_ok = span is not None and ov >= min_overlap
        checks.append(CheckResult(
            id=f"word_{seg_id}",
            ok=word_ok,
            severity="error" if required else "warn",
            message=f"{seg_id} word match={span is not None}, overlap {ov:.2f}",
            details={"overlap": round(ov, 3), "has_span": span is not None},
        ))

    sec_ok, sec_issues = _validate_section_boundaries(project)
    checks.append(CheckResult(
        id="section_boundaries",
        ok=sec_ok,
        severity="error" if required else "warn",
        message="section boundaries PASS" if sec_ok else sec_issues[0],
        details={"issues": sec_issues},
    ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(id="s08-av-sync", ok=ok, required=required, when=when, checks=checks)

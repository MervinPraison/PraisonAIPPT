"""Stage s05 — post-VO transcript validation (Whisper vs script)."""
from __future__ import annotations

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.sync_validation import validate_caption_script_lock
from praisonaippt.segment_video.align import match_fragment_to_words
from praisonaippt.segment_video.script_text import narration_text_for_tts
from praisonaippt.segment_video.validate_sync import overlap_ratio
from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def _segment_dir(project: DailySingleProject, seg_id: str, seg_folder: str | None) -> str:
    return seg_folder or seg_id


def run_s05_transcript(
    project: DailySingleProject,
    *,
    min_overlap: float = 0.35,
    phase: str = "post_vo",
    required: bool = True,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    if ctx is not None:
        min_overlap = ctx.min_transcript_overlap()

    checks: list[CheckResult] = []
    segments_out: list[dict] = []
    whisper_degraded = False

    if phase == "post_vo":
        for seg_id, seg_folder, _beat_n in SEGMENT_ORDER:
            seg_path = project.segments_dir / _segment_dir(project, seg_id, seg_folder)
            narration = seg_path / "narration.mp3"
            script = seg_path / "script.md"
            ok = narration.is_file() and script.is_file()
            checks.append(CheckResult(
                id=f"{seg_id}_vo",
                ok=ok,
                severity="error" if required else "warn",
                message=f"{seg_id} VO ready" if ok else f"{seg_id} missing script or narration.mp3",
            ))
            segments_out.append({"segment": seg_id, "ok": ok, "phase": "post_vo"})
        ok = all(c.ok or c.severity != "error" for c in checks)
        return StageReport(
            id="s05-transcript",
            ok=ok,
            required=required,
            when=when,
            checks=checks,
            details={"segments": segments_out, "phase": phase},
        )

    if phase == "post_captions":
        lock_ok, lock_issues = validate_caption_script_lock(project)
        checks.append(CheckResult(
            id="caption_script_lock",
            ok=lock_ok,
            severity="error" if required else "warn",
            message="caption lock PASS" if lock_ok else lock_issues[0],
            details={"issues": lock_issues[:5]},
        ))

    for seg_id, seg_folder, _beat_n in SEGMENT_ORDER:
        seg_dir_name = _segment_dir(project, seg_id, seg_folder)
        seg_path = project.segments_dir / seg_dir_name
        script_path = seg_path / "script.md"
        narration_path = seg_path / "narration.mp3"
        ts_path = seg_path / "timestamps.json"
        srt_path = seg_path / "segment.srt"

        if not script_path.is_file():
            continue

        script_text = narration_text_for_tts(script_path.read_text(encoding="utf-8"))
        sentences = split_caption_cues(script_text)
        probe = sentences[0] if sentences else script_text[:120]

        if not narration_path.is_file():
            checks.append(CheckResult(
                id=f"{seg_id}_narration",
                ok=False,
                severity="error" if required else "warn",
                message=f"missing narration.mp3 for {seg_id}",
            ))
            continue

        if not ts_path.is_file():
            whisper_degraded = True
            if srt_path.is_file():
                checks.append(CheckResult(
                    id=f"{seg_id}_whisper",
                    ok=True,
                    severity="warn",
                    message=f"{seg_id} proportional captions (no Whisper timestamps)",
                ))
                segments_out.append({"segment": seg_id, "ok": True, "degraded": True, "reason": "proportional"})
                continue
            checks.append(CheckResult(
                id=f"{seg_id}_whisper",
                ok=False,
                severity="error" if required else "warn",
                message=f"{seg_id} missing timestamps.json — run build-captions",
            ))
            continue

        td = load_whisper_json(ts_path)
        spoken = td.text or " ".join(s.text for s in td.segments)
        ov = overlap_ratio(script_text, spoken)
        span = match_fragment_to_words(probe, td)
        word_ok = ov >= min_overlap and span is not None
        if not word_ok:
            checks.append(CheckResult(
                id=f"{seg_id}_overlap",
                ok=False,
                severity="error",
                message=f"{seg_id} overlap {ov:.2f}, word_match={span is not None}",
                details={"overlap": round(ov, 3)},
            ))
        else:
            checks.append(CheckResult(
                id=f"{seg_id}_overlap",
                ok=True,
                severity="info",
                message=f"{seg_id} overlap {ov:.2f}",
            ))
        segments_out.append({"segment": seg_id, "ok": word_ok, "overlap": round(ov, 3)})

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(
        id="s05-transcript",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"segments": segments_out, "min_overlap": min_overlap, "phase": phase},
        degraded=whisper_degraded,
    )

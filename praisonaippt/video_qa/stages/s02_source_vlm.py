"""Stage s02 — VLM timeline on source motion clips (post-sync)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from praisonaippt.daily_single.media_sync import load_handoff_topic, _videos_dir
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.media import ffprobe_duration
from praisonaippt.video_qa.adapters import qa_dir
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext
from praisonaippt.video_qa.vlm_cache import describe_frame_cached
from praisonaippt.daily_single.visual_audit import export_frame


def _sample_times(duration: float, interval: float) -> list[float]:
    if duration <= 0:
        return [0.0]
    times = [0.0]
    t = interval
    while t < duration - 0.1:
        times.append(t)
        t += interval
    return times


def run_s02_source_vlm(
    project: DailySingleProject,
    *,
    interval_sec: float = 5.0,
    use_vision: bool = True,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []
    topic = load_handoff_topic(project)
    videos_dir = _videos_dir(project)
    qa = qa_dir(project)
    frames_dir = qa / "s02_frames"
    timeline: list[dict] = []

    entries = list(topic.get("videos") or []) + list(topic.get("youtube") or [])
    if not entries:
        checks.append(CheckResult(
            id="source_videos",
            ok=False,
            severity="warn",
            message="no handoff videos to sample",
        ))
        return StageReport(id="s02-source-vlm", ok=True, required=required, when=when, checks=checks)

    if os.environ.get("PRAISONAIPPT_QA_OFFLINE", "").lower() in ("1", "true", "yes") or not os.environ.get("OPENAI_API_KEY"):
        checks.append(CheckResult(
            id="vlm_skipped",
            ok=True,
            severity="info",
            message="VLM skipped (offline or no API key)",
        ))
        return StageReport(id="s02-source-vlm", ok=True, required=required, when=when, checks=checks, skipped=True)

    for entry in entries:
        fn = entry.get("filename") or ""
        path = Path(entry.get("path") or videos_dir / fn)
        if not path.is_file():
            checks.append(CheckResult(
                id=f"missing_{fn}",
                ok=False,
                severity="error" if required else "warn",
                message=f"missing source video {fn}",
            ))
            continue
        dur = ffprobe_duration(path)
        for t in _sample_times(dur, interval_sec):
            frame = export_frame(path, t, frames_dir / f"{path.stem}-{t:.1f}.jpg")
            row: dict = {"file": fn, "t_sec": round(t, 2), "duration_sec": round(dur, 2)}
            if use_vision:
                try:
                    vision = describe_frame_cached(qa, frame, fn)
                except Exception as exc:
                    vision = {"description": "", "topics": [], "generic_broll": False, "error": str(exc)[:120]}
                row["vision"] = vision
                if vision.get("generic_broll"):
                    checks.append(CheckResult(
                        id=f"generic_{fn}_{t:.0f}",
                        ok=False,
                        severity="warn",
                        message=f"generic B-roll flagged in {fn} @ {t:.1f}s",
                    ))
            timeline.append(row)

    out = qa / "s02_source_vlm_timeline.json"
    out.write_text(json.dumps({"samples": timeline, "interval_sec": interval_sec}, indent=2), encoding="utf-8")

    ok = all(c.ok or c.severity != "error" for c in checks)
    if ok and timeline:
        checks.append(CheckResult(
            id="timeline",
            ok=True,
            severity="info",
            message=f"sampled {len(timeline)} frame(s) from {len(entries)} clip(s)",
            details={"path": str(out)},
        ))
    return StageReport(
        id="s02-source-vlm",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"timeline_path": str(out), "samples": len(timeline)},
    )

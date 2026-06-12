"""Build merge/timeline.json from assembled beat MP4s or narration-only preview."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from praisonaippt.daily_single.brand_bumper import BUMPER_STEM
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.segment_video.media import ffprobe_duration


def build_timeline_from_narration(project: DailySingleProject) -> dict:
    """Pre-assemble preview timeline from segment narration.mp3 durations (no beat MP4s yet)."""
    segments: list[dict] = []
    t = 0.0
    for label, seg_dir, beat in SEGMENT_ORDER:
        mp3 = project.segments_dir / seg_dir / "narration.mp3"
        if not mp3.is_file():
            continue
        d = ffprobe_duration(mp3)
        tl_id = label if label in ("00-hook", "99-outro") else f"beat-{beat:02d}"
        segments.append({"id": tl_id, "start_sec": round(t, 2), "duration_sec": round(d, 2)})
        t += d
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(t, 2),
        "segments": segments,
        "source": "narration_preview",
    }
    out = project.merge_dir / "timeline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_timeline(project: DailySingleProject) -> dict:
    order = [project.beats_dir / "00-hook.mp4"]
    bumper = project.beats_dir / f"{BUMPER_STEM}.mp4"
    if bumper.is_file():
        order.append(bumper)
    order += [project.beats_dir / f"beat-{i:02d}.mp4" for i in range(1, 11)]
    order.append(project.beats_dir / "99-outro.mp4")
    segments = []
    t = 0.0
    for p in order:
        if not p.is_file():
            continue
        d = ffprobe_duration(p)
        segments.append({"id": p.stem, "start_sec": round(t, 2), "duration_sec": round(d, 2)})
        t += d
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(t, 2),
        "segments": segments,
    }
    out = project.merge_dir / "timeline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({t:.1f}s)")
    return payload

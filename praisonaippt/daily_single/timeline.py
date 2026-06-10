"""Build merge/timeline.json from assembled beat MP4s."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.media import ffprobe_duration


def build_timeline(project: DailySingleProject) -> dict:
    order = [project.beats_dir / "00-hook.mp4"]
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

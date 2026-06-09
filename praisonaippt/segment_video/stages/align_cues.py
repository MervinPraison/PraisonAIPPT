"""align-cues stage — Whisper-aligned cue timings per segment."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from ..align import align_cues_to_transcript, save_cue_timings
from ..timeline import build_segment_timeline, write_cue_timings_srt
from ..manifest import load_manifest
from ..media import ffprobe_duration
from ..project import SegmentVideoProject
from ..timeline import load_segment_yaml, verses_from_yaml


def run_align_cues(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    root = project.root
    manifest = load_manifest(root)
    assets_path = root / "media_assets.json"
    assets = json.loads(assets_path.read_text(encoding="utf-8")).get("segments", {}) if assets_path.is_file() else {}

    for seg in manifest.get("segments", []):
        d = seg["dir"]
        if segments and d not in segments:
            continue
        seg_dir = root / "segments" / d
        ts = seg_dir / "timestamps.json"
        heygen = seg_dir / "heygen.mp4"
        if not ts.is_file():
            emit(f"align-cues skip {d}: no timestamps.json")
            continue
        entry = assets.get(d, {})
        cues = entry.get("cues") or []
        if not cues:
            script = (seg_dir / "script.md").read_text(encoding="utf-8").strip() if (seg_dir / "script.md").is_file() else ""
            cues = [{"script_fragment": script, "file": ""}]
        dur = ffprobe_duration(heygen) if heygen.is_file() else None
        timings = align_cues_to_transcript(cues, ts, total_duration=dur)
        save_cue_timings(seg_dir, timings)
        write_cue_timings_srt(seg_dir, timings)
        build_segment_timeline(seg_dir, root)
        emit(f"align-cues {d}: {len(timings)} cues")
        yaml_data = load_segment_yaml(seg_dir)
        n_verses = len(verses_from_yaml(yaml_data)) if yaml_data else 0
        if n_verses and n_verses != len(timings):
            emit(f"align-cues {d}: WARN run yaml — segment.yaml has {n_verses} verses, cue_timings has {len(timings)}")
    return 0

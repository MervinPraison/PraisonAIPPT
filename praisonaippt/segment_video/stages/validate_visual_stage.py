"""validate-visual + validate-sync stages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import yaml

from ..manifest import load_manifest
from ..project import SegmentVideoProject
from ..timeline import build_segment_timeline, build_project_timeline
from ..validate_sync import validate_segment_sync
from ..visual import export_cue_frames, validate_segment_visual


def run_validate_sync(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    manifest = load_manifest(project.root)
    protocol = project.load_protocol()
    sv = protocol.get("sync_validation") or {}
    min_overlap = float(sv.get("min_fragment_overlap", 0.45))
    max_drift = float(sv.get("max_start_drift_sec", 0.5))
    failed = 0
    for seg in manifest.get("segments", []):
        d = seg["dir"]
        if segments and d not in segments:
            continue
        seg_dir = project.root / "segments" / d
        ok, issues = validate_segment_sync(seg_dir, min_overlap=min_overlap, max_drift=max_drift)
        if not ok:
            failed += 1
            for item in issues:
                emit(f"sync FAIL {d}: {item}")
        else:
            emit(f"sync OK {d}")
    return 1 if failed else 0


def run_validate_visual(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    manifest = load_manifest(project.root)
    failed = 0
    for seg in manifest.get("segments", []):
        d = seg["dir"]
        if segments and d not in segments:
            continue
        seg_dir = project.root / "segments" / d
        mp4 = seg_dir / "segment.mp4"
        yaml_path = seg_dir / "segment.yaml"
        if mp4.is_file() and yaml_path.is_file():
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            verses = []
            for sec in data.get("sections") or []:
                verses.extend(sec.get("verses") or [])
            pipeline = data.get("pipeline") or {}
            if pipeline.get("export_mp4_frames"):
                frames_dir = seg_dir / (pipeline.get("mp4_frames_dir") or "slide_jpegs/mp4-frames")
                export_cue_frames(mp4, verses, frames_dir, log=emit)
        report = validate_segment_visual(seg_dir)
        build_segment_timeline(seg_dir, project.root)
        if not report.get("ok"):
            failed += 1
            for item in report.get("issues", []):
                emit(f"visual FAIL {d}: {item}")
        else:
            emit(f"visual OK {d}")
    build_project_timeline(project.root, manifest, project.load_protocol())
    return 1 if failed else 0

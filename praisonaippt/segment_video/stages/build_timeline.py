"""build-timeline stage — refresh timeline.json for all segments."""
from __future__ import annotations

from typing import Callable

from ..manifest import load_manifest
from ..project import SegmentVideoProject
from ..timeline import build_project_timeline, build_segment_timeline


def run_build_timeline(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    manifest = load_manifest(project.root)
    for seg in manifest.get("segments", []):
        d = seg["dir"]
        if segments and d not in segments:
            continue
        seg_dir = project.root / "segments" / d
        if (seg_dir / "segment.yaml").is_file():
            build_segment_timeline(seg_dir, project.root)
            emit(f"timeline {d}")
    build_project_timeline(project.root, manifest, project.load_protocol())
    emit("merge/timeline.json")
    return 0

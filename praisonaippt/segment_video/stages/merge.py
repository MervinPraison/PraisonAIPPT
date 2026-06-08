"""Merge segment MP4s with optional crossfade transitions + SRT stitch."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from praisonaippt.ffmpeg_composer import concat_segments_with_transitions
from praisonaippt.video_protocol import ResolvedEdgeTransition, effective_timeline_sec

from ..manifest import load_manifest, save_manifest
from ..media import ffprobe_duration
from ..project import SegmentVideoProject
from ..protocol import merge_transition_config


def parse_srt(text: str) -> list[tuple[float, float, str]]:
    blocks = re.split(r"\n\n+", text.strip())
    cues = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start_s, end_s = [x.strip() for x in lines[1].split("-->")]
        body = " ".join(lines[2:]).strip()
        cues.append((_srt_ts(start_s), _srt_ts(end_s), body))
    return cues


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _fmt_ts(sec: float) -> str:
    ms = int(round((sec % 1) * 1000))
    s = int(sec) % 60
    m = (int(sec) // 60) % 60
    h = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _build_edges(count: int, transition: dict) -> list[ResolvedEdgeTransition]:
    ttype = str(transition.get("default") or "none")
    dur = float(transition.get("duration_sec") or 0.0)
    if ttype == "none" or count < 2:
        return []
    return [
        ResolvedEdgeTransition(
            after_slide=i + 1,
            type=ttype,
            duration_sec=dur,
            source="merge_transitions",
        )
        for i in range(count - 1)
    ]


def run_merge(
    project: SegmentVideoProject,
    *,
    no_transitions: bool = False,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    root = project.root
    merge_dir = root / "merge"
    merge_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(root)
    protocol = project.load_protocol()
    transition = merge_transition_config(protocol, no_transitions=no_transitions)

    paths: list[Path] = []
    durations: list[float] = []
    per_segment_cues: list[list[tuple[float, float, str]]] = []

    for seg in manifest["segments"]:
        mp4 = root / "segments" / seg["dir"] / "segment.mp4"
        if not mp4.is_file():
            raise FileNotFoundError(f"missing {mp4}")
        paths.append(mp4)
        dur = ffprobe_duration(mp4)
        durations.append(dur)
        srt = mp4.with_suffix(".srt")
        per_segment_cues.append(
            parse_srt(srt.read_text(encoding="utf-8")) if srt.is_file() else []
        )

    concat_list = merge_dir / "concat-video.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in paths) + "\n",
        encoding="utf-8",
    )
    out_mp4 = merge_dir / "final-roundup.mp4"
    edges = _build_edges(len(paths), transition)

    if edges and any(e.is_blend() for e in edges):
        emit(f"merge: {len(edges)} crossfade edges, duration={transition.get('duration_sec')}s")
        concat_segments_with_transitions(
            [str(p) for p in paths],
            durations,
            edges,
            str(out_mp4),
        )
        entries = [{"duration_sec": d} for d in durations]
        starts = effective_timeline_sec(entries, edges)
        merged: list[tuple[float, float, str]] = []
        for i, cues in enumerate(per_segment_cues):
            base = starts[i]
            for start, end, body in cues:
                merged.append((base + start, base + end, body))
    else:
        emit("merge: hard concat (no transitions)")
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(out_mp4)],
            check=False,
        )
        if not out_mp4.is_file() or out_mp4.stat().st_size < 1000:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", str(out_mp4)],
                check=True,
            )
        merged = []
        offset = 0.0
        for i, cues in enumerate(per_segment_cues):
            for start, end, body in cues:
                merged.append((offset + start, offset + end, body))
            offset += durations[i]

    out_srt = merge_dir / "final-roundup.srt"
    parts = [f"{i}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{body}\n" for i, (start, end, body) in enumerate(merged, 1)]
    out_srt.write_text("\n".join(parts), encoding="utf-8")

    total = ffprobe_duration(out_mp4)
    emit(f"merged {out_mp4} duration={total:.1f}s")
    emit(f"captions {out_srt}")

    manifest = load_manifest(root)
    prev = manifest.get("final_video") or {}
    manifest["pipeline_status"] = "merged"
    manifest["final_video"] = {
        "path": "merge/final-roundup.mp4",
        "duration_sec": round(total, 1),
        "captions": "merge/final-roundup.srt",
        "merge_transitions": f"{transition.get('default')} {transition.get('duration_sec')}s",
    }
    for key in ("wordpress_attachment_id", "wordpress_url"):
        if prev.get(key):
            manifest["final_video"][key] = prev[key]
    save_manifest(root, manifest)
    return 0

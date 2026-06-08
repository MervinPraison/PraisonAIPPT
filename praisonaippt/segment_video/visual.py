"""Visual QA — multi-frame export and basic validation."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

import yaml


def export_cue_frames(
    mp4_path: Path,
    verses: list[dict],
    out_dir: Path,
    *,
    log: Callable[[str], None] | None = None,
) -> list[str]:
    """Export start/mid/end JPEG per verse at audio_start_sec."""
    emit = log or (lambda _: None)
    out_dir.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    for i, v in enumerate(verses, start=1):
        start = v.get("audio_start_sec")
        if start is None:
            continue
        start_f = float(start)
        dur = float(v.get("duration_sec") or 1.0)
        points = {
            "start": max(0.0, start_f + 0.35),
            "mid": start_f + dur / 2,
            "end": max(start_f, start_f + dur - 0.35),
        }
        for tag, t in points.items():
            dest = out_dir / f"mp4-slide-{i:03d}-{tag}.jpg"
            cmd = [
                "ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(mp4_path.resolve()),
                "-frames:v", "1", "-q:v", "2", str(dest),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            exported.append(str(dest))
            emit(f"frame {dest.name} @ {t:.2f}s")
    return exported


def validate_segment_visual(seg_dir: Path) -> dict:
    """Basic visual validation report."""
    issues: list[str] = []
    yaml_path = seg_dir / "segment.yaml"
    mp4 = seg_dir / "segment.mp4"
    if not yaml_path.is_file():
        return {"ok": False, "issues": ["missing segment.yaml"]}
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    verses = []
    for sec in data.get("sections") or []:
        verses.extend(sec.get("verses") or [])

    frames_dir = seg_dir / "slide_jpegs" / "mp4-frames"
    for i in range(len(verses)):
        mid = frames_dir / f"mp4-slide-{i + 1:03d}-mid.jpg"
        legacy = frames_dir / f"mp4-slide-{i + 1:03d}.jpg"
        if not mid.is_file() and not legacy.is_file():
            issues.append(f"missing mp4 frame for verse {i + 1}")

    srt = seg_dir / "segment.srt"
    if mp4.is_file() and not srt.is_file():
        issues.append("missing segment.srt")

    report = {
        "ok": len(issues) == 0,
        "issues": issues,
        "verse_count": len(verses),
        "scores": {
            "frames_present": len(issues) == 0,
            "caption_sync": srt.is_file() if mp4.is_file() else None,
        },
    }
    (seg_dir / "visual_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

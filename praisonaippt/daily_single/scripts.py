"""Write per-beat segment scripts from create-news video-script.md."""
from __future__ import annotations

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS
from praisonaippt.segment_video.script_text import extract_beat_section


def write_beat_scripts(project: DailySingleProject) -> list[Path]:
    text = project.video_script_path.read_text(encoding="utf-8")
    written: list[Path] = []
    for n, dirname in BEAT_SEGMENT_DIRS.items():
        body = extract_beat_section(text, n)
        if not body:
            continue
        seg_dir = project.segments_dir / dirname
        seg_dir.mkdir(parents=True, exist_ok=True)
        out = seg_dir / "script.md"
        out.write_text(body + "\n", encoding="utf-8")
        written.append(out)
        print(f"Wrote {out.relative_to(project.root)}")
    return written

"""Batch segment narration and merge."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from praisonaippt.daily_single.env import require_keys
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.tts import synthesise


def _segment_dirs(project: DailySingleProject, only: list[str] | None) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for label, seg_dir, _beat in SEGMENT_ORDER:
        if seg_dir is None:
            continue
        if only and seg_dir not in only and label not in only:
            continue
        script = project.segment_script(seg_dir)
        if script.is_file():
            rows.append((seg_dir, script))
    return rows


def synthesise_segments(
    project: DailySingleProject,
    *,
    only: list[str] | None = None,
    skip_existing: bool = False,
) -> Path:
    """Generate segments/*/narration.mp3 and merge/narration.mp3."""
    require_keys("ELEVEN_API_KEY")
    mp3s: list[Path] = []
    for name, script in _segment_dirs(project, only):
        out = project.segment_narration(name)
        if skip_existing and out.is_file() and out.stat().st_size > 500:
            print(f"skip TTS {name}")
            mp3s.append(out)
            continue
        print(f"TTS {name}...")
        synthesise(script.read_text(encoding="utf-8"), out)
        mp3s.append(out)

    if only:
        # Rebuild merge from full segment order (existing files kept).
        mp3s = []
        for _label, seg_dir, _beat in SEGMENT_ORDER:
            if seg_dir is None:
                continue
            p = project.segment_narration(seg_dir)
            if p.is_file():
                mp3s.append(p)

    merge = project.merge_dir / "narration.mp3"
    merge.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in mp3s:
            f.write(f"file '{p.resolve()}'\n")
        lst = f.name
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", str(merge)],
        check=True,
    )
    print(f"Wrote {merge}")
    return merge

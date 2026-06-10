"""Stage s07 — framing / PiP presence (Phase 1: hook + outro HeyGen)."""
from __future__ import annotations

import subprocess

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def _video_dims(path) -> tuple[int, int] | None:
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        w, h = proc.stdout.strip().split(",")
        return int(w), int(h)
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def run_s07_framing(
    project: DailySingleProject,
    *,
    required: bool = False,
    when: str = "post_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []
    for label in ("00-hook", "99-outro"):
        path = project.segments_dir / label / "heygen.mp4"
        if not path.is_file():
            checks.append(CheckResult(
                id=f"{label}_heygen",
                ok=False,
                severity="warn",
                message=f"missing {label}/heygen.mp4",
            ))
            continue
        dims = _video_dims(path)
        ok_dims = dims is not None and dims[0] >= 720 and dims[1] >= 720
        checks.append(CheckResult(
            id=f"{label}_dims",
            ok=ok_dims,
            severity="warn",
            message=f"{label} {dims[0]}x{dims[1]}" if dims else f"{label} unreadable",
        ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(id="s07-framing", ok=ok, required=required, when=when, checks=checks)

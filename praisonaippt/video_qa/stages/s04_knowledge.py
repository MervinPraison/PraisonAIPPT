"""Stage s04 — knowledge completeness before build."""
from __future__ import annotations

import json

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS, SEGMENT_ORDER
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s04_knowledge(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []

    manifest = project.root / "manifest.json"
    ok_manifest = manifest.is_file()
    checks.append(CheckResult(
        id="manifest",
        ok=ok_manifest,
        severity="error",
        message="manifest.json present" if ok_manifest else "missing manifest.json",
    ))

    script_path = project.video_script_path
    ok_script = script_path.is_file() and script_path.stat().st_size > 100
    checks.append(CheckResult(
        id="video_script",
        ok=ok_script,
        severity="error",
        message="video-script.md present" if ok_script else "missing or empty video-script.md",
        details={"path": str(script_path)},
    ))

    ok_handoff = (project.research_dir / "video-handoff.json").is_file()
    checks.append(CheckResult(
        id="handoff",
        ok=ok_handoff,
        severity="error",
        message="video-handoff.json present" if ok_handoff else "missing video-handoff.json",
    ))

    ok_beat = project.beat_map_path.is_file()
    checks.append(CheckResult(
        id="beat_map",
        ok=ok_beat,
        severity="error",
        message="beat-map.json present" if ok_beat else "missing beat-map.json",
    ))

    if ok_beat:
        try:
            bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
            n_beats = len(bm.get("beats") or {})
            checks.append(CheckResult(
                id="beat_map_entries",
                ok=n_beats >= 10,
                severity="warn" if n_beats >= 8 else "error",
                message=f"beat-map has {n_beats} beat(s)",
                details={"count": n_beats},
            ))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(CheckResult(
                id="beat_map_parse",
                ok=False,
                severity="error",
                message=f"beat-map unreadable: {exc}",
            ))

    missing_segments: list[str] = []
    empty_segments: list[str] = []
    for seg_id, seg_dir, beat_n in SEGMENT_ORDER:
        if seg_dir is None:
            path = project.segment_script(seg_id)
        else:
            path = project.segment_script(seg_dir)
        if not path.is_file():
            missing_segments.append(seg_id)
        elif path.stat().st_size < 20:
            empty_segments.append(seg_id)

    checks.append(CheckResult(
        id="segment_scripts",
        ok=not missing_segments and not empty_segments,
        severity="error" if missing_segments else "warn",
        message=(
            "all segment scripts present"
            if not missing_segments and not empty_segments
            else f"missing={missing_segments} empty={empty_segments}"
        ),
        details={"missing": missing_segments, "empty": empty_segments},
    ))

    for n, seg_dir in BEAT_SEGMENT_DIRS.items():
        path = project.segment_script(seg_dir)
        if path.is_file():
            continue
        checks.append(CheckResult(
            id=f"beat_{n}_script",
            ok=False,
            severity="error",
            message=f"missing script for beat {n} ({seg_dir})",
        ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(
        id="s04-knowledge",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
    )

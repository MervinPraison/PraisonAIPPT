"""validate-hook stage — hook montage display ↔ speech ↔ captions."""
from __future__ import annotations

import json
from typing import Callable

from ..project import SegmentVideoProject
from ..validation.hook_display import validate_hook_display


def run_validate_hook(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    if segments and "00-hook" not in segments:
        emit("validate-hook: skipped (not in segment list)")
        return 0

    protocol = project.load_protocol()
    report = validate_hook_display(project.root, protocol)
    out = project.root / "hook_validation_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    emit(f"validate-hook → {out} ({'PASS' if report['ok'] else 'FAIL'})")
    emit(
        f"  captions↔timeline: {s['caption_aligned']}/{s['cues']} | "
        f"image↔topic: {s['image_topic_ok']}/{s['cues']} | "
        f"speech timing: {s['speech_ok']}/{s['cues']} "
        f"(method: {report['timing_method']})"
    )
    for issue in report.get("issues") or []:
        emit(f"  - {issue}")
    return 0 if report.get("ok") else 1

"""validate-display stage — deep caption / slide / speech / catalogue audit."""
from __future__ import annotations

import json
from typing import Callable

from ..project import SegmentVideoProject
from ..validation.display_sync import validate_project_display
from ..validation.hook_display import validate_hook_display


def run_validate_display(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    protocol = project.load_protocol()
    fetch = bool((protocol.get("validation_suite") or {}).get("display_sync", {}).get("fetch_canonical", True))

    emit("validate-display: catalogue + caption/slide + speech overlap…")
    report = validate_project_display(project.root, protocol, fetch_canonical=fetch)

    # Always refresh hook sub-report
    hook = validate_hook_display(project.root, protocol)
    (project.root / "hook_validation_report.json").write_text(
        json.dumps(hook, indent=2) + "\n", encoding="utf-8",
    )
    report["hook"] = hook

    out = project.root / "display_validation_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    s = report["summary"]
    emit(f"validate-display → {out} ({'PASS' if report['ok'] else 'FAIL'})")
    emit(f"  catalogue: {report['catalogue']['summary']['total'] - report['catalogue']['summary']['failed']}/{report['catalogue']['summary']['total']} topics ok")
    emit(f"  segments: {s['segments_checked'] - s['segments_failed']}/{s['segments_checked']} ok")
    if hook:
        emit(f"  hook speech: {hook['summary'].get('speech_ok', 0)}/{hook['summary'].get('cues', 0)} cues")

    for seg in report.get("segments") or []:
        if seg.get("ok"):
            continue
        d = seg["dir"]
        for issue in (seg.get("caption_slides") or {}).get("issues") or []:
            emit(f"  [{d}] caption/slide: {issue}")
        for issue in (seg.get("speech_overlap") or {}).get("issues") or []:
            emit(f"  [{d}] speech: {issue}")

    for topic in report.get("catalogue", {}).get("topics") or []:
        if topic.get("ok"):
            continue
        emit(f"  [catalogue {topic['dir']}] " + "; ".join(topic.get("issues") or []))

    return 0 if report.get("ok") else 1

"""audit-images stage — transcript ↔ slide image fit report."""
from __future__ import annotations

import json
from typing import Callable

from ..image_audit import audit_project_images
from ..manifest import load_manifest
from ..project import SegmentVideoProject


def run_audit_images(
    project: SegmentVideoProject,
    *,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    manifest = load_manifest(project.root)
    protocol = project.load_protocol()
    report = audit_project_images(project.root, manifest, protocol)
    out = project.root / "image_audit_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    emit(f"image audit → {out} ({report['summary']['passed']}/{report['summary']['total']} ok)")

    for seg in report.get("segments") or []:
        if seg.get("skipped"):
            continue
        mark = "OK" if seg.get("ok") else "FAIL"
        emit(f"  [{mark}] {seg['dir']}: {len(seg.get('cues') or [])} cues, {len(seg.get('issues') or [])} issues")
        for item in seg.get("issues") or []:
            emit(f"    - {item}")

    return 1 if not report.get("ok") else 0

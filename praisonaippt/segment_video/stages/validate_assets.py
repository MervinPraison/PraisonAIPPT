"""Pipeline stage — validate handoff assets cover spoken content."""
from __future__ import annotations

import json
from typing import Callable

from ..project import SegmentVideoProject
from ..validation.required_assets import audit_required_assets


def run_validate_assets(
    project: SegmentVideoProject,
    *,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    protocol = project.load_protocol()
    cfg = (protocol.get("validation_suite") or {}).get("required_assets") or {}
    fetch = bool(cfg.get("fetch_canonical", True))
    strict = bool(cfg.get("strict", True))

    emit("validate-assets: auditing handoff vs speech…")
    report = audit_required_assets(project.root, protocol, fetch_canonical=fetch)
    out = project.root / "asset_gaps_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    ok_count = report["summary"]["total"] - report["summary"]["failed"]
    emit(f"validate-assets → {out} ({ok_count}/{report['summary']['total']} topics ok)")

    for row in report.get("topics") or []:
        if row.get("ok"):
            continue
        for gap in row.get("gaps") or []:
            if gap.get("type") == "manual_exempt":
                continue
            emit(f"  [{row['dir']}] {gap['type']}: {gap['detail']}")

    if strict and not report.get("ok"):
        return 1
    return 0

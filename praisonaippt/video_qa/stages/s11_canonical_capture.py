"""Stage s11 — canonical scroll capture quality (pre-assemble)."""
from __future__ import annotations

import json

from praisonaippt.daily_single.canonical_scroll import scroll_video_path
from praisonaippt.daily_single.page_capture_quality import (
    capture_report_path,
    saved_screenshot_path,
    validate_scroll_asset,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport


def run_s11_canonical_capture(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_assemble",
    ctx=None,
) -> StageReport:
    checks: list[CheckResult] = []
    try:
        beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        beat_map = {}
    if beat_map.get("variant") in ("trust-audit", "social-comparison", "combined"):
        checks.append(CheckResult(
            id="scroll_asset",
            ok=True,
            severity="info",
            message=f"canonical scroll not required for {beat_map.get('variant')} variant",
        ))
        return StageReport(
            id="s11-canonical-capture",
            ok=True,
            required=required,
            when=when,
            checks=checks,
        )

    scroll = scroll_video_path(project)
    if not scroll:
        checks.append(CheckResult(
            id="scroll_asset",
            ok=False,
            severity="error" if required else "warn",
            message="missing assets/videos/canonical-scroll.mp4 — run record-canonical-scroll",
        ))
        return StageReport(id="s11-canonical-capture", ok=False, required=required, when=when, checks=checks)

    ok, details = validate_scroll_asset(project, scroll)
    checks.append(CheckResult(
        id="scroll_asset",
        ok=ok,
        severity="error" if required else "warn",
        message="canonical scroll asset OK" if ok else "; ".join(details.get("issues") or [])[:200],
        details=details,
    ))

    cap_report = capture_report_path(project)
    shot = saved_screenshot_path(project)
    checks.append(CheckResult(
        id="capture_artefacts",
        ok=cap_report.is_file() and shot.is_file(),
        severity="error" if required else "warn",
        message="capture_report.json + page.png present" if cap_report.is_file() else "missing merge/qa/canonical_capture/",
    ))

    cap_ok = True
    if cap_report.is_file():
        cap_ok = bool(json.loads(cap_report.read_text(encoding="utf-8")).get("ok"))
        checks.append(CheckResult(
            id="capture_report",
            ok=cap_ok,
            severity="error" if required else "warn",
            message="capture marked OK" if cap_ok else "capture_report.json ok=false — re-run record-canonical-scroll",
        ))

    stage_ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(
        id="s11-canonical-capture",
        ok=stage_ok,
        required=required,
        when=when,
        checks=checks,
    )

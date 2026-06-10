"""Stage s01 — asset verification (pre-sync manifest + post-sync inventory)."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.media_sync import load_handoff_topic, validate_media_inventory
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def _beat_map_missing_paths(project: DailySingleProject) -> list[str]:
    if not project.beat_map_path.is_file():
        return []
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["beat-map unreadable"]
    missing: list[str] = []
    for beat_n, beat in (bm.get("beats") or {}).items():
        for key in ("generated", "images", "clips"):
            for item in beat.get(key) or []:
                path = Path(item.get("path") or project.assets_dir / (item.get("filename") or ""))
                if path.suffix and not path.is_file():
                    missing.append(f"beat {beat_n}: {path.name}")
    return missing[:12]


def run_s01_assets(
    project: DailySingleProject,
    *,
    phase: str = "post_sync",
    min_assets_per_beat: int = 1,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    if ctx is not None:
        min_assets_per_beat = ctx.min_coverage_assets()
    checks: list[CheckResult] = []

    if phase == "pre_sync":
        handoff = project.research_dir / "video-handoff.json"
        ok_handoff = handoff.is_file()
        checks.append(CheckResult(
            id="handoff_json",
            ok=ok_handoff,
            severity="error" if required else "warn",
            message="video-handoff.json present" if ok_handoff else "missing video-handoff.json",
            details={"path": str(handoff)},
        ))
        ok_beat = project.beat_map_path.is_file()
        checks.append(CheckResult(
            id="beat_map",
            ok=ok_beat,
            severity="error" if required else "warn",
            message="beat-map.json present" if ok_beat else "missing beat-map.json",
            details={"path": str(project.beat_map_path)},
        ))
        if ok_handoff:
            try:
                topic = load_handoff_topic(project)
                n_img = len(topic.get("images") or [])
                n_vid = len(topic.get("videos") or []) + len(topic.get("youtube") or [])
                checks.append(CheckResult(
                    id="handoff_pool",
                    ok=n_img + n_vid > 0,
                    severity="warn",
                    message=f"handoff lists {n_img} image(s), {n_vid} video(s)",
                    details={"images": n_img, "videos": n_vid},
                ))
            except OSError as exc:
                checks.append(CheckResult(
                    id="handoff_read",
                    ok=False,
                    severity="error",
                    message=f"cannot read handoff: {exc}",
                ))
        ok = all(c.ok or c.severity != "error" for c in checks)
        return StageReport(
            id="s01-assets",
            ok=ok,
            required=required,
            when=when,
            checks=checks,
            details={"phase": phase},
        )

    ok, inventory = validate_media_inventory(project)
    for issue in inventory.get("issues") or []:
        checks.append(CheckResult(
            id="inventory",
            ok=False,
            severity="error",
            message=issue,
        ))
    if ok:
        checks.append(CheckResult(
            id="inventory",
            ok=True,
            severity="info",
            message=(
                f"{len(inventory.get('images') or [])} images, "
                f"{len(inventory.get('videos') or [])} videos OK"
            ),
        ))
    bm_missing = _beat_map_missing_paths(project)
    if bm_missing:
        checks.append(CheckResult(
            id="beat_map_paths",
            ok=False,
            severity="warn",
            message=f"{len(bm_missing)} beat-map path(s) missing on disk",
            details={"missing": bm_missing},
        ))
    return StageReport(
        id="s01-assets",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"phase": phase, "inventory": inventory},
    )

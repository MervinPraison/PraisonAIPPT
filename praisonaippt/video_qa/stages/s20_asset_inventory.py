"""Stage s20 — per-asset frame inventory (one verification row per planned asset)."""
from __future__ import annotations

from praisonaippt.daily_single.asset_inventory_audit import validate_asset_inventory
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def run_s20_asset_inventory(
    project: DailySingleProject,
    *,
    required: bool = True,
    when: str = "pre_assemble",
    ctx: SuiteContext | None = None,
) -> StageReport:
    use_vision = True
    if ctx and ctx.degradation.get("vlm", {}).get("behaviour") == "pixel_only":
        use_vision = False
    report = validate_asset_inventory(project, export_frames=True, use_vision=use_vision)
    ok = bool(report.get("ok"))
    checks = [
        CheckResult(
            id="asset_inventory",
            ok=ok,
            severity="error" if required and not ok else ("warn" if not ok else "info"),
            message=(
                f"asset inventory OK ({report.get('assets_pass')}/{report.get('assets_total')} assets, "
                f"frames in {report.get('frame_dir')})"
                if ok
                else "; ".join(report.get("issues") or [])[:240]
            ),
        )
    ]
    return StageReport(
        id="s20-asset-inventory",
        ok=ok or not required,
        required=required,
        when=when,
        checks=checks,
        details=report,
    )

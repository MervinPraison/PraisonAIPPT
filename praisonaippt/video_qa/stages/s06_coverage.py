"""Stage s06 — transcript-to-asset coverage gaps."""
from __future__ import annotations

import json

from praisonaippt.daily_single.hook_montage import build_hook_montage_plan
from praisonaippt.daily_single.hook_validation import validate_hook_montage
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS, SEGMENT_ORDER
from praisonaippt.segment_video.image_selection import sentence_groups
from praisonaippt.segment_video.script_text import narration_text_for_tts
from praisonaippt.video_qa.base import CheckResult, StageReport
from praisonaippt.video_qa.context import SuiteContext


def _beat_assets(beat_map: dict, beat_n: int) -> int:
    beat = (beat_map.get("beats") or {}).get(str(beat_n)) or {}
    count = 0
    for key in ("generated", "images", "clips"):
        count += len(beat.get(key) or [])
    return count


def run_s06_coverage(
    project: DailySingleProject,
    *,
    phase: str = "post_scripts",
    min_assets_per_beat: int = 1,
    required: bool = True,
    when: str = "pre_build",
    ctx: SuiteContext | None = None,
) -> StageReport:
    checks: list[CheckResult] = []
    gaps: list[dict] = []

    beat_map: dict = {}
    if project.beat_map_path.is_file():
        try:
            beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    for seg_id, seg_folder, beat_n in SEGMENT_ORDER:
        if beat_n is not None:
            seg_dir = seg_folder or seg_id
            script_path = project.segment_script(seg_dir)
            if not script_path.is_file():
                gaps.append({"segment": seg_id, "type": "missing_script", "beat": beat_n})
                continue
            text = narration_text_for_tts(script_path.read_text(encoding="utf-8"))
            n_sent = len(sentence_groups(text))
            n_assets = _beat_assets(beat_map, beat_n)
            if n_assets < min_assets_per_beat:
                gaps.append({
                    "segment": seg_id,
                    "type": "beat_no_assets",
                    "beat": beat_n,
                    "sentences": n_sent,
                    "assets": n_assets,
                })
            elif n_sent > 4 and n_assets < 2 and phase == "post_sync":
                gaps.append({
                    "segment": seg_id,
                    "type": "sparse_assets",
                    "beat": beat_n,
                    "sentences": n_sent,
                    "assets": n_assets,
                })

    hook_script = project.segment_script("00-hook")
    if hook_script.is_file() and phase in ("post_scripts", "post_sync"):
        try:
            montage_ok, montage_report = validate_hook_montage(project)
            if not montage_ok:
                gaps.append({
                    "segment": "00-hook",
                    "type": "hook_montage_validation",
                    "issues": montage_report.get("issues") or [],
                })
        except (OSError, FileNotFoundError, KeyError):
            pass
        try:
            plan = build_hook_montage_plan(project)
            cues = plan.get("cues") or []
            if len(cues) < 5:
                gaps.append({
                    "segment": "00-hook",
                    "type": "hook_montage_short",
                    "cues": len(cues),
                    "min": 5,
                })
            unresolved = [c for c in cues if not c.get("ok")]
            if unresolved:
                gaps.append({
                    "segment": "00-hook",
                    "type": "hook_unresolved",
                    "count": len(unresolved),
                })
        except (OSError, ValueError, KeyError) as exc:
            gaps.append({"segment": "00-hook", "type": "hook_plan_error", "detail": str(exc)})

    beat5 = (beat_map.get("beats") or {}).get("5") or {}
    n_clips = len(beat5.get("clips") or [])
    if n_clips >= 2 and phase == "post_sync":
        script5 = project.segment_script(BEAT_SEGMENT_DIRS[5])
        if script5.is_file():
            n_sent = len(sentence_groups(narration_text_for_tts(script5.read_text(encoding="utf-8"))))
            if n_sent >= 2 and n_clips < n_sent:
                gaps.append({
                    "segment": "beat-05",
                    "type": "beat5_clip_shortfall",
                    "clips": n_clips,
                    "sentences": n_sent,
                })

    for gap in gaps:
        severity = "error" if gap["type"] in ("missing_script", "beat_no_assets", "hook_unresolved") else "warn"
        checks.append(CheckResult(
            id=f"gap_{gap['segment']}_{gap['type']}",
            ok=False,
            severity=severity if required else "warn",
            message=f"{gap['segment']}: {gap['type']}",
            details=gap,
        ))

    if not gaps:
        checks.append(CheckResult(
            id="coverage",
            ok=True,
            severity="info",
            message=f"coverage OK ({phase})",
        ))

    ok = all(c.ok or c.severity != "error" for c in checks)
    return StageReport(
        id="s06-coverage",
        ok=ok,
        required=required,
        when=when,
        checks=checks,
        details={"phase": phase, "gaps": gaps},
    )

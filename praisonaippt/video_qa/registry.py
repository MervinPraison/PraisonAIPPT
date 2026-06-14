"""QA stage registry."""
from __future__ import annotations

from typing import Any, Callable

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.base import StageReport
from praisonaippt.video_qa.context import SuiteContext
from praisonaippt.video_qa.stages.s00_bookends import run_s00_bookends
from praisonaippt.video_qa.stages.s01_assets import run_s01_assets
from praisonaippt.video_qa.stages.s02_source_vlm import run_s02_source_vlm
from praisonaippt.video_qa.stages.s03_image_speech import run_s03_image_speech
from praisonaippt.video_qa.stages.s04_knowledge import run_s04_knowledge
from praisonaippt.video_qa.stages.s05_transcript import run_s05_transcript
from praisonaippt.video_qa.stages.s06_coverage import run_s06_coverage
from praisonaippt.video_qa.stages.s07_framing import run_s07_framing
from praisonaippt.video_qa.stages.s08_av_sync import run_s08_av_sync
from praisonaippt.video_qa.stages.s09_on_screen_text import run_s09_on_screen_text
from praisonaippt.video_qa.stages.s10_final_composite import run_s10_final_composite
from praisonaippt.video_qa.stages.s11_canonical_capture import run_s11_canonical_capture
from praisonaippt.video_qa.stages.s12_hook_attention import run_s12_hook_attention
from praisonaippt.video_qa.stages.s13_slide_design import run_s13_slide_design
from praisonaippt.video_qa.stages.s14_engagement import run_s14_engagement
from praisonaippt.video_qa.stages.s15_viral_readiness import run_s15_viral_readiness
from praisonaippt.video_qa.stages.s16_montage_clock import run_s16_montage_clock
from praisonaippt.video_qa.stages.s17_cue_picture_map import run_s17_cue_picture_map
from praisonaippt.video_qa.stages.s18_video_first_policy import run_s18_video_first_policy
from praisonaippt.video_qa.stages.s19_chart_script import run_s19_chart_script
from praisonaippt.video_qa.stages.s20_asset_inventory import run_s20_asset_inventory
from praisonaippt.video_qa.stages.s21_beat_map_policy import run_s21_beat_map_policy
from praisonaippt.video_qa.stages.s22_word_visual_sync import run_s22_word_visual_sync
from praisonaippt.video_qa.stages.s23_clip_trim_range import run_s23_clip_trim_range
from praisonaippt.video_qa.stages.s24_resource_usefulness import run_s24_resource_usefulness

StageFn = Callable[..., StageReport]

STAGE_RUNNERS: dict[str, StageFn] = {
    "s00-bookends": run_s00_bookends,
    "s01-assets": run_s01_assets,
    "s02-source-vlm": run_s02_source_vlm,
    "s03-image-speech": run_s03_image_speech,
    "s04-knowledge": run_s04_knowledge,
    "s05-transcript": run_s05_transcript,
    "s06-coverage": run_s06_coverage,
    "s07-framing": run_s07_framing,
    "s08-av-sync": run_s08_av_sync,
    "s09-on-screen-text": run_s09_on_screen_text,
    "s10-final-composite": run_s10_final_composite,
    "s11-canonical-capture": run_s11_canonical_capture,
    "s12-hook-attention": run_s12_hook_attention,
    "s13-slide-design": run_s13_slide_design,
    "s14-engagement": run_s14_engagement,
    "s15-viral-readiness": run_s15_viral_readiness,
    "s16-montage-clock": run_s16_montage_clock,
    "s17-cue-picture-map": run_s17_cue_picture_map,
    "s18-video-first-policy": run_s18_video_first_policy,
    "s19-chart-script": run_s19_chart_script,
    "s20-asset-inventory": run_s20_asset_inventory,
    "s21-beat-map-policy": run_s21_beat_map_policy,
    "s22-word-visual-sync": run_s22_word_visual_sync,
    "s23-clip-trim-range": run_s23_clip_trim_range,
    "s24-resource-usefulness": run_s24_resource_usefulness,
}


def list_stages() -> list[str]:
    return sorted(STAGE_RUNNERS.keys())


def run_registered_stage(
    stage_id: str,
    project: DailySingleProject,
    stage_cfg: dict[str, Any],
    *,
    ctx: SuiteContext | None = None,
) -> StageReport:
    fn = STAGE_RUNNERS.get(stage_id)
    if fn is None:
        return StageReport(
            id=stage_id,
            ok=False,
            required=bool(stage_cfg.get("required", True)),
            when=str(stage_cfg.get("when", "all")),
            checks=[],
            details={"error": "unknown stage"},
        )

    kwargs: dict[str, Any] = {
        "required": bool(stage_cfg.get("required", True)),
        "when": str(stage_cfg.get("when", "all")),
        "ctx": ctx,
    }
    if stage_id == "s01-assets":
        kwargs["phase"] = stage_cfg.get("phase", "post_sync")
        if ctx:
            kwargs["min_assets_per_beat"] = ctx.min_coverage_assets()
    elif stage_id == "s06-coverage":
        kwargs["phase"] = stage_cfg.get("phase", "post_scripts")
        if ctx:
            kwargs["min_assets_per_beat"] = ctx.min_coverage_assets()
    elif stage_id == "s02-source-vlm":
        kwargs["interval_sec"] = float(stage_cfg.get("interval_sec", 5.0))
        kwargs["use_vision"] = bool(stage_cfg.get("use_vision", True))
    elif stage_id == "s03-image-speech":
        kwargs["phase"] = stage_cfg.get("phase", "post_render")
    elif stage_id == "s05-transcript":
        kwargs["phase"] = stage_cfg.get("phase", "post_vo")
        if ctx:
            kwargs["min_overlap"] = ctx.min_transcript_overlap()
    elif stage_id == "s08-av-sync" and ctx:
        kwargs["min_overlap"] = ctx.min_transcript_overlap()
    elif stage_id == "s10-final-composite":
        kwargs["sync_runs"] = int(stage_cfg.get("sync_runs", 3))
    elif stage_id == "s12-hook-attention":
        kwargs["seconds"] = int(stage_cfg.get("seconds", 5))
    elif stage_id == "s22-word-visual-sync":
        kwargs["use_vlm"] = bool(stage_cfg.get("use_vlm", True))

    return fn(project, **kwargs)

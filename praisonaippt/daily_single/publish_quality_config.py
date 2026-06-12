"""Thresholds for slide design, engagement, and viral-readiness gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import DEFAULT_PROTOCOL

DEFAULT_ENGAGEMENT: dict[str, Any] = {
    "motion_ratio_min": 0.25,
    "min_beats_with_clips": 2,
    "min_social_captures": 0,
    "text_slide_max_body_ratio": 0.55,
    "demo_beats": [4, 5],
    "min_proof_cues": 6,
    "min_comparison_beats": 1,
}

TRUST_AUDIT_ENGAGEMENT: dict[str, Any] = {
    "motion_ratio_min": 0.35,
    "min_beats_with_clips": 3,
    "min_social_captures": 2,
    "text_slide_max_body_ratio": 0.40,
    "demo_beats": [3, 4, 5],
    "min_proof_cues": 8,
    "min_comparison_beats": 2,
}

SOCIAL_COMPARISON_ENGAGEMENT: dict[str, Any] = {
    "motion_ratio_min": 0.40,
    "min_beats_with_clips": 4,
    "min_social_captures": 3,
    "text_slide_max_body_ratio": 0.45,
    "demo_beats": [1, 2, 3, 4, 5],
    "min_proof_cues": 6,
    "min_comparison_beats": 4,
}

DEFAULT_SLIDE_DESIGN: dict[str, Any] = {
    "text_slide_max_kb": 120,
    "text_slide_max_body_ratio": 0.55,
    "min_gpt_image_ratio": 0.25,
}

TRUST_AUDIT_SLIDE_DESIGN: dict[str, Any] = {
    "text_slide_max_kb": 120,
    "text_slide_max_body_ratio": 0.40,
    "min_gpt_image_ratio": 0.35,
}


def _load_protocol(project: DailySingleProject) -> dict[str, Any]:
    path = project.protocol_path
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return DEFAULT_PROTOCOL


def beat_map_variant(project: DailySingleProject) -> str:
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        return str(bm.get("variant") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def engagement_config(project: DailySingleProject) -> dict[str, Any]:
    proto = _load_protocol(project)
    block = proto.get("engagement_audit") or {}
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        bm = {}
    variant = str(bm.get("variant") or "")
    if bm.get("asset_policy") == "video-first-local":
        if variant == "social-comparison":
            return {
                **SOCIAL_COMPARISON_ENGAGEMENT,
                **(block.get("social_comparison") or block.get("video_first") or {}),
            }
        return {
            **TRUST_AUDIT_ENGAGEMENT,
            "min_social_captures": 1,
            **(block.get("video_first") or {}),
        }
    if variant == "social-comparison":
        return {**SOCIAL_COMPARISON_ENGAGEMENT, **(block.get("social_comparison") or {})}
    if variant == "trust-audit":
        return {**TRUST_AUDIT_ENGAGEMENT, **(block.get("trust_audit") or {})}
    return {**DEFAULT_ENGAGEMENT, **(block.get("default") or block)}


def slide_design_config(project: DailySingleProject) -> dict[str, Any]:
    proto = _load_protocol(project)
    block = proto.get("slide_design_audit") or {}
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        bm = {}
    if bm.get("asset_policy") == "video-first-local":
        return {
            **TRUST_AUDIT_SLIDE_DESIGN,
            "min_gpt_image_ratio": 0.0,
            "text_slide_max_body_ratio": 0.55,
            **(block.get("video_first") or {}),
        }
    if beat_map_variant(project) == "trust-audit":
        return {**TRUST_AUDIT_SLIDE_DESIGN, **(block.get("trust_audit") or {})}
    return {**DEFAULT_SLIDE_DESIGN, **(block.get("default") or block)}


def asset_tier(path: str, item: dict[str, Any] | None = None) -> str:
    """Classify visual asset for quality gates."""
    if item and item.get("asset_tier"):
        tier = str(item["asset_tier"])
        if tier == "social":
            return "social-capture"
        return tier
    p = Path(path)
    fn = p.name.lower()
    if fn.endswith(".mp4"):
        if fn.startswith("x-") or fn.startswith("linkedin-"):
            return "social-capture"
        return "motion"
    if "social-capture" in fn or fn.startswith("hn-") or fn.startswith("reddit-"):
        return "social-capture"
    if not p.is_file():
        return "missing"
    size_kb = p.stat().st_size / 1024
    if fn.startswith("beat") and "-point-" in fn:
        return "text_slide"
    if fn.startswith("v2-") and size_kb < 120:
        return "text_slide"
    if "/generated/beat" in path.replace("\\", "/") or (
        "generated" in path and fn.startswith("beat") and size_kb > 200
    ):
        return "gpt-image"
    if size_kb > 200 and fn.endswith(".png"):
        return "gpt-image"
    if any(m in fn for m in ("benchmark", "classifier", "chart", "alignment")):
        return "chart"
    return "png"


def is_social_capture_path(path: str) -> bool:
    fn = Path(path).name.lower()
    return (
        "social-capture" in fn
        or fn.startswith("hn-")
        or fn.startswith("reddit-")
        or fn.startswith("x-")
        or fn.startswith("youtube-")
        or fn.startswith("linkedin-")
        or "linkedin-cintas" in fn
    )


def requires_heygen_bookends(project: DailySingleProject) -> bool:
    """Video-first builds use montage + CTA slide instead of HeyGen bookends."""
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    return str(bm.get("asset_policy") or "") != "video-first-local"

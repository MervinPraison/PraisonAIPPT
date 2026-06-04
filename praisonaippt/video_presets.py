"""Shared video export presets (single source for compositor and post-render QC)."""

from __future__ import annotations

from typing import Any, Dict

VIDEO_PRESETS: Dict[str, Dict[str, int]] = {
    "draft": {"width": 1280, "height": 720, "fps": 24, "dpi": 120},
    "standard": {"width": 1920, "height": 1080, "fps": 30, "dpi": 192},
    "high": {"width": 1920, "height": 1080, "fps": 30, "dpi": 240},
    "4k": {"width": 3840, "height": 2160, "fps": 30, "dpi": 300},
}


def expected_video_spec(deck: dict) -> Dict[str, int]:
    """Resolve width/height/fps from ``video_export`` (mirrors :class:`VideoOptions`)."""
    vex = deck.get("video_export") or {}
    preset = str(vex.get("preset") or "standard")
    spec = dict(VIDEO_PRESETS.get(preset, VIDEO_PRESETS["standard"]))
    res = vex.get("resolution") or {}
    if isinstance(res, dict):
        if res.get("width"):
            spec["width"] = int(res["width"])
        if res.get("height"):
            spec["height"] = int(res["height"])
    if vex.get("fps"):
        spec["fps"] = int(vex["fps"])
    return spec

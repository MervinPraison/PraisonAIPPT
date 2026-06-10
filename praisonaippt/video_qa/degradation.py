"""Detect runtime degradation modes for QA stages."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject


def qa_offline_mode() -> bool:
    return os.environ.get("PRAISONAIPPT_QA_OFFLINE", "").lower() in ("1", "true", "yes")


def resolve_final_mp4(project: DailySingleProject) -> Path | None:
    for name in ("final.mp4", "final-with-audio.mp4", "final-silent.mp4"):
        path = project.merge_dir / name
        if path.is_file():
            return path
    return None


def detect_degradation(project: DailySingleProject) -> dict[str, Any]:
    """Return active degradation flags for merge/qa/summary.json."""
    flags: dict[str, Any] = {}

    if qa_offline_mode():
        flags["offline"] = True

    if not os.environ.get("OPENAI_API_KEY"):
        flags["vlm"] = "offline"

    if resolve_final_mp4(project) is None:
        flags["final_mp4"] = "missing"

    for label in ("00-hook", "99-outro"):
        heygen = project.segments_dir / label / "heygen.mp4"
        heygen_meta = project.segments_dir / label / "heygen_meta.json"
        if heygen_meta.is_file():
            try:
                import json

                meta = json.loads(heygen_meta.read_text(encoding="utf-8"))
                if meta.get("reused") or meta.get("stale"):
                    flags["heygen"] = "stale_reuse"
            except (OSError, ValueError):
                pass
        elif not heygen.is_file():
            flags.setdefault("heygen", "missing")

    return flags


def stage_should_skip(stage: dict[str, Any], degradation: dict[str, Any]) -> tuple[bool, str]:
    """Return (skip, reason) when degradation blocks a stage."""
    sid = stage.get("id", "")
    when = stage.get("when", "")

    if degradation.get("offline") and not stage.get("offline_ok", True):
        return True, "offline_mode"

    if degradation.get("vlm") == "offline" and sid == "s02-source-vlm":
        return True, "vlm_offline"

    if when == "post_build" and degradation.get("final_mp4") == "missing":
        if sid in ("s03-image-speech", "s07-framing", "s08-av-sync", "s09-on-screen-text", "s10-final-composite"):
            return True, "missing_final_mp4"

    return False, ""


def effective_required(stage: dict[str, Any], degradation: dict[str, Any]) -> bool:
    """Downgrade required stages when degradation policy says warn-only."""
    if not stage.get("required", True):
        return False
    if degradation.get("whisper") and stage.get("id") == "s05-transcript":
        phase = stage.get("phase", "")
        if phase == "post_captions":
            return True
    return True

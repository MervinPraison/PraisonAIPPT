from __future__ import annotations

from typing import Any


STAGE_ALIASES: dict[str, str] = {"script": "scripts"}


REGENERATE_CHAINS: dict[str, list[str]] = {
    "script": ["media", "align-cues", "yaml", "build", "validate-sync", "validate-visual", "merge"],
    "hero": ["catalogue-media", "sync-media", "validate-media", "align-cues", "yaml", "build", "validate-sync", "validate-visual", "merge"],
    "deck": ["build", "validate-sync", "validate-visual", "merge"],
    "merge_only": ["merge", "build-timeline"],
    "transitions": ["merge", "build-timeline"],
    "publish": ["publish"],
    "full_segment": [
        "catalogue-media", "sync-media", "validate-media", "media", "align-cues", "yaml", "build",
        "fix-jpegs", "seed-golden", "validate-sync", "validate-visual", "merge", "build-timeline",
    ],
    "audio": ["media", "align-cues", "yaml", "build", "validate-sync", "validate-visual", "merge"],
    "timing": ["align-cues", "yaml", "build", "validate-sync", "validate-visual", "merge"],
    "validate_only": ["validate-all"],
}


def resolve_stage_id(stage_id: str) -> str:
    return STAGE_ALIASES.get(stage_id, stage_id)


def stage_def(protocol: dict, stage_id: str) -> dict | None:
    stage_id = resolve_stage_id(stage_id)
    for st in protocol.get("stages", []):
        if st.get("id") == stage_id:
            return st
    return None


def stage_scope(protocol: dict, stage_id: str) -> str:
    st = stage_def(protocol, stage_id)
    return (st or {}).get("scope", "project")


def validate_deps(protocol: dict, stage_id: str) -> list[str]:
    st = stage_def(protocol, stage_id)
    if not st:
        return [f"unknown stage: {stage_id}"]
    missing = []
    for dep in st.get("depends_on", []):
        if not stage_def(protocol, dep):
            missing.append(f"stage {stage_id} depends on missing {dep}")
    return missing


def merge_transition_config(protocol: dict, *, no_transitions: bool = False) -> dict[str, Any]:
    if no_transitions:
        return {"default": "none", "duration_sec": 0.0}
    return dict(protocol.get("merge_transitions") or {"default": "crossfade", "duration_sec": 0.30})

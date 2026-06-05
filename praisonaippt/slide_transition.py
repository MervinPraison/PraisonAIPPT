"""Deck-side slide transition plan (parity with hero/avatar calibration hooks)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from .video_protocol import (
    ResolvedEdgeTransition,
    TransitionDefaults,
    parse_transition_defaults,
    resolve_edge_transitions,
)


@dataclass
class SlideTransitionConfig:
    enabled: bool = True
    default: str = "none"
    duration_sec: float = 0.30

    @classmethod
    def from_dict(cls, raw: Optional[dict]) -> "SlideTransitionConfig":
        raw = raw or {}
        if isinstance(raw, list):
            return cls()
        defs = parse_transition_defaults({"slide_transitions": raw})
        return cls(
            enabled=defs.enabled,
            default=defs.default,
            duration_sec=defs.duration_sec,
        )


def format_transition_report(
    edges: Sequence[ResolvedEdgeTransition],
    *,
    slide_count: int,
) -> str:
    lines = [f"Slide transition plan ({slide_count} slides, {len(edges)} edges):"]
    lines.append(f"{'After':>6}  {'Type':<14}  {'Dur(s)':>7}  Source")
    lines.append("-" * 44)
    for edge in edges:
        lines.append(
            f"{edge.after_slide:>6}  {edge.type:<14}  {edge.duration_sec:>7.3f}  {edge.source}"
        )
    return "\n".join(lines)


def maybe_apply_slide_transitions_deck(
    data: dict,
    entries: Optional[Sequence[Any]] = None,
    *,
    source_file: Optional[str] = None,
) -> dict:
    """Resolve edge transitions and store on ``_slide_transitions`` sidecar."""
    from .video_exporter import iter_slide_plan

    if entries is None:
        entries = list(iter_slide_plan(data))
    vex = data.get("video_export") or {}
    st = data.get("slide_transitions")
    defs = parse_transition_defaults(data, vex)
    edges = resolve_edge_transitions(entries, vex, st, defaults=defs)
    data["_slide_transitions"] = {
        "defaults": {
            "enabled": defs.enabled,
            "default": defs.default,
            "duration_sec": defs.duration_sec,
        },
        "edges": [
            {
                "after_slide": e.after_slide,
                "type": e.type,
                "duration_sec": e.duration_sec,
                "source": e.source,
            }
            for e in edges
        ],
        "report": format_transition_report(edges, slide_count=len(entries)),
    }
    if source_file:
        data["_slide_transitions"]["source_file"] = source_file
    return data

"""Shared anchor constants for hero text panels (single source of truth)."""

from __future__ import annotations

HERO_PANEL_ANCHORS = frozenset({
    "top_left", "top_right", "bottom_left", "bottom_right", "top", "bottom",
})

TEXT_PANEL_ANCHORS = HERO_PANEL_ANCHORS | {"auto"}

HERO_PANEL_ANCHOR_ORDER = (
    "top_left", "top_right", "bottom_left", "bottom_right", "top", "bottom",
)

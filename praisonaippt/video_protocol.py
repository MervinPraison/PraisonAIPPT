"""
Protocol-driven video overlay and slide-transition configuration.

Overlay precedence (later wins): deck ``video_export`` → ``slide_style.layouts`` →
verse flat keys → ``verse.video_overlay`` / ``video_export.overlay``.

Transition precedence (later wins): per-edge ``slide_transitions`` list → verse
``transition_out`` → ``slide_transitions`` defaults → ``video_export.transitions`` →
legacy ``transition_fade_sec`` → ``none``.

See ``docs/video-export.md`` and ``docs/slide-transitions.md``.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

logger = logging.getLogger(__name__)

TRANSITION_TYPES = frozenset({
    "none", "segment_fade", "crossfade",
    "wipeleft", "wiperight", "slideleft", "slideright",
})
BLEND_TRANSITION_TYPES = frozenset({
    "crossfade", "wipeleft", "wiperight", "slideleft", "slideright",
})
TRANSITION_ALIASES = {"fade": "segment_fade"}

TRANSITION_BLOCK_KEYS = frozenset({
    "enabled", "default", "duration_sec", "min_slide_sec", "max_fade_ratio", "edges",
})
EDGE_TRANSITION_KEYS = frozenset({"after_slide", "type", "duration_sec"})
VERSE_TRANSITION_KEYS = frozenset({"transition_out", "transition_duration_sec"})
VIDEO_EXPORT_TRANSITION_KEYS = frozenset({"default", "duration_sec"})

from .avatar_layouts import RegionBox, _pip_box_at

PIP_ANCHORS = frozenset({
    "bottom_right", "bottom_left", "top_right", "top_left", "center",
    "br", "bl", "tr", "tl",
})

OVERLAY_PLACEMENT_KEYS = frozenset({
    "anchor", "position", "pip_position",
    "width_ratio", "pip_width_ratio", "margin_in", "pip_margin_in",
    "left_in", "top_in", "width_in", "height_in", "box",
    "offset_px", "crop_x_ratio", "crop_y_ratio", "zoom_ratio", "fit", "shape",
})

VIDEO_OVERLAY_KEYS = frozenset({"avatar", "media", "offset_px"})

BOX_KEYS = frozenset({"left_in", "top_in", "width_in", "height_in"})


@dataclass
class OverlayPlacement:
    """Resolved placement + framing for one compositor layer (avatar or media)."""

    anchor: Optional[str] = None
    width_ratio: Optional[float] = None
    margin_in: Optional[float] = None
    left_in: Optional[float] = None
    top_in: Optional[float] = None
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    offset_px: Tuple[int, int] = (0, 0)
    crop_x_ratio: Optional[float] = None
    crop_y_ratio: Optional[float] = None
    zoom_ratio: Optional[float] = None
    fit: Optional[str] = None
    shape: Optional[str] = None

    def has_explicit_box(self) -> bool:
        return all(
            v is not None
            for v in (self.left_in, self.top_in, self.width_in, self.height_in)
        )

    def has_anchor_box(self) -> bool:
        return self.anchor is not None and self.width_ratio is not None


@dataclass
class ResolvedSlideOverlays:
    avatar: OverlayPlacement = field(default_factory=OverlayPlacement)
    media: OverlayPlacement = field(default_factory=OverlayPlacement)
    global_offset_px: Tuple[int, int] = (0, 0)


def _normalise_anchor(value: Any) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).lower().strip().replace("-", "_")
    aliases = {"br": "bottom_right", "bl": "bottom_left", "tr": "top_right", "tl": "top_left"}
    return aliases.get(raw, raw)


def parse_placement(raw: Any) -> OverlayPlacement:
    """Parse a YAML overlay block into :class:`OverlayPlacement`."""
    if not raw or not isinstance(raw, dict):
        return OverlayPlacement()
    p = OverlayPlacement()
    box = raw.get("box")
    if isinstance(box, dict):
        for key in BOX_KEYS:
            if box.get(key) is not None:
                setattr(p, key, float(box[key]))
    for key in BOX_KEYS:
        if raw.get(key) is not None:
            setattr(p, key, float(raw[key]))
    anchor = raw.get("anchor") or raw.get("position") or raw.get("pip_position")
    p.anchor = _normalise_anchor(anchor)
    if raw.get("width_ratio") is not None:
        p.width_ratio = float(raw["width_ratio"])
    elif raw.get("pip_width_ratio") is not None:
        p.width_ratio = float(raw["pip_width_ratio"])
    if raw.get("margin_in") is not None:
        p.margin_in = float(raw["margin_in"])
    elif raw.get("pip_margin_in") is not None:
        p.margin_in = float(raw["pip_margin_in"])
    off = raw.get("offset_px")
    if isinstance(off, dict):
        p.offset_px = (int(off.get("x", 0)), int(off.get("y", 0)))
    if raw.get("crop_x_ratio") is not None:
        p.crop_x_ratio = float(raw["crop_x_ratio"])
    if raw.get("crop_y_ratio") is not None:
        p.crop_y_ratio = float(raw["crop_y_ratio"])
    if raw.get("zoom_ratio") is not None:
        p.zoom_ratio = float(raw["zoom_ratio"])
    if raw.get("fit") is not None:
        p.fit = str(raw["fit"]).lower().strip()
    if raw.get("shape") is not None:
        p.shape = str(raw["shape"]).lower().strip()
    return p


def merge_placement(*layers: Optional[OverlayPlacement]) -> OverlayPlacement:
    """Merge placements; later layers override earlier non-None fields."""
    out = OverlayPlacement()
    for layer in layers:
        if not layer:
            continue
        for field_name in (
            "anchor", "width_ratio", "margin_in",
            "left_in", "top_in", "width_in", "height_in",
            "crop_x_ratio", "crop_y_ratio", "zoom_ratio", "fit", "shape",
        ):
            val = getattr(layer, field_name)
            if val is not None:
                setattr(out, field_name, val)
        if layer.offset_px != (0, 0):
            ox, oy = out.offset_px
            lx, ly = layer.offset_px
            out.offset_px = (ox + lx, oy + ly)
    return out


def placement_from_layout(style: dict, layout_kind: str) -> OverlayPlacement:
    """Map ``slide_style.layouts.<kind>`` pip fields to placement."""
    block = (style.get("layouts") or {}).get(layout_kind) or {}
    if not isinstance(block, dict):
        return OverlayPlacement()
    return parse_placement(block)


def placement_from_verse_flat(verse: dict, *, layer: str) -> OverlayPlacement:
    """Verse-level shortcuts: ``avatar_zoom_ratio``, ``media_fit``, etc."""
    if not verse:
        return OverlayPlacement()
    prefix = "avatar_" if layer == "avatar" else "media_"
    p = OverlayPlacement()
    if verse.get(f"{prefix}crop_x_ratio") is not None:
        p.crop_x_ratio = float(verse[f"{prefix}crop_x_ratio"])
    if verse.get(f"{prefix}crop_y_ratio") is not None:
        p.crop_y_ratio = float(verse[f"{prefix}crop_y_ratio"])
    if verse.get(f"{prefix}zoom_ratio") is not None:
        p.zoom_ratio = float(verse[f"{prefix}zoom_ratio"])
    if verse.get(f"{prefix}fit") is not None:
        p.fit = str(verse[f"{prefix}fit"])
    if layer == "avatar" and verse.get("avatar_shape") is not None:
        p.shape = str(verse["avatar_shape"])
    return p


def resolve_slide_overlays(
    *,
    verse: Optional[dict],
    slide_type: Optional[str],
    style: dict,
    video_export: dict,
    framing_kind: str,
) -> ResolvedSlideOverlays:
    """Build merged avatar/media overlay protocol for one manifest slide."""
    vex = video_export or {}
    vo = verse or {}
    global_off = (0, 0)
    overlay_root = vex.get("overlay")
    if isinstance(overlay_root, dict) and isinstance(overlay_root.get("offset_px"), dict):
        g = overlay_root["offset_px"]
        global_off = (int(g.get("x", 0)), int(g.get("y", 0)))

    verse_overlay = vo.get("video_overlay") or {}
    if not isinstance(verse_overlay, dict):
        verse_overlay = {}

    def _layers(layer: str) -> OverlayPlacement:
        deck_block = vex.get(layer) if isinstance(vex.get(layer), dict) else {}
        return merge_placement(
            parse_placement(deck_block),
            placement_from_layout(style, "pip"),
            placement_from_layout(style, framing_kind),
            placement_from_verse_flat(vo, layer=layer),
            parse_placement(verse_overlay.get(layer)),
        )

    avatar = _layers("avatar")
    media = _layers("media")
    if isinstance(verse_overlay.get("offset_px"), dict):
        o = verse_overlay["offset_px"]
        avatar.offset_px = (
            avatar.offset_px[0] + int(o.get("x", 0)),
            avatar.offset_px[1] + int(o.get("y", 0)),
        )
        media.offset_px = avatar.offset_px

    return ResolvedSlideOverlays(
        avatar=avatar, media=media, global_offset_px=global_off,
    )


def region_from_placement(
    base: Optional[RegionBox],
    placement: OverlayPlacement,
    slide_w_in: float,
    slide_h_in: float,
    style: dict,
    layout_kind: str,
) -> Optional[RegionBox]:
    """Apply protocol box/anchor on top of layout-exported region."""
    if placement.has_explicit_box():
        return RegionBox(
            placement.left_in, placement.top_in,
            placement.width_in, placement.height_in,
        )
    if placement.has_anchor_box():
        anchor = placement.anchor or "bottom_right"
        ratio = placement.width_ratio or 0.2
        margin = placement.margin_in if placement.margin_in is not None else 0.38
        kind_style = dict(style)
        layouts = dict(kind_style.get("layouts") or {})
        block = dict(layouts.get(layout_kind) or {})
        block["pip_width_ratio"] = ratio
        block["pip_margin_in"] = margin
        block["pip_position"] = anchor
        layouts[layout_kind] = block
        kind_style["layouts"] = layouts
        return _pip_box_at(0, 0, slide_w_in, slide_h_in, kind_style, layout_kind, anchor)
    return base


def apply_pixel_offset(box_px: Optional[dict], offset: Tuple[int, int]) -> Optional[dict]:
    if not box_px or offset == (0, 0):
        return box_px
    ox, oy = offset
    return {
        "x": int(box_px["x"]) + ox,
        "y": int(box_px["y"]) + oy,
        "width": int(box_px["width"]),
        "height": int(box_px["height"]),
    }


def resolve_framing(
    placement: OverlayPlacement,
    style: dict,
    layout_kind: str,
    *,
    default_crop: float,
    default_zoom: float,
    default_fit: str,
    default_shape: str,
) -> Tuple[float, float, float, str, str]:
    """Return crop_x, crop_y, zoom, fit, shape with protocol + layout fallbacks."""
    from .avatar_layouts import avatar_framing

    crop_x, crop_y, zoom = avatar_framing(style, layout_kind)
    if placement.crop_x_ratio is not None:
        crop_x = float(placement.crop_x_ratio)
    if placement.crop_y_ratio is not None:
        crop_y = float(placement.crop_y_ratio)
    if placement.zoom_ratio is not None:
        zoom = max(1.0, float(placement.zoom_ratio))
    fit = placement.fit or default_fit
    shape = placement.shape or default_shape
    return crop_x, crop_y, zoom, fit, shape


def validate_overlay_placement(raw: Any, path: str) -> None:
    """Validate one overlay placement mapping (raises :class:`SchemaError`)."""
    from .exceptions import SchemaError
    from .yaml_validate import _AVATAR_FIT, _AVATAR_SHAPES, _check_enum, _check_positive_number

    if raw is None:
        return
    if not isinstance(raw, dict):
        raise SchemaError(f"{path} must be a mapping")
    allowed = OVERLAY_PLACEMENT_KEYS | {"box"}
    for key in raw:
        if key not in allowed:
            from .yaml_validate import _warn_unknown
            _warn_unknown([key], allowed, path)
    anchor = raw.get("anchor") or raw.get("position") or raw.get("pip_position")
    if anchor is not None:
        norm = _normalise_anchor(anchor)
        if norm not in PIP_ANCHORS:
            opts = ", ".join(sorted(PIP_ANCHORS))
            raise SchemaError(f"{path}.anchor must be one of: {opts} (got {anchor!r})")
    for ratio_key in ("width_ratio", "pip_width_ratio"):
        if raw.get(ratio_key) is not None:
            val = float(raw[ratio_key])
            if val <= 0 or val > 1:
                raise SchemaError(f"{path}.{ratio_key} must be between 0 and 1, got {val}")
    for inch_key in ("left_in", "top_in", "width_in", "height_in", "margin_in", "pip_margin_in"):
        if raw.get(inch_key) is not None:
            _check_positive_number(raw[inch_key], f"{path}.{inch_key}", allow_zero=True)
    box = raw.get("box")
    if box is not None:
        if not isinstance(box, dict):
            raise SchemaError(f"{path}.box must be a mapping")
        for bk in box:
            if bk not in BOX_KEYS:
                raise SchemaError(f"{path}.box: unknown key {bk!r}")
            _check_positive_number(box[bk], f"{path}.box.{bk}", allow_zero=True)
    if raw.get("crop_x_ratio") is not None:
        val = float(raw["crop_x_ratio"])
        if val < 0.2 or val > 0.8:
            raise SchemaError(f"{path}.crop_x_ratio must be between 0.2 and 0.8, got {val}")
    if raw.get("crop_y_ratio") is not None:
        val = float(raw["crop_y_ratio"])
        if val < 0 or val > 0.45:
            raise SchemaError(f"{path}.crop_y_ratio must be between 0 and 0.45, got {val}")
    if raw.get("zoom_ratio") is not None:
        val = float(raw["zoom_ratio"])
        if val < 0.5 or val > 3.0:
            raise SchemaError(f"{path}.zoom_ratio must be between 0.5 and 3.0, got {val}")
    _check_enum(raw.get("fit"), _AVATAR_FIT, f"{path}.fit")
    _check_enum(raw.get("shape"), _AVATAR_SHAPES, f"{path}.shape")
    off = raw.get("offset_px")
    if off is not None:
        if not isinstance(off, dict):
            raise SchemaError(f"{path}.offset_px must be {{x, y}} integers")
        for axis in ("x", "y"):
            if off.get(axis) is not None and not isinstance(off[axis], int):
                try:
                    int(off[axis])
                except (TypeError, ValueError):
                    raise SchemaError(f"{path}.offset_px.{axis} must be an integer")


def validate_video_overlay_block(raw: Any, path: str) -> None:
    from .exceptions import SchemaError

    if raw is None:
        return
    block = raw if isinstance(raw, dict) else None
    if block is None:
        raise SchemaError(f"{path} must be a mapping")
    for key in block:
        if key not in VIDEO_OVERLAY_KEYS:
            from .yaml_validate import _warn_unknown
            _warn_unknown([key], VIDEO_OVERLAY_KEYS, path)
    if block.get("avatar") is not None:
        validate_overlay_placement(block["avatar"], f"{path}.avatar")
    if block.get("media") is not None:
        validate_overlay_placement(block["media"], f"{path}.media")
    if block.get("offset_px") is not None:
        validate_overlay_placement({"offset_px": block["offset_px"]}, path)


# ---------------------------------------------------------------------------
# Slide transitions (protocol)
# ---------------------------------------------------------------------------


@dataclass
class TransitionDefaults:
    """Global transition defaults from YAML."""

    enabled: bool = True
    default: str = "none"
    duration_sec: float = 0.30
    min_slide_sec: float = 0.5
    max_fade_ratio: float = 0.25
    legacy_fade_sec: float = 0.0

    def is_active(self) -> bool:
        return self.enabled and (
            self.default != "none"
            or self.legacy_fade_sec > 0
        )


@dataclass
class ResolvedEdgeTransition:
    """One transition leaving slide *after_slide* (1-based) → next slide."""

    after_slide: int
    type: str = "none"
    duration_sec: float = 0.0
    source: str = "default"

    def is_blend(self) -> bool:
        return self.type in BLEND_TRANSITION_TYPES

    def is_segment_fade(self) -> bool:
        return self.type == "segment_fade"


@dataclass
class VideoComposePlan:
    """Resolved slide list plus *n-1* edge transitions."""

    entries: list
    edges: List[ResolvedEdgeTransition] = field(default_factory=list)


def normalise_transition_type(value: Any, *, path: str = "") -> str:
    """Map YAML type strings to canonical names; warn on deprecated aliases."""
    if value is None:
        return "none"
    raw = str(value).lower().strip().replace("-", "_")
    if raw in TRANSITION_ALIASES:
        canonical = TRANSITION_ALIASES[raw]
        if raw == "fade":
            warnings.warn(
                f"{path or 'transition'} type 'fade' is deprecated; use 'segment_fade'",
                DeprecationWarning,
                stacklevel=2,
            )
        return canonical
    return raw


def _float_or(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_transition_defaults(
    data: Optional[dict],
    video_export: Optional[dict] = None,
) -> TransitionDefaults:
    """Merge ``slide_transitions`` block and ``video_export.transitions``."""
    data = data or {}
    vex = video_export or data.get("video_export") or {}
    out = TransitionDefaults()
    ve_tr = vex.get("transitions") if isinstance(vex.get("transitions"), dict) else {}
    st_raw = data.get("slide_transitions")
    st_cfg: dict = {}
    if isinstance(st_raw, dict):
        st_cfg = st_raw
    if ve_tr:
        if ve_tr.get("default") is not None:
            out.default = normalise_transition_type(ve_tr["default"], path="video_export.transitions")
        if ve_tr.get("duration_sec") is not None:
            out.duration_sec = max(0.0, _float_or(ve_tr["duration_sec"], out.duration_sec))
    if st_cfg:
        if st_cfg.get("enabled") is not None:
            out.enabled = bool(st_cfg["enabled"])
        if st_cfg.get("default") is not None:
            out.default = normalise_transition_type(st_cfg["default"], path="slide_transitions")
        if st_cfg.get("duration_sec") is not None:
            out.duration_sec = max(0.0, _float_or(st_cfg["duration_sec"], out.duration_sec))
        if st_cfg.get("min_slide_sec") is not None:
            out.min_slide_sec = max(0.1, _float_or(st_cfg["min_slide_sec"], out.min_slide_sec))
        if st_cfg.get("max_fade_ratio") is not None:
            out.max_fade_ratio = max(0.01, min(1.0, _float_or(st_cfg["max_fade_ratio"], out.max_fade_ratio)))
    if vex.get("transition_fade_sec") is not None:
        legacy = max(0.0, _float_or(vex["transition_fade_sec"], 0.0))
        if legacy > 0:
            out.legacy_fade_sec = legacy
            if out.default == "none" and not st_cfg.get("default") and not ve_tr.get("default"):
                out.default = "segment_fade"
                out.duration_sec = legacy
                warnings.warn(
                    "video_export.transition_fade_sec is deprecated; use "
                    "video_export.transitions or slide_transitions",
                    DeprecationWarning,
                    stacklevel=2,
                )
    return out


def parse_edge_transition_list(raw: Any) -> List[dict]:
    """Extract per-edge overrides from list or ``slide_transitions.edges``."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [e for e in raw if isinstance(e, dict) and e.get("after_slide") is not None]
    if isinstance(raw, dict):
        edges = raw.get("edges")
        if isinstance(edges, list):
            return [e for e in edges if isinstance(e, dict) and e.get("after_slide") is not None]
    return []


def clamp_transition_duration(
    duration_sec: float,
    slide_duration_sec: float,
    defaults: TransitionDefaults,
) -> float:
    """Single clamp policy shared by segment fade and xfade (matches render_slide_segment)."""
    dur = max(0.0, float(duration_sec))
    slide_dur = max(0.1, float(slide_duration_sec))
    if dur <= 0 or slide_dur < defaults.min_slide_sec:
        return 0.0
    max_by_ratio = slide_dur * defaults.max_fade_ratio
    capped = min(dur, max_by_ratio)
    if slide_dur > capped * 2.5:
        capped = min(capped, slide_dur / 4.0)
    else:
        return 0.0
    return max(0.0, capped)


def _verse_for_plan_entry(entry: Any) -> Optional[dict]:
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("verse") if "verse" in entry else entry
    return getattr(entry, "verse", None)


def _slide_duration_for_edge(entries: Sequence[Any], after_slide: int) -> float:
    idx = after_slide - 1
    if idx < 0 or idx >= len(entries):
        return 5.0
    entry = entries[idx]
    if isinstance(entry, dict):
        return float(entry.get("duration_sec") or 5.0)
    return float(getattr(entry, "duration_sec", None) or 5.0)


def resolve_edge_transitions(
    entries: Sequence[Any],
    video_export: Optional[dict] = None,
    slide_transitions: Any = None,
    *,
    defaults: Optional[TransitionDefaults] = None,
) -> List[ResolvedEdgeTransition]:
    """Resolve *n-1* edges for *n* slides. Precedence: edge list > verse > global > legacy."""
    n = len(entries)
    if n <= 1:
        return []
    vex = video_export or {}
    defs = defaults or parse_transition_defaults({"slide_transitions": slide_transitions}, vex)
    edge_overrides: Dict[int, dict] = {}
    for item in parse_edge_transition_list(slide_transitions):
        try:
            after = int(item["after_slide"])
        except (TypeError, ValueError):
            continue
        if 1 <= after < n:
            edge_overrides[after] = item

    edges: List[ResolvedEdgeTransition] = []
    for i in range(1, n):
        verse = _verse_for_plan_entry(entries[i - 1])
        slide_dur = _slide_duration_for_edge(entries, i)
        resolved = ResolvedEdgeTransition(after_slide=i, source="default")

        if not defs.enabled:
            resolved.type = "none"
            resolved.duration_sec = 0.0
        elif i in edge_overrides:
            ov = edge_overrides[i]
            resolved.type = normalise_transition_type(
                ov.get("type", defs.default), path=f"slide_transitions[{i}]",
            )
            resolved.duration_sec = _float_or(
                ov.get("duration_sec", defs.duration_sec), defs.duration_sec,
            )
            resolved.source = "edge"
        elif verse and verse.get("transition_out") is not None:
            resolved.type = normalise_transition_type(
                verse["transition_out"], path=f"verse[{i}].transition_out",
            )
            resolved.duration_sec = _float_or(
                verse.get("transition_duration_sec", defs.duration_sec), defs.duration_sec,
            )
            resolved.source = "verse"
        elif defs.default != "none":
            resolved.type = defs.default
            resolved.duration_sec = defs.duration_sec
            resolved.source = "global"
        elif defs.legacy_fade_sec > 0:
            resolved.type = "segment_fade"
            resolved.duration_sec = defs.legacy_fade_sec
            resolved.source = "legacy"
        else:
            resolved.type = "none"
            resolved.duration_sec = 0.0

        if resolved.type == "none":
            resolved.duration_sec = 0.0
        else:
            clamped = clamp_transition_duration(resolved.duration_sec, slide_dur, defs)
            if clamped <= 0:
                resolved.type = "none"
                resolved.duration_sec = 0.0
                resolved.source = f"{resolved.source}:clamped"
            else:
                resolved.duration_sec = clamped

        edges.append(resolved)
    return edges


def segment_fade_sec_for_slide(
    slide_index: int,
    edges: Sequence[ResolvedEdgeTransition],
) -> float:
    """Symmetric segment fade duration for slide *slide_index* (0-based)."""
    if slide_index < len(edges) and edges[slide_index].is_blend():
        return 0.0
    fade = 0.0
    if slide_index < len(edges) and edges[slide_index].is_segment_fade():
        fade = max(fade, edges[slide_index].duration_sec)
    if slide_index > 0 and slide_index - 1 < len(edges):
        prev = edges[slide_index - 1]
        if prev.is_segment_fade():
            fade = max(fade, prev.duration_sec)
    return fade


def effective_timeline_sec(
    entries: Sequence[Any],
    edges: Sequence[ResolvedEdgeTransition],
) -> List[float]:
    """Start time (seconds) for each slide; accounts for xfade overlap."""
    times: List[float] = []
    t = 0.0
    for i, entry in enumerate(entries):
        times.append(t)
        if isinstance(entry, dict):
            dur = float(entry.get("duration_sec") or 5.0)
        else:
            dur = float(getattr(entry, "duration_sec", None) or 5.0)
        if i < len(edges) and edges[i].is_blend():
            t += dur - edges[i].duration_sec
        else:
            t += dur
    return times


def total_output_duration_sec(
    entries: Sequence[Any],
    edges: Sequence[ResolvedEdgeTransition],
) -> float:
    """Total MP4 length after transitions."""
    starts = effective_timeline_sec(entries, edges)
    if not entries:
        return 0.0
    last = len(entries) - 1
    if isinstance(entries[last], dict):
        last_dur = float(entries[last].get("duration_sec") or 5.0)
    else:
        last_dur = float(getattr(entries[last], "duration_sec", None) or 5.0)
    return starts[last] + last_dur


def any_blend_edges(edges: Sequence[ResolvedEdgeTransition]) -> bool:
    return any(e.is_blend() for e in edges)


def validate_transition_type(value: Any, path: str) -> None:
    from .exceptions import SchemaError
    from .transition_backends import known_transition_types

    if value is None:
        return
    norm = normalise_transition_type(value, path=path)
    allowed = known_transition_types()
    if norm not in allowed:
        opts = ", ".join(sorted(allowed))
        raise SchemaError(f"{path} must be one of: {opts} (got {value!r})")


def validate_transition_defaults(raw: Any, path: str = "slide_transitions") -> None:
    from .exceptions import SchemaError
    from .yaml_validate import _check_bool, _check_positive_number, _warn_unknown

    if raw is None:
        return
    if isinstance(raw, list):
        for i, item in enumerate(raw):
            validate_edge_transition_entry(item, f"{path}[{i}]")
        return
    block = raw if isinstance(raw, dict) else None
    if block is None:
        raise SchemaError(f"{path} must be a mapping or list of edge overrides")
    _warn_unknown(block.keys(), TRANSITION_BLOCK_KEYS, path)
    if block.get("enabled") is not None:
        _check_bool(block["enabled"], f"{path}.enabled")
    validate_transition_type(block.get("default"), f"{path}.default")
    if block.get("duration_sec") is not None:
        _check_positive_number(block["duration_sec"], f"{path}.duration_sec", allow_zero=True)
    if block.get("min_slide_sec") is not None:
        _check_positive_number(block["min_slide_sec"], f"{path}.min_slide_sec")
    if block.get("max_fade_ratio") is not None:
        val = float(block["max_fade_ratio"])
        if val <= 0 or val > 1:
            raise SchemaError(f"{path}.max_fade_ratio must be between 0 and 1")
    edges = block.get("edges")
    if edges is not None:
        if not isinstance(edges, list):
            raise SchemaError(f"{path}.edges must be a list")
        for i, item in enumerate(edges):
            validate_edge_transition_entry(item, f"{path}.edges[{i}]")


def validate_edge_transition_entry(raw: Any, path: str) -> None:
    from .exceptions import SchemaError
    from .yaml_validate import _check_positive_number, _warn_unknown

    if raw is None:
        return
    if not isinstance(raw, dict):
        raise SchemaError(f"{path} must be a mapping")
    _warn_unknown(raw.keys(), EDGE_TRANSITION_KEYS, path)
    if raw.get("after_slide") is None:
        raise SchemaError(f"{path}.after_slide is required")
    try:
        after = int(raw["after_slide"])
    except (TypeError, ValueError):
        raise SchemaError(f"{path}.after_slide must be an integer")
    if after < 1:
        raise SchemaError(f"{path}.after_slide must be >= 1")
    validate_transition_type(raw.get("type"), f"{path}.type")
    if raw.get("duration_sec") is not None:
        _check_positive_number(raw["duration_sec"], f"{path}.duration_sec", allow_zero=True)


def validate_verse_transition_keys(verse: dict, path: str) -> None:
    from .yaml_validate import _check_positive_number

    if verse.get("transition_out") is not None:
        validate_transition_type(verse["transition_out"], f"{path}.transition_out")
    if verse.get("transition_duration_sec") is not None:
        _check_positive_number(
            verse["transition_duration_sec"], f"{path}.transition_duration_sec", allow_zero=True,
        )


def validate_video_export_transitions(raw: Any, path: str = "video_export.transitions") -> None:
    from .exceptions import SchemaError
    from .yaml_validate import _check_positive_number, _warn_unknown

    if raw is None:
        return
    if not isinstance(raw, dict):
        raise SchemaError(f"{path} must be a mapping")
    _warn_unknown(raw.keys(), VIDEO_EXPORT_TRANSITION_KEYS, path)
    validate_transition_type(raw.get("default"), f"{path}.default")
    if raw.get("duration_sec") is not None:
        _check_positive_number(raw["duration_sec"], f"{path}.duration_sec", allow_zero=True)

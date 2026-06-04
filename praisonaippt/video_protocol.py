"""
Protocol-driven video overlay configuration.

Precedence (later wins): deck ``video_export`` → ``slide_style.layouts`` → verse
flat keys → ``verse.video_overlay`` / ``video_export.overlay``.

See ``docs/video-export.md`` for the YAML schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

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
            placement_from_layout(style, framing_kind),
            placement_from_layout(style, "pip"),
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

"""Validate deck YAML/JSON against documented slide_style, layouts, and video_export options."""

from __future__ import annotations

import difflib
from typing import Any, Dict, Iterable, Optional, Set

from .exceptions import SchemaError
from .layout_tokens import LAYOUT_DEFAULTS, TYPOGRAPHY_DEFAULTS

# Re-export for tests
__all__ = [
    "validate_deck_options",
    "validate_verse_options",
    "validate_slide_style",
    "validate_video_export",
    "validate_slide_size",
    "validate_pipeline",
    "validate_avatar_calibration",
    "ALLOWED_LAYOUT_KINDS",
]

_ALIGNMENT = frozenset({"left", "center", "right"})
_REFERENCE_POSITION = frozenset({"bottom", "below", "top"})
_LIST_TYPE = frozenset({"bullet", "numbered"})
_IMAGE_FIT = frozenset({"contain", "cover", "fill"})
_IMAGE_SIDE = frozenset({"left", "right"})
_NARRATION_MODE = frozenset({"fixed", "audio_file", "avatar", "tts", "auto"})
_AUDIO_SOURCE = frozenset({
    "heygen_video", "heygen", "video", "external", "separate", "mp3", "tts",
})
_SYNC_MODE = frozenset({"avatar_lead", "notes_lead", "longest"})
_AVATAR_TIMELINE = frozenset({"per_slide", "continuous", "auto"})
_VIDEO_BACKEND = frozenset({"compositor", "auto", "powerpoint", "aspose_frames"})
_VIDEO_PRESET = frozenset({"draft", "standard", "high", "4k"})
_AVATAR_FIT = frozenset({"cover", "stretch", "contain"})
_PIP_SHAPES = frozenset({
    "circle", "round", "rounded", "square", "rect", "rectangle",
})
_AVATAR_SHAPES = frozenset({
    "auto", "circle", "round", "rounded", "square", "rect", "rectangle",
    "h_rect", "horizontal", "wide", "v_rect", "vertical", "tall",
})
_SLIDE_SIZE_PRESETS = frozenset({"widescreen", "16:9", "standard", "4:3", "16:10"})

_VIDEO_EXPORT_KEYS = frozenset({
    "backend", "narration_mode", "audio_source", "output_path", "preset", "resolution",
    "fps", "dpi", "slide_duration_sec", "avatar_timeline", "avatar",
    "media", "overlay", "tts", "captions", "slide_cache",
})
_VIDEO_AVATAR_KEYS = frozenset({
    "fit", "shape", "crop_x_ratio", "crop_y_ratio", "zoom_ratio", "loop_if_shorter",
    "anchor", "position", "pip_position", "width_ratio", "pip_width_ratio",
    "margin_in", "pip_margin_in", "left_in", "top_in", "width_in", "height_in",
    "box", "offset_px",
})
_VIDEO_MEDIA_KEYS = _VIDEO_AVATAR_KEYS - {"loop_if_shorter", "shape"}
_VIDEO_OVERLAY_ROOT_KEYS = frozenset({"offset_px"})
_VERSE_VIDEO_FLAT_KEYS = frozenset({
    "video_overlay", "avatar_crop_x_ratio", "avatar_crop_y_ratio", "avatar_zoom_ratio", "avatar_fit",
    "media_crop_y_ratio", "media_zoom_ratio", "media_fit",
})
_VIDEO_TTS_KEYS = frozenset({"provider", "voice"})
_VIDEO_CAPTIONS_KEYS = frozenset({"enabled"})
_VIDEO_RESOLUTION_KEYS = frozenset({"width", "height"})

_PIPELINE_KEYS = frozenset({
    "content_master", "transcript_path", "auto_sync", "validate_pip", "strict_pip",
    "variant_prefix", "golden_slide_dir", "export_mp4_frames", "mp4_frames_dir",
    "validate_slide_qa", "require_rights_ack", "rights_acknowledged",
    "content_approved", "plan_approved", "plan_draft",
    "export_mp4", "export_slide_jpegs", "post_render_qc", "strict_post_render",
    "fail_fast", "validate_plan", "validate_rights", "seed_timing", "report_path",
})
_CALIBRATION_METHODS = frozenset({"hybrid", "balance", "mediapipe", "fixed", "yolo"})
_CALIBRATION_DETECTORS = frozenset({"auto", "mediapipe", "yunet", "yolo"})
_AVATAR_CALIBRATION_KEYS = frozenset({
    "auto", "method", "crop_x_preferred", "crop_x_window", "crop_y_preferred",
    "anchor_weight", "detector", "min_detection_confidence", "crop_x_step", "force",
})

_SLIDE_STYLE_BASE_KEYS = frozenset({
    "background_image", "background_color", "text_color", "reference_color",
    "title_color", "subtitle_color", "section_title_color", "highlight_color",
    "annotation_color", "font_name", "alignment", "reference_position",
    "split_max_length", "avatar_pip", "layouts", "typography", "preset",
    "overrides", "color_scheme",
})

# Keys used by deck colour presets (allowed on slide_style without warning).
def _deck_style_colour_keys() -> Set[str]:
    from .deck_slides import DECK_COLOR_PRESETS

    keys: Set[str] = set()
    for preset in DECK_COLOR_PRESETS.values():
        keys.update(preset.keys())
    return keys


def _layout_keys_for_kind(kind: str) -> Set[str]:
    base = set(LAYOUT_DEFAULTS.get(kind, {}).keys())
    extra = _LAYOUT_EXTRA_KEYS.get(kind, frozenset())
    shared = _LAYOUT_SHARED_KEYS
    return base | extra | shared


_LAYOUT_SHARED_KEYS = frozenset({"content_width_in", "color_scheme", "avatar_shape"})
_LAYOUT_EXTRA_KEYS: Dict[str, frozenset] = {
    "table": frozenset({
        "header_fill", "header_text", "row_fill", "row_alt_fill", "body_text",
    }),
    "pip": frozenset({"position", "pip_shape", "avatar_shape"}),
    "avatar_headline": frozenset({"pip_position", "pip_shape"}),
    "avatar_headline_full": frozenset({"pip_shape"}),
    "avatar_media_3": frozenset({
        "pip_position", "pip_shape", "hero_layout", "text_style", "text_anchor",
        "text_pip_gap_in",
    }),
    "avatar_name_card": frozenset({"pip_shape"}),
    "avatar_quote": frozenset({"pip_position", "pip_shape"}),
    "avatar_media_border_3": frozenset({"pip_position", "pip_shape"}),
}

ALLOWED_LAYOUT_KINDS: frozenset = frozenset(LAYOUT_DEFAULTS.keys())


def _warn_unknown(actual: Iterable[str], allowed: Set[str], where: str) -> None:
    import logging

    logger = logging.getLogger("praisonaippt.schema")
    for key in actual:
        if key in allowed or str(key).startswith("x-"):
            continue
        suggestion = difflib.get_close_matches(key, allowed, n=1)
        hint = f" (did you mean '{suggestion[0]}'?)" if suggestion else ""
        logger.warning("Unknown key %r in %s%s", key, where, hint)


def _require_mapping(value: Any, path: str) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SchemaError(f"{path} must be a mapping")
    return value


def _check_enum(value: Any, allowed: frozenset, path: str) -> None:
    if value is None:
        return
    normalised = str(value).lower().strip()
    if normalised not in allowed:
        opts = ", ".join(sorted(allowed))
        raise SchemaError(f"{path} must be one of: {opts} (got {value!r})")


def _check_positive_number(value: Any, path: str, *, allow_zero: bool = False) -> None:
    if value is None:
        return
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise SchemaError(f"{path} must be a number, got {type(value).__name__}")
    if allow_zero and num < 0:
        raise SchemaError(f"{path} must be >= 0, got {num}")
    if not allow_zero and num <= 0:
        raise SchemaError(f"{path} must be > 0, got {num}")


def _check_bool(value: Any, path: str) -> None:
    if value is None:
        return
    if not isinstance(value, bool):
        raise SchemaError(f"{path} must be a boolean, got {type(value).__name__}")


def validate_slide_size(slide_size: Any, path: str = "slide_size") -> None:
    if slide_size is None:
        return
    if isinstance(slide_size, str):
        if slide_size.lower() not in _SLIDE_SIZE_PRESETS:
            opts = ", ".join(sorted(_SLIDE_SIZE_PRESETS))
            raise SchemaError(
                f"{path} preset must be one of: {opts}, or use {{width, height}} in inches"
            )
        return
    if isinstance(slide_size, dict):
        for key in slide_size:
            if key not in ("width", "height"):
                raise SchemaError(f"{path}: unknown key {key!r} (use 'width' and 'height' in inches)")
        return
    raise SchemaError(f"{path} must be a preset string or {{width, height}} mapping")


def validate_slide_style(slide_style: Any, path: str = "slide_style") -> None:
    style = _require_mapping(slide_style, path)
    if not style:
        return

    allowed_top = _SLIDE_STYLE_BASE_KEYS | _deck_style_colour_keys()
    _warn_unknown(style.keys(), allowed_top, path)

    _check_enum(style.get("alignment"), _ALIGNMENT, f"{path}.alignment")
    _check_enum(style.get("reference_position"), _REFERENCE_POSITION, f"{path}.reference_position")

    if style.get("split_max_length") is not None:
        try:
            n = int(style["split_max_length"])
        except (TypeError, ValueError):
            raise SchemaError(f"{path}.split_max_length must be an integer")
        if n < 50:
            raise SchemaError(f"{path}.split_max_length must be at least 50")

    _check_bool(style.get("avatar_pip"), f"{path}.avatar_pip")

    preset = style.get("color_scheme")
    if preset is not None:
        from .deck_slides import DECK_COLOR_PRESETS

        if str(preset) not in DECK_COLOR_PRESETS:
            opts = ", ".join(sorted(DECK_COLOR_PRESETS.keys()))
            raise SchemaError(f"{path}.color_scheme must be one of: {opts}")

    typography = style.get("typography")
    if typography is not None:
        typo = _require_mapping(typography, f"{path}.typography")
        _warn_unknown(typo.keys(), set(TYPOGRAPHY_DEFAULTS.keys()), f"{path}.typography")
        for key, val in typo.items():
            if val is not None:
                _check_positive_number(val, f"{path}.typography.{key}")

    layouts = style.get("layouts")
    if layouts is not None:
        blocks = _require_mapping(layouts, f"{path}.layouts")
        for kind, block in blocks.items():
            if kind not in ALLOWED_LAYOUT_KINDS:
                close = difflib.get_close_matches(kind, ALLOWED_LAYOUT_KINDS, n=1)
                hint = f" (did you mean '{close[0]}'?)" if close else ""
                import logging
                logging.getLogger("praisonaippt.schema").warning(
                    "Unknown layout kind %r in %s.layouts%s", kind, path, hint,
                )
                continue
            if block is None:
                continue
            blk = _require_mapping(block, f"{path}.layouts.{kind}")
            allowed_keys = _layout_keys_for_kind(kind)
            _warn_unknown(blk.keys(), allowed_keys, f"{path}.layouts.{kind}")
            if blk.get("avatar_shape") is not None:
                _check_enum(blk["avatar_shape"], _AVATAR_SHAPES, f"{path}.layouts.{kind}.avatar_shape")
            if kind == "pip":
                _check_enum(blk.get("shape"), _PIP_SHAPES, f"{path}.layouts.pip.shape")
                _check_enum(blk.get("pip_shape"), _PIP_SHAPES, f"{path}.layouts.pip.pip_shape")
            anchor = blk.get("pip_position") or blk.get("position")
            if anchor is not None:
                from .video_protocol import PIP_ANCHORS, _normalise_anchor

                norm = _normalise_anchor(anchor)
                if norm not in PIP_ANCHORS:
                    opts = ", ".join(sorted(PIP_ANCHORS))
                    raise SchemaError(
                        f"{path}.layouts.{kind}.pip_position must be one of: {opts} (got {anchor!r})"
                    )
            for ratio_key in ("pip_width_ratio", "width_ratio"):
                if blk.get(ratio_key) is not None:
                    val = float(blk[ratio_key])
                    if val <= 0 or val > 1:
                        raise SchemaError(
                            f"{path}.layouts.{kind}.{ratio_key} must be between 0 and 1, got {val}"
                        )
            if blk.get("crop_x_ratio") is not None:
                val = float(blk["crop_x_ratio"])
                if val < 0.2 or val > 0.8:
                    raise SchemaError(
                        f"{path}.layouts.{kind}.crop_x_ratio must be between 0.2 and 0.8, got {val}"
                    )
            if blk.get("crop_y_ratio") is not None:
                val = float(blk["crop_y_ratio"])
                if val < 0 or val > 0.45:
                    raise SchemaError(
                        f"{path}.layouts.{kind}.crop_y_ratio must be between 0 and 0.45, got {val}"
                    )
            if blk.get("zoom_ratio") is not None:
                val = float(blk["zoom_ratio"])
                if val < 0.5 or val > 3.0:
                    raise SchemaError(
                        f"{path}.layouts.{kind}.zoom_ratio must be between 0.5 and 3.0, got {val}"
                    )


def validate_video_export(video_export: Any, path: str = "video_export") -> None:
    raw = _require_mapping(video_export, path)
    if not raw:
        return

    _warn_unknown(raw.keys(), _VIDEO_EXPORT_KEYS, path)

    if raw.get("backend") is not None:
        _check_enum(raw["backend"], _VIDEO_BACKEND, f"{path}.backend")

    _check_enum(raw.get("narration_mode"), _NARRATION_MODE, f"{path}.narration_mode")
    _check_enum(raw.get("audio_source"), _AUDIO_SOURCE, f"{path}.audio_source")
    _check_enum(raw.get("preset"), _VIDEO_PRESET, f"{path}.preset")
    _check_enum(raw.get("avatar_timeline"), _AVATAR_TIMELINE, f"{path}.avatar_timeline")

    _check_positive_number(raw.get("slide_duration_sec"), f"{path}.slide_duration_sec")
    if raw.get("fps") is not None:
        _check_positive_number(raw["fps"], f"{path}.fps")
    if raw.get("dpi") is not None:
        _check_positive_number(raw["dpi"], f"{path}.dpi")

    res = raw.get("resolution")
    if res is not None:
        res_map = _require_mapping(res, f"{path}.resolution")
        _warn_unknown(res_map.keys(), _VIDEO_RESOLUTION_KEYS, f"{path}.resolution")
        if res_map.get("width") is not None:
            _check_positive_number(res_map["width"], f"{path}.resolution.width")
        if res_map.get("height") is not None:
            _check_positive_number(res_map["height"], f"{path}.resolution.height")

    from .video_protocol import validate_overlay_placement, validate_video_overlay_block

    avatar = raw.get("avatar")
    if avatar is not None:
        av = _require_mapping(avatar, f"{path}.avatar")
        _warn_unknown(av.keys(), _VIDEO_AVATAR_KEYS, f"{path}.avatar")
        validate_overlay_placement(av, f"{path}.avatar")
        _check_enum(av.get("fit"), _AVATAR_FIT, f"{path}.avatar.fit")
        _check_enum(av.get("shape"), _AVATAR_SHAPES, f"{path}.avatar.shape")
        if av.get("loop_if_shorter") is not None:
            _check_bool(av["loop_if_shorter"], f"{path}.avatar.loop_if_shorter")

    media = raw.get("media")
    if media is not None:
        md = _require_mapping(media, f"{path}.media")
        _warn_unknown(md.keys(), _VIDEO_MEDIA_KEYS, f"{path}.media")
        validate_overlay_placement(md, f"{path}.media")
        _check_enum(md.get("fit"), _AVATAR_FIT, f"{path}.media.fit")

    overlay = raw.get("overlay")
    if overlay is not None:
        ov = _require_mapping(overlay, f"{path}.overlay")
        _warn_unknown(ov.keys(), _VIDEO_OVERLAY_ROOT_KEYS, f"{path}.overlay")
        validate_video_overlay_block(overlay, f"{path}.overlay")

    tts = raw.get("tts")
    if tts is not None:
        tts_map = _require_mapping(tts, f"{path}.tts")
        _warn_unknown(tts_map.keys(), _VIDEO_TTS_KEYS, f"{path}.tts")

    caps = raw.get("captions")
    if caps is not None:
        caps_map = _require_mapping(caps, f"{path}.captions")
        _warn_unknown(caps_map.keys(), _VIDEO_CAPTIONS_KEYS, f"{path}.captions")
        if caps_map.get("enabled") is not None:
            _check_bool(caps_map["enabled"], f"{path}.captions.enabled")

    if raw.get("slide_cache") is not None:
        _check_bool(raw["slide_cache"], f"{path}.slide_cache")


def validate_slide_timestamps(timestamps: Any, path: str = "slide_timestamps") -> None:
    if timestamps is None:
        return
    if not isinstance(timestamps, list):
        raise SchemaError(f"{path} must be a list of numbers (seconds)")
    prev = -1.0
    for i, ts in enumerate(timestamps):
        try:
            val = float(ts)
        except (TypeError, ValueError):
            raise SchemaError(f"{path}[{i}] must be a number, got {type(ts).__name__}")
        if val < 0:
            raise SchemaError(f"{path}[{i}] must be >= 0, got {val}")
        if val < prev:
            import logging
            logging.getLogger("praisonaippt.schema").warning(
                "%s[%d] (%.3f) is before %s[%d] (%.3f); video timing may be wrong",
                path, i, val, path, i - 1, prev,
            )
        prev = val


def _validate_qa_block(qa: Any, path: str) -> None:
    if qa is None:
        return
    if not isinstance(qa, dict):
        raise SchemaError(f"{path} must be a mapping")
    for key in ("expect_pip", "expect_media"):
        if qa.get(key) is not None:
            _check_bool(qa[key], f"{path}.{key}")
    if qa.get("min_media_width_ratio") is not None:
        try:
            ratio = float(qa["min_media_width_ratio"])
        except (TypeError, ValueError):
            raise SchemaError(f"{path}.min_media_width_ratio must be a number")
        if ratio < 0.0 or ratio > 1.0:
            raise SchemaError(f"{path}.min_media_width_ratio must be between 0 and 1")
    if qa.get("min_hero_coverage_ratio") is not None:
        try:
            ratio = float(qa["min_hero_coverage_ratio"])
        except (TypeError, ValueError):
            raise SchemaError(f"{path}.min_hero_coverage_ratio must be a number")
        if ratio < 0.0 or ratio > 1.0:
            raise SchemaError(f"{path}.min_hero_coverage_ratio must be between 0 and 1")


_TEXT_PANEL_ANCHORS = frozenset({
    "top_left", "top_right", "bottom_left", "bottom_right", "top", "bottom",
})


def _validate_text_panel(tp: Any, path: str) -> None:
    if tp is None:
        return
    if not isinstance(tp, dict):
        raise SchemaError(f"{path} must be a mapping")
    anchor = tp.get("anchor")
    if anchor is not None and str(anchor).lower().strip() not in _TEXT_PANEL_ANCHORS:
        raise SchemaError(f"{path}.anchor must be one of: {', '.join(sorted(_TEXT_PANEL_ANCHORS))}")
    for key in ("width_ratio", "height_in", "margin_in", "max_width_ratio"):
        if tp.get(key) is not None:
            _check_positive_number(tp[key], f"{path}.{key}", allow_zero=False)
    style = tp.get("style")
    if style is not None and str(style).lower().strip() not in {"navy_panel", "overlay", "semi_panel"}:
        raise SchemaError(f"{path}.style must be navy_panel, overlay, or semi_panel")
    layout = tp.get("hero_layout")
    if layout is not None and str(layout).lower().strip() not in {"stacked", "full_bleed"}:
        raise SchemaError(f"{path}.hero_layout must be stacked or full_bleed")


def validate_verse_options(verse: dict, path: str) -> None:
    """Enum and shape checks shared by all verse types (after renderer-specific rules)."""
    _check_enum(verse.get("alignment"), _ALIGNMENT, f"{path}.alignment")
    _check_enum(verse.get("reference_position"), _REFERENCE_POSITION, f"{path}.reference_position")
    _check_enum(verse.get("list_type"), _LIST_TYPE, f"{path}.list_type")
    _check_enum(verse.get("image_fit"), _IMAGE_FIT, f"{path}.image_fit")
    _check_enum(verse.get("media_fit"), _IMAGE_FIT, f"{path}.media_fit")
    _check_enum(verse.get("image_side"), _IMAGE_SIDE, f"{path}.image_side")
    _check_enum(verse.get("narration_mode"), _NARRATION_MODE, f"{path}.narration_mode")
    _check_enum(verse.get("sync_mode"), _SYNC_MODE, f"{path}.sync_mode")

    if verse.get("header_row") is not None:
        _check_bool(verse["header_row"], f"{path}.header_row")

    for key in ("font_size", "reference_font_size"):
        if verse.get(key) is not None:
            try:
                n = int(verse[key])
            except (TypeError, ValueError):
                raise SchemaError(f"{path}.{key} must be an integer")
            if n < 8 or n > 200:
                raise SchemaError(f"{path}.{key} must be between 8 and 200")

    if verse.get("split_max_length") is not None:
        try:
            n = int(verse["split_max_length"])
        except (TypeError, ValueError):
            raise SchemaError(f"{path}.split_max_length must be an integer")
        if n < 50:
            raise SchemaError(f"{path}.split_max_length must be at least 50")

    _check_positive_number(verse.get("duration_sec"), f"{path}.duration_sec", allow_zero=True)
    _check_positive_number(verse.get("audio_start_sec"), f"{path}.audio_start_sec", allow_zero=True)

    _validate_qa_block(verse.get("qa"), f"{path}.qa")
    _validate_text_panel(verse.get("text_panel"), f"{path}.text_panel")

    if verse.get("avatar_shape") is not None:
        _check_enum(verse["avatar_shape"], _AVATAR_SHAPES, f"{path}.avatar_shape")

    from .video_protocol import validate_overlay_placement, validate_video_overlay_block

    for flat_key in ("avatar_crop_x_ratio",):
        if verse.get(flat_key) is not None:
            val = float(verse[flat_key])
            if val < 0.2 or val > 0.8:
                raise SchemaError(f"{path}.{flat_key} must be between 0.2 and 0.8, got {val}")
    for flat_key in ("avatar_crop_y_ratio", "media_crop_y_ratio"):
        if verse.get(flat_key) is not None:
            val = float(verse[flat_key])
            if val < 0 or val > 0.45:
                raise SchemaError(f"{path}.{flat_key} must be between 0 and 0.45, got {val}")
    for flat_key in ("avatar_zoom_ratio", "media_zoom_ratio"):
        if verse.get(flat_key) is not None:
            val = float(verse[flat_key])
            if val < 0.5 or val > 3.0:
                raise SchemaError(f"{path}.{flat_key} must be between 0.5 and 3.0, got {val}")
    _check_enum(verse.get("avatar_fit"), _AVATAR_FIT, f"{path}.avatar_fit")
    if verse.get("video_overlay") is not None:
        validate_video_overlay_block(verse["video_overlay"], f"{path}.video_overlay")

    preset = verse.get("color_scheme")
    if preset is not None:
        from .deck_slides import DECK_COLOR_PRESETS

        if str(preset) not in DECK_COLOR_PRESETS:
            opts = ", ".join(sorted(DECK_COLOR_PRESETS.keys()))
            raise SchemaError(f"{path}.color_scheme must be one of: {opts}")

    slide_type = verse.get("slide_type")
    if slide_type == "table":
        _validate_table_rows(verse, path)


def _validate_table_rows(verse: dict, path: str) -> None:
    raw = verse.get("table_rows") or verse.get("rows")
    if raw is None:
        return
    if not isinstance(raw, list) or not raw:
        raise SchemaError(f"{path} table_rows must be a non-empty list")
    for r_idx, row in enumerate(raw):
        if isinstance(row, list):
            if not row:
                raise SchemaError(f"{path} table_rows[{r_idx}] must not be empty")
            continue
        if isinstance(row, dict):
            continue
        raise SchemaError(
            f"{path} table_rows[{r_idx}] must be a list of cells or a mapping"
        )


def validate_pipeline(pipe: Any) -> None:
    """Validate optional ``pipeline`` block (CI gates and orchestration)."""
    if pipe is None:
        return
    raw = _require_mapping(pipe, "pipeline")
    _warn_unknown(raw.keys(), _PIPELINE_KEYS, "pipeline")
    for key in (
        "auto_sync", "validate_pip", "strict_pip", "require_rights_ack",
        "rights_acknowledged", "content_approved", "plan_approved",
        "export_mp4", "export_slide_jpegs", "post_render_qc", "strict_post_render",
        "fail_fast", "validate_plan", "validate_rights", "seed_timing",
    ):
        if key in raw and not isinstance(raw[key], bool):
            raise SchemaError(f"pipeline.{key} must be a boolean")
    for key in ("content_master", "transcript_path", "variant_prefix", "golden_slide_dir", "plan_draft", "report_path"):
        if key in raw and raw[key] is not None and not isinstance(raw[key], str):
            raise SchemaError(f"pipeline.{key} must be a string")


def validate_avatar_calibration(ac: Any) -> None:
    """Validate optional ``avatar_calibration`` block."""
    if ac is None:
        return
    raw = _require_mapping(ac, "avatar_calibration")
    _warn_unknown(raw.keys(), _AVATAR_CALIBRATION_KEYS, "avatar_calibration")
    for key in ("auto", "force"):
        if key in raw and not isinstance(raw[key], bool):
            raise SchemaError(f"avatar_calibration.{key} must be a boolean")
    if "method" in raw:
        method = str(raw["method"]).lower()
        if method not in _CALIBRATION_METHODS:
            opts = ", ".join(sorted(_CALIBRATION_METHODS))
            raise SchemaError(f"avatar_calibration.method must be one of: {opts}")
    if "detector" in raw:
        det = str(raw["detector"]).lower()
        if det not in _CALIBRATION_DETECTORS:
            opts = ", ".join(sorted(_CALIBRATION_DETECTORS))
            raise SchemaError(f"avatar_calibration.detector must be one of: {opts}")
    window = raw.get("crop_x_window")
    if window is not None:
        if not isinstance(window, (list, tuple)) or len(window) < 2:
            raise SchemaError("avatar_calibration.crop_x_window must be [lo, hi]")
        lo, hi = float(window[0]), float(window[1])
        if lo >= hi:
            raise SchemaError("avatar_calibration.crop_x_window: lo must be < hi")


def validate_deck_options(data: dict) -> None:
    """Validate top-level deck options documented in the layout / video guides."""
    validate_slide_size(data.get("slide_size"))
    validate_slide_style(data.get("slide_style"))
    validate_video_export(data.get("video_export"))
    validate_slide_timestamps(data.get("slide_timestamps"))
    validate_pipeline(data.get("pipeline"))
    validate_avatar_calibration(data.get("avatar_calibration"))
    _validate_slide_timestamp_count(data)
    _validate_qa_block(data.get("slide_qa"), "slide_qa")
    if data.get("slide_images_dir") is not None and not isinstance(data.get("slide_images_dir"), str):
        raise SchemaError("slide_images_dir must be a string path")
    if data.get("jpeg_show_pip_preview") is not None:
        _check_bool(data["jpeg_show_pip_preview"], "jpeg_show_pip_preview")


def _validate_slide_timestamp_count(data: dict) -> None:
    """Warn when ``slide_timestamps`` length does not match the slide plan."""
    ts = data.get("slide_timestamps")
    if not ts or not isinstance(ts, list):
        return
    try:
        from .video_exporter import iter_slide_plan

        plan_len = len(list(iter_slide_plan(data)))
    except Exception:
        return
    if len(ts) not in (plan_len, plan_len + 1):
        import logging

        logging.getLogger("praisonaippt.schema").warning(
            "slide_timestamps has %d entries but the slide plan has %d slides "
            "(expected %d or %d boundaries); durations may drift unless every verse sets duration_sec",
            len(ts),
            plan_len,
            plan_len,
            plan_len + 1,
        )

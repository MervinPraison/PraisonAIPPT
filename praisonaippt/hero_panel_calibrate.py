"""Automatic hero text-panel anchor placement from screenshot text regions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pptx import Presentation
from pptx.util import Inches

from .avatar_layouts import (
    RegionBox,
    _hero_layout_mode,
    _verse_text_panel_cfg,
    export_slide_regions,
    region_box_to_pixels,
)
from .layout_tokens import layout_in
from .text_panel_anchors import HERO_PANEL_ANCHOR_ORDER, HERO_PANEL_ANCHORS
from .text_region_detect import TextRegion, detect_text_regions
from .utils import resolve_asset_path

_CACHE_VERSION = 2
_SLIDE_OUT_W = 1920
_SLIDE_OUT_H = 1080
_WIDESCREEN_IN = (13.33, 7.5)
_SLIDE_SIZE_PRESETS = {
    "widescreen": (13.33, 7.5),
    "16:9": (13.33, 7.5),
    "standard": (10.0, 7.5),
    "4:3": (10.0, 7.5),
    "16:10": (13.33, 8.33),
}

_OVERLAP_REJECT = 0.15
_IOA_POWER = 1.8


@dataclass
class HeroTextConfig:
    """Runtime options from ``hero_text_placement`` YAML block."""

    auto: bool = False
    method: str = "hybrid"
    detector: str = "auto"
    min_confidence: float = 0.55
    fallback_anchor: str = "top_left"
    preferred_anchor: str = "top_right"
    pad_hard_px: float = 20.0
    pad_soft_px: float = 8.0
    vision_fallback: bool = False
    force: bool = False
    anchor_weight: float = 0.15

    @classmethod
    def from_dict(cls, raw: Optional[dict], *, style: Optional[dict] = None) -> "HeroTextConfig":
        raw = raw or {}
        style = style or {}
        hero = ((style.get("layouts") or {}).get("avatar_media_3") or {})
        fallback = raw.get("fallback_anchor") or hero.get("text_anchor") or "top_left"
        preferred = raw.get("preferred_anchor") or hero.get("text_anchor") or "top_right"
        return cls(
            auto=bool(raw.get("auto", False)),
            method=str(raw.get("method", "hybrid")).lower(),
            detector=str(raw.get("detector", "auto")).lower(),
            min_confidence=float(raw.get("min_confidence", 0.55)),
            fallback_anchor=str(fallback).lower().strip(),
            preferred_anchor=str(preferred).lower().strip(),
            pad_hard_px=float(raw.get("pad_hard_px", 20)),
            pad_soft_px=float(raw.get("pad_soft_px", 8)),
            vision_fallback=bool(raw.get("vision_fallback", False)),
            force=bool(raw.get("force", False)),
            anchor_weight=float(raw.get("anchor_weight", 0.15)),
        )

    def cache_key_part(self, *, style: Optional[dict] = None) -> str:
        return (
            f"v{_CACHE_VERSION}:{self.method}:{self.detector}:{self.min_confidence}:"
            f"{self.preferred_anchor}:{self.fallback_anchor}:{self.pad_hard_px}:"
            f"{self.pad_soft_px}:{self.anchor_weight}:{self.vision_fallback}:"
            f"{_layout_cache_part(style)}"
        )


@dataclass
class HeroPanelResult:
    """Chosen anchor for one hero slide."""

    media_path: str
    anchor: str
    score: float
    confidence: float
    detector: str
    region_count: int = 0
    method: str = "hybrid"
    alternates: List[str] = field(default_factory=list)
    version: int = _CACHE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _effective_detector(cfg: HeroTextConfig) -> str:
    if cfg.method == "vision":
        return "vision"
    if cfg.method in ("paddle", "rapidocr", "east", "mser", "heuristic"):
        return cfg.method if cfg.method != "heuristic" else "mser"
    return cfg.detector


def _layout_cache_part(style: Optional[dict]) -> str:
    layouts = (style or {}).get("layouts") or {}
    hero = layouts.get("avatar_media_3") or {}
    pip = layouts.get("pip") or {}
    parts = []
    for key in (
        "pip_width_ratio", "pip_margin_in", "pip_position", "panel_width_ratio",
        "panel_margin_in", "panel_height_in", "text_pip_gap_in", "hero_layout", "text_anchor",
    ):
        val = hero.get(key, pip.get(key))
        if val is not None:
            parts.append(f"{key}={val}")
    return "|".join(parts) or "default"


def _slide_dims_in(data: dict) -> Tuple[float, float]:
    size = data.get("slide_size")
    if isinstance(size, dict):
        return float(size.get("width", 13.33)), float(size.get("height", 7.5))
    key = str(size or "widescreen").lower()
    return _SLIDE_SIZE_PRESETS.get(key, _WIDESCREEN_IN)


def calibration_presentation(data: dict) -> Presentation:
    """Presentation sized to deck ``slide_size`` for panel/PiP geometry."""
    w_in, h_in = _slide_dims_in(data)
    prs = Presentation()
    prs.slide_width = Inches(w_in)
    prs.slide_height = Inches(h_in)
    return prs


def _pip_rect_norm(pip: Dict[str, int]) -> dict:
    return {
        "x": pip["x"] / _SLIDE_OUT_W,
        "y": pip["y"] / _SLIDE_OUT_H,
        "w": pip["width"] / _SLIDE_OUT_W,
        "h": pip["height"] / _SLIDE_OUT_H,
    }


def _try_vision_anchor(
    path: Path,
    verse: dict,
    pip: Dict[str, int],
    *,
    prs: Presentation,
    style: dict,
    obstacles: Sequence[Tuple[int, int, int, int]],
    cfg: HeroTextConfig,
    regions: Sequence[TextRegion],
    ranked: Optional[List[Tuple[str, float]]] = None,
) -> Optional[HeroPanelResult]:
    from .vision_suggest import suggest_panel_anchor

    suggestion = suggest_panel_anchor(
        path, str(verse.get("headline") or ""), _pip_rect_norm(pip),
    )
    if not suggestion or suggestion.get("anchor") not in HERO_PANEL_ANCHORS:
        return None
    vis_anchor = suggestion["anchor"]
    panel = _panel_px(prs, style, verse, vis_anchor)
    sc = score_anchor(panel, obstacles, pip, anchor=vis_anchor, cfg=cfg)
    if sc is None and ranked is None:
        return HeroPanelResult(
            media_path=str(verse.get("media_path") or ""),
            anchor=vis_anchor,
            score=0.5,
            confidence=float(suggestion.get("confidence") or 0.5),
            detector="vision",
            region_count=len(regions),
            method="vision",
            alternates=list(suggestion.get("alternates") or []),
        )
    if sc is None:
        return None
    return HeroPanelResult(
        media_path=str(verse.get("media_path") or ""),
        anchor=vis_anchor,
        score=sc,
        confidence=float(suggestion.get("confidence") or 0.6),
        detector="vision",
        region_count=len(regions),
        method="vision+offline",
        alternates=[a for a, _ in (ranked or [])[:3]],
    )


def _image_size(path: Path) -> Tuple[int, int]:
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def map_regions_to_slide_px(
    regions: Sequence[TextRegion],
    *,
    img_w: int,
    img_h: int,
    slide_w_in: float,
    slide_h_in: float,
    media_fit: str,
) -> List[Tuple[int, int, int, int]]:
    """Map image-normalised regions to slide output pixels (1920×1080 space)."""
    sw, sh = _SLIDE_OUT_W, _SLIDE_OUT_H
    fit = (media_fit or "contain").lower()
    if fit not in ("contain", "cover"):
        fit = "contain"

    if fit == "contain":
        scale = min(sw / max(1, img_w), sh / max(1, img_h))
    else:
        scale = max(sw / max(1, img_w), sh / max(1, img_h))

    disp_w = int(round(img_w * scale))
    disp_h = int(round(img_h * scale))
    off_x = (sw - disp_w) // 2
    off_y = (sh - disp_h) // 2

    out: List[Tuple[int, int, int, int]] = []
    for r in regions:
        x0 = off_x + int(round(r.xmin * disp_w))
        y0 = off_y + int(round(r.ymin * disp_h))
        x1 = off_x + int(round(r.xmax * disp_w))
        y1 = off_y + int(round(r.ymax * disp_h))
        if x1 <= x0 or y1 <= y0:
            continue
        out.append((x0, y0, x1, y1))
    return out


def _panel_px(
    prs: Presentation,
    style: dict,
    verse: dict,
    anchor: str,
) -> Dict[str, int]:
    v = dict(verse)
    tp = dict(v.get("text_panel") or {})
    tp["anchor"] = anchor
    v["text_panel"] = tp
    cfg = _verse_text_panel_cfg(style, v, "avatar_media_3")
    cfg["anchor"] = anchor
    regions = export_slide_regions(prs, "avatar_media_3", style, verse=v)
    panel = regions.get("text_panel")
    if panel is None:
        sw, sh = prs.slide_width.inches, prs.slide_height.inches
        return region_box_to_pixels(
            RegionBox(0.35, 0.35, 4.0, 1.0),
            sw, sh, _SLIDE_OUT_W, _SLIDE_OUT_H,
        )
    sw, sh = prs.slide_width.inches, prs.slide_height.inches
    return region_box_to_pixels(panel, sw, sh, _SLIDE_OUT_W, _SLIDE_OUT_H)


def _pip_px(prs: Presentation, style: dict, verse: dict) -> Dict[str, int]:
    regions = export_slide_regions(prs, "avatar_media_3", style, verse=verse)
    pip = regions.get("avatar")
    if pip is None:
        return {"x": 1600, "y": 800, "width": 280, "height": 280}
    sw, sh = prs.slide_width.inches, prs.slide_height.inches
    box = region_box_to_pixels(pip, sw, sh, _SLIDE_OUT_W, _SLIDE_OUT_H)
    gap_in = float(layout_in(style, "avatar_media_3", "text_pip_gap_in", 0.14))
    gap_px = int(round(gap_in / sh * _SLIDE_OUT_H))
    return {
        "x": box["x"] - gap_px,
        "y": box["y"] - gap_px,
        "width": box["width"] + 2 * gap_px,
        "height": box["height"] + 2 * gap_px,
    }


def _rect_area(r: Tuple[int, int, int, int]) -> int:
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def _intersection(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> int:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def _ioa(panel: Tuple[int, int, int, int], obstacle: Tuple[int, int, int, int]) -> float:
    inter = _intersection(panel, obstacle)
    area = _rect_area(panel)
    return inter / area if area > 0 else 0.0


def _panel_tuple(box: Dict[str, int]) -> Tuple[int, int, int, int]:
    return (
        box["x"],
        box["y"],
        box["x"] + box["width"],
        box["y"] + box["height"],
    )


def _min_distance(panel: Tuple[int, int, int, int], obstacles: Sequence[Tuple[int, int, int, int]]) -> float:
    if not obstacles:
        return 1.0
    px = (panel[0] + panel[2]) / 2
    py = (panel[1] + panel[3]) / 2
    best = float("inf")
    for ox0, oy0, ox1, oy1 in obstacles:
        nx = max(ox0, min(px, ox1))
        ny = max(oy0, min(py, oy1))
        d = ((px - nx) ** 2 + (py - ny) ** 2) ** 0.5
        best = min(best, d)
    diag = (_SLIDE_OUT_W ** 2 + _SLIDE_OUT_H ** 2) ** 0.5
    return best / diag


def _anchor_prior(anchor: str, preferred: str) -> float:
    if anchor == preferred:
        return 0.0
    opposites = {
        "top_left": "bottom_right",
        "top_right": "bottom_left",
        "bottom_left": "top_right",
        "bottom_right": "top_left",
    }
    if opposites.get(preferred) == anchor:
        return 1.0
    return 0.35


def score_anchor(
    panel: Dict[str, int],
    obstacles: Sequence[Tuple[int, int, int, int]],
    pip: Dict[str, int],
    *,
    anchor: str,
    cfg: HeroTextConfig,
) -> Optional[float]:
    """Lower score is better; ``None`` when hard-rejected."""
    pt = _panel_tuple(panel)
    pip_t = _pip_tuple(pip)
    if _intersection(pt, pip_t) > 0:
        return None

    overlap_sum = sum(_ioa(pt, o) ** _IOA_POWER for o in obstacles)
    if overlap_sum > _OVERLAP_REJECT:
        return None

    margin = _min_distance(pt, obstacles)
    prior = _anchor_prior(anchor, cfg.preferred_anchor)
    return overlap_sum - 0.25 * margin + cfg.anchor_weight * prior


def _pip_tuple(pip: Dict[str, int]) -> Tuple[int, int, int, int]:
    return (pip["x"], pip["y"], pip["x"] + pip["width"], pip["y"] + pip["height"])


def calibrate_hero_panel(
    verse: dict,
    *,
    style: dict,
    data: dict,
    source_file: Optional[str] = None,
    cfg: Optional[HeroTextConfig] = None,
    prs: Optional[Presentation] = None,
) -> HeroPanelResult:
    """Pick best anchor for one ``avatar_media_3`` full-bleed verse."""
    cfg = cfg or HeroTextConfig()
    media = verse.get("media_path")
    if not media:
        return HeroPanelResult(
            media_path="", anchor=cfg.fallback_anchor, score=999.0,
            confidence=0.0, detector="", method=cfg.method,
        )

    resolved = resolve_asset_path(str(media), source_file=source_file) or str(media)
    path = Path(resolved)
    if not path.is_file():
        return HeroPanelResult(
            media_path=str(media), anchor=cfg.fallback_anchor, score=999.0,
            confidence=0.0, detector="", method=cfg.method,
        )

    if _hero_layout_mode(style, verse, "avatar_media_3") != "full_bleed":
        anchor = str((verse.get("text_panel") or {}).get("anchor") or cfg.fallback_anchor)
        return HeroPanelResult(
            media_path=str(media), anchor=anchor, score=0.0,
            confidence=1.0, detector="manual", method="stacked",
        )

    tp = verse.get("text_panel") or {}
    if tp.get("anchor") and str(tp["anchor"]).lower() != "auto":
        return HeroPanelResult(
            media_path=str(media), anchor=str(tp["anchor"]).lower(),
            score=0.0, confidence=1.0, detector="manual", method="explicit",
        )

    detector = _effective_detector(cfg)
    if detector == "vision":
        regions = []
        detector_used = "vision"
    else:
        regions = detect_text_regions(
            path,
            detector=detector,
            min_confidence=cfg.min_confidence * 0.8,
            pad_hard_px=cfg.pad_hard_px,
            pad_soft_px=cfg.pad_soft_px,
        )
        detector_used = regions[0].detector if regions else detector

    img_w, img_h = _image_size(path)
    media_fit = str(verse.get("media_fit") or "contain")
    slide_w_in, slide_h_in = _slide_dims_in(data)
    obstacles = map_regions_to_slide_px(
        regions, img_w=img_w, img_h=img_h,
        slide_w_in=slide_w_in, slide_h_in=slide_h_in, media_fit=media_fit,
    )

    if prs is None:
        prs = calibration_presentation(data)

    pip = _pip_px(prs, style, verse)
    ranked: List[Tuple[str, float]] = []
    for anchor in HERO_PANEL_ANCHOR_ORDER:
        panel = _panel_px(prs, style, verse, anchor)
        sc = score_anchor(panel, obstacles, pip, anchor=anchor, cfg=cfg)
        if sc is not None:
            ranked.append((anchor, sc))

    if cfg.method == "vision" or (not ranked and cfg.vision_fallback):
        vis = _try_vision_anchor(
            path, verse, pip, prs=prs, style=style, obstacles=obstacles,
            cfg=cfg, regions=regions, ranked=ranked or None,
        )
        if vis is not None:
            return vis

    if not ranked:
        return HeroPanelResult(
            media_path=str(media), anchor=cfg.fallback_anchor, score=999.0,
            confidence=0.2, detector=detector_used, region_count=len(regions),
            method=cfg.method,
        )

    ranked.sort(key=lambda t: t[1])
    best_anchor, best_score = ranked[0]
    max_overlap = max((_ioa(_panel_tuple(_panel_px(prs, style, verse, best_anchor)), o) for o in obstacles), default=0.0)
    confidence = max(0.0, min(1.0, 1.0 - best_score - max_overlap))

    if confidence < cfg.min_confidence and cfg.vision_fallback:
        vis = _try_vision_anchor(
            path, verse, pip, prs=prs, style=style, obstacles=obstacles,
            cfg=cfg, regions=regions, ranked=ranked,
        )
        if vis is not None:
            return vis

    alternates = [a for a, _ in ranked[1:4]]
    return HeroPanelResult(
        media_path=str(media), anchor=best_anchor, score=best_score,
        confidence=confidence, detector=detector_used, region_count=len(regions),
        method=cfg.method, alternates=alternates,
    )


def _cache_dir(data: dict) -> Path:
    raw = (data.get("hero_text_placement") or {}).get("cache_dir")
    if raw:
        return Path(raw)
    sf = data.get("_source_file")
    if sf:
        return Path(sf).resolve().parent / ".praisonaippt" / "hero-text-placement"
    return Path.cwd() / ".praisonaippt" / "hero-text-placement"


def _cache_path(
    image: Path,
    cache_dir: Path,
    cfg: HeroTextConfig,
    verse: dict,
    *,
    style: Optional[dict] = None,
) -> Path:
    stat = image.stat()
    tp = verse.get("text_panel") or {}
    panel_key = (
        f"{tp.get('width_ratio')}:{tp.get('height_in')}:{tp.get('margin_in')}:"
        f"{verse.get('headline')}:{verse.get('subheader')}"
    )
    key = (
        f"{cfg.cache_key_part(style=style)}:{image.resolve()}:{stat.st_size}:"
        f"{int(stat.st_mtime)}:{panel_key}:{verse.get('media_fit')}"
    )
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.json"


def load_cached_result(
    image_path: str,
    cache_dir: Path,
    cfg: HeroTextConfig,
    verse: dict,
    *,
    style: Optional[dict] = None,
) -> Optional[HeroPanelResult]:
    path = Path(image_path)
    if not path.is_file():
        return None
    cache_file = _cache_path(path, cache_dir, cfg, verse, style=style)
    if not cache_file.is_file():
        return None
    try:
        raw = json.loads(cache_file.read_text(encoding="utf-8"))
        if raw.get("version") != _CACHE_VERSION:
            return None
        return HeroPanelResult(**{k: v for k, v in raw.items() if k in HeroPanelResult.__dataclass_fields__})
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def save_cached_result(
    result: HeroPanelResult,
    image_path: str,
    cache_dir: Path,
    cfg: HeroTextConfig,
    verse: dict,
    *,
    style: Optional[dict] = None,
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = Path(image_path)
    cache_file = _cache_path(path, cache_dir, cfg, verse, style=style)
    cache_file.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return cache_file


def write_validation_png(
    image_path: str | Path,
    result: HeroPanelResult,
    *,
    style: dict,
    data: dict,
    verse: dict,
    out_path: str | Path,
    cfg: Optional[HeroTextConfig] = None,
) -> Path:
    """Save L/R/T/B clearance diagram (delegates to hero_panel_measure)."""
    from .hero_panel_measure import measure_hero_panel_image, save_hero_panel_validation_diagram

    cfg = cfg or HeroTextConfig.from_dict(data.get("hero_text_placement"), style=style)
    metrics, cal_result = measure_hero_panel_image(
        image_path, style=style, data=data, verse=verse, cfg=cfg, anchor=result.anchor,
    )
    return save_hero_panel_validation_diagram(
        image_path, metrics, out_path,
        style=style, data=data, verse=verse, cfg=cfg, result=cal_result,
    )


def calibrate_deck_hero_panels(
    data: dict,
    *,
    cache_dir: Optional[Path] = None,
    force: bool = False,
    source_file: Optional[str] = None,
) -> Dict[str, HeroPanelResult]:
    """Calibrate all ``avatar_media_3`` verses with ``text_panel.anchor: auto``."""
    cfg = HeroTextConfig.from_dict(
        data.get("hero_text_placement"),
        style=data.get("slide_style") or {},
    )
    if not cfg.auto and not force:
        return {}

    style = data.get("slide_style") or {}
    sf = source_file or data.get("_source_file")
    cache = cache_dir or _cache_dir(data)
    prs = calibration_presentation(data)

    results: Dict[str, HeroPanelResult] = {}
    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for verse in section.get("verses") or []:
            if not isinstance(verse, dict):
                continue
            if verse.get("slide_type") != "avatar_media_3":
                continue
            tp = verse.get("text_panel") or {}
            if str(tp.get("anchor", "")).lower() != "auto":
                continue
            media = verse.get("media_path")
            if not media:
                continue
            resolved = resolve_asset_path(str(media), source_file=sf) or str(media)
            if not force:
                cached = load_cached_result(resolved, cache, cfg, verse, style=style)
                if cached:
                    results[str(media)] = cached
                    continue
            result = calibrate_hero_panel(
                verse, style=style, data=data, source_file=sf, cfg=cfg, prs=prs,
            )
            save_cached_result(result, resolved, cache, cfg, verse, style=style)
            results[str(media)] = result
    return results


def maybe_auto_place_hero_text_deck(data: dict, *, source_file: Optional[str] = None) -> dict:
    """When ``hero_text_placement.auto`` is true, set ``_hero_panel_anchor`` on verses."""
    cfg_raw = data.get("hero_text_placement") or {}
    if not cfg_raw.get("auto"):
        return data

    force = bool(cfg_raw.get("force"))
    cache_raw = cfg_raw.get("cache_dir")
    cache_dir = Path(cache_raw) if cache_raw else None
    results = calibrate_deck_hero_panels(
        data, cache_dir=cache_dir, force=force, source_file=source_file,
    )
    if not results:
        return data

    data = dict(data)
    sections = []
    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            sections.append(section)
            continue
        verses = []
        for verse in section.get("verses") or []:
            if not isinstance(verse, dict):
                verses.append(verse)
                continue
            v = dict(verse)
            media = v.get("media_path")
            if media and str(media) in results:
                v["_hero_panel_anchor"] = results[str(media)].anchor
            verses.append(v)
        sec = dict(section)
        sec["verses"] = verses
        sections.append(sec)
    data["sections"] = sections
    data["_hero_text_placement"] = {k: r.to_dict() for k, r in results.items()}
    return data


def format_hero_panel_report(results: Dict[str, HeroPanelResult]) -> str:
    lines = ["Hero text panel placement:"]
    for path, r in results.items():
        name = Path(path).name
        lines.append(
            f"  {name}: anchor={r.anchor} score={r.score:.3f} conf={r.confidence:.2f} "
            f"det={r.detector} regions={r.region_count}"
        )
    return "\n".join(lines)


def hero_text_deps_hint(cfg: Optional[HeroTextConfig] = None) -> str:
    """Short hint when hero-text detection extras are missing."""
    from .text_region_detect import text_detect_available

    cfg = cfg or HeroTextConfig()
    if cfg.method == "vision":
        return (
            'Tip: set PRAISONAIPPT_VISION_PROVIDER and OPENAI_API_KEY / ANTHROPIC_API_KEY '
            "for vision fallback, or install hero-text-detect extras."
        )
    if text_detect_available():
        return ""
    return (
        'Tip: pip install -e ".[hero-text-detect]" for OpenCV EAST/MSER text detection '
        '(optional ".[hero-text-paddle]" or ".[hero-text-rapidocr]").'
    )

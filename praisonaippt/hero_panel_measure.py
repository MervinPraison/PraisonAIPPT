"""Measure hero text-panel placement vs detected UI text (parity with pip_face_measure)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .hero_panel_calibrate import (
    HeroPanelResult,
    HeroTextConfig,
    _SLIDE_OUT_H,
    _SLIDE_OUT_W,
    _effective_detector,
    _image_size,
    _panel_px,
    _pip_px,
    calibrate_hero_panel,
    calibration_presentation,
    map_regions_to_slide_px,
    score_anchor,
)
from .text_region_detect import detect_text_regions


@dataclass
class HeroPanelMetrics:
    """Panel placement quality on a hero screenshot (1920×1080 slide space)."""

    anchor: str
    panel_left: int
    panel_top: int
    panel_width: int
    panel_height: int
    overlap_ratio: float
    clearance_left: int
    clearance_right: int
    clearance_top: int
    clearance_bottom: int
    score: float
    confidence: float
    region_count: int
    detector: str
    pip_overlap: bool = False

    @property
    def is_clear(self) -> bool:
        return (
            not self.pip_overlap
            and self.overlap_ratio <= 0.15
            and min(self.clearance_left, self.clearance_right, self.clearance_top, self.clearance_bottom) >= 8
        )

    @property
    def min_clearance_px(self) -> int:
        return min(
            self.clearance_left, self.clearance_right,
            self.clearance_top, self.clearance_bottom,
        )

    def summary_line(self) -> str:
        return (
            f"anchor={self.anchor} overlap={self.overlap_ratio:.3f} "
            f"score={self.score:.3f} conf={self.confidence:.2f} "
            f"regions={self.region_count} det={self.detector}"
        )


@dataclass
class HeroPlacementAdvice:
    """Suggest anchor changes when the panel overlaps UI text."""

    is_clear: bool
    overlap_ratio: float
    min_clearance_px: int
    summary: str
    detail: str
    suggested_anchor: Optional[str] = None


def _panel_tuple(box: Dict[str, int]) -> Tuple[int, int, int, int]:
    return (
        box["x"], box["y"],
        box["x"] + box["width"], box["y"] + box["height"],
    )


def _intersection_area(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> int:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def _panel_area(panel: Tuple[int, int, int, int]) -> int:
    return max(0, panel[2] - panel[0]) * max(0, panel[3] - panel[1])


def _overlap_ratio(panel: Tuple[int, int, int, int], obstacles: Sequence[Tuple[int, int, int, int]]) -> float:
    area = _panel_area(panel)
    if area <= 0:
        return 1.0
    return sum(_intersection_area(panel, o) for o in obstacles) / area


def _edge_clearances(
    panel: Tuple[int, int, int, int],
    obstacles: Sequence[Tuple[int, int, int, int]],
) -> Tuple[int, int, int, int]:
    """Pixel gap from panel edges to nearest obstacle (large if none on that side)."""
    pl, pt, pr, pb = panel
    left = pl
    right = _SLIDE_OUT_W - pr
    top = pt
    bottom = _SLIDE_OUT_H - pb
    for ox0, oy0, ox1, oy1 in obstacles:
        if ox1 <= pl:
            left = min(left, pl - ox1)
        if ox0 >= pr:
            right = min(right, ox0 - pr)
        if oy1 <= pt:
            top = min(top, pt - oy1)
        if oy0 >= pb:
            bottom = min(bottom, oy0 - pb)
    return (
        max(0, int(left)),
        max(0, int(right)),
        max(0, int(top)),
        max(0, int(bottom)),
    )


def panel_clearance_score(metrics: HeroPanelMetrics) -> float:
    """Lower is better — used by tests and calibration (parity with face_centre_symmetry_score)."""
    score = metrics.overlap_ratio * 2.0
    if metrics.pip_overlap:
        score += 1.0
    min_c = metrics.min_clearance_px
    if min_c < 24:
        score += (24 - min_c) / 48.0
    return score


def placement_advice(metrics: HeroPanelMetrics, *, alternates: Optional[List[str]] = None) -> HeroPlacementAdvice:
    """Human-readable guidance from measured panel metrics."""
    if metrics.is_clear:
        return HeroPlacementAdvice(
            is_clear=True,
            overlap_ratio=metrics.overlap_ratio,
            min_clearance_px=metrics.min_clearance_px,
            summary="Panel clears detected UI text and PiP.",
            detail=(
                f"L {metrics.clearance_left}px R {metrics.clearance_right}px "
                f"T {metrics.clearance_top}px B {metrics.clearance_bottom}px to nearest text"
            ),
        )
    parts = []
    if metrics.pip_overlap:
        parts.append("panel overlaps PiP — try top_left or top anchor")
    if metrics.overlap_ratio > 0.15:
        parts.append("panel overlaps UI text — try another anchor")
    if metrics.min_clearance_px < 12:
        parts.append(f"min clearance only {metrics.min_clearance_px}px")
    alt = (alternates or [None])[0]
    return HeroPlacementAdvice(
        is_clear=False,
        overlap_ratio=metrics.overlap_ratio,
        min_clearance_px=metrics.min_clearance_px,
        summary="Adjust placement: " + "; ".join(parts) if parts else "Panel placement needs review",
        detail=(
            f"overlap={metrics.overlap_ratio:.3f} anchor={metrics.anchor} "
            f"clearances L{metrics.clearance_left} R{metrics.clearance_right} "
            f"T{metrics.clearance_top} B{metrics.clearance_bottom}px"
        ),
        suggested_anchor=alt,
    )


def measure_hero_panel_image(
    image_path: str | Path,
    *,
    style: dict,
    data: dict,
    verse: dict,
    cfg: Optional[HeroTextConfig] = None,
    anchor: Optional[str] = None,
) -> Tuple[HeroPanelMetrics, HeroPanelResult]:
    """Measure panel placement on one hero screenshot; returns metrics + calibration result."""
    cfg = cfg or HeroTextConfig.from_dict(
        data.get("hero_text_placement"), style=style,
    )
    path = Path(image_path)
    result = calibrate_hero_panel(
        verse, style=style, data=data,
        source_file=data.get("_source_file"), cfg=cfg,
    )
    use_anchor = anchor or result.anchor

    detector = _effective_detector(cfg)
    if detector == "vision":
        regions = []
    else:
        regions = detect_text_regions(
            path, detector=detector,
            min_confidence=cfg.min_confidence * 0.8,
            pad_hard_px=cfg.pad_hard_px, pad_soft_px=cfg.pad_soft_px,
        )
    img_w, img_h = _image_size(path)
    media_fit = str(verse.get("media_fit") or "contain")
    from .hero_panel_calibrate import _slide_dims_in

    slide_w_in, slide_h_in = _slide_dims_in(data)
    obstacles = map_regions_to_slide_px(
        regions, img_w=img_w, img_h=img_h,
        slide_w_in=slide_w_in, slide_h_in=slide_h_in, media_fit=media_fit,
    )

    prs = calibration_presentation(data)
    panel_box = _panel_px(prs, style, verse, use_anchor)
    pip = _pip_px(prs, style, verse)
    pt = _panel_tuple(panel_box)
    pip_t = _panel_tuple(pip)

    overlap = _overlap_ratio(pt, obstacles)
    cl, cr, ct, cb = _edge_clearances(pt, obstacles)
    pip_hit = _intersection_area(pt, pip_t) > 0
    sc = score_anchor(panel_box, obstacles, pip, anchor=use_anchor, cfg=cfg)

    if use_anchor != result.anchor:
        result = HeroPanelResult(
            media_path=result.media_path,
            anchor=use_anchor,
            score=sc if sc is not None else 999.0,
            confidence=result.confidence,
            detector=result.detector,
            region_count=len(regions),
            method=result.method,
            alternates=result.alternates,
        )

    metrics = HeroPanelMetrics(
        anchor=use_anchor,
        panel_left=panel_box["x"],
        panel_top=panel_box["y"],
        panel_width=panel_box["width"],
        panel_height=panel_box["height"],
        overlap_ratio=round(overlap, 4),
        clearance_left=cl,
        clearance_right=cr,
        clearance_top=ct,
        clearance_bottom=cb,
        score=sc if sc is not None else 999.0,
        confidence=result.confidence,
        region_count=len(regions),
        detector=regions[0].detector if regions else detector,
        pip_overlap=pip_hit,
    )
    return metrics, result


def default_hero_validation_image_path(image_path: str | Path) -> Path:
    p = Path(image_path)
    return p.with_name(f"{p.stem}_hero_panel_validation.png")


def save_hero_panel_validation_diagram(
    image_path: str | Path,
    metrics: HeroPanelMetrics,
    output_path: str | Path,
    *,
    style: dict,
    data: dict,
    verse: dict,
    cfg: Optional[HeroTextConfig] = None,
    result: Optional[HeroPanelResult] = None,
) -> Path:
    """Draw panel, text obstacles, PiP, and L/R/T/B clearance labels (parity with PiP diagram)."""
    from PIL import Image, ImageDraw, ImageFont

    cfg = cfg or HeroTextConfig.from_dict(data.get("hero_text_placement"), style=style)
    path = Path(image_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    img_w, img_h = _image_size(path)
    detector = _effective_detector(cfg)
    regions = detect_text_regions(
        path, detector=detector,
        min_confidence=cfg.min_confidence * 0.8,
        pad_hard_px=cfg.pad_hard_px, pad_soft_px=cfg.pad_soft_px,
    ) if detector != "vision" else []
    media_fit = str(verse.get("media_fit") or "contain")
    from .hero_panel_calibrate import _slide_dims_in

    slide_w_in, slide_h_in = _slide_dims_in(data)
    obstacles = map_regions_to_slide_px(
        regions, img_w=img_w, img_h=img_h,
        slide_w_in=slide_w_in, slide_h_in=slide_h_in, media_fit=media_fit,
    )

    prs = calibration_presentation(data)
    pip = _pip_px(prs, style, verse)
    panel = {
        "x": metrics.panel_left,
        "y": metrics.panel_top,
        "width": metrics.panel_width,
        "height": metrics.panel_height,
    }

    canvas = Image.new("RGB", (_SLIDE_OUT_W, _SLIDE_OUT_H), (18, 18, 18))
    try:
        bg = Image.open(path).convert("RGB")
        scale = min(_SLIDE_OUT_W / bg.width, _SLIDE_OUT_H / bg.height)
        dw, dh = int(bg.width * scale), int(bg.height * scale)
        bg = bg.resize((dw, dh))
        ox, oy = (_SLIDE_OUT_W - dw) // 2, (_SLIDE_OUT_H - dh) // 2
        canvas.paste(bg, (ox, oy))
    except OSError:
        pass

    overlay = Image.new("RGBA", (_SLIDE_OUT_W, _SLIDE_OUT_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()

    for ox0, oy0, ox1, oy1 in obstacles:
        draw.rectangle([ox0, oy0, ox1, oy1], outline=(220, 60, 60, 220), width=2)

    px0, py0 = panel["x"], panel["y"]
    px1, py1 = px0 + panel["width"], py0 + panel["height"]
    draw.rectangle([px0, py0, px1, py1], outline=(60, 220, 100, 255), width=3)

    pip0 = (pip["x"], pip["y"], pip["x"] + pip["width"], pip["y"] + pip["height"])
    draw.rectangle(list(pip0), outline=(255, 220, 80, 255), width=2)

    mid_y = (py0 + py1) / 2.0
    mid_x = (px0 + px1) / 2.0
    draw.line((0, mid_y, px0, mid_y), fill=(255, 140, 40, 255), width=3)
    draw.text((4, mid_y - 14), f"L {metrics.clearance_left}px", fill=(255, 180, 80, 255), font=font)
    draw.line((px1, mid_y, _SLIDE_OUT_W, mid_y), fill=(60, 220, 255, 255), width=3)
    draw.text((px1 + 4, mid_y + 2), f"R {metrics.clearance_right}px", fill=(120, 230, 255, 255), font=font)
    draw.line((mid_x, 0, mid_x, py0), fill=(220, 100, 255, 255), width=3)
    draw.text((mid_x + 4, 4), f"T {metrics.clearance_top}px", fill=(230, 150, 255, 255), font=font)
    draw.line((mid_x, py1, mid_x, _SLIDE_OUT_H), fill=(255, 100, 180, 255), width=3)
    draw.text((mid_x + 4, py1 - 14), f"B {metrics.clearance_bottom}px", fill=(255, 150, 200, 255), font=font)

    composed = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    banner_h = 56
    final = Image.new("RGB", (_SLIDE_OUT_W, _SLIDE_OUT_H + banner_h), (18, 18, 22))
    final.paste(composed.convert("RGB"), (0, 0))

    advice = placement_advice(metrics, alternates=(result.alternates if result else None))
    clear = "YES" if advice.is_clear else "no"
    banner = ImageDraw.Draw(final)
    line1 = (
        f"anchor={metrics.anchor}  overlap={metrics.overlap_ratio:.3f}  "
        f"score={metrics.score:.3f}  clear={clear}"
    )
    line2 = (
        f"clearances px: L {metrics.clearance_left}  R {metrics.clearance_right}  "
        f"T {metrics.clearance_top}  B {metrics.clearance_bottom}  regions={metrics.region_count}"
    )
    line3 = f"detector={metrics.detector}  green=panel  red=text  yellow=PiP  L/R/T/B=gap to UI text"
    banner.text((8, _SLIDE_OUT_H + 6), line1, fill=(230, 230, 235), font=font)
    banner.text((8, _SLIDE_OUT_H + 20), line2, fill=(180, 190, 200), font=font)
    banner.text((8, _SLIDE_OUT_H + 34), line3, fill=(140, 150, 165), font=font)

    final.save(out, format="PNG")
    return out


def write_validation_for_hero_image(
    image_path: str | Path,
    metrics: HeroPanelMetrics,
    output_path: Optional[str | Path] = None,
    *,
    style: dict,
    data: dict,
    verse: dict,
    cfg: Optional[HeroTextConfig] = None,
    result: Optional[HeroPanelResult] = None,
) -> Path:
    out = Path(output_path) if output_path else default_hero_validation_image_path(image_path)
    return save_hero_panel_validation_diagram(
        image_path, metrics, out,
        style=style, data=data, verse=verse, cfg=cfg, result=result,
    )


def format_hero_panel_measure_report(
    metrics: HeroPanelMetrics,
    *,
    image_path: Optional[Path] = None,
    result: Optional[HeroPanelResult] = None,
) -> str:
    lines = ["Hero text panel measurement:"]
    lines.append(f"  {metrics.summary_line()}")
    lines.append(
        f"  panel px: x={metrics.panel_left} y={metrics.panel_top} "
        f"w={metrics.panel_width} h={metrics.panel_height}"
    )
    lines.append(
        f"  clearances px: L={metrics.clearance_left} R={metrics.clearance_right} "
        f"T={metrics.clearance_top} B={metrics.clearance_bottom}"
    )
    if image_path:
        lines.append(f"  image: {image_path}")
    advice = placement_advice(metrics, alternates=result.alternates if result else None)
    lines.append(f"  clear: {'yes' if advice.is_clear else 'no'}")
    lines.append(f"  {advice.summary}")
    if not advice.is_clear:
        lines.append(f"  adjust: {advice.detail}")
        if advice.suggested_anchor:
            lines.append(f"  try anchor: {advice.suggested_anchor}")
    lines.append("  (use --validation-image to save L/R/T/B clearance diagram)")
    return "\n".join(lines)

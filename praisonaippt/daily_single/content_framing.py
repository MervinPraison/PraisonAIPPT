"""Content-aware crop for hook canonical scroll — column projection + MSER + DOM merge."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from praisonaippt.text_region_detect import TextRegion, detect_text_regions

W, H = 1920, 1080
MAX_SIDE_MARGIN = 0.12
MIN_CONTENT_FILL = 0.55
TARGET_SCROLL_PX_PER_SEC = 70.0
MAX_SCROLL_PX_PER_SEC = 100.0
CROP_PAD_FRAC = 0.02
MIN_CROP_WIDTH_PX = 720
MIN_CONTENT_WIDTH_RATIO = 0.35

_DOM_JS = """
() => {
  const pick = (sel) => document.querySelector(sel);
  let el = pick('article') || pick('main') || pick('[role="main"]');
  if (!el) {
    const h1 = pick('h1');
    if (h1) el = h1.closest('article, main, section') || h1.parentElement;
  }
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width < 400 || r.height < 200) return null;
  return { x: r.x, y: r.y, width: r.width, height: r.height };
}
"""


@dataclass
class ContentFrame:
    x0: int
    y0: int
    x1: int
    y1: int
    source: str = "unknown"
    confidence: float = 0.5

    @property
    def width(self) -> int:
        return max(1, self.x1 - self.x0)

    @property
    def height(self) -> int:
        return max(1, self.y1 - self.y0)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HookFramingMetrics:
    image_width: int
    image_height: int
    left_margin_ratio: float
    right_margin_ratio: float
    content_fill_ratio: float
    content_bbox: ContentFrame
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_bbox"] = self.content_bbox.to_dict()
        return d


def detect_dom_content_bbox(page: Any) -> ContentFrame | None:
    """Playwright page bbox for main/article content."""
    try:
        raw = page.evaluate(_DOM_JS)
    except Exception:
        return None
    if not raw:
        return None
    pad = 16
    x0 = max(0, int(raw["x"]) - pad)
    y0 = max(0, int(raw["y"]) - pad)
    x1 = int(raw["x"] + raw["width"]) + pad
    y1 = int(raw["y"] + raw["height"]) + pad
    return ContentFrame(x0, y0, x1, y1, source="dom", confidence=1.0)


def _load_rgb(path: Path) -> tuple[np.ndarray, int, int]:
    from PIL import Image

    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    return np.asarray(img), iw, ih


def detect_column_projection(path: Path, *, y_start_frac: float = 0.10, y_end_frac: float = 0.85) -> ContentFrame | None:
    """Find centred content column via vertical ink projection (skips nav/footer band)."""
    rgb, iw, ih = _load_rgb(path)
    y0 = int(ih * y_start_frac)
    y1 = int(ih * y_end_frac)
    band = rgb[y0:y1]
    if band.size == 0:
        return None

    edge_w = max(4, iw // 20)
    bg = np.median(np.concatenate([band[:, :edge_w], band[:, -edge_w:]], axis=1), axis=(0, 1))
    diff = np.mean(np.abs(band.astype(np.int16) - bg.astype(np.int16)), axis=2)
    ink = diff > 28
    col_density = ink.mean(axis=0)
    peak = float(col_density.max()) if col_density.size else 0.0
    if peak < 0.04:
        return None
    thresh = max(0.04, peak * 0.20)
    cols = np.where(col_density >= thresh)[0]
    if cols.size == 0:
        return None
    x0, x1 = int(cols[0]), int(cols[-1]) + 1
    if (x1 - x0) / max(1, iw) < MIN_CONTENT_WIDTH_RATIO:
        return None
    return ContentFrame(x0, y0, x1, y1, source="column", confidence=min(1.0, peak * 4))


def _regions_union(regions: list[TextRegion], iw: int, ih: int) -> ContentFrame | None:
    if len(regions) < 4:
        return None
    x0 = int(min(r.xmin for r in regions) * iw)
    y0 = int(min(r.ymin for r in regions) * ih)
    x1 = int(max(r.xmax for r in regions) * iw)
    y1 = int(max(r.ymax for r in regions) * ih)
    pad = 24
    return ContentFrame(
        max(0, x0 - pad), max(0, y0 - pad),
        min(iw, x1 + pad), min(ih, y1 + pad),
        source="mser", confidence=0.7,
    )


def detect_mser_content_bbox(path: Path, *, min_confidence: float = 0.30) -> ContentFrame | None:
    _, iw, ih = _load_rgb(path)
    regions = detect_text_regions(
        path, detector="mser", min_confidence=min_confidence,
        pad_hard_px=24, pad_soft_px=12,
    )
    y_cut = int(ih * 0.08)
    filtered = [
        r for r in regions
        if r.ymin * ih >= y_cut and (r.xmax - r.xmin) * iw < iw * 0.55
    ]
    return _regions_union(filtered or regions, iw, ih)


def merge_content_frames(
    iw: int,
    ih: int,
    *frames: ContentFrame | None,
) -> ContentFrame | None:
    """Merge DOM/column base with MSER widening."""
    valid = [f for f in frames if f is not None]
    if not valid:
        return None
    base = next((f for f in valid if f.source == "dom"), None)
    if base is None:
        base = next((f for f in valid if f.source == "column"), valid[0])
    mser = next((f for f in valid if f.source == "mser"), None)

    x0, y0, x1, y1 = base.x0, base.y0, base.x1, base.y1
    if mser is not None:
        bc = (base.x0 + base.x1) / 2
        mc = (mser.x0 + mser.x1) / 2
        if abs(bc - mc) / max(1, iw) <= 0.12:
            x0 = min(x0, mser.x0)
            x1 = max(x1, mser.x1)
            y0 = min(y0, mser.y0)
            y1 = max(y1, mser.y1)
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(iw, x1)
    y1 = min(ih, y1)
    if x1 - x0 < MIN_CROP_WIDTH_PX:
        return None
    if (x1 - x0) / max(1, iw) > 0.92:
        mser_only = next((f for f in valid if f.source == "mser"), None)
        if mser_only and mser_only.width >= MIN_CROP_WIDTH_PX:
            return mser_only
        return None
    sources = sorted({f.source for f in valid})
    conf = max(f.confidence for f in valid)
    return ContentFrame(x0, y0, x1, y1, source="+".join(sources), confidence=conf)


def measure_framing(path: Path, frame: ContentFrame | None = None) -> HookFramingMetrics:
    _, iw, ih = _load_rgb(path)
    if frame is None:
        frame = merge_content_frames(
            iw, ih,
            detect_column_projection(path),
            detect_mser_content_bbox(path),
        ) or ContentFrame(0, 0, iw, ih, source="full", confidence=0.0)
    left = frame.x0 / max(1, iw)
    right = (iw - frame.x1) / max(1, iw)
    fill = (frame.width * frame.height) / max(1, iw * ih)
    return HookFramingMetrics(
        image_width=iw,
        image_height=ih,
        left_margin_ratio=round(left, 4),
        right_margin_ratio=round(right, 4),
        content_fill_ratio=round(fill, 4),
        content_bbox=frame,
        sources=[frame.source],
    )


def measure_viewport_gutters(path: Path, *, strip_frac: float = 0.05) -> tuple[float, float]:
    """Detect uniform empty strips on outer left/right edges (browser gutters, not in-page layout)."""
    from praisonaippt.daily_single.visual_audit import _gray_array

    gray = _gray_array(path, w=1920, h=1080)
    if gray is None:
        return 0.0, 0.0
    h, w = gray.shape
    sw = max(8, int(w * strip_frac))
    left = gray[:, :sw]
    right = gray[:, -sw:]

    def empty_frac(strip: np.ndarray) -> float:
        std = float(np.std(strip))
        mean = float(np.mean(strip))
        if std > 18.0:
            return 0.0
        if mean > 232.0:
            return 1.0
        if mean > 210.0 and std < 12.0:
            return 0.85
        return 0.0

    return round(empty_frac(left), 3), round(empty_frac(right), 3)


def validate_viewport_gutters(path: Path) -> tuple[bool, list[str]]:
    left, right = measure_viewport_gutters(path)
    issues: list[str] = []
    if left > 0.75 and right > 0.75:
        issues.append(f"viewport gutters too wide (L={left:.2f} R={right:.2f})")
    return len(issues) == 0, issues


def validate_framing(metrics: HookFramingMetrics) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if max(metrics.left_margin_ratio, metrics.right_margin_ratio) > MAX_SIDE_MARGIN:
        issues.append(
            f"side margins too wide (L={metrics.left_margin_ratio:.2f} "
            f"R={metrics.right_margin_ratio:.2f} > {MAX_SIDE_MARGIN})"
        )
    if metrics.content_fill_ratio < MIN_CONTENT_FILL:
        issues.append(
            f"content too zoomed out (fill={metrics.content_fill_ratio:.2f} < {MIN_CONTENT_FILL})"
        )
    return len(issues) == 0, issues


def scroll_speed_px_per_sec(travel_px: int, duration_sec: float) -> float:
    if duration_sec <= 0:
        return float("inf")
    return travel_px / duration_sec


def effective_scroll_duration(travel_px: int, requested_sec: float) -> float:
    if travel_px <= 0:
        return requested_sec
    min_dur = travel_px / TARGET_SCROLL_PX_PER_SEC
    return max(requested_sec, min_dur)


def validate_scroll_speed(travel_px: int, duration_sec: float) -> tuple[bool, list[str]]:
    speed = scroll_speed_px_per_sec(travel_px, duration_sec)
    if travel_px > 0 and speed > MAX_SCROLL_PX_PER_SEC:
        return False, [f"scroll too fast ({speed:.0f}px/s > {MAX_SCROLL_PX_PER_SEC:.0f}px/s)"]
    return True, []


def trim_for_hook_scroll(src: Path, dest: Path, *, max_travel_px: int) -> Path:
    """Keep only the top portion needed for a capped hook scroll."""
    from PIL import Image

    img = Image.open(src).convert("RGB")
    keep_h = min(img.size[1], H + max(0, max_travel_px))
    if keep_h >= img.size[1]:
        if dest != src:
            dest.write_bytes(src.read_bytes())
        return dest
    cropped = img.crop((0, 0, img.size[0], keep_h))
    dest.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest)
    return dest


def apply_content_crop(src: Path, frame: ContentFrame, dest: Path) -> Path:
    """Crop side gutters only; ffmpeg scales to 1920px width during encode."""
    from PIL import Image

    img = Image.open(src).convert("RGB")
    iw, ih = img.size
    pad_x = int(frame.width * CROP_PAD_FRAC)
    x0 = max(0, frame.x0 - pad_x)
    x1 = min(iw, frame.x1 + pad_x)
    cropped = img.crop((x0, 0, x1, ih))
    dest.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest)
    return dest


def reframe_page_shot(
    shot: Path,
    *,
    dom_bbox: ContentFrame | None = None,
    dest: Path | None = None,
) -> tuple[Path, ContentFrame, HookFramingMetrics]:
    """Detect content column, crop, scale to full width; return reframed PNG + metrics."""
    _, iw, ih = _load_rgb(shot)
    merged = merge_content_frames(
        iw, ih,
        dom_bbox,
        detect_column_projection(shot),
        detect_mser_content_bbox(shot),
    )
    raw_metrics = measure_framing(shot, merged)
    out = dest or shot.with_name("page-reframed.png")
    wide_margins = max(raw_metrics.left_margin_ratio, raw_metrics.right_margin_ratio) > MAX_SIDE_MARGIN
    needs_crop = merged is not None and (
        raw_metrics.content_fill_ratio < MIN_CONTENT_FILL or wide_margins
    )
    if needs_crop:
        apply_content_crop(shot, merged, out)
        _, iw, ih = _load_rgb(out)
        post = HookFramingMetrics(
            image_width=iw,
            image_height=ih,
            left_margin_ratio=0.0,
            right_margin_ratio=0.0,
            content_fill_ratio=1.0,
            content_bbox=ContentFrame(0, 0, iw, ih, source="crop", confidence=1.0),
            sources=["crop"],
        )
        return out, merged, post
    if out != shot:
        out.write_bytes(shot.read_bytes())
    return shot, merged or ContentFrame(0, 0, iw, ih, source="full"), raw_metrics


def save_framing_diagram(
    image_path: Path,
    metrics: HookFramingMetrics,
    output_path: Path,
) -> Path:
    from PIL import Image, ImageDraw

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    b = metrics.content_bbox
    draw.rectangle([b.x0, b.y0, b.x1, b.y1], outline=(255, 64, 64), width=4)
    label = (
        f"L={metrics.left_margin_ratio:.0%} R={metrics.right_margin_ratio:.0%} "
        f"fill={metrics.content_fill_ratio:.0%}"
    )
    draw.text((b.x0 + 8, max(0, b.y0 - 24)), label, fill=(255, 64, 64))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def write_framing_report(project_qa_dir: Path, metrics: HookFramingMetrics, *, ok: bool, issues: list[str]) -> Path:
    report = {
        "schema_version": 1,
        "ok": ok,
        "issues": issues,
        "thresholds": {
            "max_side_margin": MAX_SIDE_MARGIN,
            "min_content_fill": MIN_CONTENT_FILL,
            "max_scroll_px_per_sec": MAX_SCROLL_PX_PER_SEC,
            "target_scroll_px_per_sec": TARGET_SCROLL_PX_PER_SEC,
        },
        "metrics": metrics.to_dict(),
    }
    out = project_qa_dir / "framing_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out

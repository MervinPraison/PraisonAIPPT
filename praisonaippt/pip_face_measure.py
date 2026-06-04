"""Measure face position inside a circular PiP frame (MediaPipe + balance heuristic)."""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .ffmpeg_composer import _circle_alpha_filter, _cover_scale_filter, pip_face_balance


@dataclass
class PipFaceMetrics:
    """Face centre vs PiP circle — offsets and border margins (normalised 0–1)."""

    face_fx: Optional[float]
    face_fy: Optional[float]
    centre_offset_x: float
    centre_offset_y: float
    balance: float
    margin_left: Optional[float]
    margin_right: Optional[float]
    margin_top: Optional[float]
    margin_bottom: Optional[float]
    detector: str = ""
    face_xmin: Optional[float] = None
    face_ymin: Optional[float] = None
    face_xmax: Optional[float] = None
    face_ymax: Optional[float] = None

    @property
    def is_centred(self) -> bool:
        return abs(self.centre_offset_x) < 0.05 and abs(self.centre_offset_y) < 0.08

    @property
    def margin_lr_delta(self) -> Optional[float]:
        """Left minus right margin (norm); 0 when horizontally centred in circle."""
        if self.margin_left is None or self.margin_right is None:
            return None
        return self.margin_left - self.margin_right

    @property
    def margin_tb_delta(self) -> Optional[float]:
        """Top minus bottom margin (norm); 0 when vertically centred in circle."""
        if self.margin_top is None or self.margin_bottom is None:
            return None
        return self.margin_top - self.margin_bottom

    def summary_line(self) -> str:
        det = f" detector={self.detector}" if self.detector else ""
        face = (
            f"face=({self.face_fx:.3f},{self.face_fy:.3f})"
            if self.face_fx is not None
            else "face=not_detected"
        )
        return (
            f"{face} offset_x={self.centre_offset_x:+.3f} offset_y={self.centre_offset_y:+.3f} "
            f"balance={self.balance:+.3f}{det}"
        )


@dataclass
class PipCentringAdvice:
    """How to adjust crop ratios when the face is off-centre in the PiP circle."""

    is_centred: bool
    offset_x: float
    offset_y: float
    margin_lr_delta: Optional[float]
    margin_tb_delta: Optional[float]
    crop_x_delta: float
    crop_y_delta: float
    summary: str
    detail: str


def centring_advice(metrics: PipFaceMetrics) -> PipCentringAdvice:
    """Suggest crop_x / crop_y moves from validation metrics (for CLI and calibration SDK)."""
    ox, oy = metrics.centre_offset_x, metrics.centre_offset_y
    lr = metrics.margin_lr_delta
    tb = metrics.margin_tb_delta
    centred = metrics.is_centred

    # Face right of circle centre (ox>0) → raise crop_x to shift face left in frame.
    crop_x_d = max(-0.08, min(0.08, ox * 0.85))
    if lr is not None and abs(lr) > 0.03:
        crop_x_d = max(-0.08, min(0.08, crop_x_d + lr * 0.45))

    # Face below centre (oy>0) → lower crop_y to shift face up in frame.
    crop_y_d = max(-0.06, min(0.06, -oy * 0.55))
    if tb is not None and abs(tb) > 0.03:
        crop_y_d = max(-0.06, min(0.06, crop_y_d - tb * 0.35))

    parts = []
    if centred:
        summary = "Head is centred in the PiP circle (L≈R, T≈B)."
        detail = summary
    else:
        if abs(ox) >= 0.03:
            parts.append(
                "increase crop_x" if ox > 0 else "decrease crop_x",
            )
        if abs(oy) >= 0.03:
            parts.append(
                "decrease crop_y" if oy > 0 else "increase crop_y",
            )
        if lr is not None and abs(lr) > 0.04 and not parts:
            parts.append("increase crop_x" if lr > 0 else "decrease crop_x")
        summary = "Move head toward centre: " + ", ".join(parts) if parts else "Adjust crop_x / crop_y"
        detail = (
            f"offset_x={ox:+.3f} offset_y={oy:+.3f} "
            f"(try crop_x {crop_x_d:+.3f}, crop_y {crop_y_d:+.3f} from current values)"
        )
        if lr is not None:
            detail += f" | margin L−R={lr:+.3f} T−B={tb:+.3f}" if tb is not None else f" | margin L−R={lr:+.3f}"

    return PipCentringAdvice(
        is_centred=centred,
        offset_x=ox,
        offset_y=oy,
        margin_lr_delta=lr,
        margin_tb_delta=tb,
        crop_x_delta=round(crop_x_d, 3),
        crop_y_delta=round(crop_y_d, 3),
        summary=summary,
        detail=detail,
    )


def face_centre_symmetry_score(metrics: PipFaceMetrics) -> float:
    """Lower is better — used by calibration to match validation diagram L/R/T/B."""
    if metrics.face_fx is None:
        return 1.0
    score = abs(metrics.centre_offset_x) + 0.6 * abs(metrics.centre_offset_y)
    lr = metrics.margin_lr_delta
    tb = metrics.margin_tb_delta
    if lr is not None:
        score += 0.5 * abs(lr)
    if tb is not None:
        score += 0.5 * abs(tb)
    return score


def _circle_margins_for_bbox(
    xmin: float, ymin: float, xmax: float, ymax: float,
) -> Tuple[float, float, float, float]:
    """Min normalised distance from bbox edges to the unit-circle inscribed in a unit square."""
    samples = 24
    left_m = right_m = top_m = bottom_m = 1.0
    for i in range(samples + 1):
        t = i / samples
        y = ymin + (ymax - ymin) * t
        cy = y - 0.5
        if abs(cy) >= 0.5:
            continue
        half_chord = math.sqrt(max(0.0, 0.25 - cy * cy))
        x_lo = 0.5 - half_chord
        x_hi = 0.5 + half_chord
        left_m = min(left_m, xmin - x_lo)
        right_m = min(right_m, x_hi - xmax)
    for i in range(samples + 1):
        t = i / samples
        x = xmin + (xmax - xmin) * t
        cx = x - 0.5
        if abs(cx) >= 0.5:
            continue
        half_chord = math.sqrt(max(0.0, 0.25 - cx * cx))
        y_lo = 0.5 - half_chord
        y_hi = 0.5 + half_chord
        top_m = min(top_m, ymin - y_lo)
        bottom_m = min(bottom_m, y_hi - ymax)
    return left_m, right_m, top_m, bottom_m


def measure_pip_image(
    image_path: str | Path,
    *,
    detector: str = "auto",
    min_confidence: float = 0.5,
) -> PipFaceMetrics:
    """Measure face centre and margins inside an existing PiP PNG (ideally circular)."""
    from PIL import Image

    from .face_detect import detect_face_centre

    path = Path(image_path)
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        w, h = rgba.size
        balance = pip_face_balance(rgba)

    centre = detect_face_centre(path, detector=detector, min_confidence=min_confidence)
    if centre is None:
        return PipFaceMetrics(
            face_fx=None,
            face_fy=None,
            centre_offset_x=0.0,
            centre_offset_y=0.0,
            balance=balance,
            margin_left=None,
            margin_right=None,
            margin_top=None,
            margin_bottom=None,
        )

    fx, fy = centre.fx, centre.fy
    xmin, xmax = centre.xmin, centre.xmax
    ymin, ymax = centre.ymin, centre.ymax

    left_m, right_m, top_m, bottom_m = _circle_margins_for_bbox(xmin, ymin, xmax, ymax)

    return PipFaceMetrics(
        face_fx=fx,
        face_fy=fy,
        centre_offset_x=fx - 0.5,
        centre_offset_y=fy - 0.5,
        balance=balance,
        margin_left=left_m,
        margin_right=right_m,
        margin_top=top_m,
        margin_bottom=bottom_m,
        detector=centre.detector,
        face_xmin=xmin,
        face_ymin=ymin,
        face_xmax=xmax,
        face_ymax=ymax,
    )


def render_pip_probe_frame(
    video_path: str,
    *,
    seek_sec: float = 0.5,
    crop_x: float = 0.5,
    crop_y: float = 0.03,
    zoom: float = 1.45,
    width: int = 461,
    height: int = 461,
    shape: str = "circle",
    tmp_dir: Optional[Path] = None,
) -> Path:
    """Render one PiP probe PNG (same ffmpeg path as avatar calibration)."""
    path = Path(video_path)
    work = tmp_dir or path.parent / ".praisonaippt-calibrate"
    work.mkdir(parents=True, exist_ok=True)
    out = work / f"measure_{seek_sec:.2f}_{crop_x:.3f}.png"
    vf = _cover_scale_filter(
        width, height, crop_x_ratio=crop_x, crop_y_ratio=crop_y, zoom_ratio=zoom,
    )
    if shape in ("circle", "round", "rounded"):
        vf = f"{vf},{_circle_alpha_filter()}"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{seek_sec:.3f}", "-i", str(path),
            "-vframes", "1", "-vf", vf, str(out),
        ],
        check=True,
        timeout=60,
    )
    return out


def measure_pip_video(
    video_path: str,
    *,
    seek_sec: float = 0.5,
    crop_x: float = 0.5,
    crop_y: float = 0.03,
    zoom: float = 1.45,
    width: int = 461,
    height: int = 461,
    shape: str = "circle",
    detector: str = "auto",
    min_confidence: float = 0.5,
    tmp_dir: Optional[Path] = None,
) -> Tuple[PipFaceMetrics, Path]:
    """Render a PiP probe from video and return metrics + probe image path."""
    probe = render_pip_probe_frame(
        video_path,
        seek_sec=seek_sec,
        crop_x=crop_x,
        crop_y=crop_y,
        zoom=zoom,
        width=width,
        height=height,
        shape=shape,
        tmp_dir=tmp_dir,
    )
    metrics = measure_pip_image(
        probe, detector=detector, min_confidence=min_confidence,
    )
    return metrics, probe


def default_validation_image_path(probe_path: str | Path) -> Path:
    """Default annotated diagram path beside the probe PNG."""
    p = Path(probe_path)
    return p.with_name(f"{p.stem}_pip_validation.png")


def _circle_x_bounds_at_y(cx: float, cy: float, r: float, y: float) -> Tuple[float, float]:
    dy = y - cy
    if abs(dy) >= r:
        return cx, cx
    half = math.sqrt(max(0.0, r * r - dy * dy))
    return cx - half, cx + half


def _circle_y_bounds_at_x(cx: float, cy: float, r: float, x: float) -> Tuple[float, float]:
    dx = x - cx
    if abs(dx) >= r:
        return cy, cy
    half = math.sqrt(max(0.0, r * r - dx * dx))
    return cy - half, cy + half


def save_pip_validation_diagram(
    image_path: str | Path,
    metrics: PipFaceMetrics,
    output_path: str | Path,
) -> Path:
    """Draw centre crosshair, face bbox, and side margin lines with pixel labels."""
    from PIL import Image, ImageDraw, ImageFont

    src = Path(image_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(src) as im:
        base = im.convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = w / 2.0, h / 2.0
    r = min(w, h) / 2.0 * 0.98

    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        outline=(0, 255, 120, 220),
        width=3,
    )
    cross = 14
    draw.line((cx - cross, cy, cx + cross, cy), fill=(0, 255, 120, 255), width=2)
    draw.line((cx, cy - cross, cx, cy + cross), fill=(0, 255, 120, 255), width=2)
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(0, 255, 120, 255))

    font = ImageFont.load_default()
    label_h = 12

    def _text(pos: Tuple[float, float], text: str, fill: Tuple[int, int, int, int]) -> None:
        draw.text(pos, text, fill=fill, font=font)

    if metrics.face_fx is not None and metrics.face_fy is not None:
        fx = metrics.face_fx * w
        fy = metrics.face_fy * h
        draw.ellipse((fx - 6, fy - 6, fx + 6, fy + 6), fill=(80, 160, 255, 255))
        draw.line((cx, cy, fx, fy), fill=(80, 160, 255, 160), width=1)

    if metrics.face_xmin is not None:
        x0 = metrics.face_xmin * w
        y0 = metrics.face_ymin * h
        x1 = metrics.face_xmax * w
        y1 = metrics.face_ymax * h
        draw.rectangle((x0, y0, x1, y1), outline=(255, 220, 60, 255), width=2)

        if metrics.margin_left is not None:
            mid_y = (y0 + y1) / 2.0
            x_lo, x_hi = _circle_x_bounds_at_y(cx, cy, r, mid_y)
            # Left: bbox left → circle edge
            draw.line((x_lo, mid_y, x0, mid_y), fill=(255, 140, 40, 255), width=3)
            px_l = max(0, int(round((x0 - x_lo))))
            _text((x_lo + 2, mid_y - label_h - 2), f"L {px_l}px", (255, 180, 80, 255))
            # Right
            draw.line((x1, mid_y, x_hi, mid_y), fill=(60, 220, 255, 255), width=3)
            px_r = max(0, int(round((x_hi - x1))))
            _text((x1 + 2, mid_y + 2), f"R {px_r}px", (120, 230, 255, 255))
            # Top
            mid_x = (x0 + x1) / 2.0
            y_lo, y_hi = _circle_y_bounds_at_x(cx, cy, r, mid_x)
            draw.line((mid_x, y_lo, mid_x, y0), fill=(220, 100, 255, 255), width=3)
            px_t = max(0, int(round((y0 - y_lo))))
            _text((mid_x + 4, y_lo + 2), f"T {px_t}px", (230, 150, 255, 255))
            # Bottom
            draw.line((mid_x, y1, mid_x, y_hi), fill=(255, 100, 180, 255), width=3)
            px_b = max(0, int(round((y_hi - y1))))
            _text((mid_x + 4, y1 - label_h - 2), f"B {px_b}px", (255, 150, 200, 255))

    composed = Image.alpha_composite(base, overlay)
    banner_h = 56
    canvas = Image.new("RGB", (w, h + banner_h), (18, 18, 22))
    canvas.paste(composed.convert("RGB"), (0, 0))

    banner = ImageDraw.Draw(canvas)
    centred = "YES" if metrics.is_centred else "no"
    off_x = metrics.centre_offset_x
    off_y = metrics.centre_offset_y
    line1 = (
        f"offset_x={off_x:+.3f}  offset_y={off_y:+.3f}  balance={metrics.balance:+.3f}  "
        f"centred={centred}"
    )
    if metrics.margin_left is not None:
        ml = int(round(metrics.margin_left * w))
        mr = int(round(metrics.margin_right * w))
        mt = int(round(metrics.margin_top * h))
        mb = int(round(metrics.margin_bottom * h))
        line2 = f"margins px: L {ml}  R {mr}  T {mt}  B {mb}  (L≈R and T≈B when centred)"
    else:
        line2 = "face not detected — install praisonaippt[avatar-calibrate]"
    det = metrics.detector or "n/a"
    line3 = f"detector={det}  green=circle centre  yellow=face box  L/R/T/B=gap to circle"

    banner.text((8, h + 6), line1, fill=(230, 230, 235), font=font)
    banner.text((8, h + 20), line2, fill=(180, 190, 200), font=font)
    banner.text((8, h + 34), line3, fill=(140, 150, 165), font=font)

    canvas.save(out, format="PNG")
    return out


def write_validation_for_probe(
    probe_path: str | Path,
    metrics: PipFaceMetrics,
    output_path: Optional[str | Path] = None,
) -> Path:
    """Save annotated diagram for an existing probe PNG."""
    probe = Path(probe_path)
    out = Path(output_path) if output_path else default_validation_image_path(probe)
    return save_pip_validation_diagram(probe, metrics, out)


def format_pip_face_report(metrics: PipFaceMetrics, *, probe_path: Optional[Path] = None) -> str:
    lines = ["PiP face centre measurement:"]
    lines.append(f"  {metrics.summary_line()}")
    if metrics.margin_left is not None:
        lines.append(
            f"  margins (norm): left={metrics.margin_left:.3f} right={metrics.margin_right:.3f} "
            f"top={metrics.margin_top:.3f} bottom={metrics.margin_bottom:.3f}"
        )
    if metrics.face_fx is not None:
        if metrics.centre_offset_x > 0.03:
            lines.append("  hint: face is right of centre — increase crop_x_ratio to shift face left")
        elif metrics.centre_offset_x < -0.03:
            lines.append("  hint: face is left of centre — decrease crop_x_ratio to shift face right")
    if probe_path:
        lines.append(f"  probe: {probe_path}")
    advice = centring_advice(metrics)
    lines.append(f"  centred: {'yes' if advice.is_centred else 'no'}")
    lines.append(f"  {advice.summary}")
    if not advice.is_centred:
        lines.append(f"  adjust: {advice.detail}")
    if metrics.margin_left is not None:
        lines.append(
            "  (use --validation-image to save a diagram with L/R/T/B pixel gaps to the circle)"
        )
    return "\n".join(lines)

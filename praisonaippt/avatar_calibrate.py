"""Automatic PiP / panel avatar framing from source video (hybrid face detect + balance refine)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .ffmpeg_composer import (
    _circle_alpha_filter,
    _cover_scale_filter,
    face_x_to_crop_x_ratio,
    ffprobe_media_size,
    pip_face_balance,
)
from .layout_tokens import layout_in
from .utils import resolve_asset_path

_MAX_CALIBRATION_SEEKS = 3
_CACHE_VERSION = 4
_LOCAL_SWEEP_RADIUS = 0.04
_LOCAL_SWEEP_STEP = 0.01


@dataclass
class CalibrationConfig:
    """Runtime options from ``avatar_calibration`` YAML block."""

    method: str = "hybrid"
    crop_x_preferred: float = 0.53
    crop_x_window: Tuple[float, float] = (0.50, 0.56)
    crop_y_preferred: float = 0.03
    anchor_weight: float = 0.15
    detector: str = "auto"
    min_detection_confidence: float = 0.5
    crop_x_step: float = 0.01

    @classmethod
    def from_dict(cls, raw: Optional[dict], *, pip_layout: Optional[dict] = None) -> "CalibrationConfig":
        raw = raw or {}
        pip = pip_layout or {}
        window = raw.get("crop_x_window") or [0.50, 0.56]
        if len(window) >= 2:
            win = (float(window[0]), float(window[1]))
        else:
            win = (0.50, 0.56)
        crop_y = raw.get("crop_y_preferred")
        if crop_y is None:
            crop_y = pip.get("crop_y_ratio", 0.03)
        return cls(
            method=str(raw.get("method", "hybrid")).lower(),
            crop_x_preferred=float(raw.get("crop_x_preferred", 0.53)),
            crop_x_window=win,
            crop_y_preferred=float(crop_y),
            anchor_weight=float(raw.get("anchor_weight", 0.15)),
            detector=str(raw.get("detector", "auto")).lower(),
            min_detection_confidence=float(raw.get("min_detection_confidence", 0.5)),
            crop_x_step=float(raw.get("crop_x_step", 0.01)),
        )

    def cache_key_part(self) -> str:
        """Stable string for cache invalidation when tuning parameters change."""
        lo, hi = self.crop_x_window
        return (
            f"{self.method}:{self.crop_x_preferred}:{lo}:{hi}:"
            f"{self.anchor_weight}:{self.detector}:{self.min_detection_confidence}:"
            f"{self.crop_x_step}:{self.crop_y_preferred}"
        )


def _effective_detector(cfg: CalibrationConfig) -> str:
    if cfg.method == "yolo":
        return "yolo"
    if cfg.method == "mediapipe":
        return "mediapipe"
    return cfg.detector


@dataclass
class AvatarFramingResult:
    """Calibrated crop/zoom for one avatar source file."""

    video_path: str
    crop_x_ratio: float
    crop_y_ratio: float
    zoom_ratio: float
    balance_score: float
    seek_samples: List[float] = field(default_factory=list)
    layout_kind: str = "pip"
    shape: str = "circle"
    method: str = "hybrid"
    detector: str = ""
    seed_x: float = 0.0
    version: int = _CACHE_VERSION

    def to_layout_dict(self) -> Dict[str, float]:
        return {
            "crop_x_ratio": round(self.crop_x_ratio, 3),
            "crop_y_ratio": round(self.crop_y_ratio, 3),
            "zoom_ratio": round(self.zoom_ratio, 2),
        }


def pip_probe_size_px(style: dict, slide_w_px: int = 1920) -> Tuple[int, int]:
    """Square PiP probe size matching export width_ratio on a 1920px-wide frame."""
    ratio = float(layout_in(style, "pip", "width_ratio", 0.14))
    size = max(64, int(round(slide_w_px * ratio)))
    return size, size


def collect_avatar_seek_samples(data: dict) -> Dict[str, List[float]]:
    """Map each ``avatar_video_path`` to seek times from verse ``audio_start_sec``."""
    out: Dict[str, List[float]] = {}
    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for verse in section.get("verses") or []:
            if not isinstance(verse, dict):
                continue
            av = verse.get("avatar_video_path")
            if not av:
                continue
            seeks = out.setdefault(str(av), [])
            if verse.get("audio_start_sec") is not None:
                seeks.append(max(0.0, float(verse["audio_start_sec"]) + 0.35))
    for key, seeks in list(out.items()):
        if 0.5 not in seeks:
            seeks.append(0.5)
        seeks = sorted(set(seeks))
        if len(seeks) > _MAX_CALIBRATION_SEEKS:
            mid = seeks[len(seeks) // 2]
            seeks = [seeks[0], mid, seeks[-1]]
        out[key] = seeks
    return out


def _cache_path(
    video: Path,
    cache_dir: Path,
    cfg: CalibrationConfig,
    *,
    probe_w: int,
    probe_h: int,
    zoom: float,
    shape: str,
) -> Path:
    stat = video.stat()
    key = (
        f"v{_CACHE_VERSION}:{video.resolve()}:{stat.st_size}:{int(stat.st_mtime)}:"
        f"{cfg.cache_key_part()}:{probe_w}:{probe_h}:{zoom}:{shape}"
    )
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.json"


def _extract_raw_frame(
    video: str,
    seek_sec: float,
    tmp_dir: Path,
) -> Path:
    out = tmp_dir / f"raw_{seek_sec:.2f}.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{seek_sec:.3f}", "-i", video,
            "-vframes", "1", str(out),
        ],
        check=True,
        timeout=60,
    )
    return out


def _pip_balance_at_seek(
    video: str,
    *,
    crop_x: float,
    crop_y: float,
    zoom: float,
    seek_sec: float,
    width: int,
    height: int,
    shape: str = "circle",
    tmp_dir: Path,
) -> float:
    """Fast face-balance probe (same ffmpeg crop as export, no full segment render)."""
    from PIL import Image

    out = tmp_dir / f"probe_{seek_sec:.2f}_{crop_x:.3f}.png"
    vf = _cover_scale_filter(
        width, height, crop_x_ratio=crop_x, crop_y_ratio=crop_y, zoom_ratio=zoom,
    )
    if shape in ("circle", "round", "rounded"):
        vf = f"{vf},{_circle_alpha_filter()}"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{seek_sec:.3f}", "-i", video,
            "-vframes", "1", "-vf", vf, str(out),
        ],
        check=True,
        timeout=60,
    )
    with Image.open(out) as im:
        return pip_face_balance(im)


def _pip_metrics_at_seek(
    video: str,
    *,
    crop_x: float,
    crop_y: float,
    zoom: float,
    seek_sec: float,
    width: int,
    height: int,
    shape: str = "circle",
    tmp_dir: Path,
    detector: str = "auto",
    min_confidence: float = 0.5,
):
    """Face metrics on a PiP probe frame (same path as validation diagram)."""
    from .pip_face_measure import measure_pip_image

    out = tmp_dir / f"metrics_{seek_sec:.2f}_{crop_x:.3f}_{crop_y:.2f}.png"
    vf = _cover_scale_filter(
        width, height, crop_x_ratio=crop_x, crop_y_ratio=crop_y, zoom_ratio=zoom,
    )
    if shape in ("circle", "round", "rounded"):
        vf = f"{vf},{_circle_alpha_filter()}"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{seek_sec:.3f}", "-i", video,
            "-vframes", "1", "-vf", vf, str(out),
        ],
        check=True,
        timeout=60,
    )
    return measure_pip_image(
        out, detector=detector, min_confidence=min_confidence,
    )


def _iter_crop_y_values(centre: float, *, radius: float = 0.06, step: float = 0.01) -> List[float]:
    lo = max(0.0, centre - radius)
    hi = min(0.14, centre + radius)
    values: List[float] = []
    y = lo
    while y <= hi + 1e-9:
        values.append(round(y, 3))
        y += step
    return values or [round(centre, 3)]


def _pick_best_crop_x_face_centred(
    video: str,
    seeks: Sequence[float],
    *,
    candidates: Sequence[float],
    cfg: CalibrationConfig,
    crop_y: float,
    zoom: float,
    width: int,
    height: int,
    shape: str,
    tmp_dir: Path,
) -> Tuple[float, float]:
    """Pick crop_x minimising face offset and L/R margin asymmetry (validation diagram parity)."""
    from .pip_face_measure import face_centre_symmetry_score

    det = _effective_detector(cfg)
    best_x = _clamp_window(candidates[0], cfg)
    best_score = 1e9
    for x in candidates:
        scores: List[float] = []
        for seek in seeks:
            try:
                m = _pip_metrics_at_seek(
                    video,
                    crop_x=x,
                    crop_y=crop_y,
                    zoom=zoom,
                    seek_sec=seek,
                    width=width,
                    height=height,
                    shape=shape,
                    tmp_dir=tmp_dir,
                    detector=det,
                    min_confidence=cfg.min_detection_confidence,
                )
                scores.append(face_centre_symmetry_score(m))
            except (subprocess.SubprocessError, OSError):
                scores.append(1.0)
        mean_s = sum(scores) / len(scores) if scores else 1.0
        score = mean_s + cfg.anchor_weight * (x - cfg.crop_x_preferred) ** 2
        if score < best_score:
            best_score = score
            best_x = x
    return best_x, best_score


def _pick_best_crop_y_face_centred(
    video: str,
    seeks: Sequence[float],
    *,
    crop_x: float,
    centre_y: float,
    cfg: CalibrationConfig,
    zoom: float,
    width: int,
    height: int,
    shape: str,
    tmp_dir: Path,
) -> Tuple[float, float]:
    from .pip_face_measure import face_centre_symmetry_score

    det = _effective_detector(cfg)
    candidates = _iter_crop_y_values(centre_y)
    best_y = centre_y
    best_score = 1e9
    for y in candidates:
        scores: List[float] = []
        for seek in seeks:
            try:
                m = _pip_metrics_at_seek(
                    video,
                    crop_x=crop_x,
                    crop_y=y,
                    zoom=zoom,
                    seek_sec=seek,
                    width=width,
                    height=height,
                    shape=shape,
                    tmp_dir=tmp_dir,
                    detector=det,
                    min_confidence=cfg.min_detection_confidence,
                )
                scores.append(face_centre_symmetry_score(m))
            except (subprocess.SubprocessError, OSError):
                scores.append(1.0)
        mean_s = sum(scores) / len(scores) if scores else 1.0
        score = mean_s + 0.05 * (y - cfg.crop_y_preferred) ** 2
        if score < best_score:
            best_score = score
            best_y = y
    return best_y, best_score


def _anchored_score(mean_balance: float, crop_x: float, cfg: CalibrationConfig) -> float:
    penalty = cfg.anchor_weight * (crop_x - cfg.crop_x_preferred) ** 2
    return mean_balance + penalty


def _mean_balance_for_crop_x(
    video: str,
    crop_x: float,
    *,
    seeks: Sequence[float],
    crop_y: float,
    zoom: float,
    width: int,
    height: int,
    shape: str,
    tmp_dir: Path,
) -> float:
    scores: List[float] = []
    for seek in seeks:
        try:
            scores.append(
                abs(
                    _pip_balance_at_seek(
                        video,
                        crop_x=crop_x,
                        crop_y=crop_y,
                        zoom=zoom,
                        seek_sec=seek,
                        width=width,
                        height=height,
                        shape=shape,
                        tmp_dir=tmp_dir,
                    )
                )
            )
        except (subprocess.SubprocessError, OSError):
            scores.append(1.0)
    return sum(scores) / len(scores) if scores else 1.0


def _clamp_window(x: float, cfg: CalibrationConfig) -> float:
    lo, hi = cfg.crop_x_window
    return max(lo, min(hi, x))


def _iter_sweep_values(center: float, cfg: CalibrationConfig) -> List[float]:
    lo, hi = cfg.crop_x_window
    start = max(lo, center - _LOCAL_SWEEP_RADIUS)
    end = min(hi, center + _LOCAL_SWEEP_RADIUS)
    values: List[float] = []
    x = start
    while x <= end + 1e-9:
        values.append(round(x, 4))
        x += cfg.crop_x_step
    if not values:
        values.append(_clamp_window(center, cfg))
    return values


def _face_seed_crop_x(
    video: str,
    seeks: Sequence[float],
    *,
    cfg: CalibrationConfig,
    probe_w: int,
    probe_h: int,
    zoom: float,
    tmp_dir: Path,
) -> Tuple[float, str]:
    from .face_detect import detect_face_centre

    try:
        sw, sh = ffprobe_media_size(video)
    except (RuntimeError, OSError):
        return cfg.crop_x_preferred, ""

    ratios: List[float] = []
    detector = ""
    for seek in seeks:
        try:
            frame = _extract_raw_frame(video, seek, tmp_dir)
            centre = detect_face_centre(
                frame,
                detector=_effective_detector(cfg),
                min_confidence=cfg.min_detection_confidence,
            )
            if centre is None:
                continue
            detector = centre.detector
            ratios.append(
                face_x_to_crop_x_ratio(
                    centre.fx, sw, sh, probe_w, probe_h, zoom_ratio=zoom,
                )
            )
        except (subprocess.SubprocessError, OSError):
            continue

    if not ratios:
        return cfg.crop_x_preferred, detector

    derived = sum(ratios) / len(ratios)
    derived = _clamp_window(derived, cfg)
    blended = 0.7 * derived + 0.3 * cfg.crop_x_preferred
    return _clamp_window(blended, cfg), detector


def _iter_window_crop_values(cfg: CalibrationConfig) -> List[float]:
    lo, hi = cfg.crop_x_window
    values: List[float] = []
    x = lo
    while x <= hi + 1e-9:
        values.append(round(x, 4))
        x += cfg.crop_x_step
    return values or [_clamp_window(cfg.crop_x_preferred, cfg)]


def _pick_best_crop_x(
    video: str,
    seeks: Sequence[float],
    *,
    candidates: Sequence[float],
    cfg: CalibrationConfig,
    crop_y: float,
    zoom: float,
    width: int,
    height: int,
    shape: str,
    tmp_dir: Path,
) -> Tuple[float, float]:
    best_x = _clamp_window(candidates[0], cfg)
    best_score = 1e9
    for x in candidates:
        mean_bal = _mean_balance_for_crop_x(
            video, x, seeks=seeks, crop_y=crop_y, zoom=zoom,
            width=width, height=height, shape=shape, tmp_dir=tmp_dir,
        )
        score = _anchored_score(mean_bal, x, cfg)
        if score < best_score:
            best_score = score
            best_x = x
    return best_x, best_score


def calibrate_avatar_framing(
    video_path: str,
    *,
    seek_secs: Optional[Sequence[float]] = None,
    crop_y_ratio: float = 0.03,
    zoom_ratio: float = 1.45,
    layout_kind: str = "pip",
    shape: str = "circle",
    crop_x_range: Optional[Tuple[float, float]] = None,
    crop_x_step: float = 0.02,
    tmp_dir: Optional[Path] = None,
    source_file: Optional[str] = None,
    config: Optional[CalibrationConfig] = None,
    probe_width: Optional[int] = None,
    probe_height: Optional[int] = None,
) -> AvatarFramingResult:
    """Pick ``crop_x_ratio`` using hybrid face detection and anchored balance refine."""
    cfg = config or CalibrationConfig()
    if crop_x_range is not None:
        cfg = CalibrationConfig(
            method=cfg.method,
            crop_x_preferred=cfg.crop_x_preferred,
            crop_x_window=crop_x_range,
            crop_y_preferred=crop_y_ratio,
            anchor_weight=cfg.anchor_weight,
            detector=cfg.detector,
            min_detection_confidence=cfg.min_detection_confidence,
            crop_x_step=crop_x_step if crop_x_step != 0.02 else cfg.crop_x_step,
        )

    resolved = resolve_asset_path(video_path, source_file=source_file)
    path = Path(resolved if resolved else video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Avatar video not found: {video_path}")

    seeks = list(seek_secs or [0.5, 2.0])
    work = tmp_dir or Path(path.parent) / ".praisonaippt-calibrate"
    work.mkdir(parents=True, exist_ok=True)

    if probe_width is None:
        pw, ph = pip_probe_size_px({"layouts": {"pip": {"width_ratio": 0.24}}})
    else:
        pw = probe_width
        ph = probe_height or probe_width
    method = cfg.method

    if method == "fixed":
        crop_x = _clamp_window(cfg.crop_x_preferred, cfg)
        score = _mean_balance_for_crop_x(
            str(path), crop_x, seeks=seeks, crop_y=crop_y_ratio, zoom=zoom_ratio,
            width=pw, height=ph, shape=shape, tmp_dir=work,
        )
        return AvatarFramingResult(
            video_path=str(path),
            crop_x_ratio=round(crop_x, 3),
            crop_y_ratio=crop_y_ratio,
            zoom_ratio=zoom_ratio,
            balance_score=round(score, 4),
            seek_samples=list(seeks),
            layout_kind=layout_kind,
            shape=shape,
            method=method,
            seed_x=crop_x,
            version=_CACHE_VERSION,
        )

    seed_x, detector = cfg.crop_x_preferred, ""
    if method in ("hybrid", "mediapipe", "yolo"):
        seed_x, detector = _face_seed_crop_x(
            str(path), seeks, cfg=cfg, probe_w=pw, probe_h=ph, zoom=zoom_ratio, tmp_dir=work,
        )

    if method in ("mediapipe", "yolo"):
        crop_x = round(_clamp_window(seed_x if detector else cfg.crop_x_preferred, cfg), 3)
        score = _mean_balance_for_crop_x(
            str(path), crop_x, seeks=seeks, crop_y=crop_y_ratio, zoom=zoom_ratio,
            width=pw, height=ph, shape=shape, tmp_dir=work,
        )
        return AvatarFramingResult(
            video_path=str(path),
            crop_x_ratio=crop_x,
            crop_y_ratio=crop_y_ratio,
            zoom_ratio=zoom_ratio,
            balance_score=round(score, 4),
            seek_samples=list(seeks),
            layout_kind=layout_kind,
            shape=shape,
            method=method,
            detector=detector,
            seed_x=round(seed_x, 3),
            version=_CACHE_VERSION,
        )

    if method == "balance":
        candidates = _iter_window_crop_values(cfg)
        best_x, best_score = _pick_best_crop_x(
            str(path), seeks,
            candidates=candidates,
            cfg=cfg,
            crop_y=crop_y_ratio,
            zoom=zoom_ratio,
            width=pw,
            height=ph,
            shape=shape,
            tmp_dir=work,
        )
        best_y = crop_y_ratio
    else:
        sweep_centre = seed_x if method == "hybrid" else cfg.crop_x_preferred
        candidates = _iter_sweep_values(sweep_centre, cfg)
        best_x, best_score = _pick_best_crop_x_face_centred(
            str(path), seeks,
            candidates=candidates,
            cfg=cfg,
            crop_y=crop_y_ratio,
            zoom=zoom_ratio,
            width=pw,
            height=ph,
            shape=shape,
            tmp_dir=work,
        )
        best_y, _ = _pick_best_crop_y_face_centred(
            str(path), seeks,
            crop_x=best_x,
            centre_y=crop_y_ratio,
            cfg=cfg,
            zoom=zoom_ratio,
            width=pw,
            height=ph,
            shape=shape,
            tmp_dir=work,
        )

    return AvatarFramingResult(
        video_path=str(path),
        crop_x_ratio=round(best_x, 3),
        crop_y_ratio=round(best_y, 3),
        zoom_ratio=zoom_ratio,
        balance_score=round(best_score, 4),
        seek_samples=list(seeks),
        layout_kind=layout_kind,
        shape=shape,
        method=method,
        detector=detector,
        seed_x=round(seed_x, 3),
        version=_CACHE_VERSION,
    )


def load_cached_framing(
    video_path: str,
    cache_dir: Path,
    *,
    source_file: Optional[str] = None,
    config: Optional[CalibrationConfig] = None,
    probe_w: int = 461,
    probe_h: int = 461,
    zoom: float = 1.45,
    shape: str = "circle",
) -> Optional[AvatarFramingResult]:
    resolved = resolve_asset_path(video_path, source_file=source_file)
    path = Path(resolved if resolved else video_path)
    if not path.is_file():
        return None
    cfg = config or CalibrationConfig()
    cache_file = _cache_path(
        path, cache_dir, cfg, probe_w=probe_w, probe_h=probe_h, zoom=zoom, shape=shape,
    )
    if not cache_file.is_file():
        return None
    try:
        raw = json.loads(cache_file.read_text(encoding="utf-8"))
        if int(raw.get("version", 0)) < _CACHE_VERSION:
            return None
        allowed = {f.name for f in AvatarFramingResult.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in allowed}
        return AvatarFramingResult(**filtered)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def save_cached_framing(
    result: AvatarFramingResult,
    cache_dir: Path,
    *,
    config: Optional[CalibrationConfig] = None,
    probe_w: int = 461,
    probe_h: int = 461,
    zoom: float = 1.45,
    shape: str = "circle",
) -> Path:
    cfg = config or CalibrationConfig()
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = _cache_path(
        Path(result.video_path), cache_dir, cfg,
        probe_w=probe_w, probe_h=probe_h, zoom=zoom, shape=shape,
    )
    out.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    return out


def merge_framing_into_slide_style(style: dict, result: AvatarFramingResult, *, layout_kind: str = "pip") -> dict:
    """Write calibrated values under ``slide_style.layouts.<kind>``."""
    style = dict(style or {})
    layouts = dict(style.get("layouts") or {})
    block = dict(layouts.get(layout_kind) or {})
    block.update(result.to_layout_dict())
    layouts[layout_kind] = block
    style["layouts"] = layouts
    return style


def calibrate_deck_avatars(
    data: dict,
    *,
    cache_dir: Optional[Path] = None,
    force: bool = False,
    source_file: Optional[str] = None,
) -> Dict[str, AvatarFramingResult]:
    """Calibrate every unique ``avatar_video_path`` referenced in *data*."""
    sf = source_file or data.get("_source_file")
    base = Path(sf).parent if sf else Path.cwd()
    cache = cache_dir or base / ".praisonaippt" / "avatar-framing"
    cfg = CalibrationConfig.from_dict(
        data.get("avatar_calibration"),
        pip_layout=((data.get("slide_style") or {}).get("layouts") or {}).get("pip"),
    )
    samples = collect_avatar_seek_samples(data)
    results: Dict[str, AvatarFramingResult] = {}
    style = data.get("slide_style") or {}
    pip = (style.get("layouts") or {}).get("pip") or {}
    crop_y = float(pip.get("crop_y_ratio", cfg.crop_y_preferred))
    zoom = float(pip.get("zoom_ratio", 1.45))
    shape = str(pip.get("shape", "circle"))
    pw, ph = pip_probe_size_px(style)

    for av_path, seeks in samples.items():
        if not force:
            cached = load_cached_framing(
                av_path, cache, source_file=sf, config=cfg,
                probe_w=pw, probe_h=ph, zoom=zoom, shape=shape,
            )
            if cached:
                results[av_path] = cached
                continue
        result = calibrate_avatar_framing(
            av_path,
            seek_secs=seeks,
            crop_y_ratio=crop_y,
            zoom_ratio=zoom,
            source_file=sf,
            config=cfg,
            probe_width=pw,
            probe_height=ph,
            shape=shape,
        )
        save_cached_framing(
            result, cache, config=cfg, probe_w=pw, probe_h=ph, zoom=zoom, shape=shape,
        )
        results[av_path] = result
    return results


def maybe_auto_calibrate_deck(data: dict, *, source_file: Optional[str] = None) -> dict:
    """When ``avatar_calibration.auto`` is true, merge calibrated pip framing into *data*."""
    cfg = data.get("avatar_calibration") or {}
    if not cfg.get("auto"):
        return data
    force = bool(cfg.get("force"))
    cache_raw = cfg.get("cache_dir")
    cache_dir = Path(cache_raw) if cache_raw else None
    results = calibrate_deck_avatars(
        data, cache_dir=cache_dir, force=force, source_file=source_file,
    )
    if not results:
        return data
    primary = next(iter(results.values()))
    style = merge_framing_into_slide_style(data.get("slide_style") or {}, primary)
    data = dict(data)
    data["slide_style"] = style
    data["_avatar_calibration"] = {k: asdict(v) for k, v in results.items()}
    return data


def format_calibration_report(results: Dict[str, AvatarFramingResult]) -> str:
    lines = ["Avatar framing calibration:"]
    for path, r in results.items():
        name = Path(path).name
        det = f" detector={r.detector}" if r.detector else ""
        lines.append(
            f"  {name}: method={r.method} seed_x={r.seed_x} → crop_x={r.crop_x_ratio} "
            f"balance={r.balance_score}{det}"
        )
        lines.append(
            f"    full path: {path}  crop_y={r.crop_y_ratio} zoom={r.zoom_ratio} seeks={r.seek_samples}"
        )
    return "\n".join(lines)


def calibration_deps_hint(cfg: Optional[CalibrationConfig] = None) -> str:
    """Short hint when ML calibration extras are missing."""
    cfg = cfg or CalibrationConfig()
    det = _effective_detector(cfg)
    if cfg.method not in ("hybrid", "mediapipe", "yolo") and det not in ("auto", "mediapipe", "yunet", "yolo"):
        return ""
    if det == "yolo":
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            return (
                'Tip: pip install -e ".[avatar-calibrate-yolo]" for YOLO face detection '
                "(AGPL) or set avatar_calibration.method: balance."
            )
        return ""
    from .face_detect import mediapipe_available

    try:
        import cv2  # noqa: F401
        has_cv = True
    except ImportError:
        has_cv = False
    if det == "yunet" and not has_cv:
        return 'Tip: pip install -e ".[avatar-calibrate]" for OpenCV YuNet (or method: balance).'
    if det in ("auto", "mediapipe") and not mediapipe_available() and not has_cv:
        return (
            'Tip: pip install -e ".[avatar-calibrate]" for MediaPipe face detection '
            "(or set avatar_calibration.method: balance)."
        )
    return ""

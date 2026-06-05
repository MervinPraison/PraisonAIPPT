"""Text-region detection for hero panel placement (Paddle/RapidOCR, EAST, MSER heuristic)."""

from __future__ import annotations

import tarfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

_MODEL_CACHE = Path.home() / ".praisonaippt" / "models"
_EAST_URL = (
    "https://www.dropbox.com/s/r2ingd0l3zt8hxs/frozen_east_text_detection.tar.gz?dl=1"
)
_EAST_PB = "frozen_east_text_detection.pb"

DetectorFn = Callable[[Path, float], List["TextRegion"]]
_EXTRA_DETECTORS: Dict[str, DetectorFn] = {}


def register_text_detector(name: str, fn: DetectorFn) -> None:
    """Register a custom text detector (``name`` must match YAML ``detector`` value)."""
    _EXTRA_DETECTORS[str(name).lower()] = fn

_MODEL_CACHE = Path.home() / ".praisonaippt" / "models"
_EAST_URL = (
    "https://www.dropbox.com/s/r2ingd0l3zt8hxs/frozen_east_text_detection.tar.gz?dl=1"
)
_EAST_PB = "frozen_east_text_detection.pb"


@dataclass(frozen=True)
class TextRegion:
    """Normalised bounding box in source image space (0–1)."""

    xmin: float
    ymin: float
    xmax: float
    ymax: float
    confidence: float
    detector: str

    @property
    def area(self) -> float:
        return max(0.0, self.xmax - self.xmin) * max(0.0, self.ymax - self.ymin)


def _download_model(url: str, name: str) -> Path:
    _MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    dest = _MODEL_CACHE / name
    if not dest.is_file():
        try:
            with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Failed to download model {name}: {exc}") from exc
    return dest


def _ensure_east_model() -> Path:
    pb = _MODEL_CACHE / _EAST_PB
    if pb.is_file():
        return pb
    archive = _download_model(_EAST_URL, "frozen_east_text_detection.tar.gz")
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(_MODEL_CACHE)
    if not pb.is_file():
        for candidate in _MODEL_CACHE.rglob(_EAST_PB):
            return candidate
    return pb


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _norm_box(x: float, y: float, w: float, h: float, iw: int, ih: int) -> TextRegion:
    return TextRegion(
        xmin=_clip01(x / max(1, iw)),
        ymin=_clip01(y / max(1, ih)),
        xmax=_clip01((x + w) / max(1, iw)),
        ymax=_clip01((y + h) / max(1, ih)),
        confidence=0.5,
        detector="",
    )


def _nms(regions: Sequence[TextRegion], iou_thresh: float = 0.35) -> List[TextRegion]:
    if not regions:
        return []
    boxes = sorted(regions, key=lambda r: r.confidence, reverse=True)
    kept: List[TextRegion] = []

    def iou(a: TextRegion, b: TextRegion) -> float:
        ix0 = max(a.xmin, b.xmin)
        iy0 = max(a.ymin, b.ymin)
        ix1 = min(a.xmax, b.xmax)
        iy1 = min(a.ymax, b.ymax)
        inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
        if inter <= 0:
            return 0.0
        union = a.area + b.area - inter
        return inter / union if union > 0 else 0.0

    for box in boxes:
        if all(iou(box, k) < iou_thresh for k in kept):
            kept.append(box)
    return kept


def _expand_region(r: TextRegion, hard_px: float, soft_px: float, iw: int, ih: int) -> TextRegion:
    pad_x = (hard_px + soft_px) / max(1, iw)
    pad_y = (hard_px + soft_px) / max(1, ih)
    return TextRegion(
        xmin=_clip01(r.xmin - pad_x),
        ymin=_clip01(r.ymin - pad_y),
        xmax=_clip01(r.xmax + pad_x),
        ymax=_clip01(r.ymax + pad_y),
        confidence=r.confidence,
        detector=r.detector,
    )


def _filter_regions(
    regions: Sequence[TextRegion],
    *,
    iw: int,
    ih: int,
    min_height_px: float = 8.0,
    max_area_ratio: float = 0.30,
) -> List[TextRegion]:
    out: List[TextRegion] = []
    for r in regions:
        h_px = (r.ymax - r.ymin) * ih
        if h_px < min_height_px:
            continue
        if r.area > max_area_ratio:
            continue
        if r.xmax <= r.xmin or r.ymax <= r.ymin:
            continue
        out.append(r)
    return out


def _postprocess(
    regions: Sequence[TextRegion],
    *,
    iw: int,
    ih: int,
    pad_hard_px: float,
    pad_soft_px: float,
) -> List[TextRegion]:
    filtered = _filter_regions(regions, iw=iw, ih=ih)
    merged = _nms(filtered)
    return [_expand_region(r, pad_hard_px, pad_soft_px, iw, ih) for r in merged]


def _detect_mser(image_path: Path, min_confidence: float) -> List[TextRegion]:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []

    img = cv2.imread(str(image_path))
    if img is None:
        return []
    ih, iw = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        mser = cv2.MSER_create()
        mser.setDelta(5)
        mser.setMinArea(60)
        mser.setMaxArea(int(iw * ih * 0.08))
    except (AttributeError, cv2.error):
        mser = cv2.MSER_create(_delta=5, _min_area=60, _max_area=int(iw * ih * 0.08))
    regions_raw, _ = mser.detectRegions(gray)
    candidates: List[TextRegion] = []
    for pts in regions_raw:
        x, y, w, h = cv2.boundingRect(pts.reshape(-1, 1, 2))
        if w < 12 or h < 6 or w > iw * 0.85 or h > ih * 0.4:
            continue
        aspect = w / max(1, h)
        if aspect < 0.15 or aspect > 25:
            continue
        roi = gray[y : y + h, x : x + w]
        if roi.size == 0:
            continue
        var = float(np.var(roi))
        if var < 120:
            continue
        conf = min(0.85, 0.35 + var / 800.0)
        if conf < min_confidence:
            continue
        box = _norm_box(float(x), float(y), float(w), float(h), iw, ih)
        candidates.append(
            TextRegion(
                box.xmin, box.ymin, box.xmax, box.ymax,
                confidence=conf, detector="mser",
            )
        )
    return candidates


def _decode_east(
    scores: "object",
    geometry: "object",
    orig_iw: int,
    orig_ih: int,
    net_w: int,
    net_h: int,
    conf_thresh: float,
) -> List[TextRegion]:
    import numpy as np

    sx = orig_iw / max(1, net_w)
    sy = orig_ih / max(1, net_h)
    num_rows, num_cols = scores.shape[2:4]
    boxes: List[TextRegion] = []
    for y in range(num_rows):
        scores_data = scores[0, 0, y]
        x_data0 = geometry[0, 0, y]
        x_data1 = geometry[0, 1, y]
        x_data2 = geometry[0, 2, y]
        x_data3 = geometry[0, 3, y]
        angles_data = geometry[0, 4, y]
        for x in range(num_cols):
            if scores_data[x] < conf_thresh:
                continue
            offset_x = x * 4.0
            offset_y = y * 4.0
            angle = angles_data[x]
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            h = x_data0[x] + x_data2[x]
            w = x_data1[x] + x_data3[x]
            end_x = (offset_x + cos_a * x_data1[x] + sin_a * x_data2[x]) * sx
            end_y = (offset_y - sin_a * x_data1[x] + cos_a * x_data2[x]) * sy
            start_x = end_x - w * sx
            start_y = end_y - h * sy
            conf = float(scores_data[x])
            boxes.append(
                TextRegion(
                    _clip01(start_x / max(1, orig_iw)),
                    _clip01(start_y / max(1, orig_ih)),
                    _clip01(end_x / max(1, orig_iw)),
                    _clip01(end_y / max(1, orig_ih)),
                    confidence=conf,
                    detector="east",
                )
            )
    return boxes


def _detect_east(image_path: Path, min_confidence: float) -> List[TextRegion]:
    try:
        import cv2
    except ImportError:
        return []

    try:
        model_path = _ensure_east_model()
    except (RuntimeError, OSError, tarfile.TarError):
        return []
    if not model_path.is_file():
        return []

    img = cv2.imread(str(image_path))
    if img is None:
        return []
    ih, iw = img.shape[:2]
    new_w = (iw // 32) * 32 or 32
    new_h = (ih // 32) * 32 or 32
    try:
        blob = cv2.dnn.blobFromImage(
            img, 1.0, (new_w, new_h), (123.68, 116.78, 103.94), swapRB=True, crop=False,
        )
        net = cv2.dnn.readNet(str(model_path))
        net.setInput(blob)
        scores, geometry = net.forward(
            ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"],
        )
    except cv2.error:
        return []
    return _decode_east(scores, geometry, iw, ih, new_w, new_h, min_confidence)


def _detect_paddle(image_path: Path, min_confidence: float) -> List[TextRegion]:
    try:
        from paddleocr import TextDetection
    except ImportError:
        return _detect_rapidocr(image_path, min_confidence)

    try:
        det = TextDetection(model_name="PP-OCRv5_mobile_det")
    except Exception:
        return _detect_rapidocr(image_path, min_confidence)

    try:
        from PIL import Image
    except ImportError:
        return []

    img = Image.open(image_path)
    iw, ih = img.size
    result = det.predict(str(image_path))
    boxes: List[TextRegion] = []
    for item in result or []:
        polys = getattr(item, "dt_polys", None) or item.get("dt_polys") if isinstance(item, dict) else None
        if polys is None and hasattr(item, "json"):
            polys = item.json.get("res", {}).get("dt_polys")
        if not polys:
            continue
        for poly in polys:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            conf = min(0.99, max(min_confidence, 0.7))
            boxes.append(
                TextRegion(
                    _clip01(min(xs) / max(1, iw)),
                    _clip01(min(ys) / max(1, ih)),
                    _clip01(max(xs) / max(1, iw)),
                    _clip01(max(ys) / max(1, ih)),
                    confidence=conf,
                    detector="paddle",
                )
            )
    return boxes


def _detect_rapidocr(image_path: Path, min_confidence: float) -> List[TextRegion]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []

    engine = RapidOCR()
    result, _ = engine(str(image_path))
    if not result:
        return []
    try:
        from PIL import Image
        iw, ih = Image.open(image_path).size
    except Exception:
        iw, ih = 1, 1
    boxes: List[TextRegion] = []
    for row in result:
        if len(row) < 2:
            continue
        poly, conf_raw = row[0], row[1]
        conf = float(conf_raw) if conf_raw is not None else min_confidence
        if conf < min_confidence:
            continue
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        boxes.append(
            TextRegion(
                _clip01(min(xs) / max(1, iw)),
                _clip01(min(ys) / max(1, ih)),
                _clip01(max(xs) / max(1, iw)),
                _clip01(max(ys) / max(1, ih)),
                confidence=conf,
                detector="rapidocr",
            )
        )
    return boxes


def detect_text_regions(
    image_path: str | Path,
    *,
    detector: str = "auto",
    min_confidence: float = 0.45,
    pad_hard_px: float = 20.0,
    pad_soft_px: float = 8.0,
) -> List[TextRegion]:
    """Return padded text regions in normalised image coordinates."""
    path = Path(image_path)
    if not path.is_file():
        return []

    try:
        from PIL import Image
        iw, ih = Image.open(path).size
    except ImportError:
        return []
    except OSError:
        return []

    det = detector.lower()
    order_map = {
        "paddle": ("paddle",),
        "rapidocr": ("rapidocr",),
        "east": ("east",),
        "mser": ("mser",),
        "heuristic": ("mser",),
        "auto": ("paddle", "rapidocr", "east", "mser"),
    }
    if det in _EXTRA_DETECTORS:
        order = (det,)
    else:
        order = order_map.get(det, order_map["auto"])

    raw: List[TextRegion] = []
    used = ""
    for name in order:
        if name in _EXTRA_DETECTORS:
            hit = _EXTRA_DETECTORS[name](path, min_confidence)
        elif name == "paddle":
            hit = _detect_paddle(path, min_confidence)
        elif name == "rapidocr":
            hit = _detect_rapidocr(path, min_confidence)
        elif name == "east":
            hit = _detect_east(path, min_confidence)
        elif name == "mser":
            hit = _detect_mser(path, min_confidence)
        else:
            hit = []
        if hit:
            raw = hit
            used = name if name != "mser" else "mser_heuristic"
            break

    if not raw:
        return []

    out = _postprocess(raw, iw=iw, ih=ih, pad_hard_px=pad_hard_px, pad_soft_px=pad_soft_px)
    return [
        TextRegion(r.xmin, r.ymin, r.xmax, r.ymax, r.confidence, used or r.detector)
        for r in out
    ]


def text_detect_available() -> bool:
    """True when at least one offline detector backend is importable."""
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        from paddleocr import TextDetection  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        from rapidocr_onnxruntime import RapidOCR  # noqa: F401
        return True
    except ImportError:
        return False

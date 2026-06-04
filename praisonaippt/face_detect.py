"""Optional face-centre detection for avatar PiP calibration (MediaPipe, YuNet, YOLO)."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

_MODEL_CACHE = Path.home() / ".praisonaippt" / "models"
_MEDIAPIPE_SHORT_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
)
_YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/master/models/face_detection_yunet/"
    "face_detection_yunet_2023mar.onnx"
)


@dataclass(frozen=True)
class FaceCentre:
    """Normalised face centre and bbox in source image (0–1)."""

    fx: float
    fy: float
    confidence: float
    detector: str
    xmin: float = 0.0
    ymin: float = 0.0
    xmax: float = 1.0
    ymax: float = 1.0


def _download_model(url: str, name: str) -> Path:
    _MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    dest = _MODEL_CACHE / name
    if not dest.is_file():
        try:
            with urllib.request.urlopen(url, timeout=60) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Failed to download face model {name}: {exc}") from exc
    return dest


def _largest_face(candidates: list) -> Optional[FaceCentre]:
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.confidence)


def _detect_mediapipe(image_path: Path, min_confidence: float) -> Optional[FaceCentre]:
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks import python as mp_python
    except ImportError:
        return None

    model_path = _download_model(_MEDIAPIPE_SHORT_URL, "blaze_face_short_range.tflite")
    options = vision.FaceDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.IMAGE,
        min_detection_confidence=min_confidence,
    )
    detector = vision.FaceDetector.create_from_options(options)
    try:
        mp_image = mp.Image.create_from_file(str(image_path))
        result = detector.detect(mp_image)
    finally:
        detector.close()

    if not result.detections:
        return None

    w = mp_image.width
    h = mp_image.height
    best: Optional[FaceCentre] = None
    for det in result.detections:
        box = det.bounding_box
        if box is None:
            continue
        ox, oy, bw, bh = box.origin_x, box.origin_y, box.width, box.height
        fx = (ox + bw / 2.0) / max(1, w)
        fy = (oy + bh / 2.0) / max(1, h)
        conf = float(det.categories[0].score) if det.categories else 0.5
        cand = FaceCentre(
            fx=fx, fy=fy, confidence=conf, detector="mediapipe",
            xmin=ox / max(1, w), ymin=oy / max(1, h),
            xmax=(ox + bw) / max(1, w), ymax=(oy + bh) / max(1, h),
        )
        if best is None or cand.confidence > best.confidence:
            best = cand
    return best


def _detect_yunet(image_path: Path, min_confidence: float) -> Optional[FaceCentre]:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    model_path = _download_model(_YUNET_URL, "face_detection_yunet_2023mar.onnx")
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(
        str(model_path),
        "",
        (w, h),
        score_threshold=min_confidence,
        nms_threshold=0.3,
        top_k=5000,
    )
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    if faces is None:
        return None

    candidates: list = []
    for row in faces:
        x, y, fw, fh, score = row[0], row[1], row[2], row[3], row[-1]
        if float(score) < min_confidence:
            continue
        candidates.append(
            FaceCentre(
                fx=(x + fw / 2.0) / max(1, w),
                fy=(y + fh / 2.0) / max(1, h),
                confidence=float(score),
                detector="yunet",
                xmin=x / max(1, w), ymin=y / max(1, h),
                xmax=(x + fw) / max(1, w), ymax=(y + fh) / max(1, h),
            )
        )
    return _largest_face(candidates)


def _detect_yolo(image_path: Path, min_confidence: float) -> Optional[FaceCentre]:
    try:
        from ultralytics import YOLO
    except ImportError:
        return None

    try:
        model = YOLO("yolov8n-face.pt")
    except Exception:
        return None

    results = model(str(image_path), verbose=False)
    if not results:
        return None
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return None

    try:
        import cv2
        img = cv2.imread(str(image_path))
        h, w = img.shape[:2] if img is not None else (1, 1)
    except ImportError:
        w, h = 1, 1

    candidates: list = []
    for box in boxes:
        conf = float(box.conf[0]) if box.conf is not None else 0.0
        if conf < min_confidence:
            continue
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy
        candidates.append(
            FaceCentre(
                fx=(x1 + x2) / 2.0 / max(1, w),
                fy=(y1 + y2) / 2.0 / max(1, h),
                confidence=conf,
                detector="yolo",
                xmin=x1 / max(1, w), ymin=y1 / max(1, h),
                xmax=x2 / max(1, w), ymax=y2 / max(1, h),
            )
        )
    return _largest_face(candidates)


def detect_face_centre(
    image_path: str | Path,
    *,
    detector: str = "auto",
    min_confidence: float = 0.5,
) -> Optional[FaceCentre]:
    """Return normalised face centre from a still image, or ``None`` if unavailable."""
    path = Path(image_path)
    if not path.is_file():
        return None

    order = {
        "mediapipe": ("mediapipe",),
        "yunet": ("yunet",),
        "yolo": ("yolo",),
        "auto": ("mediapipe", "yunet"),
    }.get(detector.lower(), ("mediapipe", "yunet"))

    for name in order:
        if name == "mediapipe":
            hit = _detect_mediapipe(path, min_confidence)
        elif name == "yunet":
            hit = _detect_yunet(path, min_confidence)
        elif name == "yolo":
            hit = _detect_yolo(path, min_confidence)
        else:
            hit = None
        if hit is not None:
            return hit
    return None


def mediapipe_available() -> bool:
    try:
        import mediapipe  # noqa: F401
        return True
    except ImportError:
        return False

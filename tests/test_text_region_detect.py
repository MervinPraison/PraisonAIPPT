"""Unit tests for text region detection helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest

from praisonaippt.text_region_detect import (
    TextRegion,
    _filter_regions,
    _nms,
    _postprocess,
    detect_text_regions,
    register_text_detector,
)


def test_nms_merges_overlapping():
    a = TextRegion(0.0, 0.0, 0.5, 0.2, 0.9, "test")
    b = TextRegion(0.05, 0.0, 0.55, 0.2, 0.8, "test")
    kept = _nms([a, b])
    assert len(kept) == 1
    assert kept[0].confidence == 0.9


def test_filter_drops_tiny_boxes():
    tiny = TextRegion(0.0, 0.0, 0.01, 0.001, 0.5, "test")
    out = _filter_regions([tiny], iw=1920, ih=1080)
    assert out == []


def test_postprocess_expands_boxes():
    r = TextRegion(0.2, 0.2, 0.4, 0.3, 0.8, "test")
    out = _postprocess([r], iw=1000, ih=800, pad_hard_px=20, pad_soft_px=8)
    assert len(out) == 1
    assert out[0].xmin < r.xmin
    assert out[0].xmax > r.xmax


@patch("praisonaippt.text_region_detect._ensure_east_model", side_effect=RuntimeError("network"))
def test_detect_east_download_failure_returns_empty(mock_east):
    del mock_east
    out = detect_text_regions("/nonexistent/path.jpg", detector="east")
    assert out == []


def test_detect_missing_file_returns_empty():
    assert detect_text_regions("/no/such/image.jpg") == []


def test_register_custom_detector(tmp_path):
    img = tmp_path / "x.png"
    from PIL import Image
    Image.new("RGB", (64, 64), (128, 128, 128)).save(img)

    def fake_det(path: Path, min_conf: float):
        return [TextRegion(0.05, 0.05, 0.9, 0.25, 0.9, "custom")]

    register_text_detector("custom", fake_det)
    out = detect_text_regions(img, detector="custom")
    assert out and out[0].detector == "custom"

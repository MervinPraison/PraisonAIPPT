"""Tests for hook content framing detection and validation."""
from pathlib import Path

import numpy as np
from PIL import Image

from praisonaippt.daily_single.content_framing import (
    MAX_SCROLL_PX_PER_SEC,
    MIN_CONTENT_FILL,
    MAX_SIDE_MARGIN,
    ContentFrame,
    apply_content_crop,
    detect_column_projection,
    effective_scroll_duration,
    measure_framing,
    merge_content_frames,
    reframe_page_shot,
    scroll_speed_px_per_sec,
    validate_framing,
    validate_scroll_speed,
)


def _wide_margin_page(path: Path, *, iw: int = 1920, ih: int = 1080, col_w: int = 720) -> None:
    img = np.full((ih, iw, 3), 245, dtype=np.uint8)
    x0 = (iw - col_w) // 2
    img[:, x0 : x0 + col_w] = (40, 40, 40)
    Image.fromarray(img).save(path)


def _tight_fill_page(path: Path, *, iw: int = 1920, ih: int = 1080) -> None:
    img = np.zeros((ih, iw, 3), dtype=np.uint8)
    img[:, :] = (30, 30, 30)
    Image.fromarray(img).save(path)


def test_column_projection_finds_centre_column(tmp_path: Path):
    src = tmp_path / "wide.png"
    _wide_margin_page(src, col_w=800)
    frame = detect_column_projection(src)
    assert frame is not None
    assert frame.width >= 720
    metrics = measure_framing(src, frame)
    assert metrics.left_margin_ratio > 0.15
    assert metrics.right_margin_ratio > 0.15


def test_validate_framing_fails_wide_margins(tmp_path: Path):
    src = tmp_path / "wide.png"
    _wide_margin_page(src)
    metrics = measure_framing(src)
    ok, issues = validate_framing(metrics)
    assert not ok
    assert any("margin" in i for i in issues)


def test_reframe_reduces_margins(tmp_path: Path):
    src = tmp_path / "wide.png"
    out = tmp_path / "reframed.png"
    _wide_margin_page(src, col_w=760)
    _, _, post = reframe_page_shot(src, dest=out)
    ok, issues = validate_framing(post)
    assert ok, issues
    assert post.content_fill_ratio >= MIN_CONTENT_FILL


def test_validate_framing_passes_tight_fill(tmp_path: Path):
    src = tmp_path / "tight.png"
    _tight_fill_page(src)
    metrics = measure_framing(src)
    ok, issues = validate_framing(metrics)
    assert ok, issues
    assert metrics.content_fill_ratio >= MIN_CONTENT_FILL


def test_scroll_speed_validation():
    assert scroll_speed_px_per_sec(1400, 5.0) == 280.0
    ok, issues = validate_scroll_speed(1400, 5.0)
    assert not ok
    dur = effective_scroll_duration(1400, 5.0)
    assert dur >= 1400 / 70.0
    ok, _ = validate_scroll_speed(1400, dur)
    assert ok


def test_merge_prefers_dom_over_column():
    dom = ContentFrame(560, 100, 1360, 900, source="dom", confidence=1.0)
    col = ContentFrame(580, 120, 1340, 880, source="column", confidence=0.8)
    merged = merge_content_frames(1920, 1080, dom, col)
    assert merged is not None
    assert merged.x0 <= dom.x0


def test_apply_content_crop_removes_side_gutter(tmp_path: Path):
    src = tmp_path / "wide.png"
    dest = tmp_path / "cropped.png"
    _wide_margin_page(src, col_w=800)
    frame = detect_column_projection(src)
    assert frame is not None
    apply_content_crop(src, frame, dest)
    out = Image.open(dest)
    assert out.size[0] < 1920
    metrics = measure_framing(dest)
    assert metrics.left_margin_ratio < MAX_SIDE_MARGIN

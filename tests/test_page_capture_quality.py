"""Tests for browser error page detection in hook capture."""
from pathlib import Path

import numpy as np
from PIL import Image

from praisonaippt.daily_single.page_capture_quality import (
    frame_looks_like_browser_error,
    screenshot_looks_like_error_page,
    validate_live_page,
)


class _FakePage:
    def __init__(self, *, title: str, body: str, url: str):
        self._title = title
        self._body = body
        self.url = url

    def title(self) -> str:
        return self._title

    def inner_text(self, _sel: str) -> str:
        return self._body


def _error_page_png(path: Path) -> None:
    img = np.full((1080, 1920, 3), 255, dtype=np.uint8)
    Image.fromarray(img).save(path)


def _news_page_png(path: Path) -> None:
    import subprocess
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "gradients=s=1920x1080:c0=red:c1=blue",
            "-frames:v", "1", str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_validate_live_page_rejects_error_text():
    page = _FakePage(
        title="Error",
        body="This page couldn't load. Reload to try again.",
        url="https://www.anthropic.com/news/claude-fable-5-mythos-5",
    )
    ok, issues = validate_live_page(page, "https://www.anthropic.com/news/claude-fable-5-mythos-5")
    assert not ok
    assert any("error" in i.lower() for i in issues)


def test_validate_live_page_accepts_news_body():
    page = _FakePage(
        title="Claude Fable 5 and Mythos 5",
        body="Anthropic announces Claude Fable 5 for everyday teams with new benchmarks.",
        url="https://www.anthropic.com/news/claude-fable-5-mythos-5",
    )
    ok, issues = validate_live_page(page, "https://www.anthropic.com/news/claude-fable-5-mythos-5")
    assert ok, issues


def test_validate_scroll_asset_checks_framing(tmp_path: Path):
    from praisonaippt.daily_single.page_capture_quality import validate_scroll_asset

    project_root = tmp_path / "proj"
    scroll = project_root / "assets" / "videos" / "canonical-scroll.mp4"
    scroll.parent.mkdir(parents=True)
    _news_page_png(tmp_path / "frame.png")
    import subprocess
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(tmp_path / "frame.png"),
            "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(scroll),
        ],
        check=True,
        capture_output=True,
    )

    class _Proj:
        root = project_root
        merge_dir = project_root / "merge"
        research_dir = project_root / "research"
        slug = "test"

    _Proj.merge_dir.mkdir(parents=True)
    ok, details = validate_scroll_asset(_Proj(), scroll)
    assert "framing" in details


def test_screenshot_heuristic_detects_error_layout(tmp_path: Path):
    err = tmp_path / "error.png"
    good = tmp_path / "good.png"
    _error_page_png(err)
    _news_page_png(good)
    assert screenshot_looks_like_error_page(err)[0]
    assert not screenshot_looks_like_error_page(good)[0]
    assert frame_looks_like_browser_error(err)

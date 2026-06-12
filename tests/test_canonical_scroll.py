"""Tests for canonical scroll / zoom hook attention capture."""
from pathlib import Path

from praisonaippt.daily_single.canonical_scroll import (
    MIN_MOTION,
    build_scroll_video,
    build_zoom_video,
    video_has_motion,
)


def _gradient_page(path: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "gradients=s=1920x1080:c0=red:c1=blue",
            "-frames:v", "1", str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_zoom_video_has_motion(tmp_path: Path):
    src = tmp_path / "page.png"
    _gradient_page(src)
    dest = tmp_path / "zoom.mp4"
    build_zoom_video(src, dest, duration=2.0)
    assert dest.is_file()
    assert video_has_motion(dest, min_motion=MIN_MOTION)


def test_scroll_video_from_tall_image(tmp_path: Path):
    import subprocess

    src = tmp_path / "tall.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "gradients=s=1920x2400:c0=green:c1=purple",
            "-frames:v", "1", str(src),
        ],
        check=True,
        capture_output=True,
    )
    dest = tmp_path / "scroll.mp4"
    build_scroll_video(src, dest, duration=2.0)
    assert dest.is_file()
    assert video_has_motion(dest, min_motion=MIN_MOTION)
    rate = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", str(dest),
        ],
        text=True,
    ).strip()
    assert rate == "30/1", f"expected 30fps scroll, got {rate}"

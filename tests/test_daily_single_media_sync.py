"""Tests for daily_single canonical asset sync."""
from __future__ import annotations

from praisonaippt.daily_single.media_sync import MIN_VIDEO_HEIGHT, YTDLP_FORMAT


def test_ytdlp_format_prefers_merged_hd():
    assert "bestvideo" in YTDLP_FORMAT
    assert "bestaudio" in YTDLP_FORMAT
    assert "best[ext=mp4][height" not in YTDLP_FORMAT


def test_min_video_height_is_hd_floor():
    assert MIN_VIDEO_HEIGHT >= 720

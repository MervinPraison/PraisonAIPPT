"""Verify social-comparison Fable 5 demo clips are on disk and in beat-map."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-social-comparison"
XDIR = PROJECT / "research/reference-videos/x"
BEAT_MAP = PROJECT / "research/beat-map-v2.json"
SOCIAL_SOURCES = PROJECT / "research/social-sources.json"

DEMO_CLIPS = [
    "x-demo-deveshcodes-blackhole.mp4",
    "x-demo-coldopn-github.mp4",
    "x-demo-kieradev-racing.mp4",
    "x-demo-ai-for-success-dino.mp4",
    "x-demo-scottstts-friends.mp4",
    "x-demo-tetumemo-solar.mp4",
    "x-demo-intheworldofai-macos.mp4",
    "x-demo-quanghuynt-watch.mp4",
    "x-demo-vikvang-rust-mc.mp4",
    "x-demo-ydamitcodes-minecraft.mp4",
]


@pytest.mark.parametrize("filename", DEMO_CLIPS)
def test_demo_clip_exists_and_decodes(filename: str) -> None:
    path = XDIR / filename
    assert path.is_file(), f"missing {filename}"
    assert path.stat().st_size >= 40_000
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert float(proc.stdout.strip()) >= 3.0


def test_all_demos_in_beat_map() -> None:
    data = json.loads(BEAT_MAP.read_text(encoding="utf-8"))
    used = {
        Path(c.get("filename") or c.get("path", "")).name
        for spec in (data.get("beats") or {}).values()
        for c in spec.get("clips") or []
    }
    missing = [f for f in DEMO_CLIPS if f not in used]
    assert not missing, f"beat-map missing: {missing}"


def test_all_demos_in_social_sources() -> None:
    data = json.loads(SOCIAL_SOURCES.read_text(encoding="utf-8"))
    catalog = {Path(e.get("local_file", "")).name for e in data.get("clips") or []}
    missing = [f for f in DEMO_CLIPS if f not in catalog]
    assert not missing, f"social-sources missing: {missing}"

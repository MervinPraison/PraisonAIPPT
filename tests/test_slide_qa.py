"""Slide QA manifest and MP4 frame helpers."""

from pathlib import Path

import yaml

from praisonaippt.deck_pipeline import expected_deck_duration
from praisonaippt.slide_qa import (
    check_slide_qa_manifest,
    export_mp4_plan_frames,
    _content_width_ratio,
)
from praisonaippt.video_exporter import iter_slide_plan

PKG = Path(__file__).resolve().parent.parent
IMAGES = PKG / "examples" / "heygen-50590-video-audio-heygen-images.yaml"
IMG_DIR = PKG / "examples" / "slide_images" / "heygen-50590-images"
MP4 = PKG / "examples" / "heygen-50590-video-audio-heygen-images.mp4"


def test_images_slide_timestamps_match_plan():
    data = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
    plan = list(iter_slide_plan(data))
    ts = data["slide_timestamps"]
    assert len(ts) == len(plan) + 1
    assert abs(ts[-1] - expected_deck_duration(data)) < 0.2
    for i, item in enumerate(plan):
        verse = item.get("verse") or {}
        if verse.get("audio_start_sec") is not None:
            assert abs(ts[i] - float(verse["audio_start_sec"])) < 0.05


def test_check_slide_qa_manifest_on_exports():
    data = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
    step = check_slide_qa_manifest(
        data,
        source_file=str(IMAGES),
        jpeg_dir=IMG_DIR,
    )
    assert step.ok, step.detail


def test_content_width_ratio_on_hero_jpeg():
    jpg = IMG_DIR / "slide-002.jpg"
    if not jpg.is_file():
        return
    ratio = _content_width_ratio(jpg)
    assert ratio is not None and ratio >= 0.35


def test_export_mp4_plan_frames():
    if not MP4.is_file():
        return
    data = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
    out = PKG / "examples" / "slide_images" / "heygen-50590-images" / "_test_mp4_frames"
    out.mkdir(parents=True, exist_ok=True)
    paths = export_mp4_plan_frames(MP4, data, out, source_file=str(IMAGES))
    assert len(paths) == len(list(iter_slide_plan(data)))
    for p in paths:
        assert Path(p).stat().st_size > 5000

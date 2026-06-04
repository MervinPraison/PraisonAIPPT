"""Regression: images variant keeps HeyGen timing fields aligned with base deck."""

from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent.parent
BASE = PKG / "examples" / "heygen-50590-video-audio-heygen.yaml"
IMAGES = PKG / "examples" / "heygen-50590-video-audio-heygen-images.yaml"

_TIMING_KEYS = ("audio_start_sec", "duration_sec", "notes")


def _verses(path: Path) -> list:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return (data.get("sections") or [{}])[0].get("verses") or []


def test_images_variant_timing_matches_base():
    base = _verses(BASE)
    images = _verses(IMAGES)
    assert len(base) == len(images)
    for i, (b, img) in enumerate(zip(base, images)):
        for key in _TIMING_KEYS:
            assert b.get(key) == img.get(key), f"verse[{i}].{key} drifted"
    images_ts = yaml.safe_load(IMAGES.read_text())["slide_timestamps"]
    assert images_ts[0] == 0.0
    assert len(images_ts) == len(images) + 1


def test_images_variant_skips_auto_title_slide():
    from praisonaippt.video_exporter import iter_slide_plan

    data = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
    plan = list(iter_slide_plan(data))
    assert plan[0]["slide_type"] == "big_number"
    assert len(plan) == len(_verses(IMAGES))

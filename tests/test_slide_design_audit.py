"""Tests for slide design and publish quality tier detection."""
from pathlib import Path

from praisonaippt.daily_single.publish_quality_config import asset_tier, is_social_capture_path


def test_asset_tier_text_slide_v2(tmp_path: Path):
    p = tmp_path / "v2-headline-vs-receipt.png"
    p.write_bytes(b"x" * 50_000)
    assert asset_tier(str(p)) == "text_slide"


def test_asset_tier_gpt_image_large(tmp_path: Path):
    p = tmp_path / "beat3-stripe-card.png"
    p.write_bytes(b"x" * 300_000)
    assert asset_tier(str(p), {"asset_tier": "gpt-image"}) == "gpt-image"


def test_asset_tier_social_capture():
    assert is_social_capture_path("/ref/social-capture-hn-beast-ferrari.png")
    assert asset_tier("/ref/social-capture-reddit-inequality.png") == "social-capture"


def test_asset_tier_motion_mp4(tmp_path: Path):
    p = tmp_path / "pokemon-timelapse.mp4"
    p.write_bytes(b"fake")
    assert asset_tier(str(p)) == "motion"


def test_asset_tier_explicit_override():
    assert asset_tier("/any/path.png", {"asset_tier": "chart"}) == "chart"

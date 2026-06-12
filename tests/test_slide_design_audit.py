"""Tests for slide design and publish quality tier detection."""
import json
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


def test_is_social_capture_youtube_and_linkedin():
    assert is_social_capture_path("/ref/youtube-coderabbit-review.mp4")
    assert is_social_capture_path("/ref/linkedin-cintas-fable5-vs-opus.mp4")


def test_engagement_config_social_comparison(tmp_path: Path):
    from praisonaippt.daily_single.publish_quality_config import engagement_config
    from praisonaippt.daily_single.project import DailySingleProject

    root = tmp_path / "social"
    (root / "research").mkdir(parents=True)
    bm = root / "research/beat-map-v2.json"
    bm.write_text(
        '{"variant":"social-comparison","asset_policy":"video-first-local","beats":{}}',
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "social",
            "create_news_research": str(tmp_path / "research"),
            "beat_map": str(bm),
        }),
        encoding="utf-8",
    )
    (root / "scripts/config").mkdir(parents=True)
    project = DailySingleProject.from_root(root)
    cfg = engagement_config(project)
    assert cfg["min_social_captures"] >= 3


def test_video_script_prefers_local_project_copy(tmp_path: Path):
    from praisonaippt.daily_single.project import DailySingleProject

    root = tmp_path / "proj"
    (root / "research").mkdir(parents=True)
    local = root / "research/video-script.md"
    local.write_text("# local script", encoding="utf-8")
    ext_research = tmp_path / "external-research"
    ext_research.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test",
            "create_news_research": str(ext_research),
            "beat_map": str(root / "research/beat-map-v2.json"),
        }),
        encoding="utf-8",
    )
    (root / "research/beat-map-v2.json").write_text("{}", encoding="utf-8")
    project = DailySingleProject.from_root(root)
    assert project.video_script_path == local

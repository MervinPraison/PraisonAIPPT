"""Tests for beat-map policy gate — banned assets, LinkedIn placement, clip mix."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.beat_map_audit import validate_beat_map_policy
from praisonaippt.daily_single.project import DailySingleProject

TRUST = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-trust-audit"


def _trust_project(tmp_path: Path, beat_map: dict) -> DailySingleProject:
    root = tmp_path / "proj"
    root.mkdir(parents=True)
    vid = root / "research/reference-videos/social"
    vid.mkdir(parents=True)
    clip = vid / "linkedin-cintas-fable5-vs-opus.mp4"
    clip.write_bytes(b"\x00" * 100)
    demo = root / "research/reference-videos/anthropic"
    demo.mkdir(parents=True)
    for name in ("demo-fluid.mp4", "demo-factorio.mp4", "demo-vibecad.mp4", "demo-launch.mp4"):
        (demo / name).write_bytes(b"\x00" * 100)

    bm_path = root / "research/beat-map-v2.json"
    bm_path.write_text(json.dumps(beat_map), encoding="utf-8")
    (root / "merge").mkdir()
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test-trust",
            "create_news_research": str(tmp_path / "research"),
            "beat_map": str(bm_path),
        }),
        encoding="utf-8",
    )
    return DailySingleProject.from_root(root)


def _base_trust_beats() -> dict:
    demo = "/demo/demo-fluid.mp4"
    return {
        "1": {"clips": [{"path": demo, "filename": "demo-fluid.mp4", "in_sec": 0, "out_sec": 8}], "images": [], "generated": []},
        "2": {"clips": [{"path": demo, "filename": "demo-factorio.mp4", "in_sec": 0, "out_sec": 12}], "images": [], "generated": []},
        "3": {"clips": [{"path": demo, "filename": "demo-factorio.mp4", "in_sec": 0, "out_sec": 14}], "images": [], "generated": []},
        "4": {"clips": [{"path": demo, "filename": "demo-vibecad.mp4", "in_sec": 0, "out_sec": 12}], "images": [], "generated": []},
    }


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_social_comparison_project_passes_beat_map():
    social = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-social-comparison"
    if not social.is_dir():
        pytest.skip("social-comparison pilot missing")
    project = DailySingleProject.from_root(social)
    report = validate_beat_map_policy(project)
    assert report.get("social_comparison")
    assert len(report.get("distinct_social_clips") or []) >= 3
    assert report["ok"] or not any("Missing social clip" in w for w in report.get("warnings") or [])


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_trust_audit_beat_map_passes_policy():
    project = DailySingleProject.from_root(TRUST)
    report = validate_beat_map_policy(project)
    issues = report.get("issues") or []
    if not report["ok"]:
        assert all("fallback-notification" in i for i in issues), issues
    assert "demo-scroll" not in str(report.get("body_clip_seconds"))


def test_rejects_v2_slide_in_beat_map(tmp_path: Path):
    beats = _base_trust_beats()
    beats["6"] = {
        "clips": [],
        "images": [{"path": "/x/v2-quote-willison.png", "filename": "v2-quote-willison.png"}],
        "generated": [],
    }
    project = _trust_project(tmp_path, {"variant": "trust-audit", "asset_policy": "video-first-local", "beats": beats})
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("v2-" in i for i in report["issues"])


def test_rejects_fallback_notification_clip(tmp_path: Path):
    beats = _base_trust_beats()
    beats["6"] = {
        "clips": [{"path": "/x/fallback-notification.mp4", "filename": "fallback-notification.mp4", "in_sec": 0, "out_sec": 10}],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {"variant": "trust-audit", "asset_policy": "video-first-local", "beats": beats})
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("fallback-notification" in i for i in report["issues"])


def test_rejects_demo_scroll_in_beat_map(tmp_path: Path):
    beats = _base_trust_beats()
    beats["5"] = {
        "clips": [{"path": "/x/demo-scroll.mp4", "filename": "demo-scroll.mp4", "in_sec": 0, "out_sec": 20}],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {"variant": "trust-audit", "asset_policy": "video-first-local", "beats": beats})
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("demo-scroll" in i for i in report["issues"])


def test_rejects_linkedin_in_body_beat_seven(tmp_path: Path):
    beats = _base_trust_beats()
    beats["7"] = {
        "clips": [{
            "path": "/x/linkedin-cintas-fable5-vs-opus.mp4",
            "filename": "linkedin-cintas-fable5-vs-opus.mp4",
            "in_sec": 0,
            "out_sec": 40,
        }],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {"variant": "trust-audit", "asset_policy": "video-first-local", "beats": beats})
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("LinkedIn" in i and "Beat 7" in i for i in report["issues"])


def test_rejects_duplicate_clip_bytes(tmp_path: Path):
    xdir = tmp_path / "clips"
    xdir.mkdir()
    clip_a = xdir / "x-claudeai-launch.mp4"
    clip_b = xdir / "x-claudedevs-launch.mp4"
    payload = b"\x01" * 200
    clip_a.write_bytes(payload)
    clip_b.write_bytes(payload)
    beats = _base_trust_beats()
    beats["5"] = {
        "clips": [
            {"path": str(clip_a), "filename": clip_a.name, "in_sec": 0, "out_sec": 10},
            {"path": str(clip_b), "filename": clip_b.name, "in_sec": 0, "out_sec": 10},
        ],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {
        "variant": "social-comparison",
        "asset_policy": "video-first-local",
        "beats": beats,
    })
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("Duplicate clip bytes" in i for i in report["issues"])


def test_rejects_duplicate_clip_bytes_trust_audit(tmp_path: Path):
    xdir = tmp_path / "clips"
    xdir.mkdir()
    clip_a = xdir / "demo-fluid-a.mp4"
    clip_b = xdir / "demo-fluid-b.mp4"
    payload = b"\x02" * 200
    clip_a.write_bytes(payload)
    clip_b.write_bytes(payload)
    beats = _base_trust_beats()
    beats["5"] = {
        "clips": [
            {"path": str(clip_a), "filename": clip_a.name, "in_sec": 0, "out_sec": 10},
            {"path": str(clip_b), "filename": clip_b.name, "in_sec": 0, "out_sec": 10},
        ],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {
        "variant": "trust-audit",
        "asset_policy": "video-first-local",
        "beats": beats,
    })
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("Duplicate clip bytes" in i for i in report["issues"])


def test_rejects_single_clip_dominating_body(tmp_path: Path):
    beats = _base_trust_beats()
    beats["5"] = {
        "clips": [{"path": "/x/demo-vibecad.mp4", "filename": "demo-vibecad.mp4", "in_sec": 0, "out_sec": 80}],
        "images": [],
        "generated": [],
    }
    beats["6"] = {
        "clips": [{"path": "/x/demo-vibecad.mp4", "filename": "demo-vibecad.mp4", "in_sec": 0, "out_sec": 80}],
        "images": [],
        "generated": [],
    }
    beats["7"] = {
        "clips": [{"path": "/x/demo-factorio.mp4", "filename": "demo-factorio.mp4", "in_sec": 0, "out_sec": 10}],
        "images": [],
        "generated": [],
    }
    project = _trust_project(tmp_path, {"variant": "trust-audit", "asset_policy": "video-first-local", "beats": beats})
    report = validate_beat_map_policy(project)
    assert not report["ok"]
    assert any("diversify" in i.lower() for i in report["issues"])

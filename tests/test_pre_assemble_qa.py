"""Tests for pre-assemble QA stages s16–s19."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.chart_script_audit import validate_chart_script_contract
from praisonaippt.daily_single.video_first_audit import validate_video_first_policy
from praisonaippt.video_qa.registry import list_stages


@pytest.fixture
def video_first_root(tmp_path: Path) -> DailySingleProject:
    root = tmp_path / "proj"
    root.mkdir(parents=True)
    research = tmp_path / "research"
    ref = root / "research/reference-images"
    ref.mkdir(parents=True)
    (ref / "jailbreak-resistance.png").write_bytes(b"x" * 300)
    (ref / "alignment-chart.png").write_bytes(b"x" * 300)
    vid = root / "research/reference-videos/social"
    vid.mkdir(parents=True)
    clip = vid / "linkedin-cintas-fable5-vs-opus.mp4"
    clip.write_bytes(b"\x00" * 100)

    beat_map = {
        "variant": "trust-audit",
        "asset_policy": "video-first-local",
        "beats": {
            "1": {
                "clips": [{"path": str(clip), "filename": clip.name}],
                "images": [],
                "generated": [],
            },
            "2": {"clips": [{"path": str(clip), "filename": clip.name}], "images": [], "generated": []},
            "4": {"clips": [{"path": str(clip), "filename": clip.name}], "images": [], "generated": []},
            "5": {"clips": [{"path": str(clip), "filename": clip.name}], "images": [], "generated": []},
        },
    }
    bm_path = root / "research/beat-map-v2.json"
    bm_path.write_text(json.dumps(beat_map), encoding="utf-8")

    (root / "merge").mkdir()
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "test-trust",
            "create_news_research": str(research),
            "beat_map": str(bm_path),
        }),
        encoding="utf-8",
    )
    seg = root / "segments/10-alignment"
    seg.mkdir(parents=True)
    (seg / "script.md").write_text(
        "The jailbreak resistance chart on screen shows attack success rates under red teaming. "
        "The alignment chart tracks misaligned behaviour scores.",
        encoding="utf-8",
    )
    return DailySingleProject.from_root(root)


def test_list_stages_includes_new_qa():
    stages = list_stages()
    assert len(stages) >= 22
    assert "s16-montage-clock" in stages
    assert "s21-beat-map-policy" in stages
    assert "s22-word-visual-sync" in stages


def test_video_first_policy_passes_local_clip(video_first_root: DailySingleProject):
    ok, issues, _ = validate_video_first_policy(video_first_root)
    assert ok, issues


def test_chart_script_passes_when_named(video_first_root: DailySingleProject):
    ok, issues, _ = validate_chart_script_contract(video_first_root)
    assert ok, issues


def test_chart_script_rejects_decision_table_on_jailbreak_chart(video_first_root: DailySingleProject):
    seg = video_first_root.segments_dir / "10-alignment" / "script.md"
    seg.write_text(
        "The safety stress-test chart on screen is a decision table for coders and testers.",
        encoding="utf-8",
    )
    ok, issues, _ = validate_chart_script_contract(video_first_root)
    assert not ok
    assert any("different chart type" in i for i in issues)


def test_cue_map_audit_clip_only_beats_general(tmp_path: Path):
    from unittest.mock import patch

    from praisonaippt.daily_single.cue_map_audit import _clip_cue_needles, validate_cue_picture_map

    root = tmp_path / "proj"
    root.mkdir(parents=True)
    clips_dir = root / "research/reference-videos/x"
    clips_dir.mkdir(parents=True)
    clip = clips_dir / "x-trq212-pipeline.mp4"
    clip.write_bytes(b"\x00" * 50)
    beat_map = {
        "variant": "social-comparison",
        "asset_policy": "video-first-local",
        "beats": {
            "7": {
                "clips": [{"path": str(clip), "filename": clip.name, "in_sec": 0, "out_sec": 8}],
                "images": [],
                "generated": [],
            },
        },
    }
    bm_path = root / "research/beat-map-v2.json"
    bm_path.write_text(json.dumps(beat_map), encoding="utf-8")
    (root / "merge").mkdir()
    (root / "manifest.json").write_text(
        json.dumps({
            "slug": "cue-test",
            "create_news_research": str(tmp_path / "research"),
            "beat_map": str(bm_path),
        }),
        encoding="utf-8",
    )
    seg = root / "segments/07-api-integration"
    seg.mkdir(parents=True)
    (seg / "narration.mp3").write_bytes(b"\x00" * 100)

    needles = _clip_cue_needles([{"path": str(clip)}])
    assert any("trq212" in n for row in needles for n in row)

    project = DailySingleProject.from_root(root)
    with patch("praisonaippt.daily_single.cue_map_audit.ffprobe_duration", return_value=30.0):
        with patch("praisonaippt.daily_single.cue_map_audit.beat6_absolute_cues", return_value=[
            (0.0, 5.0, "unrelated weather forecast for tomorrow"),
        ]):
            ok, issues, details = validate_cue_picture_map(project)
    assert any(b.get("beat") == 7 for b in details["beats"])
    assert details["beats"][0]["mode"] == "clips"

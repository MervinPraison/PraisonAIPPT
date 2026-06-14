"""Tests for related-resource usefulness QA."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.resource_usefulness_audit import (
    score_resource,
    validate_resource_usefulness,
)
from praisonaippt.daily_single.project import DailySingleProject


def _project(tmp_path: Path, *, catalog: dict, beat_map: dict | None = None) -> DailySingleProject:
    root = tmp_path / "p"
    research = tmp_path / "r"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    (root / "research").mkdir()
    (root / "research" / "social-sources.json").write_text(json.dumps(catalog), encoding="utf-8")
    if beat_map:
        (root / "research" / "beat-map-v2.json").write_text(json.dumps(beat_map), encoding="utf-8")
    return DailySingleProject.from_root(root)


def test_comparison_clip_scores_high():
    entry = {
        "id": "youtube-jono-flight-sim",
        "title": "Fable 5 vs Opus — flight simulator same prompt",
        "notes": "Physics flight sim — Opus broken vs Fable working",
        "local_file": "research/reference-videos/social/youtube-jono-flight-sim.mp4",
    }
    topic = "Fable 5 same-prompt comparisons vs Opus what builders ship"
    score, tags = score_resource(entry, topic, variant="social-comparison")
    assert score >= 0.34
    assert "informational_keywords" in tags or "comparison_fit" in tags


def test_low_value_title_scores_lower():
    entry = {
        "id": "hype-teaser",
        "title": "Logo refresh hype montage reaction only",
        "notes": "Teaser trailer",
        "local_file": "research/reference-videos/social/teaser.mp4",
    }
    score, _ = score_resource(entry, "Fable 5 benchmarks and comparisons", variant="social-comparison")
    assert score < 0.34


def test_missing_catalog_fails(tmp_path: Path):
    project = _project(tmp_path, catalog={"clips": []})
    report = validate_resource_usefulness(project)
    assert not report["ok"]

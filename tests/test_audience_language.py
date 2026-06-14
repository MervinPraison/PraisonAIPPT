"""Tests for general-audience plain language gates."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.audience_language import validate_audience_language
from praisonaippt.daily_single.project import DailySingleProject


def _mini_project(tmp_path: Path, scripts: dict[str, str]) -> DailySingleProject:
    root = tmp_path / "p"
    research = tmp_path / "r"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    for seg, text in scripts.items():
        d = root / "segments" / seg
        d.mkdir(parents=True)
        (d / "script.md").write_text(text, encoding="utf-8")
    return DailySingleProject.from_root(root)


def test_mythos_before_tier_beat_fails(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": "Mythos-level power is amazing.",
        "02-mythos-tier": "Mythos five is the partner version.",
    })
    ok, issues = validate_audience_language(project)
    assert not ok
    assert any("before tiers" in i for i in issues)


def test_mythos_after_tier_beat_in_later_segment_ok(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "02-mythos-tier": "Mythos five is the research and partner-only version.",
        "04-benchmarks": "The partner-only Mythos version scores slightly higher.",
    })
    ok, issues = validate_audience_language(project)
    assert ok, issues


def test_hard_no_flagged(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": "Safety gives a hard no instead of helping.",
    })
    ok, issues = validate_audience_language(project)
    assert not ok
    assert any("hard no" in i.lower() or "blank refusal" in i.lower() for i in issues)


def test_backup_model_needs_gloss(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": "It sends risky prompts to a backup model.",
    })
    ok, issues = validate_audience_language(project)
    assert not ok


def test_headline_logo_refresh_banned(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": "That is the headline this week: not a logo refresh.",
    })
    ok, issues = validate_audience_language(project)
    assert not ok
    assert any("01-cold-open" in i for i in issues)

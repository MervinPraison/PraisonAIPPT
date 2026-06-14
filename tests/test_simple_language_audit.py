"""Tests for dedicated simple-language pipeline gate."""
from __future__ import annotations

import json
from pathlib import Path

from praisonaippt.daily_single.audience_language import validate_audience_language
from praisonaippt.daily_single.simple_language_audit import validate_simple_language
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


def test_insider_headline_phrase_fails(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": (
            "That is the headline this week: not a logo refresh, "
            "but builders posting working games on X."
        ),
    })
    ok, issues = validate_audience_language(project)
    assert not ok
    assert len(issues) >= 2


def test_plain_replacement_passes(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": (
            "The story this week is not just a rebrand — "
            "builders posted working games on X within hours of launch."
        ),
    })
    report = validate_simple_language(project)
    assert report["ok"], report.get("issues")


def test_simple_language_report_written(tmp_path: Path):
    project = _mini_project(tmp_path, {
        "01-cold-open": "Anthropic shipped a new model for everyday teams.",
    })
    validate_simple_language(project)
    out = project.merge_dir / "simple_language_report.json"
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["ok"] is True

"""Tests for daily_single hook montage (June cross-check)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.hook_montage import (
    DEFAULT_MONTAGE_SPECS,
    build_hook_montage_plan,
    hook_visual_windows,
    parse_overview_clauses,
)
from praisonaippt.daily_single.hook_validation import validate_hook_montage
from praisonaippt.daily_single.project import DailySingleProject

FABLE = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-mythos-5"


def test_parse_overview_clauses():
    text = "In the next five minutes: Fable versus Mythos, Stripe proof, benchmark scores."
    clauses = parse_overview_clauses(text)
    assert len(clauses) == 3
    assert "Fable versus Mythos" in clauses[0]


def test_hook_visual_windows_has_five_overview_slots():
    script = (
        "Anthropic dropped Fable.\n\n"
        "In the next five minutes: Fable versus Mythos, Stripe proof, benchmarks, safety, API trap.\n\n"
        "Let's get started."
    )
    cues = [{"script_fragment": s["fragment"], "file": s["filename"], "visual": s["visual"]} for s in DEFAULT_MONTAGE_SPECS]
    wins = hook_visual_windows(0.0, 24.0, script, cues)
    overview = [w for w in wins if w.get("section") == "overview"]
    assert len(overview) == 5
    assert len({w["file"] for w in overview}) == 5
    attention = [w for w in wins if w.get("section") == "attention"]
    assert attention[0]["file"] != "claudeai-launch.mp4"


@pytest.mark.skipif(not FABLE.is_dir(), reason="pilot missing")
class TestFableHookMontage:
    def test_montage_plan_resolves_assets(self):
        project = DailySingleProject.from_root(FABLE)
        plan = build_hook_montage_plan(project)
        ok = [c for c in plan["cues"] if c["ok"]]
        assert len(ok) >= 5

    def test_validate_hook_montage_after_timeline(self):
        project = DailySingleProject.from_root(FABLE)
        if not (project.merge_dir / "timeline.json").is_file():
            pytest.skip("timeline missing")
        ok, report = validate_hook_montage(project)
        assert report["overview_windows"] >= 5 or not ok
        overview_files = report.get("distinct_files") or []
        assert "claudeai-launch.mp4" not in overview_files or not ok

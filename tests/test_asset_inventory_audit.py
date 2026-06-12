"""Tests for per-asset inventory gate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.daily_single.asset_inventory_audit import validate_asset_inventory
from praisonaippt.daily_single.hook_montage import TRUST_AUDIT_MONTAGE_SPECS, build_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject

TRUST = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-trust-audit"


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_trust_audit_hook_montage_has_no_demo_scroll():
    files = {s["filename"] for s in TRUST_AUDIT_MONTAGE_SPECS}
    assert "demo-scroll.mp4" not in files


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_asset_inventory_rejects_demo_scroll_in_hook_plan(monkeypatch):
    project = DailySingleProject.from_root(TRUST)

    def bad_specs(beat_map):
        specs = [dict(s) for s in TRUST_AUDIT_MONTAGE_SPECS]
        specs[1] = {**specs[1], "filename": "demo-scroll.mp4"}
        return specs

    monkeypatch.setattr(
        "praisonaippt.daily_single.hook_montage.montage_specs_for",
        bad_specs,
    )
    report = validate_asset_inventory(project, export_frames=False, use_vision=False)
    assert not report["ok"]
    assert any("demo-scroll" in i for i in report.get("issues") or [])


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_asset_inventory_rejects_v2_in_beat_map(monkeypatch):
    project = DailySingleProject.from_root(TRUST)
    bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    bm["beats"]["6"] = {
        "clips": [],
        "images": [{"path": str(TRUST / "research/reference-images/v2-false-positive.png"), "filename": "v2-false-positive.png"}],
        "generated": [],
    }
    project.beat_map_path.write_text(json.dumps(bm), encoding="utf-8")
    report = validate_asset_inventory(project, export_frames=False, use_vision=False)
    assert not report["ok"]
    assert any("v2-" in i for i in report.get("issues") or [])


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_asset_inventory_rejects_fallback_notification(monkeypatch):
    project = DailySingleProject.from_root(TRUST)
    bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    bm["beats"]["6"] = {
        "clips": [{
            "path": str(TRUST / "research/reference-videos/anthropic/fallback-notification.mp4"),
            "filename": "fallback-notification.mp4",
        }],
        "images": [],
        "generated": [],
    }
    project.beat_map_path.write_text(json.dumps(bm), encoding="utf-8")
    report = validate_asset_inventory(project, export_frames=False, use_vision=False)
    assert not report["ok"]
    assert any("fallback-notification" in i for i in report.get("issues") or [])


@pytest.mark.skipif(not TRUST.is_dir(), reason="trust-audit pilot missing")
def test_asset_inventory_exports_frames_for_hook_clips():
    project = DailySingleProject.from_root(TRUST)
    build_hook_montage_plan(project)
    report = validate_asset_inventory(project, export_frames=True, use_vision=False)
    hook_rows = [r for r in report["inventory"] if r["source"] == "hook_montage"]
    assert len(hook_rows) >= 5
    framed = [r for r in hook_rows if r.get("frame_path")]
    assert len(framed) >= 4
    assert "demo-scroll.mp4" not in {r["file"] for r in hook_rows}

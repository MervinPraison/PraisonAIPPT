"""Tests for daily_single pixel-level visual audit."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from praisonaippt.daily_single.hook_montage import attention_hero, hook_visual_windows, DEFAULT_MONTAGE_SPECS
from praisonaippt.daily_single.visual_audit import (
    _sample_times,
    pixel_similarity,
)

FABLE = Path(__file__).resolve().parents[1] / "examples/videos/anthropic-claude-fable-5-mythos-5"


def test_pixel_similarity_identical(tmp_path: Path):
    import subprocess
    src = tmp_path / "a.jpg"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=0.1",
         "-frames:v", "1", str(src)],
        check=True, capture_output=True,
    )
    assert pixel_similarity(src, src) >= 0.99


def test_sample_times_includes_interval_and_midpoints():
    class W:
        def __init__(self, a, b):
            self.start_sec = a
            self.end_sec = b
    times = _sample_times(20.0, 5.0, [W(0, 4), W(10, 14)])
    assert 2.5 in times
    assert 12.0 in times


def test_attention_window_uses_first_hero_not_launch():
    script = (
        "Anthropic dropped Fable.\n\n"
        "In the next five minutes: Fable versus Mythos, Stripe proof, benchmarks, safety, API trap.\n\n"
        "Let's get started."
    )
    cues = [{"script_fragment": s["fragment"], "file": s["filename"], "visual": s["visual"]} for s in DEFAULT_MONTAGE_SPECS]
    wins = hook_visual_windows(0.0, 24.0, script, cues)
    att = [w for w in wins if w.get("section") == "attention"]
    assert len(att) == 1
    assert att[0]["file"] != "claudeai-launch.mp4"
    assert att[0]["file"] == "beat2-tier-diagram.png"


def test_attention_hero_returns_first_cue():
    cues = [{"file": "beat2-tier-diagram.png", "path": "/x/beat2-tier-diagram.png"}]
    assert attention_hero(cues)["file"] == "beat2-tier-diagram.png"


@pytest.mark.skipif(not FABLE.is_dir(), reason="pilot missing")
class TestFableVisualAudit:
    def test_audit_visual_on_pilot(self):
        from praisonaippt.daily_single.project import DailySingleProject
        from praisonaippt.daily_single.visual_audit import run_visual_audit

        project = DailySingleProject.from_root(FABLE)
        mp4 = project.merge_dir / "final.mp4"
        if not mp4.is_file():
            pytest.skip("final.mp4 missing — run assemble-beats")
        report = run_visual_audit(project, interval=10.0, use_vision=False, force=True)
        assert report["samples_total"] >= 5
        assert report["generic_broll_count"] == 0
        att_failures = [
            f for f in report.get("failures") or []
            if f.get("planned_file") == "claudeai-launch.mp4"
        ]
        assert not att_failures, att_failures

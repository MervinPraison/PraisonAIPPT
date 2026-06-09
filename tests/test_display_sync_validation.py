"""Tests for display sync validation and catalogue audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.segment_video.project import SegmentVideoProject
from praisonaippt.segment_video.validation.display_sync import (
    validate_segment_caption_slides,
    validate_segment_speech_overlap,
)
from praisonaippt.segment_video.validation.validators import REGISTRY


PROJECT = Path("examples/june-2026-ai-roundup")


@pytest.fixture
def project():
    if not (PROJECT / "manifest.json").is_file():
        pytest.skip("june-2026 roundup project not present")
    return SegmentVideoProject.from_path(PROJECT.resolve())


def test_display_sync_validator_registered():
    assert "display_sync" in REGISTRY


def test_hook_caption_slides_aligned(project):
    seg = project.root / "segments" / "00-hook"
    if not seg.is_dir():
        pytest.skip("hook segment missing")
    report = validate_segment_caption_slides(seg, project.root)
    assert report["cue_count"] == 15
    aligned = sum(1 for c in report["cues"] if c["checks"]["caption_text"])
    assert aligned == 15


def test_caption_text_matches_notes_per_cue(project):
    seg = project.root / "segments" / "01-nvidia-nemotron-3-ultra"
    if not (seg / "timeline.json").is_file():
        pytest.skip("nemotron timeline missing")
    report = validate_segment_caption_slides(seg, project.root)
    for cue in report["cues"]:
        assert cue["checks"]["caption_text"], cue


def test_slide_jpeg_exists_for_nemotron_cues(project):
    seg = project.root / "segments" / "01-nvidia-nemotron-3-ultra"
    report = validate_segment_caption_slides(seg, project.root)
    for cue in report["cues"]:
        assert cue["checks"]["slide_jpeg"], f"missing jpeg for cue {cue['cue_index']}"


def test_gemma_catalogue_has_full_cue_coverage(project):
    report_path = project.root / "display_validation_report.json"
    if not report_path.is_file():
        pytest.skip("run validate-display first")
    data = json.loads(report_path.read_text())
    gemma = next((t for t in data["catalogue"]["topics"] if t["dir"] == "02-google-gemma-4-12b"), None)
    assert gemma is not None
    assert gemma["media_cues"] >= gemma["sentences"]
    assert gemma["ok"]


def test_caption_timing_accepts_zero_start(project):
    """Regression: start_sec=0.0 must not be treated as missing (0.0 or -1 bug)."""
    seg = project.root / "segments" / "01-nvidia-nemotron-3-ultra"
    if not (seg / "timeline.json").is_file():
        pytest.skip("nemotron timeline missing")
    report = validate_segment_caption_slides(seg, project.root)
    assert report["cues"][0]["checks"]["caption_timing"] is True


def test_speech_overlap_returns_cues(project):
    seg = project.root / "segments" / "01-nvidia-nemotron-3-ultra"
    report = validate_segment_speech_overlap(seg)
    assert not report.get("skipped")
    assert len(report["cues"]) >= 1

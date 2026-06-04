"""Tests for deck pipeline, variant sync, and plan-slides."""

from pathlib import Path

import pytest
import yaml

from praisonaippt.deck_pipeline import (
    check_timing_drift,
    expected_deck_duration,
    validate_deck_assets,
    validate_deck_schema,
)
from praisonaippt.plan_slides import draft_verses_from_transcript, seed_timing_from_transcript
from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.variant_sync import sync_variants_from_master, variants_drift

PKG = Path(__file__).resolve().parent.parent
TRANSCRIPT = PKG / "examples" / "short-script-50590_timestamps.json"
HEYGEN_MP4 = PKG / "examples" / "heygen-article-50590.mp4"


def test_validate_schema_heygen_content():
    data = yaml.safe_load((PKG / "examples" / "heygen-50590-content.yaml").read_text(encoding="utf-8"))
    step = validate_deck_schema(data)
    assert step.ok


def test_expected_deck_duration_positive():
    data = yaml.safe_load((PKG / "examples" / "heygen-50590-content.yaml").read_text(encoding="utf-8"))
    assert expected_deck_duration(data) > 10


@pytest.mark.skipif(not TRANSCRIPT.is_file(), reason="transcript fixture missing")
def test_timing_drift_tight_when_seeded():
    data = yaml.safe_load((PKG / "examples" / "heygen-50590-content.yaml").read_text(encoding="utf-8"))
    seeded = seed_timing_from_transcript(data, TRANSCRIPT)
    step = check_timing_drift(seeded, TRANSCRIPT, max_start_drift_sec=2.5, max_duration_drift_sec=3.0)
    assert step.ok, step.detail


@pytest.mark.skipif(not HEYGEN_MP4.is_file(), reason="HeyGen MP4 missing")
def test_validate_assets_heygen_video():
    data = {
        "sections": [{"verses": [{"avatar_video_path": str(HEYGEN_MP4)}]}],
    }
    step = validate_deck_assets(data, source_file=str(PKG / "examples" / "heygen-50590-content.yaml"))
    assert step.ok
    assert "avatar_video" in step.data.get("checked", {})


def test_sync_and_drift_roundtrip(tmp_path):
    master = tmp_path / "content.yaml"
    master.write_text(
        yaml.dump({
            "presentation_title": "T",
            "sections": [{"verses": [{"text": "a", "slide_type": "verse", "duration_sec": 1}]}],
            "video_export": {"narration_mode": "avatar"},
        }),
        encoding="utf-8",
    )
    sync_variants_from_master(master, tmp_path, prefix="demo")
    ok, issues = variants_drift(master, tmp_path, prefix="demo")
    assert ok, issues


@pytest.mark.skipif(not TRANSCRIPT.is_file(), reason="transcript fixture missing")
def test_draft_verses_from_transcript():
    td = load_whisper_json(TRANSCRIPT)
    verses = draft_verses_from_transcript(td)
    assert len(verses) >= 5
    assert all("audio_start_sec" in v for v in verses)
    assert all(v["slide_type"] != "deck_headline" for v in verses)


@pytest.mark.skipif(
    not (PKG / "examples" / "heygen-article-50590.mp4").is_file(),
    reason="HeyGen sample video missing",
)
def test_validate_pip_centring_heygen_deck():
    import yaml
    from praisonaippt.deck_pipeline import validate_pip_centring

    deck_path = PKG / "examples" / "heygen-50590-video-audio-heygen.yaml"
    data = yaml.safe_load(deck_path.read_text(encoding="utf-8"))
    data["_source_file"] = str(deck_path.resolve())
    step = validate_pip_centring(data, source_file=data["_source_file"])
    assert step.ok, step.detail
    assert step.data.get("probes")
    assert any(p.get("pass") for p in step.data["probes"])


@pytest.mark.skipif(
    not (PKG / "examples" / "heygen-50590-video-audio-heygen.mp4").is_file(),
    reason="HeyGen MP4 missing",
)
def test_post_render_qc_heygen_mp4():
    import yaml
    from praisonaippt.deck_pipeline import expected_deck_duration, post_render_qc

    data = yaml.safe_load(
        (PKG / "examples" / "heygen-50590-video-audio-heygen.yaml").read_text(encoding="utf-8"),
    )
    mp4 = PKG / "examples" / "heygen-50590-video-audio-heygen.mp4"
    step = post_render_qc(mp4, expected_duration_sec=expected_deck_duration(data))
    assert step.ok, step.detail


def test_pipeline_skip_build_no_jpeg_export(tmp_path):
    import yaml
    from praisonaippt.deck_pipeline import PipelineOptions, run_pipeline

    deck = tmp_path / "deck.yaml"
    deck.write_text(
        yaml.dump({
            "presentation_title": "T",
            "sections": [{"verses": [{"text": "a", "slide_type": "verse", "duration_sec": 1}]}],
            "slide_images_dir": "slides",
        }),
        encoding="utf-8",
    )
    (tmp_path / "slides").mkdir()
    (tmp_path / "slides" / "slide-001.jpg").write_bytes(b"x" * 6000)
    opts = PipelineOptions(
        deck_yaml=str(deck),
        build_pptx=False,
        validate_pip=False,
        validate_assets=False,
        validate_timing=False,
        check_variant_drift=False,
    )
    report = run_pipeline(opts)
    names = [s.name for s in report.steps]
    assert "slide_jpegs_export" not in names
    assert "slide_jpegs" in names


def test_pipeline_report_json_roundtrip(tmp_path):
    from praisonaippt.deck_pipeline import PipelineReport, StepResult

    report = PipelineReport(ok=True, deck_yaml="deck.yaml", started_at="2026-01-01T00:00:00Z")
    report.add(StepResult("schema", True, "ok"))
    path = report.write_json(tmp_path / "report.json")
    loaded = __import__("json").loads(path.read_text())
    assert loaded["ok"] is True
    assert len(loaded["steps"]) == 1

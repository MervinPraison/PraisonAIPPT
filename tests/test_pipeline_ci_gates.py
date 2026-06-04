"""CI gate coverage for deck pipeline (report.json gates, approval, rights, A/V)."""

import json
from pathlib import Path

import pytest
import yaml

from praisonaippt.deck_pipeline import (
    GATE_AV_SYNC,
    GATE_PIP_CENTRING,
    GATE_PLAN_APPROVAL,
    GATE_POST_RENDER,
    GATE_PRE_RENDER,
    GATE_RIGHTS,
    GATE_SLIDE_JPEG_GOLDEN,
    GATE_UNIFIED_PIPELINE,
    PipelineReport,
    StepResult,
    check_av_sync,
    post_render_qc,
    validate_plan_approval,
    validate_rights_licensing,
)
from praisonaippt.plan_slides import (
    approve_plan,
    check_plan_approval_gate,
    is_plan_approved,
    write_plan_meta,
    write_plan_yaml,
)

PKG = Path(__file__).resolve().parent.parent
TRANSCRIPT = PKG / "examples" / "short-script-50590_timestamps.json"
HEYGEN_DECK = PKG / "examples" / "heygen-50590-video-audio-heygen.yaml"
HEYGEN_MP4 = PKG / "examples" / "heygen-50590-video-audio-heygen.mp4"


def test_report_exit_code_and_gates():
    report = PipelineReport(ok=False, deck_yaml="d.yaml", started_at="t")
    report.add(StepResult("schema", True, "ok"))
    d = report.to_dict()
    assert d["exit_code"] == 1
    assert GATE_PRE_RENDER in d["gates"]
    assert d["gates"][GATE_PRE_RENDER]["validated"] is True


def test_rights_gate_blocks_when_required():
    step = validate_rights_licensing({"require_rights_ack": True, "rights_acknowledged": False})
    assert not step.ok
    step2 = validate_rights_licensing({"require_rights_ack": True, "rights_acknowledged": True})
    assert step2.ok


def test_plan_approval_checkpoint(tmp_path):
    draft = tmp_path / "draft.yaml"
    draft.write_text("presentation_title: T\nsections: []\n", encoding="utf-8")
    write_plan_meta(draft, transcript_path="t.json")
    ok, _ = check_plan_approval_gate({"plan_draft": str(draft)}, base_dir=tmp_path)
    assert not ok
    approve_plan(draft)
    assert is_plan_approved(draft)
    ok2, _ = check_plan_approval_gate({"plan_draft": str(draft)}, base_dir=tmp_path)
    assert ok2


def test_plan_approval_skipped_when_content_approved():
    step = validate_plan_approval({"content_approved": True})
    assert step.ok


@pytest.mark.skipif(not TRANSCRIPT.is_file(), reason="transcript missing")
@pytest.mark.skipif(not HEYGEN_DECK.is_file(), reason="deck missing")
def test_av_sync_heygen_deck():
    data = yaml.safe_load(HEYGEN_DECK.read_text(encoding="utf-8"))
    data["_source_file"] = str(HEYGEN_DECK.resolve())
    step = check_av_sync(
        data,
        source_file=data["_source_file"],
        transcript_path=TRANSCRIPT,
    )
    assert step.ok, step.detail


@pytest.mark.skipif(not HEYGEN_MP4.is_file(), reason="mp4 missing")
@pytest.mark.skipif(not HEYGEN_DECK.is_file(), reason="deck missing")
def test_post_render_includes_fps():
    data = yaml.safe_load(HEYGEN_DECK.read_text(encoding="utf-8"))
    from praisonaippt.deck_pipeline import _expected_video_spec, expected_deck_duration

    spec = _expected_video_spec(data)
    step = post_render_qc(
        HEYGEN_MP4,
        expected_duration_sec=expected_deck_duration(data),
        expected_width=spec["width"],
        expected_height=spec["height"],
        expected_fps=float(spec["fps"]),
        fps_tolerance=3.0,
    )
    assert step.ok, step.detail
    assert "fps" in step.data


@pytest.mark.skipif(not TRANSCRIPT.is_file(), reason="transcript missing")
def test_plan_slides_writes_pending_meta(tmp_path):
    out = tmp_path / "draft.yaml"
    write_plan_yaml(TRANSCRIPT, out)
    meta = out.with_name(f"{out.stem}.plan-meta.json")
    assert meta.is_file()
    loaded = json.loads(meta.read_text())
    assert loaded["status"] == "pending"

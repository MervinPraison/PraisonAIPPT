"""SDK tests for centralised daily-single pipeline definition and engine."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from praisonaippt.daily_single.engine import DailySinglePipelineEngine, PipelineReport, StepResult
from praisonaippt.daily_single.pipeline import (
    BUILD_PIPELINE,
    PUBLISH_GATE,
    PYTEST_MODULES,
    build_protocol_stages,
    pipeline_manifest,
)


def test_pipeline_manifest_schema():
    m = pipeline_manifest()
    assert m["schema_version"] == 2
    assert "av_order" in m
    assert m["name"] == "daily-single-pipeline"
    assert len(m["build"]) == len(BUILD_PIPELINE)
    assert len(m["publish_gate"]) == len(PUBLISH_GATE)
    assert any("test_word_visual_sync" in p for p in m["pytest_modules"])


def test_build_pipeline_order_video_first():
    ids = [s.id for s in BUILD_PIPELINE]
    assert ids.index("assemble-beats") < ids.index("validate-av-post_assemble")
    assert ids.index("validate-av-post_assemble") < ids.index("build-captions")
    assert ids.index("build-captions") < ids.index("validate-av-post_captions")
    assert ids.index("validate-av-post_captions") < ids.index("validate-spoken-visual")
    assert ids.index("validate-spoken-visual") < ids.index("validate-qa-post_build")
    assert "validate-beat-map" in ids
    assert "validate-qa-pre_build" in ids
    assert "validate-qa-pre_assemble" in ids


def test_publish_gate_pre_assemble_before_assemble_before_captions():
    gate_ids = [s.id for s in PUBLISH_GATE]
    assert gate_ids.index("validate-qa-pre_assemble") < gate_ids.index("assemble-beats")
    assert gate_ids.index("assemble-beats") < gate_ids.index("build-captions")


def test_publish_gate_includes_v1_through_v13_steps():
    gate_ids = [s.id for s in PUBLISH_GATE]
    assert gate_ids[0] == "validate-qa-pre_build"
    assert "pytest" in gate_ids
    assert "validate-qa-post_build" == gate_ids[-1]
    assert "audit-visual" in gate_ids
    assert "validate-beat-map" in gate_ids
    assert "validate-canonical-scroll" in gate_ids


def test_build_protocol_stages_unique_ids():
    stages = build_protocol_stages()
    ids = [s["pipeline_id"] for s in stages]
    assert len(ids) == len(set(ids))
    assert any(s.get("depends_on") for s in stages)


def test_engine_manifest_matches_module():
    assert DailySinglePipelineEngine.manifest() == pipeline_manifest()


def test_engine_status_minimal_project(tmp_path: Path):
    root = tmp_path / "proj"
    research = tmp_path / "research"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "sdk-test", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    merge = root / "merge"
    merge.mkdir()
    (merge / "final.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")

    engine = DailySinglePipelineEngine(root)
    status = engine.status()
    assert status["slug"] == "sdk-test"
    assert "pipeline_manifest" in status
    assert status["outputs"]["final_srt"].endswith("final.srt")


def test_engine_run_publish_gate_stops_on_fail(tmp_path: Path):
    root = tmp_path / "proj"
    research = tmp_path / "research"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "gate-test", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    (root / "merge").mkdir()

    engine = DailySinglePipelineEngine(root)
    fail_report = PipelineReport(
        ok=False,
        steps=[StepResult("validate-qa-pre_build", False, 1, "mock fail")],
    )

    with patch.object(engine, "run_qa", return_value=fail_report):
        report = engine.run_publish_gate(assemble=False, stop_on_fail=True)

    assert not report.ok
    assert len(report.steps) == 1
    assert (root / "merge" / "pipeline_report.json").is_file()


def test_refresh_fails_without_final_mp4(tmp_path: Path):
    from praisonaippt.daily_single.project import DailySingleProject
    from praisonaippt.daily_single.spoken_visual_gates import refresh_publish_validators

    root = tmp_path / "proj"
    research = tmp_path / "research"
    research.mkdir()
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "refresh-test", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    merge = root / "merge"
    merge.mkdir()
    project = DailySingleProject.from_root(root)
    ok, results = refresh_publish_validators(project)
    assert not ok
    assert results["spoken_visual"]["ok"] is False


def test_pytest_modules_exist():
    repo = Path(__file__).resolve().parents[1]
    for mod in PYTEST_MODULES:
        assert (repo / mod).is_file(), mod

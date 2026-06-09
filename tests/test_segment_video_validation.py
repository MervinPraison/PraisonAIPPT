"""Tests for protocol-driven validation suite."""
from __future__ import annotations

from pathlib import Path

import pytest

from praisonaippt.segment_video.project import SegmentVideoProject
from praisonaippt.segment_video.validation.suite import run_validation_suite
from praisonaippt.segment_video.validation.validators import REGISTRY, validate_hook_montage, validate_script_policy


PROJECT = Path("examples/videos/june-2026-ai-roundup")


@pytest.fixture
def project():
    if not (PROJECT / "manifest.json").is_file():
        pytest.skip("june-2026 roundup project not present")
    return SegmentVideoProject.from_path(PROJECT.resolve())


def test_validator_registry():
    expected = {
        "tools", "artifacts", "hook_montage", "script_policy",
        "image_audit", "segment_sync", "audio_loudness", "merge_output", "coverage", "protocol_stages",
        "manual_assets", "hook_speech_sync", "display_sync", "required_assets",
    }
    assert expected <= set(REGISTRY.keys())


def test_protocol_has_validation_suite(project):
    protocol = project.load_protocol()
    suite = protocol.get("validation_suite") or {}
    ids = {v["id"] for v in suite.get("validators", [])}
    assert "hook_montage" in ids
    assert "image_audit" in ids
    assert any(s.get("id") == "validate-all" for s in protocol.get("stages", []))


def test_run_validation_suite(project):
    suite = run_validation_suite(project)
    data = suite.to_dict()
    assert data["summary"]["validators_run"] >= 7


def test_hook_montage_pairing(project):
    protocol = project.load_protocol()
    report = validate_hook_montage(project, protocol)
    pairing = next(c for c in report.checks if c.id == "hook:topic_pairing")
    assert pairing.ok, pairing.details


def test_script_policy(project):
    protocol = project.load_protocol()
    report = validate_script_policy(project, protocol)
    assert report.ok


def test_regenerate_validate_only_chain():
    from praisonaippt.segment_video.protocol import REGENERATE_CHAINS

    assert REGENERATE_CHAINS["validate_only"] == ["validate-all"]

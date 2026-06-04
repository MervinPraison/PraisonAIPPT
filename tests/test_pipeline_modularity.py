"""Pipeline protocols, YAML validation, and build/export decoupling."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from praisonaippt.deck_pipeline import PipelineOptions, run_pipeline
from praisonaippt.exceptions import SchemaError
from praisonaippt.pipeline_protocols import default_build_presentation
from praisonaippt.video_presets import VIDEO_PRESETS, expected_video_spec
from praisonaippt.yaml_validate import validate_avatar_calibration, validate_pipeline

PKG = Path(__file__).resolve().parent.parent


def test_expected_video_spec_uses_shared_presets():
    spec = expected_video_spec({"video_export": {"preset": "draft"}})
    assert spec["width"] == VIDEO_PRESETS["draft"]["width"]
    assert spec["fps"] == VIDEO_PRESETS["draft"]["fps"]


def test_invalid_pipeline_bool_raises():
    with pytest.raises(SchemaError, match="auto_sync"):
        validate_pipeline({"auto_sync": "yes"})


def test_invalid_calibration_method_raises():
    with pytest.raises(SchemaError, match="method"):
        validate_avatar_calibration({"method": "neural"})


def test_heygen_content_pipeline_block_validates():
    data = yaml.safe_load((PKG / "examples" / "heygen-50590-content.yaml").read_text(encoding="utf-8"))
    validate_pipeline(data.get("pipeline"))
    validate_avatar_calibration(data.get("avatar_calibration"))


def test_run_pipeline_uses_injected_build_fn(tmp_path):
    deck = tmp_path / "mini.yaml"
    deck.write_text(
        yaml.dump({
            "presentation_title": "T",
            "sections": [{"verses": [{"text": "a", "slide_type": "verse"}]}],
            "pipeline": {"validate_plan": False, "validate_rights": False},
        }),
        encoding="utf-8",
    )
    build = MagicMock(return_value=str(tmp_path / "out.pptx"))
    (tmp_path / "out.pptx").write_bytes(b"x")

    opts = PipelineOptions(
        deck_yaml=str(deck),
        build_pptx=True,
        export_mp4=False,
        validate_pip=False,
        validate_plan=False,
        validate_rights=False,
        sync_variants=False,
        check_variant_drift=False,
        build_fn=build,
    )
    report = run_pipeline(opts)
    assert report.ok
    build.assert_called_once()
    assert not any(s.name == "export_mp4" for s in report.steps)


def test_default_build_is_callable():
    assert callable(default_build_presentation)


def test_load_deck_mapping_json_roundtrip(tmp_path):
    from praisonaippt.loader import load_deck_mapping, write_deck_mapping

    deck = tmp_path / "deck.json"
    payload = {
        "presentation_title": "JSON deck",
        "sections": [{"verses": [{"text": "hi", "slide_type": "verse"}]}],
        "pipeline": {"validate_plan": False, "validate_rights": False},
    }
    write_deck_mapping(deck, payload)
    loaded = load_deck_mapping(deck)
    assert loaded["pipeline"]["validate_plan"] is False


def test_run_pipeline_json_deck_schema(tmp_path):
    from praisonaippt.loader import write_deck_mapping

    deck = tmp_path / "deck.json"
    write_deck_mapping(
        deck,
        {
            "presentation_title": "T",
            "sections": [{"verses": [{"text": "a", "slide_type": "verse"}]}],
            "pipeline": {"validate_plan": False, "validate_rights": False},
        },
    )
    opts = PipelineOptions(
        deck_yaml=str(deck),
        build_pptx=False,
        export_mp4=False,
        validate_pip=False,
        validate_plan=False,
        validate_rights=False,
        sync_variants=False,
        check_variant_drift=False,
    )
    report = run_pipeline(opts)
    assert any(s.name == "schema" and s.ok for s in report.steps)

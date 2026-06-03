"""Tests for loader error paths and CLI integration."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from praisonaippt import create_presentation, load_verses_from_file

REPO_ROOT = Path(__file__).parent.parent
SAMPLE_YAML = REPO_ROOT / "examples" / "sample_verses.yaml"


def test_load_verses_from_file_missing_returns_none(capsys):
    data = load_verses_from_file("/nonexistent/path/verses.yaml")
    assert data is None
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower()


def test_load_verses_from_file_invalid_json_returns_none(capsys, tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    data = load_verses_from_file(str(bad_json))
    assert data is None
    captured = capsys.readouterr()
    assert "invalid format" in captured.out.lower()


def test_load_verses_from_file_invalid_schema_returns_none(capsys, tmp_path):
    bad_schema = tmp_path / "bad.yaml"
    bad_schema.write_text(
        "presentation_title: Bad\nsections:\n  - section: S\n    verses:\n      - highlights: []\n",
        encoding="utf-8",
    )
    data = load_verses_from_file(str(bad_schema))
    assert data is None
    captured = capsys.readouterr()
    assert "invalid schema" in captured.out.lower()


def test_cli_build_from_input(tmp_path):
    if not SAMPLE_YAML.is_file():
        pytest.skip("sample_verses.yaml missing")

    out_pptx = tmp_path / "cli_build.pptx"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "praisonaippt.cli",
            "-i",
            str(SAMPLE_YAML),
            "-o",
            str(out_pptx),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert out_pptx.is_file()


def test_cli_list_slides(tmp_path):
    if not SAMPLE_YAML.is_file():
        pytest.skip("sample_verses.yaml missing")

    pptx = tmp_path / "outline.pptx"
    data = load_verses_from_file(str(SAMPLE_YAML))
    assert data is not None
    create_presentation(data, output_file=str(pptx))

    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "list-slides", str(pptx)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "slides:" in result.stdout.lower()


def test_cli_convert_yaml_validates_schema(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps(
            {
                "presentation_title": "Invalid",
                "sections": [{"section": "S", "verses": [{"highlights": ["x"]}]}],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "convert-yaml", str(invalid)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "invalid schema" in (result.stdout + result.stderr).lower()


def test_cli_convert_json_yaml_to_json_validates(tmp_path):
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        "presentation_title: Invalid\nsections:\n  - section: S\n    verses:\n      - highlights: []\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "convert-json", str(invalid)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "invalid schema" in (result.stdout + result.stderr).lower()

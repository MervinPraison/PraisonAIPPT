"""Tests for YAML deck → Markdown export."""

import subprocess
import sys
from pathlib import Path

import pytest

import praisonaippt
from praisonaippt import deck_to_markdown, load_verses_from_file, write_deck_markdown
from praisonaippt.deck_export.highlights import apply_markdown_highlights

REPO_ROOT = Path(__file__).parent.parent
BEING_FRUITFUL = REPO_ROOT / "examples" / "being_fruitful.yaml"
SAMPLE_YAML = REPO_ROOT / "examples" / "sample_verses.yaml"


def test_deck_to_markdown_in_all():
    assert "deck_to_markdown" in praisonaippt.__all__


def test_apply_markdown_highlights_bold():
    text = "bear fruit for God"
    out = apply_markdown_highlights(text, ["bear fruit"])
    assert "**bear fruit**" in out


def test_apply_html_highlights_coloured():
    from praisonaippt.deck_export.highlights import apply_html_highlights

    text = "bear fruit for God"
    out = apply_html_highlights(text, ["bear fruit"], default_hex="#FFD700")
    assert "background-color:#FFD700" in out
    assert "bear fruit" in out


def test_apply_html_highlights_green_dict():
    from praisonaippt.deck_export.highlights import apply_html_highlights

    text = "righteousness apart from the law"
    out = apply_html_highlights(
        text,
        [{"text": "apart from the law", "color": "green"}],
    )
    assert "background-color:#32B432" in out


def test_being_fruitful_structure():
    if not BEING_FRUITFUL.is_file():
        pytest.skip("being_fruitful.yaml missing")
    data = load_verses_from_file(str(BEING_FRUITFUL))
    assert data is not None
    md = deck_to_markdown(data)

    assert md.startswith("# **Being Fruitful**")
    assert "## Key Scriptures" in md
    assert "# How to Be Fruitful" in md
    assert "## 1. Focus on Jesus" in md
    assert "## 2. Do Not Be Lukewarm" in md
    assert "Walking in the Flesh vs. Walking in the Spirit" in md

    # Section order
    assert md.index("Key Scriptures") < md.index("How to Be Fruitful")
    assert md.index("How to Be Fruitful") < md.index("1. Focus on Jesus")
    assert md.index("1. Focus on Jesus") < md.index("2. Do Not Be Lukewarm")
    assert md.index("4. It Is Free") < md.index("Walking in the Flesh")

    # Blockquote attribution
    assert '> — Romans 7:4' in md
    assert '> — Romans 7:2 (NKJV)' in md

    # Highlights
    assert "**bear fruit**" in md or "**bear fruit for God**" in md
    assert "**adulteress**" in md

    # Separator after Key Scriptures, not between chapter header and subsection 1
    key_end = md.index("# How to Be Fruitful")
    focus_start = md.index("## 1. Focus on Jesus")
    between = md[key_end:focus_start]
    assert "---" not in between


def test_being_fruitful_separators_between_sections():
    if not BEING_FRUITFUL.is_file():
        pytest.skip("being_fruitful.yaml missing")
    data = load_verses_from_file(str(BEING_FRUITFUL))
    md = deck_to_markdown(data)
    assert md.count("---") >= 5


def test_slide_type_fallbacks():
    data = {
        "presentation_title": "Types",
        "sections": [
            {
                "section": "Layouts",
                "verses": [
                    {
                        "reference": "List example",
                        "text": "Alpha\nBeta",
                        "list_type": "bullet",
                    },
                    {
                        "slide_type": "comparison",
                        "reference": "Law vs grace",
                        "columns": [
                            {"heading": "Before", "text": "Condemns"},
                            {"heading": "After", "text": "Saves"},
                        ],
                    },
                    {
                        "slide_type": "big_number",
                        "number": "100",
                        "label": "Fold",
                        "reference": "Mark 10:30",
                    },
                ],
            }
        ],
    }
    md = deck_to_markdown(data)
    assert "- Alpha" in md
    assert "| Before | Condemns |" in md
    assert "## 100" in md


def test_write_deck_markdown(tmp_path):
    data = {
        "presentation_title": "Test",
        "sections": [{"section": "S", "verses": [{"reference": "J 1:1", "text": "In the beginning."}]}],
    }
    out = tmp_path / "out.md"
    write_deck_markdown(data, out)
    assert out.read_text(encoding="utf-8").startswith("# **Test**")


def test_cli_convert_markdown_happy_path(tmp_path):
    if not SAMPLE_YAML.is_file():
        pytest.skip("sample_verses.yaml missing")
    out_md = tmp_path / "sample.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "praisonaippt.cli",
            "convert-markdown",
            str(SAMPLE_YAML),
            "--markdown-output",
            str(out_md),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert out_md.is_file()
    assert "Converted" in result.stdout


def test_cli_convert_markdown_being_fruitful(tmp_path):
    if not BEING_FRUITFUL.is_file():
        pytest.skip("being_fruitful.yaml missing")
    out_md = tmp_path / "being_fruitful.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "praisonaippt.cli",
            "convert-markdown",
            str(BEING_FRUITFUL),
            "--markdown-output",
            str(out_md),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    text = out_md.read_text(encoding="utf-8")
    assert "# **Being Fruitful**" in text
    assert "> — Galatians 3:5–6" in text


def test_cli_convert_markdown_invalid_schema(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "presentation_title: Bad\nsections:\n  - section: S\n    verses:\n      - highlights: []\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "convert-markdown", str(bad)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "invalid schema" in (result.stdout + result.stderr).lower()


def test_cli_convert_markdown_no_input():
    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "convert-markdown"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "input file required" in (result.stdout + result.stderr).lower()


def test_convert_markdown_upload_gdrive(tmp_path, monkeypatch):
    """--upload-gdrive triggers upload_to_gdrive after writing the file."""
    from praisonaippt.cli import handle_convert_markdown_command

    deck = tmp_path / "tiny.yaml"
    deck.write_text(
        "presentation_title: Upload Test\nsections:\n"
        "  - section: S\n    verses:\n      - reference: J 1:1\n        text: Hello.\n",
        encoding="utf-8",
    )
    out_md = tmp_path / "tiny.md"
    calls = []

    def _fake_upload(file_path, **kwargs):
        calls.append((file_path, kwargs))
        return {"id": "fake-id", "name": kwargs.get("file_name") or Path(file_path).stem,
                "mimeType": "application/vnd.google-apps.document",
                "webViewLink": "https://drive.example/md"}

    monkeypatch.setattr("praisonaippt.gdrive_uploader.upload_to_gdrive", _fake_upload)
    monkeypatch.setattr("praisonaippt.gdrive_uploader.is_gdrive_available", lambda: True)

    class Args:
        input_file = str(deck)
        markdown_output = str(out_md)
        no_highlights = False
        no_separators = False
        upload_gdrive = True
        gdrive_credentials = str(tmp_path / "fake-creds.json")
        gdrive_folder_id = None
        gdrive_folder_name = None
        gdrive_date_folders = False

    class ConfigStub:
        def should_auto_upload_gdrive(self):
            return False

        def get_gdrive_credentials(self):
            return None

        def get_gdrive_folder_id(self):
            return None

        def get_gdrive_folder_name(self):
            return None

        def use_date_folders(self):
            return False

        def get_date_format(self):
            return "%Y/%m"

    rc = handle_convert_markdown_command(Args(), ConfigStub())
    assert rc == 0
    assert out_md.is_file()
    assert calls and Path(calls[0][0]) == out_md.with_suffix(".html")
    assert calls[0][1].get("as_google_doc") is True
    assert calls[0][1].get("file_name") == "Upload Test"


def test_convert_markdown_auto_upload_from_yaml(tmp_path, monkeypatch):
    """auto_upload_gdrive: true in deck YAML triggers upload without --upload-gdrive."""
    from praisonaippt.cli import handle_convert_markdown_command

    deck = tmp_path / "auto.yaml"
    deck.write_text(
        "presentation_title: Auto\nauto_upload_gdrive: true\nsections:\n"
        "  - section: S\n    verses:\n      - reference: J 1:1\n        text: Hi.\n",
        encoding="utf-8",
    )
    out_md = deck.with_suffix(".md")
    calls = []

    def _fake_upload(file_path, **kwargs):
        calls.append(kwargs)
        return {"id": "x", "name": "Being Fruitful", "mimeType": "application/vnd.google-apps.document"}

    monkeypatch.setattr("praisonaippt.gdrive_uploader.upload_to_gdrive", _fake_upload)
    monkeypatch.setattr("praisonaippt.gdrive_uploader.is_gdrive_available", lambda: True)

    class Args:
        input_file = str(deck)
        markdown_output = None
        no_highlights = False
        no_separators = False
        upload_gdrive = False
        gdrive_credentials = str(tmp_path / "creds.json")
        gdrive_folder_id = None
        gdrive_folder_name = None
        gdrive_date_folders = False

    class ConfigStub:
        def should_auto_upload_gdrive(self):
            return False

        def get_gdrive_credentials(self):
            return None

        def get_gdrive_folder_id(self):
            return None

        def get_gdrive_folder_name(self):
            return None

        def use_date_folders(self):
            return False

        def get_date_format(self):
            return "%Y/%m"

    rc = handle_convert_markdown_command(Args(), ConfigStub())
    assert rc == 0
    assert calls
    assert calls[0].get("as_google_doc") is True
    assert calls[0].get("file_name") == "Auto"

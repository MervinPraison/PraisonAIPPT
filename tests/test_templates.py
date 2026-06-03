"""Tests for extendable YAML theme templates."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from praisonaippt import load_verses_from_file
from praisonaippt.exceptions import SchemaError
from praisonaippt.template_resolver import (
    apply_template_layers,
    get_template_path,
    list_templates,
    resolve_template_style,
)

REPO_ROOT = Path(__file__).parent.parent


def test_get_template_path_builtin():
    path = get_template_path("sermon-dark")
    assert path is not None
    assert path.endswith("sermon-dark.yaml")


def test_sermon_gold_extends_chain():
    resolved = resolve_template_style("sermon-gold")
    style = resolved["slide_style"]
    assert style["background_image"] == "assets/background_alt.jpg"
    assert style["text_color"] == "white"
    assert style["font_name"] == "Palatino"
    assert style["highlight_color"] == "#FFD700"
    assert style["reference_color"] == "#66B3FF"
    assert resolved.get("slide_size") == "widescreen"


def test_template_matches_why_delay_fingerprint():
    resolved = resolve_template_style("sermon-gold")
    why_delay = yaml.safe_load((REPO_ROOT / "examples" / "why_delay.yaml").read_text())
    for key, value in why_delay["slide_style"].items():
        assert resolved["slide_style"].get(key) == value


def test_deck_filename_does_not_shadow_builtin_template():
    """Deck named sermon-dark.yaml must still resolve templates/sermon-dark.yaml."""
    deck = REPO_ROOT / "examples" / "template_demos" / "sermon-dark.yaml"
    data = load_verses_from_file(str(deck))
    assert data is not None
    assert data["slide_style"]["text_color"] == "white"
    assert data["slide_style"]["font_name"] == "Palatino"
    assert data["slide_style"]["background_color"] == "#1A1A2E"


def test_deck_template_merge(tmp_path):
    deck = tmp_path / "deck.yaml"
    deck.write_text(
        textwrap.dedent(
            """
            template: sermon-dark
            presentation_title: Test
            sections:
              - section: S
                verses:
                  - reference: John 3:16
                    text: For God so loved the world.
            """
        ),
        encoding="utf-8",
    )
    data = load_verses_from_file(str(deck))
    assert data is not None
    assert data["slide_style"]["text_color"] == "white"
    assert data["slide_style"]["background_image"] == "assets/background_alt.jpg"


def test_deck_overrides_template(tmp_path):
    deck = tmp_path / "deck.yaml"
    deck.write_text(
        textwrap.dedent(
            """
            template: sermon-dark
            presentation_title: Test
            slide_style:
              highlight_color: '#FF0000'
            sections:
              - section: S
                verses:
                  - reference: John 3:16
                    text: Hello
            """
        ),
        encoding="utf-8",
    )
    data = load_verses_from_file(str(deck))
    assert data["slide_style"]["highlight_color"] == "#FF0000"
    assert data["slide_style"]["text_color"] == "white"


def test_preset_and_overrides(tmp_path):
    deck = tmp_path / "deck.yaml"
    deck.write_text(
        textwrap.dedent(
            """
            presentation_title: Test
            slide_style:
              preset: sermon-dark
              overrides:
                highlight_color: '#ABCDEF'
            sections:
              - section: S
                verses:
                  - reference: Gen 1:1
                    text: In the beginning
            """
        ),
        encoding="utf-8",
    )
    data = load_verses_from_file(str(deck))
    assert data["slide_style"]["font_name"] == "Palatino"
    assert data["slide_style"]["highlight_color"] == "#ABCDEF"


def test_extends_on_deck(tmp_path):
    parent = tmp_path / "parent.yaml"
    parent.write_text(
        "slide_style:\n  background_image: assets/background_alt.jpg\n",
        encoding="utf-8",
    )
    deck = tmp_path / "deck.yaml"
    deck.write_text(
        textwrap.dedent(
            f"""
            extends: {parent.name}
            presentation_title: Test
            slide_style:
              text_color: white
            sections:
              - section: S
                verses:
                  - reference: Ps 23:1
                    text: The Lord is my shepherd
            """
        ),
        encoding="utf-8",
    )
    data = load_verses_from_file(str(deck))
    assert data["slide_style"]["background_image"] == "assets/background_alt.jpg"
    assert data["slide_style"]["text_color"] == "white"


def test_circular_extends_raises(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("extends: b.yaml\nslide_style:\n  text_color: white\n", encoding="utf-8")
    b.write_text("extends: a.yaml\nslide_style:\n  text_color: white\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        apply_template_layers({"extends": "a.yaml"}, deck_path=a)


def test_list_templates_includes_builtin():
    names = {e["name"] for e in list_templates()}
    assert "default" in names
    assert "sermon-dark" in names
    assert "sermon-gold" in names
    assert "sermon-dark-center" in names
    assert "sermon-dark-ref-bottom" in names
    assert "light-minimal" in names


def test_user_template_dir(tmp_path, monkeypatch):
    user_dir = tmp_path / "templates"
    user_dir.mkdir()
    custom = user_dir / "custom.yaml"
    custom.write_text(
        "description: Custom user theme\nslide_style:\n  text_color: cyan\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "praisonaippt.template_resolver._user_templates_dir",
        lambda: user_dir,
    )
    assert get_template_path("custom") == str(custom.resolve())
    entries = list_templates()
    assert any(e["name"] == "custom" for e in entries)


def test_cli_list_templates():
    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "--list-templates"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0
    assert "sermon-dark" in result.stdout


def test_cli_template_show():
    result = subprocess.run(
        [sys.executable, "-m", "praisonaippt.cli", "template", "sermon-gold"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0
    assert "highlight_color" in result.stdout

"""Tests for the SlideRenderer protocol registry."""

import pytest

from praisonaippt.exceptions import SchemaError
from praisonaippt.slide_renderers import (
    get_renderer,
    list_renderers,
    register_renderer,
    resolve_renderer,
    validate_verse,
)


def test_list_renderers_includes_builtins():
    kinds = set(list_renderers())
    assert kinds >= {"verse", "list", "image", "hebrew_rename"}


def test_resolve_renderer_defaults_to_verse():
    r = resolve_renderer({"reference": "Gen 1:1", "text": "In the beginning"})
    assert r.kind == "verse"


@pytest.mark.parametrize(
    "list_type",
    ["bullet", "numbered"],
)
def test_resolve_renderer_list_types(list_type):
    r = resolve_renderer({"list_type": list_type, "text": "one\ntwo"})
    assert r.kind == "list"


def test_resolve_renderer_image():
    r = resolve_renderer({"slide_type": "image", "image_path": "pic.jpg"})
    assert r.kind == "image"


def test_resolve_renderer_hebrew():
    r = resolve_renderer({"slide_type": "hebrew_rename", "hebrew_rows": []})
    assert r.kind == "hebrew_rename"


def test_resolve_renderer_unknown_slide_type():
    with pytest.raises(SchemaError, match="Unknown slide_type"):
        resolve_renderer({"slide_type": "not_registered"})


def test_validate_image_requires_path():
    with pytest.raises(SchemaError, match="image_path"):
        validate_verse({"slide_type": "image"}, "sections[0].verses[0]")


def test_validate_image_fit():
    with pytest.raises(SchemaError, match="image_fit"):
        validate_verse(
            {"slide_type": "image", "image_path": "x.jpg", "image_fit": "stretch"},
            "v[0]",
        )


def test_validate_hebrew_requires_rows():
    with pytest.raises(SchemaError, match="hebrew_rows"):
        validate_verse({"slide_type": "hebrew_rename"}, "v[0]")


def test_validate_verse_requires_ref_or_text():
    with pytest.raises(SchemaError, match="reference.*text"):
        validate_verse({"highlights": ["x"]}, "v[0]")


def test_custom_renderer_registration():
    class _QuoteRenderer:
        kind = "quote_test"

        def validate(self, verse, path):
            pass

        def render(self, prs, verse, style, *, source_file=None):
            pass

    register_renderer(_QuoteRenderer())
    assert get_renderer("quote_test") is not None
    assert resolve_renderer({"slide_type": "quote_test"}).kind == "quote_test"

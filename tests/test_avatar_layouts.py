"""Tests for avatar layout slide types."""

from pathlib import Path

import pytest
from pptx import Presentation

from praisonaippt import create_presentation, load_verses_from_dict, list_renderers
from praisonaippt.avatar_layouts import AVATAR_SLIDE_TYPES
from praisonaippt.exceptions import SchemaError
from praisonaippt.slide_renderers import resolve_renderer, validate_verse

PKG = Path(__file__).resolve().parent.parent
IMG = PKG / "assets" / "background_alt.jpg"


def test_list_renderers_includes_avatar_kinds():
    kinds = set(list_renderers())
    assert kinds >= set(AVATAR_SLIDE_TYPES)


@pytest.mark.parametrize("slide_type", AVATAR_SLIDE_TYPES)
def test_resolve_avatar_renderer(slide_type):
    verse = {"slide_type": slide_type}
    if slide_type in ("media_only", "media_border"):
        verse["media_path"] = "assets/x.jpg"
    elif slide_type in ("avatar_name_card", "avatar_headline"):
        verse["headline"] = "Title"
    elif slide_type == "avatar_quote":
        verse["text"] = "Quote"
    assert resolve_renderer(verse).kind == slide_type


def test_media_only_requires_media_path():
    with pytest.raises(SchemaError, match="media_path"):
        validate_verse({"slide_type": "media_only"}, "sections[0].verses[0]")


def test_avatar_name_card_requires_headline():
    with pytest.raises(SchemaError, match="headline"):
        validate_verse({"slide_type": "avatar_name_card"}, "sections[0].verses[0]")


def test_invalid_media_fit():
    with pytest.raises(SchemaError, match="media_fit"):
        validate_verse(
            {"slide_type": "avatar_media_1", "media_fit": "stretch"},
            "sections[0].verses[0]",
        )


def test_split_geometry_media_left():
    from pptx import Presentation
    from praisonaippt.avatar_layouts import _slide_regions

    prs = Presentation()
    m1, a1 = _slide_regions(prs, "avatar_media_1", {})["media"], _slide_regions(
        prs, "avatar_media_1", {}
    )["avatar"]
    m2, a2 = _slide_regions(prs, "avatar_media_2", {})["media"], _slide_regions(
        prs, "avatar_media_2", {}
    )["avatar"]
    assert m1.left_in < a1.left_in
    assert abs(m1.width_in / (m1.width_in + a1.width_in) - 0.5) < 0.02
    assert abs(m2.width_in / (m2.width_in + a2.width_in) - 0.4) < 0.02
    assert m1.width_in != m2.width_in


def test_border_split_ratios_differ():
    from pptx import Presentation
    from praisonaippt.avatar_layouts import _slide_regions

    prs = Presentation()
    m1 = _slide_regions(prs, "avatar_media_border_1", {})["media"]
    m2 = _slide_regions(prs, "avatar_media_border_2", {})["media"]
    assert m1.width_in > m2.width_in


def test_avatar_quote_has_no_media_region():
    from pptx import Presentation
    from praisonaippt.avatar_layouts import _slide_regions

    prs = Presentation()
    regions = _slide_regions(prs, "avatar_quote", {})
    assert regions["media"] is None
    assert regions["avatar"] is not None


@pytest.mark.skipif(not IMG.is_file(), reason="sample image missing")
def test_avatar_layouts_build(tmp_path):
    verses = [{"slide_type": "avatar_only"}]
    for kind in AVATAR_SLIDE_TYPES:
        if kind == "avatar_only":
            continue
        entry = {"slide_type": kind}
        if kind in ("media_only", "media_border") or kind.startswith("avatar_media"):
            entry["media_path"] = "assets/background_alt.jpg"
        if kind in ("avatar_name_card", "avatar_headline"):
            entry["headline"] = "Demo"
            entry["subheader"] = "Role"
        if kind == "avatar_quote":
            entry["text"] = "Sample quote."
            entry["reference"] = "Author"
        verses.append(entry)

    data = {
        "presentation_title": "Avatar layouts",
        "_source_file": str(PKG),
        "sections": [{"section": "", "verses": verses}],
    }
    out = tmp_path / "avatar.pptx"
    create_presentation(load_verses_from_dict(data), str(out))
    prs = Presentation(out)
    assert len(prs.slides) == len(AVATAR_SLIDE_TYPES) + 1  # title slide

"""Tests for praisonaippt.schema and the loader's typed-error behaviour."""

import logging

import pytest

from praisonaippt import load_verses_from_dict
from praisonaippt.exceptions import SchemaError
from praisonaippt.schema import validate_verses


VALID = {
    "presentation_title": "T",
    "sections": [
        {
            "section": "S1",
            "verses": [
                {"reference": "Gen 1:1", "text": "In the beginning..."},
            ],
        }
    ],
}


def test_validate_verses_passes_on_valid():
    out = validate_verses(dict(VALID))
    assert out["presentation_title"] == "T"


def test_validate_verses_adds_default_sections():
    out = validate_verses({"presentation_title": "T"})
    assert out["sections"] == []


def test_validate_verses_rejects_non_dict():
    with pytest.raises(SchemaError):
        validate_verses(["nope"])


def test_validate_verses_rejects_bad_sections_type():
    with pytest.raises(SchemaError):
        validate_verses({"sections": "oops"})


def test_validate_verses_rejects_verse_without_ref_or_text():
    with pytest.raises(SchemaError):
        validate_verses(
            {
                "sections": [
                    {"section": "S", "verses": [{"highlights": ["x"]}]}
                ]
            }
        )


def test_validate_verses_warns_on_unknown_top_level_key(caplog):
    with caplog.at_level(logging.WARNING, logger="praisonaippt.schema"):
        validate_verses({"presentation_titlee": "typo", "sections": []})
    assert any("presentation_titlee" in rec.message for rec in caplog.records)


def test_load_verses_from_dict_raises_on_invalid():
    with pytest.raises(SchemaError):
        load_verses_from_dict("not a dict")

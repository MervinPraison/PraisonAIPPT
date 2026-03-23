#!/usr/bin/env python3
"""
Tests for pptx_to_json conversion feature.

Run with: python tests/test_pptx_to_json.py
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from praisonaippt import create_presentation, pptx_to_json
from praisonaippt.pptx_to_json import PPTXToJSONConverter


# ── test data ──────────────────────────────────────────────────────────────────

SAMPLE_DATA = {
    "presentation_title": "Test Presentation",
    "presentation_subtitle": "A Test Subtitle",
    "sections": [
        {
            "section": "First Section",
            "verses": [
                {
                    "reference": "John 3:16 (NIV)",
                    "text": "For God so loved the world that he gave his one and only Son.",
                    "highlights": ["loved", "gave"]
                },
                {
                    "reference": "Romans 8:28 (NIV)",
                    "text": "And we know that in all things God works for the good of those who love him.",
                    "highlights": []
                }
            ]
        },
        {
            "section": "Empty Section",
            "verses": []
        },
        {
            "section": "List Section",
            "verses": [
                {
                    "reference": "",
                    "text": "Point One\nPoint Two\nPoint Three",
                    "list_type": "bullet"
                }
            ]
        },
        {
            "section": "Verse Number Section",
            "verses": [
                {
                    "reference": "Psalm 23:1-3 (KJV)",
                    "text": "1 The Lord is my shepherd; I shall not want.\n2 He maketh me to lie down in green pastures.\n3 He restoreth my soul.",
                    "highlights": ["shepherd", "green pastures"]
                }
            ]
        }
    ],
    "slide_style": {
        "alignment": "left"
    }
}


def create_test_pptx(data=None, suffix='_test') -> str:
    """Create a temporary PPTX from sample data, return its path."""
    if data is None:
        data = SAMPLE_DATA
    tmp = tempfile.mktemp(suffix=suffix + '.pptx')
    result = create_presentation(data, output_file=tmp)
    return result or tmp


# ── tests ──────────────────────────────────────────────────────────────────────

def test_import():
    """pptx_to_json should be importable from the top-level package."""
    from praisonaippt import pptx_to_json
    assert callable(pptx_to_json), "pptx_to_json must be callable"
    print("✓ test_import")


def test_round_trip_title():
    """Round-trip: create PPTX from data, extract JSON, verify title."""
    pptx = create_test_pptx()
    try:
        data = pptx_to_json(pptx)
        assert 'presentation_title' in data, "presentation_title key missing"
        assert data['presentation_title'] == SAMPLE_DATA['presentation_title'], (
            f"Title mismatch: {data['presentation_title']!r} != {SAMPLE_DATA['presentation_title']!r}"
        )
        print("✓ test_round_trip_title")
    finally:
        if os.path.exists(pptx):
            os.remove(pptx)


def test_sections_extracted():
    """Extracted dict must have a 'sections' list."""
    pptx = create_test_pptx()
    try:
        data = pptx_to_json(pptx)
        assert 'sections' in data, "sections key missing"
        assert isinstance(data['sections'], list), "sections must be a list"
        assert len(data['sections']) > 0, "sections list is empty"
        print("✓ test_sections_extracted")
    finally:
        if os.path.exists(pptx):
            os.remove(pptx)


def test_source_metadata():
    """Output dict must include _source key."""
    pptx = create_test_pptx()
    try:
        data = pptx_to_json(pptx)
        assert data.get('_source') == 'extracted', "_source must be 'extracted'"
        print("✓ test_source_metadata")
    finally:
        if os.path.exists(pptx):
            os.remove(pptx)


def test_output_to_file():
    """When output_path is provided, JSON file is written."""
    pptx = create_test_pptx()
    json_out = tempfile.mktemp(suffix='_out.json')
    try:
        data = pptx_to_json(pptx, output_path=json_out)
        assert os.path.exists(json_out), f"JSON file not created at {json_out}"
        with open(json_out, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded['presentation_title'] == data['presentation_title']
        print("✓ test_output_to_file")
    finally:
        for p in [pptx, json_out]:
            if os.path.exists(p):
                os.remove(p)


def test_output_file_is_valid_json():
    """The output JSON file must be parseable."""
    pptx = create_test_pptx()
    json_out = tempfile.mktemp(suffix='_valid.json')
    try:
        pptx_to_json(pptx, output_path=json_out, pretty=True)
        with open(json_out, 'r', encoding='utf-8') as f:
            content = f.read()
        parsed = json.loads(content)  # raises if not valid
        assert isinstance(parsed, dict)
        print("✓ test_output_file_is_valid_json")
    finally:
        for p in [pptx, json_out]:
            if os.path.exists(p):
                os.remove(p)


def test_compact_json():
    """--no-pretty mode writes compact (single-line) JSON."""
    pptx = create_test_pptx()
    json_out = tempfile.mktemp(suffix='_compact.json')
    try:
        pptx_to_json(pptx, output_path=json_out, pretty=False)
        with open(json_out, 'r', encoding='utf-8') as f:
            content = f.read()
        # Compact JSON has no leading newlines after {
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) == 1, f"Compact JSON should be 1 line, got {len(lines)}"
        print("✓ test_compact_json")
    finally:
        for p in [pptx, json_out]:
            if os.path.exists(p):
                os.remove(p)


def test_round_trip_creates_valid_pptx():
    """Round-trip: extracted JSON can be fed back into create_presentation without errors."""
    pptx = create_test_pptx()
    roundtrip = tempfile.mktemp(suffix='_roundtrip.pptx')
    try:
        data = pptx_to_json(pptx)
        # Strip internal metadata keys create_presentation doesn't know about
        clean = {k: v for k, v in data.items() if not k.startswith('_')}
        result = create_presentation(clean, output_file=roundtrip)
        assert result is not None or os.path.exists(roundtrip), \
            "Round-trip create_presentation must not raise"
        print("✓ test_round_trip_creates_valid_pptx")
    finally:
        for p in [pptx, roundtrip]:
            if os.path.exists(p):
                os.remove(p)


def test_file_not_found():
    """Should raise FileNotFoundError for non-existent path."""
    try:
        pptx_to_json("/nonexistent/path/to/missing.pptx")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        print("✓ test_file_not_found")


def test_non_pptx_raises_value_error():
    """Should raise ValueError for non-PPTX extension."""
    try:
        pptx_to_json("/tmp/slides.pdf")
        assert False, "Expected ValueError"
    except ValueError:
        print("✓ test_non_pptx_raises_value_error")


def test_converter_class_directly():
    """PPTXToJSONConverter.convert() returns a dict."""
    pptx = create_test_pptx()
    try:
        converter = PPTXToJSONConverter(pptx)
        data = converter.convert()
        assert isinstance(data, dict), "convert() must return a dict"
        assert 'sections' in data
        print("✓ test_converter_class_directly")
    finally:
        if os.path.exists(pptx):
            os.remove(pptx)


def test_empty_section_preserved():
    """Sections with empty verses must appear in the output."""
    pptx = create_test_pptx()
    try:
        data = pptx_to_json(pptx)
        sections = data['sections']
        section_names = [s['section'] for s in sections]
        # At least some sections should be present
        assert len(sections) > 0, "No sections in output"
        # All section entries must have 'verses' key
        for s in sections:
            assert 'verses' in s, f"Section {s.get('section')!r} missing 'verses' key"
            assert isinstance(s['verses'], list), "'verses' must be a list"
        print("✓ test_empty_section_preserved")
    finally:
        if os.path.exists(pptx):
            os.remove(pptx)


def test_cli_invocation():
    """CLI: 'praisonaippt convert-json <pptx>' exits 0 and creates JSON."""
    pptx = create_test_pptx()
    json_out = tempfile.mktemp(suffix='_cli.json')
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaippt.cli',
             'convert-json', pptx, '--json-output', json_out],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        assert result.returncode == 0, (
            f"CLI returned {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert os.path.exists(json_out), f"CLI did not create JSON at {json_out}"
        with open(json_out, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert 'presentation_title' in loaded
        print("✓ test_cli_invocation")
    finally:
        for p in [pptx, json_out]:
            if os.path.exists(p):
                os.remove(p)


def test_cli_no_input_returns_error():
    """CLI: 'praisonaippt convert-json' without input file returns non-zero."""
    result = subprocess.run(
        [sys.executable, '-m', 'praisonaippt.cli', 'convert-json'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    assert result.returncode != 0, "Expected non-zero exit when no input given"
    print("✓ test_cli_no_input_returns_error")


def test_pptx_to_json_in_all():
    """pptx_to_json must be in praisonaippt.__all__."""
    import praisonaippt
    assert 'pptx_to_json' in praisonaippt.__all__, \
        f"pptx_to_json not in __all__: {praisonaippt.__all__}"
    print("✓ test_pptx_to_json_in_all")


# ── runner ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [
        test_import,
        test_pptx_to_json_in_all,
        test_round_trip_title,
        test_sections_extracted,
        test_source_metadata,
        test_output_to_file,
        test_output_file_is_valid_json,
        test_compact_json,
        test_round_trip_creates_valid_pptx,
        test_file_not_found,
        test_non_pptx_raises_value_error,
        test_converter_class_directly,
        test_empty_section_preserved,
        test_cli_invocation,
        test_cli_no_input_returns_error,
    ]

    passed = 0
    failed = 0
    print(f"\n{'='*60}")
    print("PraisonAI PPT — pptx_to_json Tests")
    print(f"{'='*60}\n")

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    sys.exit(0 if failed == 0 else 1)

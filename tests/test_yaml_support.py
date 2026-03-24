#!/usr/bin/env python3
"""
Tests for YAML-as-Default feature.

Run with: python tests/test_yaml_support.py
"""

import os
import sys
import json
import yaml
import tempfile
import subprocess
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from praisonaippt import create_presentation, pptx_to_json, load_verses_from_file
from praisonaippt.loader import list_examples, get_example_path


# ── test data ──────────────────────────────────────────────────────────────────

SAMPLE_YAML_DATA = """
presentation_title: YAML Test Presentation
presentation_subtitle: Testing YAML Support

sections:
  - section: "First Section"
    verses:
      - reference: "John 3:16 (NIV)"
        text: For God so loved the world.
        highlights:
          - loved
          - world

  - section: "Empty Section"
    verses: []

  - section: "List Section"
    verses:
      - reference: ""
        text: |
          Point One
          Point Two
          Point Three
        list_type: bullet
"""


def create_temp_yaml(content=None) -> str:
    """Create a temporary YAML file, return its path."""
    if content is None:
        content = SAMPLE_YAML_DATA
    tmp = tempfile.mktemp(suffix='.yaml')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    return tmp


# ── tests ──────────────────────────────────────────────────────────────────────

def test_load_verses_from_yaml():
    """load_verses_from_file should parse YAML files correctly."""
    yaml_file = create_temp_yaml()
    try:
        data = load_verses_from_file(yaml_file)
        assert data is not None, "load_verses_from_file returned None"
        assert data['presentation_title'] == 'YAML Test Presentation'
        assert len(data['sections']) == 3
        print("✓ test_load_verses_from_yaml")
    finally:
        if os.path.exists(yaml_file):
            os.remove(yaml_file)


def test_yaml_json_equivalence():
    """YAML and JSON should produce identical dicts."""
    yaml_content = SAMPLE_YAML_DATA
    json_content = json.dumps(yaml.safe_load(yaml_content))
    
    yaml_file = create_temp_yaml(yaml_content)
    json_file = tempfile.mktemp(suffix='.json')
    with open(json_file, 'w') as f:
        f.write(json_content)
    
    try:
        yaml_data = load_verses_from_file(yaml_file)
        json_data = load_verses_from_file(json_file)
        assert yaml_data == json_data, "YAML and JSON data should be identical"
        print("✓ test_yaml_json_equivalence")
    finally:
        for p in [yaml_file, json_file]:
            if os.path.exists(p):
                os.remove(p)


def test_list_examples_includes_yaml():
    """list_examples() should include YAML files."""
    examples = list_examples()
    assert len(examples) > 0, "No examples found"
    # Check that why_listen_word_of_god appears (it has both .yaml and .json)
    stems = [Path(e).stem for e in examples]
    assert 'why_listen_word_of_god' in stems, "why_listen_word_of_god not in examples"
    # Should not have duplicates
    assert len(stems) == len(set(stems)), "Duplicate stems found in list_examples"
    print("✓ test_list_examples_includes_yaml")


def test_list_examples_prefers_yaml():
    """list_examples() should prefer YAML extension when both exist."""
    examples = list_examples()
    # why_listen_word_of_god has both .yaml and .json - should show .yaml
    yaml_examples = [e for e in examples if e.endswith('.yaml')]
    assert any('why_listen_word_of_god' in e for e in yaml_examples), \
        "why_listen_word_of_god should be listed as .yaml"
    print("✓ test_list_examples_prefers_yaml")


def test_get_example_path_yaml_priority():
    """get_example_path should try YAML before JSON."""
    # why_listen_word_of_god has both formats
    path = get_example_path('why_listen_word_of_god')
    assert path is not None, "Example not found"
    assert path.endswith('.yaml'), f"Expected .yaml, got {path}"
    print("✓ test_get_example_path_yaml_priority")


def test_pptx_to_json_yaml_output():
    """pptx_to_json should support output_format='yaml'."""
    # Create a test PPTX first
    yaml_file = create_temp_yaml()
    pptx_file = tempfile.mktemp(suffix='.pptx')
    yaml_out = tempfile.mktemp(suffix='.yaml')
    
    try:
        data = load_verses_from_file(yaml_file)
        create_presentation(data, output_file=pptx_file)
        
        # Extract to YAML
        result = pptx_to_json(pptx_file, output_path=yaml_out, output_format='yaml')
        
        assert os.path.exists(yaml_out), f"YAML output not created at {yaml_out}"
        
        # Verify it's valid YAML
        with open(yaml_out, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert isinstance(loaded, dict), "YAML output is not a dict"
        assert 'presentation_title' in loaded, "Missing presentation_title in YAML output"
        print("✓ test_pptx_to_json_yaml_output")
    finally:
        for p in [yaml_file, pptx_file, yaml_out]:
            if os.path.exists(p):
                os.remove(p)


def test_pptx_to_json_default_json():
    """pptx_to_json should default to JSON output."""
    yaml_file = create_temp_yaml()
    pptx_file = tempfile.mktemp(suffix='.pptx')
    json_out = tempfile.mktemp(suffix='.json')
    
    try:
        data = load_verses_from_file(yaml_file)
        create_presentation(data, output_file=pptx_file)
        
        # Extract without specifying format (should default to JSON)
        pptx_to_json(pptx_file, output_path=json_out)
        
        with open(json_out, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert isinstance(loaded, dict)
        print("✓ test_pptx_to_json_default_json")
    finally:
        for p in [yaml_file, pptx_file, json_out]:
            if os.path.exists(p):
                os.remove(p)


def test_yaml_round_trip():
    """YAML → PPTX → YAML should preserve data."""
    yaml_file = create_temp_yaml()
    pptx_file = tempfile.mktemp(suffix='.pptx')
    yaml_out = tempfile.mktemp(suffix='_out.yaml')
    
    try:
        # Load original
        original = load_verses_from_file(yaml_file)
        
        # Create PPTX
        create_presentation(original, output_file=pptx_file)
        
        # Extract back to YAML
        extracted = pptx_to_json(pptx_file, output_path=yaml_out, output_format='yaml')
        
        # Key fields should match
        assert extracted['presentation_title'] == original['presentation_title'], \
            "Title mismatch in round-trip"
        print("✓ test_yaml_round_trip")
    finally:
        for p in [yaml_file, pptx_file, yaml_out]:
            if os.path.exists(p):
                os.remove(p)


def test_cli_convert_json_yaml_format():
    """CLI convert-json should support --output-format yaml."""
    yaml_file = create_temp_yaml()
    pptx_file = tempfile.mktemp(suffix='.pptx')
    yaml_out = tempfile.mktemp(suffix='.yaml')
    
    try:
        data = load_verses_from_file(yaml_file)
        create_presentation(data, output_file=pptx_file)
        
        result = subprocess.run(
            [sys.executable, '-m', 'praisonaippt.cli',
             'convert-json', pptx_file,
             '--output-format', 'yaml',
             '--json-output', yaml_out],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0, \
            f"CLI failed: {result.returncode}\nstderr: {result.stderr}"
        assert os.path.exists(yaml_out), "YAML output not created"
        
        with open(yaml_out, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert 'presentation_title' in loaded
        print("✓ test_cli_convert_json_yaml_format")
    finally:
        for p in [yaml_file, pptx_file, yaml_out]:
            if os.path.exists(p):
                os.remove(p)


def test_cli_help_mentions_yaml():
    """CLI help should mention YAML support."""
    result = subprocess.run(
        [sys.executable, '-m', 'praisonaippt.cli', '--help'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    assert result.returncode == 0
    help_text = result.stdout.lower()
    assert 'yaml' in help_text, "CLI help should mention YAML"
    print("✓ test_cli_help_mentions_yaml")


def test_yaml_examples_exist():
    """YAML example files should exist for all JSON examples."""
    examples_dir = Path(__file__).parent.parent / 'examples'
    json_files = list(examples_dir.glob('*.json'))
    yaml_files = list(examples_dir.glob('*.yaml'))
    
    json_stems = {f.stem for f in json_files}
    yaml_stems = {f.stem for f in yaml_files}
    
    # All JSON examples should have YAML equivalents
    missing = json_stems - yaml_stems
    assert len(missing) == 0, f"Missing YAML examples: {missing}"
    print("✓ test_yaml_examples_exist")


# ── runner ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [
        test_load_verses_from_yaml,
        test_yaml_json_equivalence,
        test_list_examples_includes_yaml,
        test_list_examples_prefers_yaml,
        test_get_example_path_yaml_priority,
        test_pptx_to_json_yaml_output,
        test_pptx_to_json_default_json,
        test_yaml_round_trip,
        test_cli_convert_json_yaml_format,
        test_cli_help_mentions_yaml,
        test_yaml_examples_exist,
    ]

    passed = 0
    failed = 0
    print(f"\n{'='*60}")
    print("PraisonAI PPT — YAML Support Tests")
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

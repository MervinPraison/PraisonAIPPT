"""Tests for segment video SDK — deps, regenerate chains, merge SRT offsets."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.segment_video.protocol import (
    REGENERATE_CHAINS,
    merge_transition_config,
    resolve_stage_id,
    validate_deps,
)
from praisonaippt.segment_video.stages.merge import _build_edges, parse_srt, _fmt_ts
from praisonaippt.video_protocol import effective_timeline_sec


def test_stage_alias_script():
    assert resolve_stage_id("script") == "scripts"


def test_regenerate_chains_defined():
    assert "script" in REGENERATE_CHAINS
    assert "align-cues" in REGENERATE_CHAINS["script"]
    assert "validate-media" in REGENERATE_CHAINS["hero"]
    assert "validate-visual" in REGENERATE_CHAINS["timing"]
    assert REGENERATE_CHAINS["script"][0] == "media"
    assert REGENERATE_CHAINS["deck"][0] == "build"
    assert "merge" in REGENERATE_CHAINS["deck"]
    assert REGENERATE_CHAINS["transitions"][0] == "merge"


def test_protocol_v2_deps():
    protocol_path = Path("tests/fixtures/segment_video_protocol_v3.json")
    if not protocol_path.is_file():
        protocol_path = Path("examples/videos/june-2026-ai-roundup/scripts/config/protocol.json")
    protocol = json.loads(protocol_path.read_text())
    assert protocol["schema_version"] >= 2
    assert not validate_deps(protocol, "merge")
    assert not validate_deps(protocol, "fix-jpegs")
    assert not validate_deps(protocol, "script")  # alias → scripts
    assert validate_deps(protocol, "unknown-stage") == ["unknown stage: unknown-stage"]


def test_merge_transition_config():
    protocol = {"merge_transitions": {"default": "crossfade", "duration_sec": 0.3}}
    cfg = merge_transition_config(protocol)
    assert cfg["default"] == "crossfade"
    assert cfg["duration_sec"] == 0.3
    off = merge_transition_config(protocol, no_transitions=True)
    assert off["default"] == "none"


def test_build_edges_crossfade():
    edges = _build_edges(3, {"default": "crossfade", "duration_sec": 0.3})
    assert len(edges) == 2
    assert all(e.is_blend() for e in edges)


def test_srt_parse_and_timeline_offset():
    text = "1\n00:00:01,000 --> 00:00:03,000\nHello\n\n2\n00:00:04,000 --> 00:00:06,000\nWorld\n"
    cues = parse_srt(text)
    assert len(cues) == 2
    assert cues[0][2] == "Hello"
    durations = [10.0, 10.0, 10.0]
    edges = _build_edges(3, {"default": "crossfade", "duration_sec": 0.3})
    entries = [{"duration_sec": d} for d in durations]
    starts = effective_timeline_sec(entries, edges)
    assert starts[1] == pytest.approx(9.7, abs=0.01)
    merged_start = starts[1] + cues[0][0]
    assert merged_start == pytest.approx(10.7, abs=0.01)
    assert _fmt_ts(65.5).startswith("00:01:05,")

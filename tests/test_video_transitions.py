"""Unit tests for slide transition protocol (resolve, clamp, timeline)."""

import warnings

import pytest

from praisonaippt.video_protocol import (
    TransitionDefaults,
    clamp_transition_duration,
    effective_timeline_sec,
    normalise_transition_type,
    parse_transition_defaults,
    resolve_edge_transitions,
    segment_fade_sec_for_slide,
    total_output_duration_sec,
)


def _entries(n: int, dur: float = 5.0):
    return [{"duration_sec": dur, "verse": {}} for _ in range(n)]


def test_default_none_without_yaml():
    defs = parse_transition_defaults({})
    assert defs.default == "none"
    assert defs.legacy_fade_sec == 0.0
    edges = resolve_edge_transitions(_entries(3), {}, None, defaults=defs)
    assert all(e.type == "none" for e in edges)


def test_legacy_transition_fade_sec():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        defs = parse_transition_defaults({}, {"transition_fade_sec": 0.28})
    assert defs.default == "segment_fade"
    assert defs.legacy_fade_sec == 0.28
    assert any("deprecated" in str(x.message).lower() for x in w)


def test_precedence_edge_over_verse_over_global():
    entries = [
        {"duration_sec": 5.0, "verse": {"transition_out": "crossfade"}},
        {"duration_sec": 5.0, "verse": {}},
        {"duration_sec": 5.0, "verse": {}},
    ]
    data = {
        "slide_transitions": {
            "default": "segment_fade",
            "duration_sec": 0.2,
            "edges": [{"after_slide": 1, "type": "wipeleft", "duration_sec": 0.35}],
        }
    }
    edges = resolve_edge_transitions(entries, {}, data["slide_transitions"])
    assert edges[0].type == "wipeleft"
    assert edges[0].source == "edge"
    assert edges[1].type == "segment_fade"


def test_fade_alias_deprecation():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        assert normalise_transition_type("fade") == "segment_fade"


def test_clamp_short_slide_downgrades():
    defs = TransitionDefaults(min_slide_sec=1.0, max_fade_ratio=0.25)
    assert clamp_transition_duration(0.5, 0.4, defs) == 0.0


def test_effective_timeline_xfade_overlap():
    entries = _entries(3, dur=10.0)
    edges = resolve_edge_transitions(
        entries,
        {},
        {"default": "crossfade", "duration_sec": 2.0},
    )
    starts = effective_timeline_sec(entries, edges)
    assert starts == [0.0, 8.0, 16.0]
    assert total_output_duration_sec(entries, edges) == pytest.approx(26.0)


def test_segment_fade_sec_skips_when_next_is_blend():
    from praisonaippt.video_protocol import ResolvedEdgeTransition

    edges = [
        ResolvedEdgeTransition(1, "segment_fade", 0.3, "test"),
        ResolvedEdgeTransition(2, "crossfade", 0.4, "test"),
    ]
    assert segment_fade_sec_for_slide(0, edges) == 0.3
    assert segment_fade_sec_for_slide(1, edges) == 0.0

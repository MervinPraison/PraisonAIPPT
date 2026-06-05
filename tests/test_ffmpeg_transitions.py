"""Tests for FFmpeg xfade filter chain builder."""

from praisonaippt.ffmpeg_composer import build_xfade_filter_chain
from praisonaippt.video_protocol import ResolvedEdgeTransition


def test_xfade_chain_three_segments():
    durations = [5.0, 5.0, 5.0]
    edges = [
        ResolvedEdgeTransition(1, "crossfade", 1.0, "test"),
        ResolvedEdgeTransition(2, "none", 0.0, "test"),
    ]
    filt, label = build_xfade_filter_chain(durations, edges)
    assert "xfade=transition=fade:duration=1.000:offset=4.000" in filt
    assert "concat=n=2" in filt
    assert label == "vx1"

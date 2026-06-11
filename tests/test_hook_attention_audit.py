"""Tests for hook frame cadence and spoken↔visual inline at sample times."""
from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.hook_attention_audit import hook_audit_sample_times
from praisonaippt.daily_single.spoken_visual_sync import validate_hook_sample_inline


def test_hook_audit_sample_times_cadence():
    times = hook_audit_sample_times(20.7, attention_sec=5.0)
    assert times[:5] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert times[5:] == [6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]


def test_hook_sample_inline_attention_scroll():
    window = VisualWindow(
        0.0, 5.0, "00-hook", "canonical blog scroll", "canonical-scroll.mp4",
        "attention", "Anthropic just released Claude Fable five",
    )
    spoken = "Anthropic just released Claude Fable five — if AI is part of your work, this launch matters."
    ok, score, issues = validate_hook_sample_inline(spoken, window)
    assert ok, issues
    assert score >= 0.35


def test_hook_sample_inline_overview_montage():
    window = VisualWindow(
        7.0, 9.0, "00-hook", "Stripe card", "beat3-stripe-card.png",
        "overview", "Stripe's fifty-million-line proof",
    )
    spoken = (
        "In the next five minutes: what most teams actually get, "
        "Stripe's fifty-million-line proof, benchmark scores that matter."
    )
    ok, _, issues = validate_hook_sample_inline(spoken, window)
    assert ok, issues


def test_hook_sample_inline_fails_on_mismatch():
    window = VisualWindow(
        10.0, 12.0, "00-hook", "tier diagram", "beat2-tier-diagram.png",
        "overview", "what most teams actually get",
    )
    ok, _, issues = validate_hook_sample_inline("The weather is sunny today.", window)
    assert not ok
    assert issues


def test_hook_sample_chart_inline_on_benchmark():
    window = VisualWindow(
        14.0, 16.0, "00-hook", "benchmark slide", "benchmark-table.png",
        "overview", "benchmark scores that matter",
    )
    spoken = (
        "In the next five minutes: benchmark scores that matter, "
        "Stripe's fifty-million-line proof, and safety without dead ends."
    )
    ok, score, issues = validate_hook_sample_inline(spoken, window)
    assert ok, issues
    assert score >= 0.35

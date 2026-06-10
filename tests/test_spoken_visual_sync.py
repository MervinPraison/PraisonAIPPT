"""Tests for spoken↔slide inline validation."""
from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.spoken_visual_sync import (
    fragment_token_hit,
    validate_montage_fragments,
    validate_visual_windows,
)


def test_fragment_token_hit_overview_sentence():
    overview = (
        "In the next five minutes: what most teams actually get, Stripe's fifty-million-line proof, "
        "benchmark scores that matter."
    )
    assert fragment_token_hit("Stripe's fifty-million-line proof", overview) >= 0.5


def test_montage_fragments_pass_when_inline():
    windows = [
        VisualWindow(
            7.0, 9.0, "00-hook", "tier", "beat2-tier-diagram.png",
            "overview", "what most teams actually get",
        ),
        VisualWindow(
            9.0, 11.0, "00-hook", "stripe", "beat3-stripe-card.png",
            "overview", "Stripe's fifty-million-line proof",
        ),
    ]
    cues = [
        {"start_sec": 0.0, "end_sec": 7.0, "text": "Hook line."},
        {
            "start_sec": 7.0,
            "end_sec": 12.0,
            "text": (
                "In the next five minutes: what most teams actually get, "
                "Stripe's fifty-million-line proof, benchmark scores that matter."
            ),
        },
    ]
    ok, rows = validate_montage_fragments(windows, cues)
    assert ok
    assert len(rows) == 2
    assert all(r["ok"] for r in rows)


def test_visual_window_fails_when_speech_mismatches_slide():
    windows = [
        VisualWindow(10.0, 20.0, "beat-03", "stripe card", "beat3-stripe-card.png"),
    ]
    cues = [
        {"start_sec": 10.0, "end_sec": 20.0, "text": "The weather forecast shows sunny skies all week."},
    ]
    ok, rows = validate_visual_windows(windows, cues)
    assert not ok
    assert rows[0]["ok"] is False


def test_visual_window_passes_stripe_on_stripe_card():
    windows = [
        VisualWindow(10.0, 20.0, "beat-03", "stripe card", "beat3-stripe-card.png"),
    ]
    cues = [
        {"start_sec": 10.0, "end_sec": 20.0, "text": "Stripe moved fifty million lines of code in one day."},
    ]
    ok, rows = validate_visual_windows(windows, cues)
    assert ok
    assert rows[0]["alignment"] >= 0.35

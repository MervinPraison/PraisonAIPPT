"""Unit tests for daily_single spoken↔visual mapping."""
from praisonaippt.daily_single.display_sync import (
    MIN_ALIGNMENT,
    VisualWindow,
    score_cue_visual,
    visual_at,
    _windows_for_beat,
)


def test_visual_at_midpoint():
    wins = [
        VisualWindow(0.0, 10.0, "beat-01", "clip", "a.mp4"),
        VisualWindow(10.0, 20.0, "beat-02", "card", "b.png"),
    ]
    assert visual_at(wins, 5.0).file == "a.mp4"
    assert visual_at(wins, 15.0).file == "b.png"


def test_visual_at_boundary_uses_first_window():
    wins = [VisualWindow(10.0, 20.0, "beat-01", "clip", "a.mp4")]
    assert visual_at(wins, 10.0).file == "a.mp4"


def test_score_cue_visual_stripe_on_stripe_card():
    score = score_cue_visual(
        "Stripe moved fifty million lines of code in one day",
        "beat3-stripe-card.png",
    )
    assert score >= MIN_ALIGNMENT


def test_score_cue_visual_penalty_alignment_chart_retention():
    score = score_cue_visual(
        "Thirty-day retention applies to business traffic",
        "alignment-chart.png",
    )
    assert score <= 0.2


def test_windows_beat3_stripe_before_clips():
    spec = {
        "generated": [{"path": "/tmp/beat3-stripe-card.png", "filename": "beat3-stripe-card.png"}],
        "clips": [
            {"path": "/tmp/carousel-factorio.mp4", "filename": "carousel-factorio.mp4"},
            {"path": "/tmp/carousel-vibecad.mp4", "filename": "carousel-vibecad.mp4"},
        ],
    }
    wins = _windows_for_beat("beat-03", 3, 0.0, 30.0, spec, None)  # type: ignore[arg-type]
    assert wins[0].file == "beat3-stripe-card.png"
    assert "carousel" in wins[1].file


def test_windows_beat7_table_first(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    spec = {
        "generated": [{"path": str(tmp_path / "beat7-api-table.png"), "filename": "beat7-api-table.png"}],
    }
    wins = _windows_for_beat("beat-07", 7, 100.0, 50.0, spec, assets)
    assert wins[0].file == "beat7-api-table.png"
    assert wins[0].start_sec == 100.0

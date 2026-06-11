"""Tests for spoken↔slide inline validation."""
from praisonaippt.daily_single.display_sync import VisualWindow
from praisonaippt.daily_single.spoken_visual_sync import (
    fragment_token_hit,
    is_chart_or_table_file,
    spoken_hits_visual_focus,
    validate_chart_inline,
    validate_chart_windows,
    validate_hook_sample_inline,
    validate_montage_fragments,
    validate_speech_needs_visual,
    validate_srt_plain_language,
    validate_transition_points,
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


def test_is_chart_or_table_file():
    assert is_chart_or_table_file("benchmark-table.png")
    assert is_chart_or_table_file("beat4-stat-overlay.png")
    assert not is_chart_or_table_file("heygen.mp4")


def test_chart_inline_passes_when_spoken_matches():
    ok, score, issues = validate_chart_inline(
        "Stripe moved fifty million lines — benchmark scores on the leaderboard.",
        "benchmark-table.png",
    )
    assert ok, issues
    assert score >= 0.38


def test_chart_inline_fails_views_overlay_with_brand_name_only():
    """Exact beat-01 bug: Fable talk while 26.5M views graphic is on screen."""
    ok, score, issues = validate_chart_inline(
        "Claude Fable five is what most teams will pick — strong enough for daily work, "
        "with safety that answers your question or blocks it.",
        "beat1-views-overlay.png",
    )
    assert not ok, f"should fail: score={score}, issues={issues}"
    assert issues


def test_chart_inline_passes_views_overlay_with_view_count_language():
    ok, score, issues = validate_chart_inline(
        "The official launch clip passed twenty-six million views on X in the first week.",
        "beat1-views-overlay.png",
    )
    assert ok, issues
    assert score >= 0.38


def test_spoken_hits_visual_focus_views_overlay():
    assert spoken_hits_visual_focus(
        "Twenty-six million views on X in launch week.",
        "beat1-views-overlay.png",
    )
    assert not spoken_hits_visual_focus(
        "Claude Fable five is what most teams will pick.",
        "beat1-views-overlay.png",
    )


def test_chart_windows_fails_views_overlay_with_brand_name_speech():
    windows = [
        VisualWindow(20.7, 38.3, "beat-01", "views overlay", "beat1-views-overlay.png"),
    ]
    cues = [
        {
            "start_sec": 20.7,
            "end_sec": 38.3,
            "text": (
                "Claude Fable five is what most teams will pick — strong enough for daily work, "
                "with safety that answers your question or blocks it."
            ),
        }
    ]
    ok, rows = validate_chart_windows(windows, cues)
    assert not ok
    assert not rows[0]["ok"]


def test_visual_window_fails_beat1_views_overlay_brand_name_speech():
    windows = [
        VisualWindow(20.7, 38.3, "beat-01", "views overlay", "beat1-views-overlay.png"),
    ]
    cues = [
        {
            "start_sec": 20.7,
            "end_sec": 38.3,
            "text": (
                "Claude Fable five is what most teams will pick — strong enough for daily work, "
                "with safety that answers your question."
            ),
        }
    ]
    ok, rows = validate_visual_windows(windows, cues)
    assert not ok
    assert not rows[0]["ok"]


def test_chart_inline_fails_distillation_when_cyber_only():
    ok, _, issues = validate_chart_inline(
        "Partner testing found zero harmful cyber outputs across thirty public tricks to bypass safety rules.",
        "distillation-safeguard.png",
    )
    assert not ok
    assert issues


def test_chart_inline_passes_short_stat_line():
    ok, score, issues = validate_chart_inline(
        "Longer jobs, bigger advantage.",
        "beat4-stat-overlay.png",
    )
    assert ok, issues
    assert score >= 0.38


def test_chart_inline_fails_when_spoken_unrelated():
    ok, _, issues = validate_chart_inline(
        "The weather forecast shows sunny skies.",
        "benchmark-table.png",
    )
    assert not ok
    assert issues


def test_chart_windows_validates_visible_chart():
    windows = [
        VisualWindow(10.0, 18.0, "beat-04", "benchmark", "benchmark-table.png"),
    ]
    cues = [
        {"start_sec": 10.0, "end_sec": 18.0, "text": "Benchmark scores show Fable ahead on engineering tests."},
    ]
    ok, rows = validate_chart_windows(windows, cues)
    assert ok
    assert rows[0]["ok"]


def test_speech_needs_visual_flags_missing_slide():
    windows = [
        VisualWindow(10.0, 20.0, "beat-03", "avatar", "heygen.mp4", "bridge"),
    ]
    cues = [
        {"start_sec": 10.0, "end_sec": 20.0, "text": "Benchmark scores and Stripe proof matter here."},
    ]
    ok, rows = validate_speech_needs_visual(windows, cues)
    assert not ok
    assert not rows[0]["ok"]


def test_srt_plain_language_blocks_jargon():
    ok, issues = validate_srt_plain_language([
        {"start_sec": 0.0, "end_sec": 5.0, "text": "Use the Messages API for billing."},
    ])
    assert not ok
    assert issues


def test_chart_inline_fails_copy_protection_on_biology_chart():
    ok, _, issues = validate_chart_inline(
        "Copy-protection checks catch attempts to steal the model's abilities.",
        "bio-aav-chart.png",
    )
    assert not ok
    assert issues


def test_chart_inline_passes_biology_on_bio_aav_chart():
    ok, score, issues = validate_chart_inline(
        "Biology and chemistry checks stay broad at launch — the chart shows how those safeguards work.",
        "bio-aav-chart.png",
    )
    assert ok, issues
    assert score >= 0.38


def test_transition_fails_when_cue_changes_but_slide_stays():
    """Regression: copy-protection speech while biology AAV chart still on screen (~178s bug)."""
    windows = [
        VisualWindow(171.7, 188.9, "beat-06", "AAV chart", "bio-aav-chart.png"),
    ]
    cues = [
        {
            "start_sec": 172.87,
            "end_sec": 178.47,
            "text": "Biology and chemistry checks stay broad at launch — the chart shows how those safeguards work.",
        },
        {
            "start_sec": 178.47,
            "end_sec": 182.7,
            "text": "Copy-protection checks catch attempts to steal the model's abilities.",
        },
    ]
    ok, rows = validate_transition_points(windows, cues)
    assert not ok
    assert any(not r["ok"] for r in rows if "Copy-protection" in r.get("spoken", ""))


def test_equal_thirds_beat6_caught_by_transitions_not_windows():
    """Old equal-thirds bug: windows cherry-pick best cue; transitions catch mismatch."""
    windows = [
        VisualWindow(175.3, 188.9, "beat-06", "distillation", "distillation-safeguard.png"),
    ]
    cues_bio = [
        {
            "start_sec": 172.87,
            "end_sec": 178.47,
            "text": "Biology and chemistry checks stay broad at launch — the chart shows how those safeguards work.",
        },
        {
            "start_sec": 178.47,
            "end_sec": 182.7,
            "text": "Copy-protection checks catch attempts to steal the model's abilities.",
        },
    ]
    ok_win, _ = validate_visual_windows(windows, cues_bio)
    assert ok_win  # best_spoken picks copy-protection — why transitions exist
    ok_tr, rows = validate_transition_points(windows, cues_bio)
    assert not ok_tr


def test_hook_sample_chart_at_benchmark_slide():
    window = VisualWindow(
        12.0, 14.0, "00-hook", "benchmark", "benchmark-table.png",
        "overview", "benchmark scores that matter",
    )
    spoken = (
        "In the next five minutes: what most teams actually get, "
        "Stripe's fifty-million-line proof, benchmark scores that matter."
    )
    ok, _, issues = validate_hook_sample_inline(spoken, window)
    assert ok, issues

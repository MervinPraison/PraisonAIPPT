"""Tests for YouTube quality gates."""
from praisonaippt.daily_single.youtube_quality import (
    validate_compelling_hook,
    validate_outro_cta,
    validate_plain_language,
)


def test_compelling_hook_passes():
    cue_map = [
        {"spoken": "Anthropic just dropped Claude Fable five — you cannot afford to miss this launch."},
        {"spoken": "In the next five minutes we cover Fable, Mythos, Stripe, benchmarks, safety, and pricing."},
        {"spoken": "Let's get started."},
    ]
    ok, issues = validate_compelling_hook(cue_map)
    assert ok, issues


def test_compelling_hook_fails_without_stakes():
    cue_map = [
        {"spoken": "Claude Fable five exists."},
        {"spoken": "We cover Fable, Mythos, Stripe, benchmarks, and safety today."},
    ]
    ok, issues = validate_compelling_hook(cue_map)
    assert not ok
    assert any("stakes" in i for i in issues)


def test_plain_language_blocks_jargon(tmp_path):
    from praisonaippt.daily_single.project import DailySingleProject
    import json

    root = tmp_path / "p"
    (root / "segments/07-api-integration").mkdir(parents=True)
    research = tmp_path / "r"
    research.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"slug": "t", "create_news_research": str(research)}),
        encoding="utf-8",
    )
    (root / "segments/07-api-integration/script.md").write_text(
        "Use the Messages API for blocking.",
        encoding="utf-8",
    )
    project = DailySingleProject.from_root(root)
    ok, issues = validate_plain_language(project)
    assert not ok
    assert issues

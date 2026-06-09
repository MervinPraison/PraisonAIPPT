"""Post-sync required_assets audit — synced cue counts from media_assets.json."""
from __future__ import annotations

from praisonaippt.segment_video.validation.required_assets import audit_topic_gaps

RULES = {
    "min_topic_relevance": 0.7,
    "require_topic_relevance_label": "relevant",
    "min_script_alignment": 0.35,
    "max_cues_per_segment": 4,
    "multi_cue_requires_sentences": 1,
    "no_fallback_to_marginal": True,
}


def test_synced_cues_clears_cue_shortfall():
    seg = {"dir": "09-jetbrains-mellum2-12b-moe", "slug": "jetbrains-mellum2-12b-moe", "slide_type": "avatar_media_3"}
    script = "Mellum2 MoE. Faster inference. Pairs with orchestrators."
    topic = {
        "topic_slug": "jetbrains-mellum2-12b-moe",
        "canonical_url": "",
        "images": [
            {
                "filename": "hero.jpg",
                "topic_relevance_label": "relevant",
                "topic_relevance_score": 0.8,
                "vision_description": "Mellum2 eval grid benchmark chart",
                "editorial_rank": 1,
            },
        ],
    }
    row = audit_topic_gaps(
        seg, topic, script, RULES, manual_slugs=set(), fetch_canonical=False, synced_cues=3,
    )
    assert not any(g["type"] == "cue_shortfall" for g in row["gaps"])
    assert row["synced_cues"] == 3


def test_synced_cues_clears_insufficient_pool():
    seg = {"dir": "15-meta", "slug": "meta-muse-spark-api-june", "slide_type": "avatar_media_3"}
    script = "Watch tier. No GA. Do not depend."
    topic = {
        "topic_slug": "meta-muse-spark-api-june",
        "canonical_url": "",
        "images": [
            {"filename": "card.png", "topic_relevance_label": "relevant", "topic_relevance_score": 0.8,
             "vision_description": "Meta Muse Spark watch card placeholder", "editorial_rank": 1},
        ],
    }
    row = audit_topic_gaps(
        seg, topic, script, RULES, manual_slugs=set(), fetch_canonical=False, synced_cues=3,
    )
    assert not any(g["type"] == "insufficient_pool" for g in row["gaps"])


def test_planned_shortfall_without_synced_cues():
    seg = {"dir": "09-test", "slug": "jetbrains-mellum2-12b-moe", "slide_type": "avatar_media_3"}
    script = "One. Two. Three."
    topic = {
        "topic_slug": "jetbrains-mellum2-12b-moe",
        "canonical_url": "",
        "images": [
            {"filename": "a.png", "topic_relevance_label": "relevant", "topic_relevance_score": 0.8,
             "vision_description": "chart A", "editorial_rank": 1},
            {"filename": "b.png", "topic_relevance_label": "relevant", "topic_relevance_score": 0.8,
             "vision_description": "chart B", "editorial_rank": 2},
        ],
    }
    row = audit_topic_gaps(seg, topic, script, RULES, manual_slugs=set(), fetch_canonical=False)
    assert any(g["type"] == "cue_shortfall" for g in row["gaps"]) or row["planned_cues"] >= 3

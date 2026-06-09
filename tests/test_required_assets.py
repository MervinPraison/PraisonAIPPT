"""Tests for required asset validation and canonical crawl."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from praisonaippt.segment_video.assets.canonical_crawl import (
    extract_image_urls,
    handoff_image_keys,
    is_content_image,
    missing_page_keys,
)
from praisonaippt.segment_video.image_selection import asset_type_boost, build_cue_plan, rank_images
from praisonaippt.segment_video.validation.required_assets import audit_topic_gaps
from praisonaippt.segment_video.validation.validators import REGISTRY


RULES = {
    "min_topic_relevance": 0.7,
    "require_topic_relevance_label": "relevant",
    "min_script_alignment": 0.35,
    "max_cues_per_segment": 4,
    "multi_cue_requires_sentences": 1,
    "no_fallback_to_marginal": True,
}


def test_required_assets_validator_registered():
    assert "required_assets" in REGISTRY


def test_benchmark_chart_preferred_for_throughput_sentence():
    sentence = "up to five times throughput on Blackwell."
    arch = {
        "filename": "arch.png",
        "asset_type": "architecture_diagram",
        "topic_relevance_score": 0.9,
        "topic_relevance_label": "relevant",
        "vision_description": "MoE orchestrator architecture diagram",
        "editorial_rank": 1,
    }
    chart = {
        "filename": "chart.webp",
        "asset_type": "benchmark_chart",
        "topic_relevance_score": 0.8,
        "topic_relevance_label": "relevant",
        "vision_description": "5x inference benchmark chart throughput",
        "editorial_rank": 2,
    }
    ranked = rank_images([arch, chart], sentence, RULES)
    assert ranked[0][1]["filename"] == "chart.webp"


def test_asset_type_boost_values():
    chart = {"asset_type": "benchmark_chart"}
    arch = {"asset_type": "architecture_diagram"}
    s = "five times throughput benchmark"
    assert asset_type_boost(s, chart) > asset_type_boost(s, arch)


def test_extract_image_urls_from_html():
    html = '<img src="/images/5x-inference-1-1024x466.png" alt="5x inference">'
    pairs = extract_image_urls(html, "https://developer.nvidia.com/blog/test/")
    assert pairs
    assert "5x-inference" in pairs[0][0]


def test_missing_page_keys_detects_gap():
    handoff = handoff_image_keys({"images": [{"filename": "hero.png", "source_url": ""}]})
    urls = ["https://cdn.example.com/1920x1080_hero_visual_g4.webp"]
    missing = missing_page_keys(urls, handoff)
    assert missing


def test_audit_topic_gaps_flags_selection_gap():
    seg = {"dir": "01-test", "slug": "nvidia-nemotron-3-ultra", "slide_type": "avatar_media_3"}
    script = "NVIDIA Nemotron — up to five times throughput on Blackwell. Built for agents."
    topic = {
        "topic_slug": "nvidia-nemotron-3-ultra",
        "canonical_url": "",
        "images": [
            {
                "filename": "arch.png",
                "asset_type": "architecture_diagram",
                "topic_relevance_score": 0.9,
                "topic_relevance_label": "relevant",
                "vision_description": "architecture orchestrator",
                "editorial_rank": 1,
            },
            {
                "filename": "chart.webp",
                "asset_type": "benchmark_chart",
                "topic_relevance_score": 0.8,
                "topic_relevance_label": "relevant",
                "vision_description": "5x inference throughput benchmark",
                "editorial_rank": 2,
            },
        ],
    }
    row = audit_topic_gaps(seg, topic, script, RULES, manual_slugs=set(), fetch_canonical=False)
    planned, _ = build_cue_plan(script, topic["images"], RULES)
    assert planned[0]["asset_type"] == "benchmark_chart"
    assert row["ok"] or not any(g["type"] == "selection_gap" for g in row["gaps"])


def test_is_content_image_filters_short_names():
    assert is_content_image("https://x.com/a.png") is False
    assert is_content_image("https://x.com/hero_visual_g4_1920x1080.webp") is True

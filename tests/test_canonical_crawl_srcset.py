"""Canonical crawl srcset / responsive variant matching."""
from __future__ import annotations

from praisonaippt.segment_video.assets.canonical_crawl import (
    _handoff_covers_page_key,
    _responsive_stem,
    handoff_image_keys,
    missing_page_keys,
)


def test_responsive_stem_strips_size_suffix():
    assert _responsive_stem("5x-inference-1-179x81.png") == "5x-inference-1"


def test_handoff_covers_responsive_variant():
    handoff = handoff_image_keys({
        "images": [{
            "filename": "abc.webp",
            "source_url": "https://cdn.example.com/5x-Inference-1.webp",
        }],
    })
    assert _handoff_covers_page_key("5x-inference-1-179x81.png", handoff)


def test_missing_page_keys_skips_covered_responsive():
    handoff = handoff_image_keys({
        "images": [{
            "filename": "chart.webp",
            "source_url": "https://x.com/5x-inference-1.webp",
        }],
    })
    urls = ["https://x.com/5x-inference-1-625x352.png"]
    assert missing_page_keys(urls, handoff) == []

"""Default daily_single pipeline protocol (v3-shaped)."""
from __future__ import annotations

from typing import Any

from praisonaippt.video_qa.config import DEFAULT_VIDEO_QA_PROTOCOL

DEFAULT_PROTOCOL: dict[str, Any] = {
    "schema_version": 3,
    "name": "daily-single-pipeline",
    "profile": "daily_single",
    "stages": [
        {
            "id": "write-scripts",
            "scope": "project",
            "outputs": ["segments/*/script.md"],
        },
        {
            "id": "synthesise-vo",
            "scope": "project",
            "depends_on": ["write-scripts"],
            "outputs": ["segments/*/narration.mp3", "merge/narration.mp3"],
            "skip_existing": True,
        },
        {
            "id": "bookend-media",
            "scope": "segment",
            "depends_on": ["write-scripts"],
            "outputs": ["segments/00-hook/heygen.mp4", "segments/99-outro/heygen.mp4"],
            "skip_existing": True,
        },
        {
            "id": "assemble-beats",
            "scope": "project",
            "depends_on": ["synthesise-vo"],
            "outputs": ["beats/*.mp4", "merge/final-silent.mp4"],
        },
        {
            "id": "loudnorm",
            "scope": "project",
            "depends_on": ["assemble-beats"],
            "outputs": ["merge/final.mp4"],
        },
        {
            "id": "build-captions",
            "scope": "project",
            "depends_on": ["assemble-beats"],
            "outputs": ["merge/final.srt", "segments/*/segment.srt"],
        },
        {
            "id": "build-timeline",
            "scope": "project",
            "depends_on": ["loudnorm"],
            "outputs": ["merge/timeline.json", "merge/final.srt"],
        },
        {
            "id": "validate-display",
            "scope": "project",
            "depends_on": ["build-timeline"],
            "outputs": ["merge/display_sync_report.json"],
        },
        {
            "id": "validate-spoken-visual",
            "scope": "project",
            "depends_on": ["validate-display"],
            "outputs": ["merge/spoken_visual_sync_report.json"],
        },
        {
            "id": "validate-slide-quality",
            "scope": "project",
            "depends_on": ["validate-spoken-visual"],
            "outputs": ["merge/slide_design_report.json"],
        },
        {
            "id": "validate-engagement-assets",
            "scope": "project",
            "depends_on": ["validate-slide-quality"],
            "outputs": ["merge/engagement_report.json"],
        },
        {
            "id": "validate-viral-readiness",
            "scope": "project",
            "depends_on": ["validate-engagement-assets"],
            "outputs": ["merge/viral_readiness_report.json"],
        },
        {
            "id": "audit-visual",
            "scope": "project",
            "depends_on": ["validate-viral-readiness"],
            "outputs": ["merge/visual_audit_report.json"],
        },
        {
            "id": "validate-hook-attention",
            "scope": "project",
            "depends_on": ["audit-visual"],
            "outputs": ["merge/qa/hook_attention_audit.json"],
        },
        {
            "id": "validate-sync",
            "scope": "project",
            "depends_on": ["validate-hook-attention"],
            "outputs": ["merge/sync_validation_report.json"],
        },
        {
            "id": "validate-all",
            "scope": "project",
            "depends_on": ["validate-sync"],
            "outputs": ["validation_report.json"],
        },
    ],
    "validation_suite": {
        "validators": [
            {"id": "tools", "required": True},
            {"id": "beat_coverage", "required": True},
            {"id": "final_output", "required": True},
            {"id": "audio_loudness", "required": True},
        ],
    },
    "audio_loudness": {"target_lufs": -16.0, "max_spread_lufs": 2.0},
    "hook_montage": {
        "enabled": True,
        "min_cues": 5,
        "min_alignment": 0.45,
    },
    "visual_audit": {
        "enabled": True,
        "interval_sec": 5.0,
        "min_pixel_sim": 0.42,
        "min_topic_alignment": 0.35,
        "block_generic_broll": True,
        "vision_provider": "openai",
        "vision_model": "gpt-4o-mini",
    },
    "daily_single": {
        "target_duration_sec": [340, 540],
        "final_outputs": {"mp4": "merge/final.mp4", "srt": "merge/final.srt"},
        "create_news_stages": ["analyse-clips", "build-beat-map", "generate-cards"],
    },
    "exclude_megapost": [
        "required_assets", "segment_sync",
    ],
    "video_qa": {
        **DEFAULT_VIDEO_QA_PROTOCOL,
    },
}

# Segment order for VO + assembly (extend by editing manifest segment_map later).
BEAT_SEGMENT_DIRS: dict[int, str] = {
    1: "01-cold-open",
    2: "02-mythos-tier",
    3: "03-engineers-care",
    4: "04-benchmarks",
    5: "05-vision-memory",
    6: "06-safeguards",
    7: "07-api-integration",
    8: "08-glasswing",
    9: "09-pricing",
    10: "10-alignment",
}

SEGMENT_ORDER: list[tuple[str, str | None, int | None]] = [
    ("00-hook", "00-hook", None),
    *[(f"beat-{i:02d}", BEAT_SEGMENT_DIRS[i], i) for i in range(1, 11)],
    ("99-outro", "99-outro", None),
]

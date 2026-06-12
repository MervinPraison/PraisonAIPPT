"""QA stage definitions and protocol defaults."""
from __future__ import annotations

from typing import Any, Literal

When = Literal["pre_build", "pre_assemble", "post_vo", "post_bookends", "post_assemble", "post_captions", "post_build", "all"]

DEFAULT_QA_STAGES: list[dict[str, Any]] = [
    {"id": "s04-knowledge", "when": "pre_build", "required": True, "offline_ok": True},
    {"id": "s06-coverage", "when": "pre_build", "required": True, "offline_ok": True, "phase": "post_scripts"},
    {"id": "s01-assets", "when": "pre_build", "required": True, "offline_ok": True, "phase": "pre_sync"},
    {"id": "s01-assets", "when": "pre_build", "required": True, "offline_ok": True, "phase": "post_sync"},
    {"id": "s02-source-vlm", "when": "pre_build", "required": False, "offline_ok": False, "interval_sec": 5.0},
    {"id": "s06-coverage", "when": "pre_build", "required": False, "offline_ok": True, "phase": "post_sync"},
    {"id": "s00-bookends", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s11-canonical-capture", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s05-transcript", "when": "post_vo", "required": True, "offline_ok": True, "phase": "post_vo"},
    {"id": "s00-bookends", "when": "post_bookends", "required": True, "offline_ok": True},
    {"id": "s05-transcript", "when": "post_build", "required": True, "offline_ok": True, "phase": "post_captions"},
    {"id": "s03-image-speech", "when": "post_build", "required": True, "offline_ok": True, "phase": "post_render"},
    {"id": "s22-word-visual-sync", "when": "post_build", "required": True, "offline_ok": False, "use_vlm": True},
    {"id": "s08-av-sync", "when": "post_build", "required": True, "offline_ok": True},
    {"id": "s07-framing", "when": "post_build", "required": False, "offline_ok": True},
    {"id": "s09-on-screen-text", "when": "post_build", "required": False, "offline_ok": True},
    {"id": "s10-final-composite", "when": "post_build", "required": True, "offline_ok": False, "sync_runs": 3},
    {"id": "s12-hook-attention", "when": "post_build", "required": True, "offline_ok": True, "seconds": 5},
    {"id": "s13-slide-design", "when": "post_build", "required": True, "offline_ok": True},
    {"id": "s14-engagement", "when": "post_build", "required": True, "offline_ok": True},
    {"id": "s15-viral-readiness", "when": "post_build", "required": True, "offline_ok": True},
    {"id": "s18-video-first-policy", "when": "pre_build", "required": True, "offline_ok": True, "phase": "post_scripts"},
    {"id": "s19-chart-script", "when": "pre_build", "required": True, "offline_ok": True, "phase": "post_scripts"},
    {"id": "s13-slide-design", "when": "pre_build", "required": False, "offline_ok": True, "phase": "post_scripts"},
    {"id": "s21-beat-map-policy", "when": "pre_build", "required": True, "offline_ok": True, "phase": "post_scripts"},
    {"id": "s16-montage-clock", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s20-asset-inventory", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s21-beat-map-policy", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s17-cue-picture-map", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s19-chart-script", "when": "pre_assemble", "required": True, "offline_ok": True},
    {"id": "s08-av-sync", "when": "post_assemble", "required": True, "offline_ok": True},
    {"id": "s05-transcript", "when": "post_captions", "required": True, "offline_ok": True, "phase": "post_captions"},
]

DEFAULT_DEGRADATION: dict[str, Any] = {
    "vlm": {"trigger": "no_openai_key", "behaviour": "pixel_only", "severity": "warn"},
    "heygen": {"trigger": "insufficient_credit", "behaviour": "reuse_existing", "severity": "warn"},
    "whisper": {"trigger": "transcribe_failure", "behaviour": "proportional_captions", "severity": "warn"},
    "final_mp4": {"trigger": "missing_merge_final", "behaviour": "skip_post_build", "severity": "error"},
}

DEFAULT_VIDEO_QA_PROTOCOL: dict[str, Any] = {
    "schema_version": 1,
    "stages": DEFAULT_QA_STAGES,
    "degradation": DEFAULT_DEGRADATION,
    "min_transcript_overlap": 0.35,
    "min_coverage_assets_per_beat": 1,
}

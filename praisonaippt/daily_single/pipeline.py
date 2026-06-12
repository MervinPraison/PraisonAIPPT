"""Central daily-single pipeline definition — single source of truth for build + QA order.

Import this module from CLI, SDK engine, tests, and docs generators. Do not duplicate
stage order in shell scripts except as thin wrappers calling ``DailySinglePipelineEngine``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

StageKind = Literal["build", "qa", "gate", "test"]

When = Literal["pre_build", "pre_assemble", "post_vo", "post_bookends", "post_assemble", "post_captions", "post_build", "all"]

# Video-first → audio → Whisper words → slide map (enforced by spoken_visual_gates per phase).
PIPELINE_AV_ORDER: tuple[str, ...] = (
    "video_first_assets",
    "narration_audio",
    "whisper_word_timings",
    "visual_timeline",
    "assembled_mux",
    "spoken_visual_map",
)


@dataclass(frozen=True)
class PipelineStep:
    id: str
    kind: StageKind
    label: str
    when: When | None = None
    optional: bool = False
    cli: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "when": self.when,
            "optional": self.optional,
            "cli": self.cli or self.id,
            "notes": self.notes,
        }


# Full end-to-end build (video-first). Assemble before captions; spoken↔visual gates after mux.
BUILD_PIPELINE: tuple[PipelineStep, ...] = (
    PipelineStep("sync-assets", "build", "Sync canonical images and HD clips", cli="sync-assets"),
    PipelineStep("write-scripts", "build", "Write segment scripts from research", cli="write-scripts"),
    PipelineStep(
        "validate-qa-pre_build",
        "qa",
        "Pre-build QA — assets, coverage, video-first policy, chart scripts",
        when="pre_build",
        cli="validate-qa --when pre_build",
    ),
    PipelineStep("synthesise-vo", "build", "ElevenLabs narration for all segments", cli="synthesise-vo"),
    PipelineStep(
        "validate-qa-post_vo",
        "qa",
        "Post-VO transcript overlap",
        when="post_vo",
        cli="validate-qa --when post_vo",
    ),
    PipelineStep("bookend-media", "build", "HeyGen hook + outro avatars", cli="bookend-media"),
    PipelineStep(
        "validate-av-post_bookends",
        "qa",
        "Post-bookends AV — hook/outro narration (+ whisper if present)",
        when="post_bookends",
        cli="validate-qa --when post_bookends",
    ),
    PipelineStep(
        "record-canonical-scroll",
        "build",
        "Record canonical page scroll for hook attention",
        cli="record-canonical-scroll",
        optional=True,
    ),
    PipelineStep(
        "validate-qa-pre_assemble",
        "qa",
        "Pre-assemble QA — bookends, montage clock, cue map",
        when="pre_assemble",
        cli="validate-qa --when pre_assemble",
    ),
    PipelineStep(
        "assemble-beats",
        "build",
        "ffmpeg assembly → merge/final.mp4",
        cli="assemble-beats",
    ),
    PipelineStep(
        "validate-av-post_assemble",
        "qa",
        "Post-assemble AV pillars — mux audio, Whisper words, visual timeline",
        when="post_assemble",
        cli="validate-qa --when post_assemble",
    ),
    PipelineStep(
        "build-captions",
        "build",
        "Script-aligned SRT merged from timeline (after assemble)",
        cli="build-captions",
        notes="Must run after assemble-beats so final.srt uses current timeline.json",
    ),
    PipelineStep(
        "validate-av-post_captions",
        "qa",
        "Post-captions AV pillars — global words, display sync, visual plan",
        when="post_captions",
        cli="validate-qa --when post_captions",
    ),
    PipelineStep(
        "validate-spoken-visual",
        "gate",
        "Post-build spoken ↔ visual (Whisper words + VLM frames, charts, windows)",
        cli="validate-spoken-visual",
    ),
    PipelineStep(
        "validate-qa-post_build",
        "qa",
        "Post-build QA — independent re-check (s03, s22 word/VLM, s08, s10)",
        when="post_build",
        cli="validate-qa --when post_build",
    ),
    PipelineStep(
        "validate-beat-map",
        "gate",
        "Beat-map policy — banned assets, LinkedIn placement, clip mix",
        cli="validate-beat-map",
    ),
)

# Publish gate matrix (V1–V19). Assumes BUILD_PIPELINE media steps are done.
PUBLISH_GATE: tuple[PipelineStep, ...] = (
    PipelineStep(
        "validate-qa-pre_build",
        "qa",
        "V2 pre-build QA",
        when="pre_build",
        cli="validate-qa --when pre_build",
    ),
    PipelineStep(
        "validate-qa-pre_assemble",
        "qa",
        "V14 pre-assemble QA",
        when="pre_assemble",
        cli="validate-qa --when pre_assemble",
    ),
    PipelineStep(
        "assemble-beats",
        "build",
        "Optional re-assemble",
        cli="assemble-beats",
        optional=True,
    ),
    PipelineStep("build-captions", "build", "Refresh captions after assemble", cli="build-captions"),
    PipelineStep(
        "validate-av-post_assemble",
        "qa",
        "V14b post-assemble AV pillars",
        when="post_assemble",
        cli="validate-qa --when post_assemble",
    ),
    PipelineStep(
        "validate-av-post_captions",
        "qa",
        "V14c post-captions AV pillars",
        when="post_captions",
        cli="validate-qa --when post_captions",
    ),
    PipelineStep("pytest", "test", "V1 unit tests", cli="pytest"),
    PipelineStep("validate-display", "gate", "V3 display sync", cli="validate-display"),
    PipelineStep("validate-spoken-visual", "gate", "V4 spoken ↔ visual", cli="validate-spoken-visual"),
    PipelineStep("validate-slide-quality", "gate", "V5 slide design", cli="validate-slide-quality"),
    PipelineStep(
        "validate-asset-inventory",
        "gate",
        "V5b per-asset frame inventory",
        cli="validate-asset-inventory",
    ),
    PipelineStep(
        "validate-beat-map",
        "gate",
        "V5c beat-map policy",
        cli="validate-beat-map",
    ),
    PipelineStep("validate-engagement-assets", "gate", "V6 engagement", cli="validate-engagement-assets"),
    PipelineStep("validate-viral-readiness", "gate", "V7 viral readiness", cli="validate-viral-readiness"),
    PipelineStep("audit-visual", "gate", "V8 visual audit", cli="audit-visual"),
    PipelineStep("validate-hook-attention", "gate", "V9 hook attention", cli="validate-hook-attention"),
    PipelineStep("validate-canonical-scroll", "gate", "V10 canonical scroll", cli="validate-canonical-scroll"),
    PipelineStep("validate-sync", "gate", "V11 sync idempotency", cli="validate-sync --runs 3"),
    PipelineStep("validate-all", "gate", "V12 validate-all", cli="validate-all"),
    PipelineStep(
        "validate-qa-post_build",
        "qa",
        "V13 modular post-build QA",
        when="post_build",
        cli="validate-qa --when post_build",
    ),
)

PYTEST_MODULES: tuple[str, ...] = (
    "tests/test_cue_slide_sync.py",
    "tests/test_spoken_visual_sync.py",
    "tests/test_slide_design_audit.py",
    "tests/test_asset_inventory_audit.py",
    "tests/test_beat_map_audit.py",
    "tests/test_engagement_audit.py",
    "tests/test_viral_readiness.py",
    "tests/test_video_qa.py",
    "tests/test_pre_assemble_qa.py",
    "tests/test_daily_single_engine.py",
    "tests/test_spoken_visual_gates.py",
    "tests/test_word_visual_sync.py",
    "tests/test_av_pillar_gates.py",
)


def build_protocol_stages() -> list[dict[str, Any]]:
    """Protocol.json-compatible stage list derived from BUILD_PIPELINE + PUBLISH_GATE."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    deps: list[str] = []

    def add(step: PipelineStep, *, depends_on: list[str] | None = None) -> None:
        if step.id in seen or step.kind in ("test",):
            return
        seen.add(step.id)
        entry: dict[str, Any] = {
            "id": step.cli.split()[0] if step.cli else step.id,
            "scope": "project",
            "pipeline_id": step.id,
            "label": step.label,
        }
        if depends_on:
            entry["depends_on"] = depends_on
        out.append(entry)

    for step in BUILD_PIPELINE:
        add(step, depends_on=list(deps) if deps else None)
        if step.kind == "build":
            deps = [step.cli.split()[0] if step.cli else step.id]

    gate_deps = ["assemble-beats"]
    for step in PUBLISH_GATE:
        if step.kind == "gate":
            add(step, depends_on=gate_deps)
            gate_deps = [step.cli.split()[0]]

    return out


def pipeline_manifest() -> dict[str, Any]:
    """JSON-serialisable pipeline for SDK consumers and docs."""
    return {
        "schema_version": 2,
        "name": "daily-single-pipeline",
        "av_order": list(PIPELINE_AV_ORDER),
        "build": [s.to_dict() for s in BUILD_PIPELINE],
        "publish_gate": [s.to_dict() for s in PUBLISH_GATE],
        "pytest_modules": list(PYTEST_MODULES),
    }

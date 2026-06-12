# AGENTS.md — daily-single video pipeline

All agents working on **praisonaippt** daily-single videos must follow this document.  
Single source of truth in code: `praisonaippt/daily_single/pipeline.py`  
SDK entry: `DailySinglePipelineEngine` (`praisonaippt/daily_single/engine.py`)

## Project variants

| Variant | Example | Focus |
|---------|---------|-------|
| `trust-audit` | `examples/videos/anthropic-claude-fable-5-trust-audit/` | Launch promise vs receipt; LinkedIn in beats 1–2 only |
| `social-comparison` | `examples/videos/anthropic-claude-fable-5-social-comparison/` | Same-prompt split-screen proof; LinkedIn + YouTube clips |
| (default) | `examples/videos/anthropic-claude-fable-5-mythos-5/` | Mythos slide deck + motion |

All video-first variants use `asset_policy: "video-first-local"` in `research/beat-map-v2.json`.

## BUILD_PIPELINE (run with `daily-single -p $PROJECT pipeline run`)

| Step | CLI | QA gate **before next step** |
|------|-----|------------------------------|
| 1 | `sync-assets` | — |
| 2 | `write-scripts` | — |
| 3 | **`validate-qa --when pre_build`** | s04 knowledge, s06 coverage, s01 assets, **s18 video-first**, **s19 chart-script**, **s21 beat-map** |
| 4 | `synthesise-vo` | — |
| 5 | **`validate-qa --when post_vo`** | s05 transcript overlap per segment |
| 6 | `bookend-media` | — |
| 7 | `record-canonical-scroll` *(optional)* | — |
| 8 | **`validate-qa --when pre_assemble`** | s00 bookends, s11 canonical capture, **s16 montage-clock**, **s17 cue-map**, **s20 asset-inventory**, **s21 beat-map** |
| 9 | `assemble-beats` | — |
| 10 | `build-captions` | — |
| 11 | **`validate-spoken-visual`** | windows, charts, transitions, montage, plain language → `spoken_visual_sync_report.json` |
| 12 | **`validate-beat-map`** | banned assets, clip mix, LinkedIn placement → `beat_map_policy_report.json` |

**Rule:** If a QA step fails, fix the cause, re-run from the failed **build** step, then re-run all QA gates below it.

## PUBLISH_GATE (run with `daily-single -p $PROJECT pipeline publish-gate`)

| Gate | CLI | Pass criterion |
|------|-----|----------------|
| V2 | `validate-qa --when pre_build` | All required pre-build stages |
| — | `build-captions` | `merge/final.srt` exists |
| V14 | `validate-qa --when pre_assemble` | Bookends, montage, asset inventory |
| — | `assemble-beats` *(optional `--assemble`)* | `merge/final.mp4` |
| V1 | `pytest` | 10 modules in `PYTEST_MODULES` |
| V3 | `validate-display` | All cues ≥ 0.35 alignment |
| V4 | `validate-spoken-visual` | `ok: true` in report |
| V5 | `validate-slide-quality` | Slide design tier |
| V5b | `validate-asset-inventory` | No banned hook/body assets |
| V5c | `validate-beat-map` | Beat-map policy |
| V6 | `validate-engagement-assets` | Motion + social proof |
| V7 | `validate-viral-readiness` | Composite viral score |
| V8 | `audit-visual` | 5s frame audit |
| V9 | `validate-hook-attention` | Hook frames + scroll |
| V10 | `validate-canonical-scroll` | Scroll asset quality |
| V11 | `validate-sync --runs 3` | Idempotent 3× |
| V12 | `validate-all` | Legacy rollup |
| V13 | `validate-qa --when post_build` | s03, s08, s10 composite |

## Banned assets (all video-first variants)

Enforced by **s18**, **s20**, **s21**, **validate-beat-map**:

- `demo-scroll`, `demo-pokemon`, `demo-solar`
- `v2-*` programmatic slides
- `fallback-notification.mp4` (mislabelled vintage B-roll)
- Hook PNG montage (video clips only for trust-audit / social-comparison)

## Spoken ↔ visual parity

- **`validate-spoken-visual`** — chart kind parity (`attack_rate_bar` ≠ decision table speech)
- **`s19 chart-script`** — scripts name charts before they appear on screen
- Rebuild order after script edit: `synthesise-vo` → `assemble-beats` → `build-captions` → `validate-spoken-visual`

## Social comparison research

1. Catalog URLs in `research/social-sources.json`
2. Download clips: `bash scripts/download_social_videos.sh`
3. Search X/Reddit/HN: `.cursor/skills/daily-single-video-pipeline/social-research-last30days.md`
4. LinkedIn source (verified): Alvaro Cintas post → `linkedin-cintas-fable5-vs-opus.mp4`

## Skills (read before acting)

| Skill | Path |
|-------|------|
| Script contract | `.cursor/skills/daily-single-video/SKILL.md` |
| Pipeline + QA checklist | `.cursor/skills/daily-single-video-pipeline/SKILL.md` |
| QA stage map | `.cursor/skills/daily-single-video-pipeline/reference.md` |
| Spoken/visual sync | `.cursor/skills/daily-single-video-pipeline/spoken-visual-sync.md` |
| Social research | `.cursor/skills/daily-single-video-pipeline/social-research-last30days.md` |

## Shell wrappers

```bash
PROJECT=examples/videos/<slug>
.cursor/skills/daily-single-video-pipeline/scripts/run-qa-gate.sh $PROJECT pre_build
.cursor/skills/daily-single-video-pipeline/scripts/run-spoken-visual-gate.sh $PROJECT --assemble
.cursor/skills/daily-single-video-pipeline/scripts/run-publish-gate.sh $PROJECT
```

## Environment

```bash
zsh -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate test && cd /path/to/praisonaippt"
```

## Key artefacts

| Path | Purpose |
|------|---------|
| `merge/final.mp4` | Deliverable |
| `merge/final.srt` | Script-locked captions |
| `merge/timeline.json` | Segment timing |
| `merge/spoken_visual_sync_report.json` | V4 gate |
| `merge/beat_map_policy_report.json` | V5c gate |
| `merge/asset_inventory_report.json` | V5b gate |
| `merge/qa/summary.json` | Modular QA rollup |

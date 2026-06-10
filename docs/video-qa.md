# Video QA (`video_qa`)

Modular validation for **daily single** projects. Each stage runs independently, writes JSON under `merge/qa/`, and can be triggered at the right point in the build pipeline.

**Related:** [Daily single pipeline](daily-single-video.md) · [Testing guide](daily-single-testing.md) · [Pipeline overview](pipeline-overview.md)

## Why modular QA?

Before `video_qa`, all checks ran at the end via `validate-sync` and `validate-all`. That made it hard to know *which phase* broke. Modular stages:

- Run **after the step they validate** (pre-build, post-VO, pre-assemble, post-build)
- Write **separate reports** for easier debugging
- Support **degradation** (e.g. proportional captions when Whisper fails)
- Share **cached display sync** within one suite run (no duplicate work across s03/s08)

## Commands

```bash
PROJECT=examples/videos/anthropic-claude-fable-5-mythos-5

# List all stages
python -m praisonaippt.video_qa --project $PROJECT list
daily-single -p $PROJECT validate-qa   # alias; default --when all

# Run by pipeline phase
daily-single -p $PROJECT validate-qa --when pre_build
daily-single -p $PROJECT validate-qa --when post_vo
daily-single -p $PROJECT validate-qa --when pre_assemble
daily-single -p $PROJECT validate-qa --when post_build

# Single stage
daily-single -p $PROJECT validate-qa s08-av-sync
python -m praisonaippt.video_qa --project $PROJECT run s10-final-composite
```

Console entry points: `daily-single validate-qa`, `video-qa` (see `pyproject.toml`).

## QA-gated pipeline order

Insert gates between build commands:

```text
write-scripts
    └─ validate-qa --when pre_build     (s04, s06, s01, s02)
sync-assets
synthesise-vo
    └─ validate-qa --when post_vo       (s05 narration check)
bookend-media
    └─ validate-qa --when pre_assemble  (s00 bookends)
assemble-beats                        (also writes timeline.json)
build-captions
    └─ validate-qa --when post_build    (s05 captions, s03–s10)
validate-all                          (also run inside s10)
```

## Stage map

| ID | When | Phase | Required | What it checks |
|----|------|-------|----------|----------------|
| s04-knowledge | pre_build | — | yes | manifest, video-script, handoff, beat-map, scripts |
| s06-coverage | pre_build | post_scripts | yes | Script→asset coverage, hook montage plan |
| s01-assets | pre_build | pre_sync | yes | handoff + beat-map files exist |
| s01-assets | pre_build | post_sync | yes | Media inventory on disk (images, videos ≥720p) |
| s02-source-vlm | pre_build | — | no | VLM sample every 5s on source motion clips |
| s06-coverage | pre_build | post_sync | no | Post-sync coverage gaps (warn) |
| s00-bookends | pre_assemble | — | yes | Hook/outro: script, narration, heygen.mp4 |
| s05-transcript | post_vo | post_vo | yes | Each segment has script + narration.mp3 |
| s05-transcript | post_build | post_captions | yes | Caption lock, Whisper/proportional overlap |
| s03-image-speech | post_build | post_render | yes | Display sync (spoken ↔ on-screen visual) |
| s08-av-sync | post_build | — | yes | Hook structure, word match, timeline boundaries |
| s07-framing | post_build | — | no | HeyGen dimensions (1280×720 expected) |
| s09-on-screen-text | post_build | — | no | Long cues with weak visual alignment |
| s10-final-composite | post_build | — | yes | Visual audit + validate-sync ×3 + validate-all |

## Stage details

### s04-knowledge

Validates create-news inputs before any media work. Ensures `manifest.json` points at research paths and every segment has a non-empty `script.md`.

### s06-coverage

Two phases:

- **post_scripts** — beat-map assets vs script sentence count; hook montage validator
- **post_sync** — same after `sync-assets`; warns on sparse beats (e.g. 12 sentences, 1 asset)

### s01-assets

- **pre_sync** — handoff JSON and beat-map present; counts images/videos in handoff
- **post_sync** — runs `validate_media_inventory`; verifies files resolve under review-assets

### s02-source-vlm

Exports a frame every 5s from each handoff video clip. Optional OpenAI vision describes frames and flags **generic B-roll** (vintage, stock, unrelated). Results cached in `merge/qa/vlm_cache/`.

Requires `OPENAI_API_KEY` unless skipped (offline mode or `required: false`).

### s00-bookends

Gate before `assemble-beats`. Confirms hook and outro have ElevenLabs narration and HeyGen MP4 ready.

### s05-transcript

Two phases:

| Phase | When | Checks |
|-------|------|--------|
| post_vo | After TTS | narration.mp3 + script per segment |
| post_captions | After build-captions | SRT cue lock; Whisper overlap ≥0.35 or proportional fallback |

Proportional captions (no `timestamps.json`) set `degraded: true` but pass with warnings.

### s03-image-speech

Wraps `validate_display_sync` with suite-level caching. Each SRT cue midpoint is scored against the planned asset file (keyword alignment ≥ **0.35**).

### s08-av-sync

Combines:

- Display sync summary (from cache)
- Hook structure (3-part hook)
- Word-level probe on hook/outro where Whisper timestamps exist
- **Section boundaries** — `beats/*.mp4` durations vs `merge/timeline.json` (not raw HeyGen length)

### s07-framing / s09-on-screen-text

Optional polish checks. s07 verifies HeyGen resolution. s09 lists cues with ≥6 spoken words but alignment below threshold.

### s10-final-composite

Production gate — runs three sub-systems:

1. **Visual audit** — sample `final.mp4` every 5s; pixel + optional VLM
2. **Sync suite ×3** — idempotent caption lock, hook, montage, display, YouTube quality
3. **validate-all** — tools, output spec, inventory

Mirrors legacy reports into `merge/qa/legacy_links.json`.

## Reports

```text
merge/qa/
  summary.json              # Latest suite rollup
  s04_knowledge_report.json
  s05_transcript_post_vo_report.json
  s05_transcript_post_captions_report.json
  s08_av_sync_report.json
  s10_final_composite_report.json
  s02_source_vlm_timeline.json
  vlm_cache/                  # Per-frame VLM cache
  legacy_links.json           # Pointers to display/sync/visual reports
```

### Reading `summary.json`

```json
{
  "ok": true,
  "when": "post_build",
  "degradation": { "whisper": "missing_timestamps" },
  "summary": {
    "stages_run": 6,
    "stages_passed": 6,
    "failed_required": []
  }
}
```

When `ok` is false, inspect `failed_required` then open the matching `s*_report.json` for `checks[]` with `severity: error`.

## Protocol configuration

Stages are configured in `scripts/config/protocol.json` under `video_qa`. If missing, defaults merge from `praisonaippt/video_qa/config.py`:

```bash
daily-single -p $PROJECT emit-protocol   # write full template
```

Key overrides:

| Key | Default | Purpose |
|-----|---------|---------|
| `min_transcript_overlap` | 0.35 | Whisper vs script overlap |
| `min_coverage_assets_per_beat` | 1 | s06 sparse beat threshold |
| `degradation.whisper` | proportional_captions | Warn when timestamps missing |

## Degradation and skip rules

| Condition | Affected stages | Behaviour |
|-----------|-----------------|-----------|
| `PRAISONAIPPT_QA_OFFLINE=1` | s02, s10 vision | Skip or pixel-only |
| No `OPENAI_API_KEY` | s02 | Skipped (`vlm_offline`) |
| No `merge/final.mp4` | s03, s07–s10 | Skipped (`missing_final_mp4`) |
| Whisper/transcribe failure | s05 | Proportional captions; `degraded: true` |

## Package layout

```text
praisonaippt/video_qa/
  __main__.py       # video-qa CLI
  runner.py         # run_stage, run_suite
  registry.py       # stage → function map
  config.py         # DEFAULT_QA_STAGES
  context.py        # SuiteContext (cached display sync)
  degradation.py    # detect_degradation, stage_should_skip
  adapters.py       # report paths, protocol load
  stages/           # s00 … s10 implementations
```

## Offline CI

```bash
export PRAISONAIPPT_QA_OFFLINE=1
pytest tests/test_video_qa.py -q
daily-single -p $PROJECT validate-qa --when pre_build
```

VLM stages skip; pixel-based display sync and caption lock still run where artefacts exist.

## Related documentation

- [Daily single testing](daily-single-testing.md) — pytest, legacy gates, workflow checklist
- [Daily single pipeline](daily-single-video.md) — build commands and script contract
- [Commands](commands.md#daily-single-video-pipeline)

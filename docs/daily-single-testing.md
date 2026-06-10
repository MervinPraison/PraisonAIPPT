# Daily single — testing guide

This page explains **every kind of test** used in the daily single video pipeline: what it checks, when to run it, and where results are saved. Written for operators and contributors — no need to read the Python source first.

## Three layers

```text
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Unit tests (pytest, no video project required)   │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — Modular QA (validate-qa / video_qa stages)       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — Legacy publish gates (validate-sync, validate-all)│
└─────────────────────────────────────────────────────────────┘
```

Run **Layer 1** after code changes. Run **Layer 2** after each pipeline phase. Run **Layer 3** before upload — or rely on stage **s10-final-composite**, which runs the same checks.

---

## Layer 1 — Unit tests (pytest)

Fast, offline tests. No API keys required for the core QA module tests.

```bash
conda activate test
cd /path/to/praisonaippt

# Minimal — video_qa module only
pytest tests/test_video_qa.py -q

# Full daily_single suite
pytest tests/test_daily_single_display_sync_unit.py \
       tests/test_daily_single_sync_validation.py \
       tests/test_daily_single_hook_montage.py \
       tests/test_daily_single_media_sync.py \
       tests/test_daily_single_visual_audit.py \
       tests/test_daily_single_youtube_quality.py \
       tests/test_daily_single_captions.py \
       tests/test_video_qa.py -q
```

| Test file | What it verifies |
|-----------|------------------|
| `test_video_qa.py` | Stage registry, skip rules, s04/s05/s06 behaviour, VLM cache round-trip |
| `test_daily_single_sync_validation.py` | Caption script lock, hook structure, sync suite idempotency (mocked) |
| `test_daily_single_display_sync_unit.py` | Cue → asset keyword scoring, SRT parsing |
| `test_daily_single_hook_montage.py` | Phrase → hero montage plan, montage validators |
| `test_daily_single_visual_audit.py` | Pixel similarity thresholds, generic B-roll patterns |
| `test_daily_single_youtube_quality.py` | Hook stakes, plain language, outro CTA rules |
| `test_daily_single_media_sync.py` | Handoff inventory, HD video rules |
| `test_daily_single_captions.py` | Sentence splitting, proportional caption fallback |

!!! tip "When to run"
    Run the full pytest suite before merging changes to `praisonaippt/daily_single/` or `praisonaippt/video_qa/`.

---

## Layer 2 — Modular QA (`validate-qa`)

**Module:** `praisonaippt/video_qa/`  
**CLI:** `daily-single -p $PROJECT validate-qa` or `python -m praisonaippt.video_qa --project $PROJECT run`

Each stage runs **independently** and writes a JSON report under `merge/qa/`. A rollup lives in `merge/qa/summary.json`.

### When to run

| Phase flag | Run after | Stages included |
|------------|-----------|-----------------|
| `pre_build` | Scripts + handoff ready; before or after `sync-assets` | s04, s06, s01, s02 (optional VLM) |
| `post_vo` | `synthesise-vo` | s05 (narration present per segment) |
| `pre_assemble` | `bookend-media` | s00 (hook/outro HeyGen gate) |
| `post_build` | `assemble-beats` + `build-captions` | s05 captions, s03, s08, s07, s09, s10 |
| `all` | Full rebuild audit | Every configured stage |

```bash
daily-single -p $PROJECT validate-qa --when pre_build
daily-single -p $PROJECT validate-qa --when post_build

# Single stage debug
daily-single -p $PROJECT validate-qa s08-av-sync
python -m praisonaippt.video_qa --project $PROJECT list
```

### Stage reference (what each test does)

| Stage | Plain English | Pass means |
|-------|---------------|------------|
| **s04-knowledge** | “Do we have the research inputs?” | manifest, video-script, handoff, beat-map, segment scripts exist |
| **s06-coverage** | “Does each beat have enough visuals for its script?” | No critical asset gaps; hook montage plan valid |
| **s01-assets** | “Are handoff files on disk and readable?” | Images/videos resolve; beat-map paths exist |
| **s02-source-vlm** | “Do source B-roll clips look on-topic?” (optional) | VLM samples every 5s; flags generic/stock footage |
| **s00-bookends** | “Are hook and outro ready to merge?” | script + narration + `heygen.mp4` for 00-hook and 99-outro |
| **s05-transcript** | “Does audio match the locked script?” | **post_vo:** MP3 exists; **post_captions:** SRT matches script + overlap checks |
| **s03-image-speech** | “Does each spoken line show the right image?” | Display sync: ≥35% keyword alignment per cue |
| **s08-av-sync** | “Is the timeline coherent?” | Hook structure, word-level match (hook/outro), section durations vs `timeline.json` |
| **s07-framing** | “Are HeyGen clips the expected resolution?” | Hook/outro dimensions (warn-only) |
| **s09-on-screen-text** | “Any long cues with weak visual match?” | Flags cues with ≥6 words and low alignment |
| **s10-final-composite** | “Production gate” | Visual audit 5s samples + sync×3 + validate-all |

Full stage config: [Video QA](video-qa.md).

### Degradation (warn, not fail)

Some environments cannot run every check. The suite records flags in `summary.json`:

| Flag | Cause | Behaviour |
|------|-------|-----------|
| `whisper: missing_timestamps` | Whisper/transcribe failed for beat segments | Proportional captions used; s05 passes with warnings |
| `vlm: offline` | No `OPENAI_API_KEY` | s02 skipped |
| `final_mp4: missing` | No `merge/final.mp4` | post_build visual stages skipped |

Set `PRAISONAIPPT_QA_OFFLINE=1` in CI to skip API-dependent stages.

---

## Layer 3 — Legacy publish gates

These pre-date the modular `video_qa` package but remain the **authoritative publish bar**. Stage **s10** runs them automatically; you can also run them standalone.

### `validate-display`

Maps every SRT cue to the visual shown at the cue midpoint.

| Check | Threshold |
|-------|-----------|
| Keyword alignment | ≥ **0.35** per cue |
| Borderline band | 0.35–0.45 (passes but worth spot-check) |

**Output:** `merge/display_sync_report.json`

```bash
daily-single -p $PROJECT validate-display
```

### `validate-sync --runs 3`

Runs the full spoken↔visual suite **three times** and requires identical results (idempotency).

| Sub-check | What it does |
|-----------|--------------|
| `caption_script_lock` | SRT text equals locked `script.md` — not raw Whisper text |
| `hook_structure` | Cues 1–3 = attention → overview → “Let's get started.” |
| `hook_montage` | Overview cue uses ≥ **5** distinct hero slides; alignment ≥ **0.45** |
| `image_mapping` | Same as display sync pass rate |
| `youtube_quality` | Hook stakes, plain language, pacing, outro CTA |
| `visual_audit` | Requires passing `visual_audit_report.json` |

**Output:** `merge/sync_validation_report.json`

```bash
daily-single -p $PROJECT validate-sync --runs 3
```

### `audit-visual`

Samples `merge/final.mp4` every **5 seconds** (plus cue midpoints). Compares frames to planned assets.

| Asset type | Min pixel similarity |
|------------|---------------------|
| PNG slides | 0.42 |
| Video clips | 0.28 |
| HeyGen / avatar | 0.15 |

Optional vision LLM (`gpt-4o-mini`) flags off-topic or generic B-roll.

**Output:** `merge/visual_audit_report.json`, frames in `merge/visual_audit_frames/`

```bash
daily-single -p $PROJECT audit-visual --interval 5
daily-single -p $PROJECT validate-visual-audit
```

### `validate-all`

Single publish gate combining tools, output specs, media inventory, and all reports above.

| Check | Rule |
|-------|------|
| Output | 1920×1080, duration ~280–540s |
| Beat coverage | All beats assembled |
| Bookends | HeyGen hook + outro present |
| Media | Videos ≥720p from handoff |
| Reports | display, sync, visual audit all pass |

**Output:** `validation_report.json` (project root)

```bash
daily-single -p $PROJECT validate-all
```

---

## Recommended test workflow (full rebuild)

Use this checklist when building a video step by step:

```bash
PROJECT=examples/videos/<slug>

# 1 — After scripts + handoff
daily-single -p $PROJECT validate-qa --when pre_build

# 2 — After voice-over
daily-single -p $PROJECT validate-qa --when post_vo

# 3 — After HeyGen bookends
daily-single -p $PROJECT validate-qa --when pre_assemble

# 4 — After assemble + captions (main gate)
daily-single -p $PROJECT validate-qa --when post_build

# 5 — Confirm legacy gates (optional if s10 passed)
daily-single -p $PROJECT validate-all
daily-single -p $PROJECT validate-sync --runs 3

# 6 — After code changes only
pytest tests/test_video_qa.py tests/test_daily_single_sync_validation.py -q
```

---

## Output files (where to look when something fails)

| File | Layer | Contains |
|------|-------|----------|
| `merge/qa/summary.json` | Modular QA | Overall pass/fail, `failed_required`, degradation |
| `merge/qa/s*_report.json` | Modular QA | Per-stage checks and messages |
| `merge/display_sync_report.json` | Legacy | Per-cue alignment and asset file |
| `merge/sync_validation_report.json` | Legacy | 3-run results, hook_montage, youtube_quality |
| `merge/visual_audit_report.json` | Legacy | Per-sample pixel/topic pass |
| `validation_report.json` | Legacy | Final publish gate issues list |

---

## Related

- [Daily single video pipeline](daily-single-video.md)
- [Video QA stages](video-qa.md)
- [Commands — daily single](commands.md#daily-single-video-pipeline)
- [Pipeline overview](pipeline-overview.md)

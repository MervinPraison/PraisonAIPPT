# Segment video roundup — reference

## Handoff inputs (create-news research dir)

| File | Required | Contents |
|------|----------|----------|
| `review-data.json` | **Yes** | `topics[]` with `topic_slug`, `title`, `prose_html`, `images[]` (vision scores) |
| `review-assets/{topic_slug}/` | **Yes** | Hero PNG/JPG/WebP files referenced in `images[]` |
| `video-handoff.json` | Optional | Asset manifest; no narration — scripts must be written |
| `review-report.md` | Optional | Editorial hero picks, marginal asset notes |

### `review-data.json` image fields (used by sync-media)

```json
{
  "filename": "79a28adee136.png",
  "topic_relevance_score": 0.9,
  "topic_relevance_label": "relevant",
  "asset_type": "architecture_diagram",
  "vision_description": "...",
  "relevance_reason": "...",
  "editorial_rank": 1
}
```

### `video-handoff.json`

Asset-only. Does **not** include scripts, timings, or slide YAML. Derive segment order from editorial priority in review report or topic list.

---

## Environment (repo `.env`)

```bash
ELEVEN_API_KEY=<secret>
HEYGEN_API_KEY=<secret>
ELEVEN_VOICE_ID=lJwraGf9dHERkgZPWTyE
AVATAR_ID=78b7d68884634fbdb84c965e4a9d7dee
# MER_HEYGEN_VERTICAL intentionally unset — landscape 1280×720
```

Never commit `.env`. Template: `.env.example`.

---

## manifest.json schema

```json
{
  "schema_version": 1,
  "megapost_slug": "june-2026-ai-engineering-roundup",
  "post_id": 51661,
  "post_url": "https://mer.vin/?p=51661",
  "research_dir": "/absolute/path/to/research/...",
  "review_assets_dir": "/absolute/path/to/research/.../review-assets",
  "target_duration_sec": 600,
  "pipeline_status": "pending|completed",
  "final_video": {
    "path": "merge/final-roundup.mp4",
    "duration_sec": 362.0,
    "captions": "merge/final-roundup.srt",
    "wordpress_attachment_id": null,
    "wordpress_url": null
  },
  "segments": [
    {
      "index": 0,
      "dir": "00-hook",
      "slug": "hook",
      "title": "...",
      "slide_type": "big_number|avatar_media_3|deck_thank_you",
      "headline": "...",
      "subheader": "...",
      "target_words": 62,
      "target_sec": 22,
      "hero_image": null,
      "status": "pending|completed",
      "media_cues": []
    }
  ]
}
```

`media_cues` populated by `sync_media_assets.py` after Phase 4.

---

## Project directory layout

```
examples/<slug>-roundup/
  manifest.json
  media_assets.json
  media_validation.json
  PROTOCOL.md
  slide_images/           # shared hero PNGs
  segments/
    00-hook/
      script.md
      narration.mp3
      heygen.mp4
      timestamps.json
      segment.yaml
      segment.pptx
      segment.mp4
      segment.srt
      slide_jpegs/        # per-deck JPEG exports + golden/
    01-<topic>/
    ...
    16-outro/
  merge/
    concat-video.txt
    final-roundup.mp4
    final-roundup.srt
  loudness_report.json    # normalize-audio before/after LUFS metrics
  validation_report.json
  scripts/
    pipeline.py
    config/protocol.json
    config/base_style.yaml
    sdk/
    sync_media_assets.py
    validate_media.py
    build_segment_yaml.py
    build_segment_mp4.sh
    run_segment_media.py
    merge_segments.py
    write_scripts.py
    seed_golden_slides.sh
    fix_slide_jpeg_paths.sh
```

---

## Image selection thresholds (`protocol.json`)

| Key | Default | Meaning |
|-----|---------|---------|
| `min_topic_relevance` | 0.7 | Minimum `topic_relevance_score` |
| `min_script_alignment` | 0.35 | Script vs vision text overlap score |
| `max_cues_per_segment` | 4 | Max hero images per segment |
| `multi_cue_requires_sentences` | 1 | Min script sentences to attempt multi-cue |

**Multi-image timing:** `align-cues` matches each cue fragment to Whisper → `cue_timings.json` → `build_segment_yaml.py` → verses with `audio_start_sec` / `duration_sec`. Use `avatar_timeline: continuous` when 2+ cues.

### Audit overrides (`sync_media_assets.py`)

`CUE_IMAGE_OVERRIDES` maps `topic_slug` → `{sentence_index: source_filename}` for picks already in handoff but mis-ranked by vision scores. After editing, run `sync-media` → rebuild chain.

`fill_missing_sentence_cues` reuses hero for uncovered sentences (downstream stopgap; not a handoff fix).

---

## cue_timings.json

Written by `align-cues` stage (`praisonaippt/segment_video/stages/align_cues.py`):

```json
{
  "schema_version": 1,
  "transcript_path": "timestamps.json",
  "cues": [
    {
      "cue_index": 0,
      "audio_start_sec": 0.0,
      "duration_sec": 7.27,
      "script_fragment": "...",
      "file": "bedrock.png",
      "match_method": "whisper"
    }
  ]
}
```

Hook montage uses `montage_weighted`; first cue often starts after **"roundup:"** (~2.44 s).

---

## Gap taxonomy

| Type | Owner | This skill |
|------|-------|------------|
| `handoff_uncrawled` | create-news crawl | Skip unless user asks |
| `insufficient_pool` | handoff + editorial | Hero reuse or wait for handoff |
| `selection_gap` | sync-media / overrides | Fix in `sync_media_assets.py` |
| `segment_sync` | align → yaml → build | **Fix here** |
| `hook:duration_drift` | hook lead-in + rebuild | **Fix here** |
| `image_audit` | sync-media + rebuild | **Fix here** |
| `caption↔slide` | verses SRT + timeline | **Fix here** |
| `volume_inconsistency` | normalize-audio + merge | **Fix here** |
| `not_hd` / wrong resolution | `video_export.preset: high` + rebuild | **Fix here** |

---

## validate-all validators

| ID | Required | Notes |
|----|----------|-------|
| `hook_montage` | yes | 15 montage cues; duration vs HeyGen |
| `segment_sync` | yes | cue_timings = yaml verses = media cues |
| `audio_loudness` | yes | Per-segment LUFS; spread ≤ max_spread_lufs |
| `display_sync` | yes | Per-segment caption/slide/speech |
| `image_audit` | yes | Alignment + recommend_swap |
| `required_assets` | yes | Often fails on handoff — ignore if display passes |
| `merge_output` | yes | Final MP4 exists |

Reports live in project root: `validation_report.json`, `loudness_report.json`, `asset_gaps_report.json`, `image_audit_report.json`, `display_validation_report.json`, `hook_validation_report.json`.

### audio_loudness config (`protocol.json`)

```json
"audio_loudness": {
  "target_lufs": -16.0,
  "true_peak_db": -1.5,
  "lra": 11,
  "max_spread_lufs": 2.0,
  "tolerance_lufs": 1.0,
  "skip_if_within_lufs": 0.5,
  "normalize_before_merge": true
}
```

Stage **`normalize-audio`** runs after `build`, before `merge`. Uses ffmpeg two-pass EBU R128 `loudnorm` on each `segments/*/segment.mp4` (video copy, AAC re-encode). Writes `loudness_report.json` with before/after metrics.

Crossfade overlap dips ~3–6 dB momentarily — gate on **pre-merge** segment levels, not merge overlap windows.

Measure only: `zsh .cursor/skills/segment-video-roundup/scripts/gap-audit.sh examples/<project>` (loudness + HD sections).

---

## Video resolution (HD)

Deliverable standard: **Full HD 1920×1080 @ 30 fps, 16:9, H.264 + AAC**.

| Layer | Resolution | Set in |
|-------|------------|--------|
| HeyGen avatar (`heygen.mp4`) | 1280×720 @ 60fps | `run_segment_media.py` → `"dimension": {"width": 1280, "height": 720}` |
| Compositor output (`segment.mp4`) | **1920×1080 @ 30fps** | Deck `video_export.preset: high` (via `base_style.yaml` / `build_segment_yaml.py`) |
| Final merge (`final-roundup.mp4`) | Same as segments | `merge` — crossfade only, **no scale filter** |

Presets (`praisonaippt/video_presets.py`): `draft` = 720p, `standard`/`high` = 1080p, `4k` = 2160p.

### Verify HD

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,codec_name \
  -of csv=p=0 merge/final-roundup.mp4
# Expected: h264,1920,1080,30/1
```

Or use gap-audit (checks all segments + final).

### Fix non-HD output

1. Ensure `video_export.preset: high` (or explicit `resolution: {width: 1920, height: 1080}`) in base style / segment YAML.
2. Rebuild: `build_segment_yaml.py` → `build --force` → `normalize-audio` → `merge`.
3. **Merge alone cannot upscale** — segments must already be 1080p.

For **native 1080p HeyGen** (sharper avatar, not upscaled 720p): change HeyGen dimensions in `run_segment_media.py`, regenerate all `heygen.mp4` (`media` stage), then full align → yaml → build chain.

---

## 50590 template parity

From `examples/heygen-50590-video-audio-heygen-images.yaml`:

| Field | Value |
|-------|-------|
| `slide_size` | widescreen |
| `skip_title_slide` | true |
| `slide_qa.expect_pip` | true |
| `slide_qa.min_hero_coverage_ratio` | 0.58 |
| `pipeline.validate_pip` | true |
| `hero_text_placement.auto` | true, `preferred_anchor: bottom_right` |
| `avatar_media_3` | `hero_layout: full_bleed`, `text_style: semi_panel` |
| `video_export.backend` | compositor |
| `video_export.audio_source` | heygen_video |
| `video_export.narration_mode` | avatar |
| `video_export.preset` | high (1920×1080 @ 30fps) |
| `video_export.captions.enabled` | true |
| `transitions.default` | none |

**50590 vs per-segment:** 50590 uses **one** HeyGen file + `continuous` across 7 verses. Roundup uses **one HeyGen per segment**; multi-cue segments use `continuous` **within** that segment only.

---

## ElevenLabs API (per segment)

```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
Model: eleven_multilingual_v2
Header: xi-api-key
Output: narration.mp3
```

## HeyGen API (per segment)

```
POST upload.heygen.com/v1/asset          # narration.mp3
POST api.heygen.com/v2/video/generate    # avatar + audio voice
GET  api.heygen.com/v1/video_status.get  # poll until completed
dimension: 1280×720, background #008000
```

---

## mer.vin publish checklist

- [ ] Section title: **Short video walkthrough** (not announcement clip)
- [ ] Insert before **At a glance** if present
- [ ] Gutenberg `wp:video {"id":N}` — not bare `<video>`
- [ ] `praisonaiwp update` with `--no-block-conversion`
- [ ] `curl -sI` attachment URL → 200
- [ ] Do not confuse with `_mer_heygen_video_attachment_id` (Shorts CPT meta)

---

## Common failures

| Symptom | Fix |
|---------|-----|
| WebP in PPTX build | `sync_media_assets.py` normalises to PNG |
| JPEGs in wrong nested path | `pipeline.py fix-jpegs` |
| `slide_jpegs` golden fail | `pipeline.py seed-golden` after build |
| `cue_timings count != media cues` | `align-cues --force SEG` → `build_segment_yaml.py SEG` → `build --force` |
| Hook HeyGen longer than segment.mp4 | Rebuild hook with lead-in verse; `align-cues` → `yaml` → `build --force 00-hook` |
| Caption↔slide FAIL after multi-cue | Ensure SRT from verses when counts differ (`write_verses_srt`) |
| `timing_drift` multi-cue | Regenerate via align-cues → yaml → build |
| Wrong image on slide | `CUE_IMAGE_OVERRIDES` + sync-media + rebuild |
| Uneven volume across segments | `normalize-audio --force` → `merge`; check `loudness_report.json` |
| Final video 720p not 1080p | `video_export.preset: high` → yaml → `build --force` → `normalize-audio` → `merge` |
| Corrupt `wp:video` JSON on update | Use HEREDOC/file; verify `{"id":N}` intact |
| HeyGen vertical | Keep `MER_HEYGEN_VERTICAL` unset |

---

## Interactive Studio

Local-only dashboard (`127.0.0.1` — never expose publicly).

```bash
cd examples/<project>
segment-video studio
# or: python -m praisonaippt.segment_video.studio --project .
```

| Setting | Source |
|---------|--------|
| Port | `scripts/config/protocol.json` → `studio.port` (default 8765) |
| State / jobs | `.segment-video/state.json` |

### HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/project` | manifest + protocol + status |
| GET | `/api/segments` | all segments + scripts |
| PATCH | `/api/segments/{dir}/script` | save `script.md` |
| POST | `/api/run` | run stage (async job, poll `/api/jobs/{id}`) |
| POST | `/api/regenerate` | `change` + `segment` (async) |
| POST | `/api/protocol/merge-transitions` | save crossfade settings |
| GET | `/assets/**` | segment MP4, slide JPEGs, merge output |

### Regenerate chains (`REGENERATE_CHAINS`)

| `change` | Stages |
|----------|--------|
| `script` / `audio` | media → yaml → build → normalize-audio → merge |
| `hero` | sync-media → yaml → build → normalize-audio → merge |
| `deck` | build → normalize-audio → merge |
| `full_segment` | media → yaml → build → fix-jpegs → seed-golden → normalize-audio → merge |
| `transitions` / `merge_only` | merge |
| `publish` | publish (upload + wp:video URL swap + manifest update) |

CLI alias: `segment-video regenerate --change script --segment DIR` (same as Studio **Regenerate script**).

---

## Optional master-deck polish

If per-segment lip-sync joins are jarring:

1. Concat all `script.md` → `merge/full-script.md`
2. One ElevenLabs MP3 + one HeyGen MP4
3. Single 17-verse master YAML, `avatar_timeline: continuous`, wall-clock `audio_start_sec` per verse
4. One `praisonaippt --convert-video` — replaces concat output

Use per-segment work for content QA; master pass for lip-sync quality only.

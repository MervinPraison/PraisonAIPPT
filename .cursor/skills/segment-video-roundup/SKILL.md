---
name: segment-video-roundup
description: Builds per-segment HeyGen + ElevenLabs roundup videos from research handoff (video-handoff.json, review-data.json), PraisonAIPPT avatar_media_3 decks (50590 pattern), ffmpeg merge, and mer.vin publish. Use for megapost video walkthroughs, segment video pipeline, roundup handoff, ElevenLabs TTS, HeyGen lip-sync, manifest.json segments, or re-running with new handoff data.
---

# Segment video roundup pipeline

Per-segment production (hook + N topics + outro) → compositor MP4 per segment → ffmpeg concat → **Short video walkthrough** on mer.vin.

**Reference implementation:** `examples/june-2026-ai-roundup/`  
**Deck template:** `examples/heygen-50590-video-audio-heygen-images.yaml`  
**Publish:** `.cursor/skills/mer-vin-article-video-upload/SKILL.md`  
**YAML QA:** `.cursor/skills/ppt-yaml-deck-workflow/SKILL.md`

---

## When to use

| Scenario | Action |
|----------|--------|
| New handoff (research dir + post ID) | Phase 0 → full pipeline |
| Scripts only refresh | Phase 2 → stop for review before TTS spend |
| Media exists; rebuild decks | Phases 4–6 with `--skip-existing` / `--force` |
| Replace final video on mer.vin | Phase 8 only |

**Do not regenerate ElevenLabs/HeyGen** when `narration.mp3` and `heygen.mp4` already exist unless the user explicitly asks.

---

## Prerequisites

```text
- [ ] Mac with ffprobe, ffmpeg, praisonaippt (conda env: test or windsurf)
- [ ] praisonaiwp configured: praisonaiwp doctor --server default
- [ ] Repo .env (gitignored): ELEVEN_API_KEY, HEYGEN_API_KEY, ELEVEN_VOICE_ID, AVATAR_ID
- [ ] MER_HEYGEN_VERTICAL unset → landscape 1280×720 HeyGen, 1920×1080 compositor
- [ ] Research handoff dir with review-data.json + review-assets/ (+ video-handoff.json optional)
```

Copy `.env.example` → `.env` at repo root. See [reference.md](reference.md) for env defaults.

---

## Phase 0 — Bootstrap project from handoff

Run when starting a **new** roundup (not June 2026):

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  "my-roundup-slug" \
  "/path/to/research/my-roundup" \
  POST_ID
```

Or manually:

1. Copy `examples/june-2026-ai-roundup/` → `examples/<slug>-roundup/`
2. Edit `manifest.json`: `megapost_slug`, `post_id`, `research_dir`, `review_assets_dir`, `segments[]`
3. Reset `segments/*/`, `merge/`, `media_assets.json`; keep `scripts/`, `scripts/config/`, `scripts/sdk/`
4. Derive segment list from `video-handoff.json` + editorial hero picks (see [reference.md](reference.md))

**Segment count:** typically `hook` + one segment per topic + `outro` (e.g. 17 for 15 topics).

---

## Phase 1 — Manifest

```text
Task Progress:
- [ ] manifest.json lists every segment (index, dir, slug, slide_type, headline, subheader, target_words, target_sec, hero_image)
- [ ] hook → slide_type big_number; topics → avatar_media_3; outro → deck_thank_you
- [ ] research_dir and review_assets_dir are absolute paths on Mac
```

Validate segment dirs exist: `segments/00-hook/` … `segments/NN-outro/`.

---

## Phase 2 — Segment scripts

Write tight narration (~1,350–1,450 words total, under 10 min):

| Segment | Target |
|---------|--------|
| hook | ~55–65 words, 20–25 s |
| each topic | ~80–95 words, 33–38 s |
| outro | ~40–50 words, 15–20 s |

Template per topic:

```text
{Product} — {concrete fact with number/name}.
{Why engineers care — deploy path or benchmark}.
{Try it via HF / Bedrock / Foundry / CLI / watch}.
```

```bash
cd examples/<project>/scripts
# Edit segment_scripts.json or write segments/{dir}/script.md directly
python3 write_scripts.py
```

**Gate:** User review scripts before Phase 3 (TTS costs money).

---

## Phase 3 — ElevenLabs + HeyGen (per segment)

Replicates mer.vin mu-plugins (`mer-short-audio-elevenlabs`, `mer-short-heygen-after-audio`):

```bash
cd examples/<project>/scripts
python3 run_segment_media.py --skip-existing
# One segment only:
python3 run_segment_media.py --skip-existing 01-nvidia-nemotron-3-ultra
```

Outputs per segment:

| File | Source |
|------|--------|
| `narration.mp3` | ElevenLabs `eleven_multilingual_v2` |
| `heygen.mp4` | HeyGen 1280×720, avatar + audio lip-sync, green `#008000` background |
| `timestamps.json` | `praisonaippt transcribe` or ffprobe fallback |

Log `narration_duration_sec` in manifest after each segment.

---

## Phase 4 — Image selection (validated)

Hero images come from **review-data.json**, not arbitrary picks.

```bash
python3 pipeline.py sync-media      # → media_assets.json + slide_images/*
python3 pipeline.py validate-media  # script_alignment gate (≥ 0.35)
```

Protocol:

1. Score `topics[].images[]` against `script.md` (`vision_description`, `topic_relevance_score`)
2. Copy best image(s) to `slide_images/` (WebP → PNG via ffmpeg)
3. **Multi-image:** ≥2 sentences + ≥2 relevant images → 2 `media_cues` → 2 verses, one `heygen.mp4`, `avatar_timeline: continuous` (50590 pattern)

See [reference.md](reference.md) for thresholds in `scripts/config/protocol.json`.

---

## Phase 5 — Segment YAML (50590 parity)

```bash
python3 pipeline.py yaml
```

Each `segments/{dir}/segment.yaml` must include:

- `slide_qa.expect_pip`, `min_hero_coverage_ratio: 0.58`
- `pipeline.validate_pip`, `validate_slide_qa`, `transcript_path: timestamps.json`
- `hero_text_placement.auto`, `avatar_calibration` (hybrid)
- `avatar_media_3` + `text_panel.anchor: auto` + `../../slide_images/{hero}`
- `video_export`: compositor, `audio_source: heygen_video`, captions on
- Single cue → `avatar_timeline: per_slide`; multi-cue → `continuous` + `slide_timestamps`

Paths are **relative to segment.yaml** (`heygen.mp4`, `slide_jpegs/`, `../../slide_images/`).

---

## Phase 6 — Build segment MP4s

```bash
python3 pipeline.py build                    # skip existing segment.mp4
python3 pipeline.py build --force 01-...     # rebuild one segment
zsh build_segment_mp4.sh --force 01-...      # direct
```

Per segment:

```bash
praisonaippt hero-panel-place -i segment.yaml --force
praisonaippt -i segment.yaml -o segment.pptx --convert-video --video-output segment.mp4
praisonaippt validate-deck -i segment.yaml
```

Post-build QA helpers:

```bash
python3 pipeline.py fix-jpegs    # relocate mis-placed slide JPEGs
python3 pipeline.py seed-golden  # golden MD5 for validate-deck slide_jpegs
```

**Per-segment gates:**

- [ ] `ffprobe` duration ±3 s of target
- [ ] `validate-deck` passes (timing, PiP, assets)
- [ ] `segment.srt` matches script

Set `auto_upload_gdrive: false` in generated YAML (project default in `base_style.yaml`).

---

## Phase 7 — Merge (crossfade between topics)

```bash
python3 pipeline.py merge
# or: segment-video -p . run merge
```

Produces:

- `merge/final-roundup.mp4` — must be **< 600 s** (~357 s with 17 segments + 0.30 s crossfade)
- `merge/final-roundup.srt` — offset-merged captions (`effective_timeline_sec`)
- `merge/concat-video.txt`

**Transitions** (`scripts/config/protocol.json`):

```json
"merge_transitions": {"default": "crossfade", "duration_sec": 0.30}
```

Hard cut: `segment-video run merge --no-transitions` or Studio → transition **none**.

---

## Interactive Studio

Local dashboard for segment status, script edit, preview, and regenerate:

```bash
cd examples/<project>
segment-video studio
# → http://127.0.0.1:8765 (127.0.0.1 only — do not expose publicly)
```

| Studio action | API / SDK chain |
|---------------|-----------------|
| Save script | `PATCH /api/segments/{dir}/script` |
| Regenerate audio | `change: audio` → media → yaml → build → merge |
| Rebuild deck | `change: deck` → build → merge |
| Regenerate segment | `change: full_segment` |
| Re-merge | `POST /api/run` stage `merge` |
| Publish | stage `publish` |

SDK package: `praisonaippt/segment_video/` (`PipelineEngine`, `REGENERATE_CHAINS`).

---

## Phase 8 — Publish to mer.vin

Read and follow **mer-vin-article-video-upload** skill.

```bash
praisonaiwp media upload examples/<project>/merge/final-roundup.mp4 \
  --post-id=POST_ID --server default
praisonaiwp media url ATTACHMENT_ID --server default
```

Insert **before** `At a glance`:

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">Short video walkthrough</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>One-line intro matching video length.</p>
<!-- /wp:paragraph -->

<!-- wp:video {"id":ATTACHMENT_ID} -->
<figure class="wp-block-video"><video controls src="ATTACHMENT_URL"></video></figure>
<!-- /wp:video -->
```

```bash
praisonaiwp update POST_ID --no-block-conversion --server default \
  --post-content "$(cat article-with-video.html)"
```

**Verify:**

```bash
curl -sI "ATTACHMENT_URL" | head -1    # HTTP 200
ffprobe merge/final-roundup.mp4        # duration < 600
```

Update `manifest.json` → `final_video.wordpress_attachment_id` and URL.

---

## Phase 9 — Full validation

```bash
cd examples/<project>/scripts
python3 pipeline.py status
python3 pipeline.py validate
praisonaiwp doctor --server default
praisonaippt validate-deck -i ../../heygen-50590-video-audio-heygen-images.yaml
praisonaiwp validate-deck -i ../segments/01-.../segment.yaml
```

Cross-skills:

| Skill | Gate |
|-------|------|
| ppt-yaml-deck-workflow | validate-deck per segment |
| mer-vin-article-video-upload | wp:video + HTTP 200 |
| gpt-image | N/A unless generating new hero art |

---

## Re-run with new handoff

1. **New research dir / topics:** Phase 0 → update manifest segments → Phase 2 scripts  
2. **Keep media, new heroes:** Phase 4 sync-media → Phase 5 yaml → Phase 6 build `--force` affected → Phase 7 merge → Phase 8  
3. **Optional polish:** Single continuous HeyGen + 17-slide master YAML (`avatar_timeline: continuous` on one file) — only if per-segment joins look jarring; requires new full-script TTS/HeyGen  

Copy `scripts/`, `scripts/sdk/`, `scripts/config/` unchanged; only replace project-specific `manifest.json`, `segment_scripts.json`, and `segments/`.

---

## CLI quick reference

```bash
cd examples/<project>
segment-video -p . status
segment-video -p . run sync-media
segment-video -p . run validate-media
segment-video -p . run yaml
segment-video -p . run build --force 01-nvidia-nemotron-3-ultra
segment-video -p . run merge
segment-video -p . regenerate --change script --segment 01-nvidia-nemotron-3-ultra
segment-video -p . studio
segment-video -p . validate

# Legacy shim (same engine):
cd scripts && python3 pipeline.py status && python3 pipeline.py merge
python3 run_segment_media.py --skip-existing
```

### Per-part modification

| What you change | Command |
|-----------------|---------|
| Script | `regenerate --change script --segment DIR` |
| Hero | `regenerate --change hero --segment DIR` |
| Deck | `regenerate --change deck --segment DIR` |
| Transitions only | `run merge` (edit `merge_transitions` first) |
| Publish | `run publish` |

---

## Additional resources

- Handoff inputs, manifest schema, env: [reference.md](reference.md)
- June 2026 worked example: [examples.md](examples.md)
- In-repo protocol: `examples/june-2026-ai-roundup/PROTOCOL.md`

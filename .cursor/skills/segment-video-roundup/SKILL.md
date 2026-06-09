---
name: segment-video-roundup
description: Builds per-segment HeyGen + ElevenLabs roundup videos from research handoff, PraisonAIPPT avatar_media_3 decks (50590 pattern), align-cues/yaml/build/normalize-audio/merge, validate-all (audio_loudness), HD 1080p compositor output, and mer.vin publish. Use for megapost video walkthroughs, segment video pipeline, roundup handoff, sync-media, align-cues, gap remediation, hook montage, loudness normalisation, image audit fixes, manifest.json segments, or re-running after handoff updates.
---

# Segment video roundup pipeline

Per-segment production (hook + N topics + outro) → compositor MP4 per segment → ffmpeg concat → **Short video walkthrough** on mer.vin.

**Reference:** `examples/videos/june-2026-ai-roundup/`  
**Deck template:** `examples/heygen-50590-video-audio-heygen-images.yaml`  
**Publish:** `.cursor/skills/mer-vin-article-video-upload/SKILL.md`  
**YAML QA:** `.cursor/skills/ppt-yaml-deck-workflow/SKILL.md`  
**SDK:** `praisonaippt/segment_video/`

---

## When to use

| Scenario | Action |
|----------|--------|
| New handoff (research dir + post ID) | Phase 0 → full pipeline |
| Scripts only refresh | Phase 2 → stop before TTS |
| Handoff assets updated (create-news) | Phase 4 only — **do not** re-run media unless user asks |
| Media exists; rebuild decks | Phases 5–7 with correct **align → yaml → build** order |
| Image pick / sync / caption gaps | Gap audit → downstream fixes → rebuild affected segments |
| Uneven volume / loudness check | `normalize-audio` → `merge`; gap-audit loudness section |
| Verify HD output | ffprobe final + segments (expect 1920×1080); see Phase 7 |
| Replace final video on mer.vin | Phase 8 only |

**Do not regenerate ElevenLabs/HeyGen** when `narration.mp3` and `heygen.mp4` exist unless the user explicitly asks.

**Handoff crawl / review-data enrichment** is owned by the create-news agent. This skill fixes **downstream** pipeline gaps only unless the user asks you to touch handoff files.

---

## Prerequisites

```text
- [ ] Mac: ffprobe, ffmpeg, praisonaippt (conda: test or windsurf)
- [ ] praisonaiwp: praisonaiwp doctor --server default
- [ ] Repo .env: ELEVEN_API_KEY, HEYGEN_API_KEY, ELEVEN_VOICE_ID, AVATAR_ID
- [ ] MER_HEYGEN_VERTICAL unset → landscape HeyGen 1280×720, compositor 1920×1080
- [ ] research_dir with review-data.json + review-assets/
```

See [reference.md](reference.md) for env defaults and manifest schema.

---

## Protocol stages (order matters)

Defined in `scripts/config/protocol.json`. **Critical rule:** after `sync-media` adds or changes cue count, always run **align-cues before yaml**. Running `yaml` alone leaves stale single-verse decks.

```bash
cd examples/videos/<project>/scripts
PROJECT=../  # project root
```

| Stage | Scope | Purpose |
|-------|-------|---------|
| `catalogue-media` | project | Index handoff images |
| `crawl-missing-assets` | project | **Emergency only** — patches create-news handoff; normal flow = create-news crawl |
| `sync-media` | project | `media_assets.json` + `slide_images/*` |
| `validate-assets` | project | `asset_gaps_report.json` |
| `validate-media` | project | Script alignment gate |
| `audit-images` | project | `image_audit_report.json` |
| `media` | segment | ElevenLabs + HeyGen + timestamps |
| **`align-cues`** | segment | **`cue_timings.json`** from Whisper + media cues |
| **`yaml`** | segment | **`segment.yaml`** verses from cue_timings |
| `build` | segment | `segment.mp4`, `segment.srt`, slide JPEGs |
| **`normalize-audio`** | project | EBU R128 loudnorm each `segment.mp4` → `loudness_report.json` |
| `merge` | project | `merge/final-roundup.mp4` |
| `validate-all` | project | Full validator suite (includes `audio_loudness`) |

---

## Phase 0 — Bootstrap

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  "my-roundup-slug" "/path/to/research/my-roundup" POST_ID
```

Or copy `examples/videos/june-2026-ai-roundup/` → `examples/videos/<slug>-roundup/`, edit `manifest.json`, reset `segments/*/`, `merge/`, `media_assets.json`.

---

## Phase 2 — Scripts

| Segment | Target |
|---------|--------|
| hook | ~55–65 words, roll-call after "roundup:" |
| each topic | ~80–95 words, 3 sentences when multi-cue |
| outro | ~40–50 words |

```bash
python3 write_scripts.py
```

**Gate:** User review before Phase 3 (TTS cost).

---

## Phase 3 — ElevenLabs + HeyGen

```bash
python3 run_segment_media.py --skip-existing
python3 run_segment_media.py --skip-existing 01-nvidia-nemotron-3-ultra  # one segment
```

Outputs: `narration.mp3`, `heygen.mp4`, `timestamps.json`.

---

## Phase 4 — Media sync (image selection)

```bash
python3 pipeline.py run sync-media
python3 pipeline.py run validate-media --strict
python3 pipeline.py run validate-assets    # handoff pool report
python3 pipeline.py run audit-images
```

- Heroes from `review-data.json` via `praisonaippt.segment_video.image_selection`
- Multi-cue: one sentence → one image when pool allows (`max_cues_per_segment: 4`)
- Audit-driven fixes in `scripts/sync_media_assets.py`:
  - `CUE_IMAGE_OVERRIDES` — wrong rank, file already in handoff
  - `VISION_ENRICHMENTS` — stub handoff vision → alignment keywords (prefer fixing handoff instead)
  - `HERO_REUSE_ENRICHMENTS` — thin pools (1 image / 3 sentences)
  - Overrides run **twice** (before + after `fill_missing_sentence_cues`); recalc `script_alignment`
  - Hook montage: prepend `script_fragment` to vision text before alignment
- Sparse pools: hero reuse is downstream stopgap — **handoff should supply ≥1 relevant image per sentence**
- Zoom: edit `media_fit: cover` in `segment.yaml` **after yaml, before build** (yaml resets to `contain`)

**After sync-media changes cue count → Phase 5 align-cues is mandatory.**

See [reference.md — Handoff vs downstream gaps](reference.md#handoff-vs-downstream-gaps).

---

## Phase 5 — Align, YAML, build (mandatory order)

```bash
SEGS="01-nvidia-nemotron-3-ultra 05-aws-bedrock-gpt-5-5-codex-ga"  # space-separated dirs

python3 pipeline.py run align-cues --force $SEGS
python3 build_segment_yaml.py $SEGS          # NOT optional after align
python3 pipeline.py run build --force $SEGS
python3 pipeline.py run normalize-audio --force   # always project-wide, not $SEGS
python3 pipeline.py run merge --force
```

**Footgun:** `normalize-audio $SEGS` can write an empty `loudness_report.json` and skip rebuilt segments — always run **project-wide** before merge.

### Hook montage (`00-hook`)

- Montage starts after **"roundup:"** (~2.44 s); compositor needs a **lead-in verse** or MP4 truncates ~2.7 s vs HeyGen
- `build_segment_yaml.py` prepends intro slide when first cue `audio_start_sec > 0`
- When `len(verses) != len(cue_timings)`: SRT from verses (`write_verses_srt`), not cue_timings alone
- Rebuild hook: `align-cues` → `yaml` → `build --force 00-hook` → `normalize-audio` → `merge`

### Multi-cue topic segments

- `media_assets.json` cues must match `cue_timings.json` count and `segment.yaml` verse count
- `avatar_timeline: continuous` + `slide_timestamps` for 2+ cues (50590 pattern within segment)

### Per-segment build internals

```bash
praisonaippt hero-panel-place -i segment.yaml --force
praisonaippt -i segment.yaml -o segment.pptx --convert-video --video-output segment.mp4
```

Post-build: `fix-jpegs`, `seed-golden` if validate-deck golden fails.

---

## Phase 6 — Merge

```bash
python3 pipeline.py run normalize-audio          # loudnorm segments before merge
python3 pipeline.py run normalize-audio --force  # re-normalise even if near target
python3 pipeline.py run merge
# Hard cut: segment-video run merge --no-transitions
```

Outputs:

- `merge/final-roundup.mp4` — **1920×1080 @ 30fps** (Full HD); verify with user before publish
- `merge/final-roundup.srt`
- `merge/timeline.json`

**Resolution chain:** HeyGen `1280×720` → compositor build → `segment.mp4` `1920×1080` → merge (no rescale). Merge alone cannot fix resolution — rebuild segments if not 1080p. See [reference.md](reference.md#video-resolution-hd).

---

## Phase 7 — Validation (run after every rebuild)

```bash
python3 pipeline.py status
python3 pipeline.py validate-all
python3 pipeline.py run validate-display
python3 pipeline.py run validate-hook
```

Or use the gap audit script:

```bash
zsh .cursor/skills/segment-video-roundup/scripts/gap-audit.sh examples/videos/<project>
```

### validate-all gates (downstream focus)

| Validator | Pass means |
|-----------|------------|
| `hook_montage` | 15/15 montage cues; HeyGen vs segment.mp4 drift ≤ ~1 s |
| `segment_sync` | `cue_timings` = yaml verses = media cue count |
| `audio_loudness` | All `segment.mp4` within ±1 LUFS of target (-16); spread ≤ 2 LUFS |
| `display_sync` | Per-segment caption↔slide↔speech (catalogue may fail on handoff) |
| `image_audit` | Script↔image alignment; fix via sync-media overrides + rebuild |
| `merge_output` | Final MP4 + SRT exist |

### HD verification (ffprobe)

Expected deliverable: **1920×1080, 30 fps, H.264 + AAC** on every `segment.mp4` and `merge/final-roundup.mp4`.

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate \
  -of csv=p=0 merge/final-roundup.mp4
# Expected: 1920,1080,30/1

for f in segments/*/segment.mp4; do
  echo "$f: $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$f")"
done
```

If output is 720p: set `video_export.preset: high` in deck/base style → `build_segment_yaml.py` → `build --force` → `normalize-audio` → `merge`. Native 1080p HeyGen (not upscaled 720p) requires changing `run_segment_media.py` dimensions and regenerating all `heygen.mp4`.

Ignore for downstream-only work: `handoff_uncrawled`, `insufficient_pool`, `manual_asset_gaps` (handoff agent).

Reports: `validation_report.json`, `loudness_report.json`, `image_audit_report.json`, `display_validation_report.json`, `hook_validation_report.json`.

---

## Multi-agent gap audit (recommended)

When user asks to verify or find gaps, launch **parallel explore agents** (not handoff crawl):

1. **Validation report** — read `validation_report.json`; list downstream failures only
2. **Segment sync** — compare `cue_timings.json` vs yaml verses vs `slide_jpegs/` vs heygen/segment duration drift
3. **Hook + image audit** — `hook_validation_report.json`, `image_audit_report.json` swap recommendations
4. **Loudness** — read `loudness_report.json` or gap-audit loudness section; spread should be ≤ 2 LUFS post-normalise
5. **HD resolution** — ffprobe final + sample segments; expect 1920×1080 @ 30fps on all `segment.mp4`

Fix order:

```text
sync-media (if picks wrong) → align-cues → build_segment_yaml.py → build --force → normalize-audio → merge → validate-all
```

Do **not** block on handoff catalogue failures if per-segment display_sync passes.

---

## Phase 8 — Publish

Follow **mer-vin-article-video-upload** skill.

```bash
praisonaiwp media upload examples/videos/<project>/merge/final-roundup.mp4 \
  --post-id=POST_ID --server default
```

Insert `wp:video` block before **At a glance**. Update `manifest.json` → `final_video`.

---

## Re-run cheat sheet

| Change | Commands |
|--------|----------|
| New handoff heroes only | `sync-media` → `align-cues` → `build_segment_yaml.py` → `build --force SEGS` → `normalize-audio` → `merge` |
| Script edit | `regenerate --change script --segment DIR` |
| Deck/visual only | `regenerate --change deck --segment DIR` |
| Wrong image pick | Edit `CUE_IMAGE_OVERRIDES` or handoff top_picks → `sync-media` → rebuild chain |
| Hook duration drift | `align-cues 00-hook` → `yaml` → `build --force 00-hook` → `normalize-audio` → `merge` |
| Uneven volume across segments | `normalize-audio --force` → `merge` → check `loudness_report.json` |
| Output not 1080p | `video_export.preset: high` → yaml → `build --force` → `normalize-audio` → `merge` |

Full downstream rebuild (no TTS/HeyGen):

```bash
cd examples/videos/<project>/scripts
python3 pipeline.py run sync-media
python3 pipeline.py run align-cues --force
python3 build_segment_yaml.py $(python3 -c "import json; m=json.load(open('../manifest.json')); print(' '.join(s['dir'] for s in m['segments'] if s.get('slide_type') in ('avatar_media_3','big_number')))")
python3 pipeline.py run build --force
python3 pipeline.py run normalize-audio --force
python3 pipeline.py run merge --force
python3 pipeline.py validate-all
```

---

## Studio & CLI

```bash
cd examples/videos/<project>
segment-video -p . studio
segment-video -p . regenerate --change deck --segment 01-nvidia-nemotron-3-ultra
cd scripts && python3 pipeline.py status
```

---

## Additional resources

- Handoff schema, thresholds, failures: [reference.md](reference.md)
- June 2026 worked commands: [examples.md](examples.md)
- Gap audit script: [scripts/gap-audit.sh](scripts/gap-audit.sh)
- In-repo protocol: `examples/videos/june-2026-ai-roundup/PROTOCOL.md`

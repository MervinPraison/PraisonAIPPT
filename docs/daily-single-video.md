---
layout: default
title: "Daily single video pipeline"
description: "YouTube-style single-topic videos from create-news handoff — hook montage, HD assets, captions, validation"
---

# Daily single video pipeline

Build ~5–9 minute YouTube walkthroughs from **create-news** research handoff: plain language, June-style hook/outro, script-locked captions, and multi-layer spoken↔visual validation.

**Pilot project:** `examples/videos/anthropic-claude-fable-5-mythos-5/`  
**June reference:** `examples/videos/june-2026-ai-roundup/`  
**Agent skill:** `.cursor/skills/daily-single-video/SKILL.md`

## Architecture

Two repos:

| Repo | Role |
|------|------|
| **praisonaippt** | Phase 1.5 ffmpeg pipeline (`praisonaippt/daily_single/`) |
| **create-news** | Upstream handoff: `research/<slug>/video-handoff.json`, beat-map, review-assets |

```bash
conda activate test
cd /path/to/praisonaippt
PROJECT=examples/videos/<slug>
python -m praisonaippt.daily_single --project $PROJECT <command>
```

**Do not use** `segment-video-roundup/scripts/bootstrap-project.sh` for daily_single projects.

---

## Standard pipeline order

Run in this order for every rebuild (repeat after script or handoff changes):

```bash
PROJECT=examples/videos/anthropic-claude-fable-5-mythos-5

python -m praisonaippt.daily_single --project $PROJECT sync-assets
python -m praisonaippt.daily_single --project $PROJECT synthesise-vo
python -m praisonaippt.daily_single --project $PROJECT bookend-media 00-hook 99-outro
python -m praisonaippt.daily_single --project $PROJECT assemble-beats
python -m praisonaippt.daily_single --project $PROJECT build-captions
python -m praisonaippt.daily_single --project $PROJECT audit-visual --interval 5
python -m praisonaippt.daily_single --project $PROJECT validate-sync --runs 3
python -m praisonaippt.daily_single --project $PROJECT validate-all
```

| Flag | When |
|------|------|
| `--skip-existing` | On `synthesise-vo` / `bookend-media` when scripts unchanged |
| `--segments 00-hook` | Re-s synthesise one segment only |
| `--skip-hd` | On `sync-assets` to keep existing video files |
| `--no-crawl` | On `sync-assets` to skip canonical page image crawl |
| `--force` | On `audit-visual` to re-export frames |

**After any `script.md` edit:** VO → bookends (if hook/outro) → assemble → captions → audit → validate.

---

## CLI commands

| Command | Purpose |
|---------|---------|
| `write-scripts` | Beat scripts from `video-script.md` |
| `sync-assets` | Crawl canonical URL + HD YouTube + patch beat-map |
| `synthesise-vo` | ElevenLabs TTS → `segments/*/narration.mp3`, `merge/narration.mp3` |
| `bookend-media` | HeyGen for `00-hook` / `99-outro` |
| `assemble-beats` | ffmpeg assembly → `merge/final.mp4` |
| `build-captions` | Script-aligned SRT (Whisper timing only) |
| `build-timeline` | `merge/timeline.json` |
| `validate-display` | SRT cue → visual mapping report |
| `audit-visual` | Pixel sample every N seconds vs planned assets |
| `validate-visual-audit` | Gate on `visual_audit_report.json` |
| `validate-sync` | Full text/visual suite (default 3 idempotent runs) |
| `validate-all` | Tools, output, media, sync, display, visual audit |
| `emit-protocol` | Write default `protocol.json` template |

Console alias: `daily-single` (see `pyproject.toml`).

---

## Project layout

```text
examples/videos/<slug>/
  manifest.json              # points at create-news research + beat-map
  segments/
    00-hook/script.md, heygen.mp4, hook_montage.json
    01-cold-open … 10-alignment/script.md
    99-outro/script.md, heygen.mp4
  beats/00-hook.mp4 … 99-outro.mp4
  merge/
    final.mp4                # loudnorm final (1920×1080)
    final.srt
    timeline.json
    display_sync_report.json
    sync_validation_report.json
    visual_audit_report.json
    asset_sync_report.json
    visual_audit_frames/
  scripts/config/protocol.json
```

**create-news assets:** `research/<slug>/review-assets/<slug>/` (PNGs + `videos/*.mp4`).

---

## Script contract

### Hook (`00-hook`) — three SRT cues

1. **Attention** — one punchy sentence. Label `Hook:` is stripped at TTS only.
2. **Overview** — comma-separated roll-call (one phrase → one montage hero).
3. **Bridge** — exactly: `Let's get started.`

Example (Fable pilot):

```text
Hook: Anthropic just dropped Claude Fable five — if AI is part of your job, this launch changes everything.

In the next five minutes: Fable versus Mythos, Stripe's fifty-million-line proof, benchmark scores that matter, safety without dead ends, and the app-versus-API mistake teams keep making.

Let's get started.
```

### Beats (`01`–`10`)

Content starts after Let's get started. ~2–4 plain-language sentences per beat; one sentence = one SRT cue.

### Outro (`99-outro`)

June CTA only — do **not** speak mer.vin URLs:

```text
I hope you liked this video. If it helped, like, share, and subscribe for the latest AI updates. Thanks for watching.
```

Captions detail: [video-script-captions skill](../.cursor/skills/video-script-captions/SKILL.md).

---

## Hook montage (required)

June roundup uses many hero swaps during the hook overview. daily_single **Phase 1.5** implements phrase-synced montage via ffmpeg (not full compositor yet).

| Phrase | Asset |
|--------|-------|
| Fable versus Mythos | `beat2-tier-diagram.png` |
| Stripe fifty-million-line proof | `beat3-stripe-card.png` |
| benchmark scores that matter | `benchmark-table.png` |
| safety without dead ends | `cyber-classifier.png` (fallback: `gpt-image-safeguard-fallback.png`) |
| app-versus-API mistake | `beat7-api-table.png` |

**Assembly** (`assemble.py` `_hook_montage()`):

1. Attention → first hero slide full-screen (not launch B-roll at t=0).
2. Overview → N hero PNGs (~2 s each, word-weighted).
3. Bridge → HeyGen PiP over hero background.

**Artefact:** `segments/00-hook/hook_montage.json`  
**Module:** `praisonaippt/daily_single/hook_montage.py`

**Gates:** `validate-sync` → `hook_montage` — ≥5 distinct heroes, overview alignment ≥0.45, no launch-only overview.

---

## Asset sync (`sync-assets`)

**Module:** `praisonaippt/daily_single/media_sync.py`

| Step | Action |
|------|--------|
| Crawl | Canonical news URL → Sanity CDN PNGs |
| HD video | YouTube clips re-downloaded if height &lt; 720p |
| Beat-map patch | Solar / Pokémon / fluid clips; bio-AAV chart |
| Report | `merge/asset_sync_report.json` |

**yt-dlp format (do not use `best[ext=mp4]` alone — yields 360p):**

```text
bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best
--merge-output-format mp4
```

### Fable motion inventory

| File | Source | Target resolution |
|------|--------|-------------------|
| `claudeai-launch.mp4` | X/Twitter @claudeai | 2160×2160 |
| `pokemon-timelapse.mp4` | YouTube | 1920×1080 |
| `carousel-solar.mp4` | YouTube | 1920×1080 |
| `carousel-factorio.mp4` | YouTube | 1920×1080 |
| `carousel-vibecad.mp4` | YouTube | 1920×1080 |
| `carousel-fluid.mp4` | YouTube | 1920×1080 |

Upstream harvest: create-news `scripts/harvest_motion.py` (same HD format in `media_download.py`).

---

## Beat assembly routing

VO duration drives clip lengths in `assemble.py`:

| Beat | Visuals |
|------|---------|
| 00-hook | Montage heroes + HeyGen PiP bridge |
| 1 | Launch clip + views overlay |
| 3 | Stripe card + Factorio + VibeCAD clips |
| 4 | Benchmark table + stat overlay |
| 5 | Solar → Pokémon → fluid clips + Spire stat card |
| 6 | Safeguard / bio-AAV / cyber / jailbreak slides |
| 7 | API table + safeguard flow diagram |
| 8 | Glasswing + protein complexes |
| 9 | Pricing card |
| 10 | Alignment chart + jailbreak |
| 99-outro | HeyGen full-frame |

---

## Validation layers

### 1. `validate-sync --runs 3`

Idempotent suite; fails if three consecutive reports differ.

| Check | Rule |
|-------|------|
| `caption_script_lock` | SRT text == locked scripts |
| `hook_structure` | Cues 1–3 = attention → overview → Let's get started |
| `image_mapping` | Per-cue keyword alignment ≥ **0.35** |
| `hook_montage` | ≥ **5** overview heroes; alignment ≥ **0.45** on overview |
| `youtube_quality` | Hook stakes, plain language, pacing, outro CTA |
| `visual_audit` | Requires passing `visual_audit_report.json` |

Output: `merge/sync_validation_report.json`

### 2. `validate-display`

Output: `merge/display_sync_report.json`

### 3. `audit-visual`

Samples `final.mp4` every **5 s** (+ cue midpoints). Pixel similarity vs planned asset:

| Asset type | Min pixel sim |
|------------|---------------|
| PNG slides | 0.42 |
| Video clips | 0.28 |
| Avatar / HeyGen | 0.15 |

Blocks generic B-roll (`claudeai-launch.mp4`) when enabled in protocol.  
Output: `merge/visual_audit_report.json`, frames in `merge/visual_audit_frames/`.

### 4. `validate-all`

Final gate: tools, 1920×1080 output, duration 280–540 s, beat coverage, HeyGen bookends, media inventory ≥720p, all reports pass.  
Output: `validation_report.json` at project root.

---

## Package modules

| Module | Role |
|--------|------|
| `cli.py` | Subcommands |
| `project.py` | Paths from `manifest.json` |
| `protocol.py` | `SEGMENT_ORDER`, default protocol |
| `media_sync.py` | Canonical crawl + HD video |
| `hook_montage.py` | Phrase → hero plan |
| `hook_validation.py` | Montage gates |
| `assemble.py` | ffmpeg beat assembly |
| `captions.py` | Script-aligned SRT |
| `display_sync.py` | Cue → visual scoring |
| `visual_audit.py` | Pixel frame audit |
| `sync_validation.py` | Combined validation suite |
| `youtube_quality.py` | YouTube style gates |
| `vo.py` / `tts.py` / `bookends.py` | ElevenLabs + HeyGen |

---

## Environment

Loaded from `praisonaippt/.env` and `~/elevenlabsAutomation/.env`:

| Variable | Use |
|----------|-----|
| `ELEVENLABS_API_KEY` / `ELEVEN_API_KEY` | TTS |
| `ELEVEN_VOICE_ID` | Default voice |
| `AVATAR_ID` | HeyGen avatar |
| HeyGen API key | `bookend-media` |

**Tools:** `ffmpeg`, `ffprobe`, `yt-dlp`, `curl`.

---

## Phase 2 (HeyGen compositor)

When HeyGen credits return — hook segment first:

```bash
python -m praisonaippt segment-video sync-media --project $PROJECT --segment 00-hook
python -m praisonaippt segment-video align-cues --project $PROJECT --force 00-hook
python -m praisonaippt segment-video yaml --project $PROJECT --force 00-hook
python -m praisonaippt segment-video build --project $PROJECT --force 00-hook
```

Same `script.md` contract. Phase 1.5 `hook_montage.json` feeds `sync-media`. See [segment-video-roundup skill](../.cursor/skills/segment-video-roundup/SKILL.md).

---

## Tests

```bash
pytest tests/test_daily_single_display_sync_unit.py \
       tests/test_daily_single_sync_validation.py \
       tests/test_daily_single_hook_montage.py \
       tests/test_daily_single_media_sync.py \
       tests/test_daily_single_visual_audit.py \
       tests/test_daily_single_youtube_quality.py -q
```

Run **×3** after pipeline changes for idempotency confidence.

---

## Known issues

| Issue | Mitigation |
|-------|------------|
| HeyGen `MOVIO_PAYMENT_INSUFFICIENT_CREDIT` | Reuse existing `heygen.mp4`; lip-sync may be stale vs new hook VO |
| Whisper OMP segfault | Captions fall back to proportional timing |
| Borderline cues (0.35–0.45 alignment) | Pass gate but worth human spot-check |
| Hash-named crawl images in handoff | Ignored by inventory validator; use named core images |

---

## create-news upstream

| Step | Script |
|------|--------|
| Motion harvest | `harvest_motion.py --slug <slug>` |
| Clip analysis | `analyse_motion_clips.py --slug <slug>` |
| Beat map | `build_beat_map.py --slug <slug>` |
| Generated cards | `generate_daily_cards.py --slug <slug>` |

Bootstrap: `scripts/bootstrap-daily-single.sh`

---

## Related documentation

- [Commands reference — daily_single section](commands.md#daily-single-video-pipeline)
- [Video examples](../examples/videos/README.md)
- [Fable pilot REUSE](../examples/videos/anthropic-claude-fable-5-mythos-5/REUSE.md)
- [Video export](video-export.md)

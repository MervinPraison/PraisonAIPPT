---
name: daily-single-video
description: Builds YouTube-style daily single-topic videos from create-news handoff — sync-assets HD crawl, hook montage (≥5 heroes), plain-language beats, ffmpeg assembly, script-locked captions, pixel visual audit, validate-sync ×3. Use for Fable-style stories, daily_single pipeline, beat-map videos, or when NOT using segment-video-roundup megaposts.
---

# daily-single-video

**Pipeline order + QA gates:** repo root [`AGENTS.md`](../../AGENTS.md)  
**Social comparison variant:** `examples/videos/anthropic-claude-fable-5-social-comparison/`

Single-topic walkthrough (one launch story, ~5–9 min). **Reference run:** `examples/videos/anthropic-claude-fable-5-mythos-5/`  
**June roundup pattern:** `examples/videos/june-2026-ai-roundup/`  
**Handoff:** create-news `research/<slug>/HANDOFF.md`

## Do NOT use

- `segment-video-roundup/scripts/bootstrap-project.sh` (megapost layout)
- Megapost-only validators (`required_assets` catalogue gates) — **hook_montage is required** for daily_single

## Pipeline phases

| Phase | Status | What |
|-------|--------|------|
| **1 — Script + B-roll + hook montage** | **Current** | `daily_single` CLI: scripts → VO → ffmpeg beat assembly with **phrase-synced hook heroes** |
| **2 — HeyGen decks** | When credits return | Per-beat + hook `avatar_media_3` like June roundup (`align-cues` → `yaml` → `build`) |
| **3 — Publish** | Shared | `.cursor/skills/mer-vin-article-video-upload/SKILL.md` |

Phase 1 and Phase 2 share the **same script contract** below so Phase 2 is a drop-in upgrade, not a rewrite.

---

## YouTube script contract (June-aligned)

Every video follows this spoken structure. Optimise for retention: hook in the first sentence, overview before depth, explicit handoff into content.

### `00-hook` — three parts (~55–70 words)

1. **Attention hook** — one punchy sentence (why watch *now*). Label line `Hook:` is stripped at TTS only.
2. **Overview** — comma-separated roll-call of topics (one phrase → one hero in montage). Plain language, non-developer friendly.
3. **Bridge** — end with exactly: **Let's get started.**

**June reference** (`segments/00-hook/script.md`):

```text
Fifteen stories in this roundup: Nemotron 3 Ultra, Gemma 4 … Meta Muse Spark on watch.
Now we are going to walk through every one in detail. Let's get started.
```

**Single-topic example** (`anthropic-claude-fable-5-mythos-5/segments/00-hook/script.md`):

```text
Hook: Anthropic just released Claude Fable five — if AI is part of your work, this launch matters.

In the next five minutes: what most teams actually get, Stripe's fifty-million-line proof, benchmark scores that matter, safety without dead ends, and the website-versus-developer mistake teams keep making.

Let's get started.
```

**Plain language:** `.cursor/rules/daily-single-plain-language.mdc` — no Mythos before beat 02; automated `pytest tests/test_audience_language.py`.

**Hook attention (first 5s):** `record-canonical-scroll` → blog scroll video; `validate-hook-attention` exports one JPEG per second.

**Hook montage (required):** each comma clause in the overview maps to a hero asset during cue 2 (~2s per slide). Assembly: `hook_montage.py` → `assemble.py` `_hook_montage()`. Validators: `hook_montage` in `validate-sync --runs 3` (≥5 distinct heroes, no launch-only overview).

### `01-cold-open` … `10-*` — beats

- Start **after** Let's get started — first beat is real content, not another intro.
- Plain language for a general YouTube audience; explain jargon when unavoidable (see `.cursor/rules/daily-single-plain-language.mdc`).
- ~2–4 sentences per beat; one sentence = one SRT cue (see `video-script-captions` skill).

### `99-outro` — June CTA (no spoken mer.vin)

```text
I hope you liked this video. If it helped, like, share, and subscribe for the latest AI updates. Thanks for watching.
```

Do **not** speak mer.vin URLs, integration tables, or technical recaps in the outro.

---

## Phase 1 commands

```bash
conda activate test   # or windsurf
cd /path/to/praisonaippt
PROJECT=examples/videos/<slug>
```

| Step | Command |
|------|---------|
| Scripts from beat map | `python -m praisonaippt.daily_single --project $PROJECT write-scripts` |
| Lock hook/outro manually | Edit `segments/00-hook/script.md`, `segments/99-outro/script.md` |
| **Sync canonical assets (HD)** | `python -m praisonaippt.daily_single --project $PROJECT sync-assets` |
| Voice-over | `python -m praisonaippt.daily_single --project $PROJECT synthesise-vo` |
| Hook/outro HeyGen | `python -m praisonaippt.daily_single --project $PROJECT bookend-media 00-hook 99-outro` |
| Captions | `python -m praisonaippt.daily_single --project $PROJECT build-captions` |
| Assemble B-roll | `python -m praisonaippt.daily_single --project $PROJECT assemble-beats` |
| Transcript ↔ visual map | `python -m praisonaippt.daily_single --project $PROJECT validate-display` |
| **Spoken ↔ visual gate** | `python -m praisonaippt.daily_single --project $PROJECT validate-spoken-visual` |
| **Pixel visual audit (every 5s)** | `python -m praisonaippt.daily_single --project $PROJECT audit-visual --interval 5` |
| **Robust sync test (×3)** | `python -m praisonaippt.daily_single --project $PROJECT validate-sync --runs 3` |
| Full gate | `python -m praisonaippt.daily_single --project $PROJECT validate-all` |

**Standard pipeline order:** `sync-assets` → `synthesise-vo` → `bookend-media` → `build-captions` → `assemble-beats` → `validate-display` → `validate-spoken-visual` → `audit-visual` → `validate-sync --runs 3` → `validate-all`

**Cue-aligned rebuild** (beat-06, beat-01): see `.cursor/skills/daily-single-video-pipeline/spoken-visual-sync.md`

**Step-by-step with modular QA gates:** use `.cursor/skills/daily-single-video-pipeline/SKILL.md` (`validate-qa --when pre_build|pre_assemble|post_vo|post_build`).

**Hook montage artefact:** `segments/00-hook/hook_montage.json` (phrase → hero plan; written on assemble).  
**Visual audit artefact:** `merge/visual_audit_report.json` + `merge/visual_audit_frames/` (JPEG every 5s + cue midpoints).

**Skip existing media** unless scripts changed: add `--skip-existing` to `synthesise-vo` / `bookend-media`.

**After any script edit:** re-run VO → bookends (if hook/outro) → `build-captions` → `assemble-beats` → `validate-display` → `validate-spoken-visual`.

**Before first assemble (and after handoff changes):** run `sync-assets` — crawls [canonical news URL](https://www.anthropic.com/news/claude-fable-5-mythos-5) images and re-downloads YouTube demos at **720p+** (not 360p progressive). Patches `beat-map.json` with carousel clips and biology charts.

---

## create-news upstream

| Step | Where |
|------|-------|
| Motion clip analysis | `analyse_motion_clips.py --slug <slug>` |
| Beat map | `build_beat_map.py --slug <slug>` |
| Cards / slides | `generate_daily_cards.py --slug <slug>` |
| Master script | `research/<slug>/video-script.md` (beats 1–10; hook/outro live in project `segments/`) |

Bootstrap: `scripts/bootstrap-daily-single.sh`

---

## Outputs

| File | Purpose |
|------|---------|
| `merge/final.mp4` | Loudnorm final |
| `merge/final.srt` | Script-aligned captions |
| `merge/display_sync_report.json` | Each cue → on-screen visual |
| `merge/sync_validation_report.json` | 3-run robust gate + YouTube quality |
| `merge/asset_sync_report.json` | Canonical crawl + HD video inventory |

Captions rules: `.cursor/skills/video-script-captions/SKILL.md`

---

## Phase 2 roadmap (HeyGen + June template)

When HeyGen credits return, upgrade **hook segment only** first (same script contract):

```bash
PROJECT=examples/videos/<slug>
# Hook segment — June compositor path
python -m praisonaippt segment-video sync-media --project $PROJECT --segment 00-hook
python -m praisonaippt segment-video align-cues --project $PROJECT --force 00-hook
python -m praisonaippt segment-video yaml --project $PROJECT --force 00-hook
python -m praisonaippt segment-video build --project $PROJECT --force 00-hook
python -m praisonaippt segment-video validate-hook --project $PROJECT --segment 00-hook
# Re-merge: replace beats/00-hook.mp4 with segment build, then assemble-beats
```

Phase 1.5 `hook_montage.json` becomes input to `sync-media` hero selection. Full per-beat HeyGen:

1. Keep `segments/*/script.md` unchanged (same contract).
2. Add per-segment `segment.yaml` using `examples/heygen-50590-video-audio-heygen-images.yaml` pattern.
3. Run segment-video-roundup stages per beat: `sync-media` → `align-cues` → `yaml` → `build` → `normalize-audio` → `merge`.
4. Continuous HeyGen under hook montage slides; outro = HeyGen only.

See `.cursor/skills/segment-video-roundup/SKILL.md` and [reference.md](reference.md).

---

## Quality gates before publish

- [ ] `sync-assets` pass — all handoff images + videos ≥720p from canonical page
- [ ] Hook has three parts: attention → **comma-separated overview** → **Let's get started**
- [ ] Hook overview shows **≥5 distinct heroes** (not single launch B-roll for whole overview)
- [ ] Hook attention uses **first hero slide** (not vintage launch B-roll at t=0)
- [ ] `audit-visual` pass — no generic/off-topic frames (`merge/visual_audit_report.json`)
- [ ] Beat 1 starts content (no duplicate intro)
- [ ] Outro = June subscribe CTA; no mer.vin spoken
- [ ] `validate-sync --runs 3` pass (script lock + hook + **hook_montage** + image + **YouTube quality**, idempotent)
- [ ] `build-captions` + `validate-display` + `validate-spoken-visual` pass
- [ ] `merge/spoken_visual_sync_report.json` → `ok: true`
- [ ] Plain language — readable without developer context

## Testing (spoken ↔ video ↔ image)

Three layers (mirrors June roundup, adapted for Phase 1 B-roll):

| Layer | What it checks | Command / test |
|-------|----------------|----------------|
| **Caption lock** | SRT text == locked `script.md` (not Whisper) | `validate-sync` → `caption_script_lock` |
| **Spoken↔visual gate** | Windows, charts, transitions, coverage | `validate-spoken-visual` → `spoken_visual_sync_report.json` |
| **Image mapping** | Each cue midpoint → correct asset file + keyword score ≥0.35 | `validate-display` → `display_sync_report.json` |
| **Hook structure** | Cues 1–3 = attention → overview → Let's get started | `validate-sync` → `hook_structure` |
| **Hook montage** | Overview cue → ≥5 distinct heroes; alignment ≥0.45; not launch-only | `validate-sync` → `hook_montage` |
| **Visual audit** | Pixel match + topic score every 5s; blocks generic B-roll | `audit-visual` → `visual_audit_report.json` |
| **Idempotency** | Same report on 3 consecutive runs | `validate-sync --runs 3` |
| **YouTube quality** | Compelling hook, plain language, pacing, outro CTA, alignment depth | `validate-sync` → `youtube_quality` |

```bash
pytest tests/test_daily_single_display_sync_unit.py \
       tests/test_daily_single_sync_validation.py \
       tests/test_daily_single_hook_montage.py \
       tests/test_daily_single_visual_audit.py \
       tests/test_cue_slide_sync.py \
       tests/test_spoken_visual_sync.py -q

python -m praisonaippt.daily_single --project examples/videos/<slug> validate-spoken-visual
python -m praisonaippt.daily_single --project examples/videos/<slug> validate-sync --runs 3
```

Outputs: `merge/sync_validation_report.json`, `merge/display_sync_report.json`, `merge/spoken_visual_sync_report.json`

---

## Additional resources

- **Full documentation:** [docs/daily-single-video.md](../../docs/daily-single-video.md)
- Phase 1 vs 2 detail: [reference.md](reference.md)
- REUSE bridge: `examples/videos/<slug>/REUSE.md`
- Captions: `.cursor/skills/video-script-captions/SKILL.md`

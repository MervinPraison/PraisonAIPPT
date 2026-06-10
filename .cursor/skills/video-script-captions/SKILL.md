---
name: video-script-captions
description: Builds on-point video SRT from locked segment scripts plus Whisper timing only — never raw transcription text. Use for daily_single captions, final.srt, segment.srt, subtitles, transcript alignment, YouTube hook/overview/Let's get started structure, or when captions must match June roundup quality.
---

# Video script captions

Captions show **script text**, timed by **Whisper**. Same rule as June roundup (`write_verses_srt`): viewers read the authored script, not Whisper's guess.

## Do NOT

- Put Whisper `segments[].text` directly into SRT (misheard words, filler, blabber)
- Include editor labels (`Hook:`, `Beat N:`, `[VISUAL:…]`) in caption text
- Regenerate captions from stale `merge/narration.json` after script changes
- Skip the hook/overview/**Let's get started** block at the start

## DO

| Pipeline | Command |
|----------|---------|
| **daily_single** | `python -m praisonaippt.daily_single --project . build-captions` |
| **segment roundup** | Per-segment `segment.srt` via `write_verses_srt` / `write_cue_timings_srt`; merge stitches offsets |

## YouTube opening structure (June standard)

First SRT cues must follow this order:

1. **Hook sentence** (attention)
2. **Overview sentence(s)** — use **comma-separated roll-call** so montage timing can split one cue into N hero windows (June / Fable pattern)
3. **`Let's get started.`** — own cue; content beats follow after

June roundup hook (`examples/videos/june-2026-ai-roundup/segments/00-hook/script.md`):

```text
Fifteen stories in this roundup: … Let's get started.
```

Single-topic hook — three cues minimum; overview cue should list topics separated by commas for hook montage. See `.cursor/skills/daily-single-video/SKILL.md`.

## Script density

| Segment | Target |
|---------|--------|
| Hook | ~55–70 words: attention + overview + **Let's get started** |
| Topic / beat | ~2–4 plain-language sentences |
| Outro | June CTA (~25 words): like/subscribe — **no mer.vin spoken** |

Every sentence in `script.md` becomes one SRT cue. No extra words beyond the script.

## daily_single workflow

```bash
python -m praisonaippt.daily_single --project examples/videos/<slug> build-captions
python -m praisonaippt.daily_single --project examples/videos/<slug> validate-display
```

Outputs:

- `segments/*/segment.srt` — one cue per script sentence
- `merge/final.srt` — stitched with `merge/timeline.json` offsets

Implementation: `praisonaippt/daily_single/captions.py`

## segment-video-roundup (reference)

1. `align-cues` → `cue_timings.json` (Whisper anchors)
2. `yaml` → verses with `notes` = script fragment
3. `build` → `write_verses_srt(seg_dir, verses)`
4. `merge` → offset stitch → `merge/final-roundup.srt`

See `.cursor/skills/segment-video-roundup/SKILL.md` Phase 5–6.

## Gate before publish

- [ ] First cues = hook → overview → **Let's get started**
- [ ] SRT cue text matches `segments/*/script.md`
- [ ] `validate-display` pass (≥0.35 alignment per cue)
- [ ] Re-run after any script or VO change

## Additional resources

- Hook/outro + montage contract: `.cursor/skills/daily-single-video/SKILL.md`
- Full pipeline doc: [docs/daily-single-video.md](../../docs/daily-single-video.md)
- Align API: [reference.md](reference.md)

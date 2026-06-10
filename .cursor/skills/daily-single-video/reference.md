# daily-single-video — reference

Canonical long-form doc: [docs/daily-single-video.md](../../docs/daily-single-video.md)

## Package modules

| Module | Role |
|--------|------|
| `cli.py` | Subcommands |
| `media_sync.py` | `sync-assets` — crawl + HD video |
| `hook_montage.py` | Phrase → hero plan |
| `hook_validation.py` | Montage gates |
| `assemble.py` | ffmpeg beat routing |
| `captions.py` | Script-aligned SRT |
| `display_sync.py` | Cue → visual scoring |
| `visual_audit.py` | Pixel frame audit |
| `sync_validation.py` | Combined validation suite |
| `youtube_quality.py` | YouTube style gates |
| `validation.py` | `validate-all` |

## Beat assembly routing (`assemble.py`)

| Beat | Visuals |
|------|---------|
| 00-hook | First hero → montage slideshow → HeyGen PiP |
| 1 | Launch clip + views overlay |
| 3 | Stripe card + Factorio + VibeCAD |
| 4 | Benchmark + stat overlay |
| 5 | Solar → Pokémon → fluid + Spire stat |
| 6 | Safeguard / bio-AAV / cyber / jailbreak |
| 7 | API table + flow diagram |
| 8 | Glasswing + protein complexes |
| 9 | Pricing card |
| 10 | Alignment chart + jailbreak |
| 99-outro | HeyGen full-frame |

## Validation thresholds

| Gate | Threshold |
|------|-----------|
| Per-cue alignment | ≥ 0.35 |
| Hook montage overview | ≥ 0.45, ≥ 5 distinct files |
| Visual audit pixel (PNG) | ≥ 0.42 |
| Visual audit pixel (video) | ≥ 0.28 |
| Visual audit pixel (avatar) | ≥ 0.15 |
| Final output | 1920×1080, 280–540 s |
| Motion clips | ≥ 720p height |

## Environment

| Variable | Use |
|----------|-----|
| `ELEVENLABS_API_KEY` | TTS |
| `ELEVEN_VOICE_ID` | Voice (default in `env.py`) |
| `AVATAR_ID` | HeyGen avatar |
| `PRAISONAIPPT_VISION_PROVIDER` | Optional visual audit LLM |

Conda env: `test` (not `windsurf`).

## Known issues

- HeyGen credits: reuse `heygen.mp4` if `MOVIO_PAYMENT_INSUFFICIENT_CREDIT`
- Whisper segfault: captions use proportional timing fallback
- Hash-named crawl PNGs in handoff: ignored by inventory validator

## Manifest (`manifest.json`)

```json
{
  "schema_version": 1,
  "story_type": "daily_single",
  "slug": "anthropic-claude-fable-5-mythos-5",
  "create_news_research": "/Users/praison/create-news/research/anthropic-claude-fable-5-mythos-5",
  "handoff_json": ".../video-handoff.json",
  "beat_map": ".../video-understanding/beat-map.json",
  "target_duration_sec": [360, 540],
  "output": {
    "final_mp4": "merge/final.mp4",
    "timeline_json": "merge/timeline.json"
  }
}
```

## Segment layout

```text
segments/
  00-hook/script.md          # YouTube hook (3-part)
  01-cold-open/script.md     # Beat 1 — content starts here
  02-mythos-tier/script.md
  …
  10-alignment/script.md
  99-outro/script.md         # June CTA
merge/
  final.mp4
  final.srt
  display_sync_report.json
  visual_audit_report.json
  visual_audit_frames/
  timeline.json
beats/
  00-hook.mp4 … 99-outro.mp4
```

## Hook writing checklist

| Part | Goal | Example cue |
|------|------|-------------|
| Attention | Curiosity + stakes in ≤15 words | "Anthropic just released Claude Fable five…" |
| Overview | Comma-separated topics (one hero each) | "…Fable versus Mythos, Stripe proof, benchmark scores…" |
| Bridge | Transition | "Let's get started." |

Hook visual (Phase 1.5): **phrase-synced montage** — first hero slide (attention) → N hero PNGs during overview → HeyGen PiP over hero (bridge). No vintage launch B-roll at t=0 (`assemble.py` `_hook_montage()`, `hook_montage.json`).  
Hook visual (Phase 2): June compositor with continuous HeyGen under montage slides (`align-cues` → `yaml` → `build`).

## Visual audit (`visual_audit.py`)

Samples `merge/final.mp4` every **5 seconds** (plus visual-window midpoints):

1. Extract JPEG → `merge/visual_audit_frames/frame-*.jpg`
2. Compare to planned asset via **pixel similarity** (numpy grayscale MSE)
3. Score spoken cue vs asset metadata (`VISUAL_META` / beat-map)
4. Optional vision LLM (`gpt-4o-mini` via OpenAI when `OPENAI_API_KEY` set; override with `PRAISONAIPPT_VISION_MODEL`)

```bash
python -m praisonaippt.daily_single --project $PROJECT audit-visual --interval 5
python -m praisonaippt.daily_single --project $PROJECT validate-visual-audit
```

Blocks **generic B-roll** (e.g. vintage maps/insects in attention window). Gates `validate-sync` and `validate-all`.

## sync-assets (required before assemble)

Crawls canonical news URL + downloads YouTube demos at **1080p**. Patches beat-map (solar/fluid/Pokémon, bio-AAV, alignment chart). See Fable pilot: all 6 motion clips at 1920×1080, launch at 2160×2160.

## Fable hook montage phrase → asset

| Phrase fragment | Asset |
|-----------------|-------|
| Fable versus Mythos | `beat2-tier-diagram.png` |
| Stripe fifty-million-line proof | `beat3-stripe-card.png` |
| benchmark scores that matter | `benchmark-table.png` |
| safety without dead ends | `cyber-classifier.png` (fallback: `gpt-image-safeguard-fallback.png`) |
| app-versus-API mistake | `beat7-api-table.png` |

Defined in `praisonaippt/daily_single/hook_montage.py`; written to `segments/00-hook/hook_montage.json`.

## Plain-language replacements

| Avoid | Prefer |
|-------|--------|
| classifiers | safety checks |
| fallback | backup model / automatic switch |
| Messages API | developer API |
| distillation | copying the model |
| HTTP block | error response / blocked request |
| runbooks | support playbooks |
| metered API | pay-as-you-go |

## Canonical asset sync

Run once per project (repeat after handoff or news-page updates):

```bash
python -m praisonaippt.daily_single --project examples/videos/<slug> sync-assets
```

| Source | What sync-assets does |
|--------|----------------------|
| `video-handoff.json` | Image + YouTube inventory |
| Anthropic news URL | Crawl missing Sanity CDN PNGs |
| YouTube (Claude channel) | HD merge download (1080p cap), replaces 360p files |
| `beat-map.json` | Adds solar/Pokémon/fluid clips, bio-AAV chart |

Implementation: `praisonaippt/daily_single/media_sync.py`

## Phase 1 vs Phase 2 assembly

| | Phase 1.5 (now) | Phase 2 (June template) |
|--|---------------|-------------------------|
| Hook | ffmpeg montage: first hero → N PNGs → HeyGen PiP | Compositor + continuous HeyGen under slides |
| Per beat | ffmpeg B-roll routing in `assemble.py` | `praisonaippt build` compositor MP4 |
| Avatar | Hook/outro HeyGen only | HeyGen every segment |
| Captions | `build-captions` proportional / Whisper | `align-cues` + `write_verses_srt` |
| Merge | concat beats + loudnorm | `merge` crossfade like roundup |
| Template | — | `heygen-50590-video-audio-heygen-images.yaml` |

## Package entry points

- CLI: `python -m praisonaippt.daily_single`
- Console script: `daily-single` (`pyproject.toml`)
- Protocol: `praisonaippt/daily_single/protocol.py`

## Related skills

| Skill | Role |
|-------|------|
| `video-script-captions` | SRT from script text |
| `segment-video-roundup` | Phase 2 per-segment HeyGen decks |
| `mer-vin-article-video-upload` | WordPress embed |

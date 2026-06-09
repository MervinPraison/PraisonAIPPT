# Segment video roundup — examples

## June 2026 AI Engineering Roundup (reference run)

| Item | Value |
|------|-------|
| Project dir | `examples/videos/june-2026-ai-roundup/` |
| Research | `/Users/praison/create-news/research/june-2026-ai-engineering-roundup/` |
| Post | [51661](https://mer.vin/?p=51661) |
| Segments | 17 (hook + 15 topics + outro) |
| Final video | `merge/final-roundup.mp4` (~353 s, 1920×1080) |
| Template deck | `examples/heygen-50590-video-audio-heygen-images.yaml` |

### Live validation baseline (2026-06-09)

| Gate | Result |
|------|--------|
| `validate-all` | **11/13** validators pass |
| `image_audit` | **17/17** segments |
| `segment_sync` | pass (expected warn: hook yaml **16** vs cue_timings **15**) |
| `audio_loudness` / `merge_output` / `hook_montage` | pass |
| `required_assets` catalogue | **10/15** — fail: 01 nemotron, 02 gemma, 03 mai (speech chart), 09 mellum, 11 contain |
| `display_sync` catalogue | **11/15** — fail: 01, 02, 09, 11 (mai passes catalogue; chart debt is `required_assets` only) |
| `manual_assets` | 3 warns: bedrock, mitre, meta |

`validate-all` may still fail catalogue gates until create-news crawl completes — safe to ship when `image_audit`, `segment_sync`, `audio_loudness`, and per-segment caption↔slide pass.

### Verify final video

```bash
open examples/videos/june-2026-ai-roundup/merge/final-roundup.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 \
  examples/videos/june-2026-ai-roundup/merge/final-roundup.mp4
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate -of csv=p=0 \
  examples/videos/june-2026-ai-roundup/merge/final-roundup.mp4
# Expected: 1920,1080,30/1
```

### Downstream rebuild (no TTS/HeyGen)

```bash
cd examples/videos/june-2026-ai-roundup/scripts

python3 pipeline.py run sync-media
python3 pipeline.py run align-cues --force
python3 pipeline.py run yaml --force
# or: build_segment_yaml.py $(python3 -c "import json; m=json.load(open('../manifest.json')); print(' '.join(s['dir'] for s in m['segments'] if s.get('slide_type') in ('avatar_media_3','big_number')))")
python3 pipeline.py run build --force
python3 pipeline.py run normalize-audio --force
python3 pipeline.py run merge --force
python3 pipeline.py validate-all
```

### Single-segment fix (after sync-media cue change)

```bash
SEGS="05-aws-bedrock-gpt-5-5-codex-ga"
python3 pipeline.py run align-cues --force $SEGS
python3 pipeline.py run yaml --force $SEGS   # or: build_segment_yaml.py $SEGS
python3 pipeline.py run build --force $SEGS
python3 pipeline.py run normalize-audio --force   # project-wide, not $SEGS
python3 pipeline.py run merge --force
```

### June 2026 gap lessons (handoff-first)

Most `image_audit` failures were **stub `vision_description`** in handoff (score 0.324). Prefer real captions + `asset_type` in create-news; downstream `VISION_ENRICHMENTS` is a stopgap.

| Topic | Handoff would have fixed | Downstream workaround used |
|-------|--------------------------|----------------------------|
| Holo | OSWorld benchmark chart vision + `benchmark_chart` | `VISION_ENRICHMENTS` on `f0113828e257.png` |
| MAI / MiniMax / EVA | Per-image vision matching spoken lines | Overrides + enrichments |
| Bedrock / MITRE / Meta | Crawl canonical/Sanity heroes; clear `needs_manual_asset` | Partial crawl + overrides |
| Mellum / defending-code / Meta | 3 relevant images per topic | `HERO_REUSE_ENRICHMENTS` |
| Hook montage | Rich vision on each topic hero | Prepend roll-call phrase to vision text |

### Gap audit

```bash
zsh .cursor/skills/segment-video-roundup/scripts/gap-audit.sh examples/videos/june-2026-ai-roundup
```

### First-time media (costs money)

```bash
python3 run_segment_media.py --skip-existing
```

### Publish

```bash
praisonaiwp media upload ../merge/final-roundup.mp4 --post-id=51661 --server default
praisonaiwp update 51661 --no-block-conversion --server default --post-content "$(cat article-with-video.html)"
```

### Script tone (locked)

- No greeting; hook opens with dense roll-call after "roundup:"
- Each topic: what shipped → why engineers care → where to try
- ~1,350–1,450 words total

### Hero map source

Editorial `top_picks` from `review-data.json`, validated by `sync_media_assets.py`. Mis-picks fixed via `CUE_IMAGE_OVERRIDES` in that script.

---

## Bootstrap a new roundup

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  "august-2026-ai-roundup" \
  "/Users/praison/create-news/research/august-2026-ai-engineering-roundup" \
  52000
```

Then edit `manifest.json` segments and run phases from [SKILL.md](SKILL.md).

---

## validate-deck gold standard

```bash
cd /Users/praison/praisonaippt
praisonaippt validate-deck -i examples/heygen-50590-video-audio-heygen-images.yaml
praisonaippt validate-deck -i examples/videos/june-2026-ai-roundup/segments/01-nvidia-nemotron-3-ultra/segment.yaml
```

Expect: plan_approval, schema, timing_drift, pip_centring, slide_qa; golden `slide_jpegs` when seeded.

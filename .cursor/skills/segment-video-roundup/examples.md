# Segment video roundup — examples

## June 2026 AI Engineering Roundup (reference run)

| Item | Value |
|------|-------|
| Project dir | `examples/june-2026-ai-roundup/` |
| Research | `/Users/praison/create-news/research/june-2026-ai-engineering-roundup/` |
| Post | [51661](https://mer.vin/?p=51661) |
| Segments | 17 (hook + 15 topics + outro) |
| Final video | `merge/final-roundup.mp4` (~362 s) |
| Template deck | `examples/heygen-50590-video-audio-heygen-images.yaml` |
| Multi-cue segments | Nemotron, MiniMax M3, HF CLI, Holo3.1, GPT-Rosalind |

### Commands used (end-to-end)

```bash
cd /Users/praison/praisonaippt/examples/june-2026-ai-roundup/scripts

python3 pipeline.py sync-media
python3 pipeline.py validate-media
python3 run_segment_media.py --skip-existing   # only when media missing
python3 pipeline.py yaml
python3 pipeline.py build --force 01-nvidia-nemotron-3-ultra   # multi-cue rebuild
python3 pipeline.py fix-jpegs
python3 pipeline.py seed-golden
python3 pipeline.py merge
python3 pipeline.py validate

# Publish
praisonaiwp media upload ../merge/final-roundup.mp4 --post-id=51661 --server default
praisonaiwp update 51661 --no-block-conversion --server default --post-content "$(cat article-with-video.html)"
```

### Script tone (locked)

- No greeting; hook opens with dense roll-call
- Each topic: what shipped → why engineers care → where to try
- Zero filler; ~1,350–1,450 words total

### Hero map source

Editorial `top_picks` from `review-data.json`, validated by `sync_media_assets.py` — not hardcoded `hero_slide_map.json` (deprecated; `copy_heroes.sh` delegates to sync-media).

---

## Bootstrap a new roundup

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  "august-2026-ai-roundup" \
  "/Users/praison/create-news/research/august-2026-ai-engineering-roundup" \
  52000
```

Then edit `manifest.json` segments from new `video-handoff.json` and run Phases 2–9 from [SKILL.md](SKILL.md).

---

## validate-deck gold standard

```bash
cd /Users/praison/praisonaippt
praisonaippt validate-deck -i examples/heygen-50590-video-audio-heygen-images.yaml
praisonaippt validate-deck -i examples/june-2026-ai-roundup/segments/01-nvidia-nemotron-3-ultra/segment.yaml
```

Expect: plan_approval, schema, timing_drift, pip_centring, slide_qa; golden `slide_jpegs` when seeded.

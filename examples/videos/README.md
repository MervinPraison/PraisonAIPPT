# Video examples

create-news handoff → praisonaippt video pipelines.

```
examples/videos/
  README.md
  <slug>/                    # daily single OR megapost roundup
    manifest.json
    segments/
    merge/
    …
```

| Project | Type | Docs |
|---------|------|------|
| [june-2026-ai-roundup](june-2026-ai-roundup/) | Megapost HeyGen roundup | `.cursor/skills/segment-video-roundup/SKILL.md` |
| [anthropic-claude-fable-5-mythos-5](anthropic-claude-fable-5-mythos-5/) | Daily single (ffmpeg + hook montage) | [docs/daily-single-video.md](../../docs/daily-single-video.md) |

---

## Daily single

Single-topic YouTube walkthrough (~5–9 min). **Not** the segment-video-roundup bootstrap.

| Step | Command |
|------|---------|
| Bootstrap | `scripts/bootstrap-daily-single.sh` |
| Skill | `.cursor/skills/daily-single-video/SKILL.md` |
| Full docs | [docs/daily-single-video.md](../../docs/daily-single-video.md) |

Standard pipeline:

```bash
conda activate test
PROJECT=examples/videos/<slug>

python -m praisonaippt.daily_single --project $PROJECT sync-assets
python -m praisonaippt.daily_single --project $PROJECT synthesise-vo
python -m praisonaippt.daily_single --project $PROJECT bookend-media 00-hook 99-outro
python -m praisonaippt.daily_single --project $PROJECT assemble-beats
python -m praisonaippt.daily_single --project $PROJECT build-captions
python -m praisonaippt.daily_single --project $PROJECT audit-visual --interval 5
python -m praisonaippt.daily_single --project $PROJECT validate-sync --runs 3
python -m praisonaippt.daily_single --project $PROJECT validate-all
```

Pilot REUSE: [anthropic-claude-fable-5-mythos-5/REUSE.md](anthropic-claude-fable-5-mythos-5/REUSE.md)

---

## Megapost roundup

Multi-topic HeyGen compositor pipeline.

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  august-2026-ai-roundup /path/to/create-news/research/august-2026-ai-roundup POST_ID
```

Skill: `.cursor/skills/segment-video-roundup/SKILL.md`

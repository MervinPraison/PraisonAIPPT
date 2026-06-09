# Video examples

Segment-video roundup projects (create-news handoff → praisonaippt pipeline).

```
examples/videos/
  README.md
  <slug>-roundup/          # one folder per megapost / publish cycle
    manifest.json
    scripts/
    segments/
    merge/
    slide_images/
```

| Project | Megapost slug |
|---------|----------------|
| [june-2026-ai-roundup](june-2026-ai-roundup/) | `june-2026-ai-engineering-roundup` |

Bootstrap a new project:

```bash
zsh .cursor/skills/segment-video-roundup/scripts/bootstrap-project.sh \
  august-2026-ai-roundup /path/to/create-news/research/august-2026-ai-roundup POST_ID
```

Creates `examples/videos/august-2026-ai-roundup/`.

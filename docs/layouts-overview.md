# Layouts and styling overview

PraisonAI PPT builds slides from YAML (or JSON). Layout behaviour is controlled by three layers:

1. **`slide_type`** — which renderer draws the slide (verse, table, `avatar_*`, `deck_*`, …).
2. **`slide_style`** — colours, typography, and inch/ratio tokens under `layouts.<kind>`.
3. **`video_export`** — compositor timing, avatar timeline, and FFmpeg options for MP4 export.

## Choose a layout family

| Family | Doc page | When to use |
|--------|----------|-------------|
| **Standard** | [Standard slide layouts](slide-layouts.md) | Sermons, articles, bullets, tables, quotes — `list`, `table`, `verse`, `two_column`, … |
| **Avatar / HeyGen** | [Avatar layouts & PiP](avatar-layouts.md) | Speaking-head regions, split media, floating PiP on content slides |
| **Sales deck** | [Deck layouts](deck-layouts.md) | HeyGen-style `deck_*` templates (title split, exec summary, region grid, …) |

## Styling

| Topic | Doc page |
|-------|----------|
| All `slide_style` keys, `typography.*`, `layouts.*` defaults | [Slide style reference](slide-style-reference.md) |
| Highlights, alignment, list types | [Rich text formatting](formatting.md) |
| Reusable themes (`template: sermon-dark`) | [Theme templates](templates.md) |

## Video

| Topic | Doc page |
|-------|----------|
| MP4 export, narration modes, `avatar_timeline` | [Video export](video-export.md) |
| Top-level deck keys, per-verse timing | [YAML deck reference](yaml-reference.md) |

## Example galleries

```bash
python examples/build_showcase_examples.py
```

| Gallery | YAML |
|---------|------|
| All avatar `slide_type`s | `examples/avatar_layouts.yaml` |
| All `deck_*` layouts | `examples/deck_template_gallery.yaml` |
| HeyGen 50590 article (content + PiP) | `examples/heygen-50590-content.yaml` |

## Preview docs locally (MkDocs)

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The site also publishes via Jekyll (`docs/_config.yml`) at [ppt.praison.ai](https://ppt.praison.ai); MkDocs is the recommended local preview with the full layout nav above.

# PraisonAI PPT — documentation

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://badge.fury.io/py/praisonaippt)

## MkDocs (recommended local preview)

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Configuration: `mkdocs.yml` at the repository root.

### Layout and styling docs

| Page | Topic |
|------|--------|
| [layouts-overview.md](layouts-overview.md) | Hub — choose standard, avatar, or deck layouts |
| [slide-layouts.md](slide-layouts.md) | `verse`, `list`, `table`, `quote`, … |
| [avatar-layouts.md](avatar-layouts.md) | `avatar_*`, PiP, `avatar_timeline` |
| [deck-layouts.md](deck-layouts.md) | `deck_*` sales templates |
| [slide-style-reference.md](slide-style-reference.md) | `slide_style`, `typography.*`, `layouts.*` |
| [yaml-reference.md](yaml-reference.md) | Top-level deck and video keys |
| [video-export.md](video-export.md) | PPTX → MP4 compositor |

## Jekyll site (ppt.praison.ai)

The same Markdown files publish via `docs/_config.yml` (Jekyll). MkDocs includes the full layout nav; Jekyll nav is a subset — use MkDocs locally for complete layout reference.

## Other docs

- [Main README](../README.md) — package overview
- [Quick start](quickstart.md)
- [Formatting](formatting.md) — highlights and rich text
- [Templates](templates.md) — theme presets
- [Configuration](configuration.md) — `~/.praisonaippt/config.yaml`

## Example galleries

```bash
python examples/build_showcase_examples.py
```

- `examples/avatar_layouts.yaml` — all avatar `slide_type`s
- `examples/deck_template_gallery.yaml` — all `deck_*` layouts
- `examples/heygen-50590-content.yaml` — article deck with PiP and timing

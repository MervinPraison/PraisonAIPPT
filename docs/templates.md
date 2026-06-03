# Theme templates

Reusable **style templates** for PraisonAI PPT — colours, fonts, backgrounds, and slide size — separate from sermon **content** in your deck YAML.

## Quick start

```yaml
template: sermon-dark
presentation_title: Sunday Service
sections:
  - section: Message
    verses:
      - reference: John 3:16 (NKJV)
        text: For God so loved the world…
```

```bash
praisonaippt -i my_sermon.yaml
# or
praisonaippt -i my_sermon.yaml --template sermon-gold
```

## Built-in templates

| Name | Extends | Description |
|------|---------|-------------|
| `default` | — | Dark background colour + optional image |
| `sermon-dark` | `default` | House style (white Palatino on dark background) |
| `sermon-gold` | `sermon-dark` | Gold highlights, blue references |
| `sermon-dark-center` | `sermon-dark` | Centred body text |
| `sermon-dark-ref-bottom` | `sermon-dark` | Reference line at bottom |
| `light-minimal` | — | No background image; blue highlights |

```bash
praisonaippt --list-templates
praisonaippt template sermon-gold    # show resolved style YAML
```

## Extend a template

Theme files support `extends:` (style keys only):

```yaml
# ~/.praisonaippt/templates/my-church.yaml
extends: sermon-gold.yaml
description: Our church variant
slide_style:
  highlight_color: '#E6C200'
```

Deck referencing your theme:

```yaml
template: my-church
presentation_title: …
sections: …
```

Or extend inline on the deck:

```yaml
extends: sermon-dark.yaml
slide_style:
  highlight_color: '#FFD700'
```

## Preset and overrides

Without a separate theme file:

```yaml
slide_style:
  preset: sermon-dark
  overrides:
    highlight_color: '#FFD700'
```

Deck inline `slide_style` always wins over template layers.

## Merge priority (low → high)

1. Template file `extends` chain  
2. Top-level `template:` or `--template`  
3. Deck `extends:`  
4. `slide_style.preset`  
5. `slide_style.overrides`  
6. Inline `slide_style` on the deck  

## Python API

```python
from praisonaippt import load_verses_from_file, list_templates, resolve_template_style

load_verses_from_file("sermon.yaml", template="sermon-dark")
resolve_template_style("sermon-gold")  # merged dict for tooling
list_templates()
```

## Layout SDK (optional)

Templates may include optional layout tokens under `slide_style`:

```yaml
slide_style:
  preset: sermon-dark
  typography:
    title_size_pt: 44
    subtitle_size_pt: 28
  layouts:
    title:
      margin_in: 0.6
      content_width_in: 9.0
      title_top_in: 2.5
```

Omitted keys use built-in defaults (unchanged decks).

## Content vs style templates

| Type | Location | CLI |
|------|----------|-----|
| **Content** (verses, sections) | `examples/template.yaml`, `--use-example` | `--list-examples` |
| **Style** (theme) | `templates/*.yaml`, `~/.praisonaippt/templates/` | `--list-templates` |

Copy content from [examples/template.yaml](../examples/template.yaml); apply style with `template: sermon-dark`.

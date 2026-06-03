# PraisonAI PPT theme templates

Style-only YAML packs (colours, fonts, backgrounds). Use with a content deck:

```yaml
template: sermon-dark
presentation_title: My Sermon
sections: [...]
```

## Built-in themes

| Name | Extends | Source example |
|------|---------|----------------|
| `default` | — | `love_of_god.yaml` |
| `sermon-dark` | `default` | `100_fold_blessing.yaml` |
| `sermon-gold` | `sermon-dark` | `why_delay.yaml` |
| `sermon-dark-center` | `sermon-dark` | — |
| `sermon-dark-ref-bottom` | `sermon-dark` | — |
| `light-minimal` | — | `they_didnt_wait_for_god_light.yaml` |

Gallery: run `python examples/template_demos/build_demos.py` to regenerate
`examples/template_demos/{name}.yaml` and `.pptx` for every theme.

## Extend a theme

```yaml
# my-church.yaml in ~/.praisonaippt/templates/
extends: sermon-gold.yaml
slide_style:
  highlight_color: '#E6C200'
```

## CLI

```bash
praisonaippt --list-templates
praisonaippt template show sermon-gold
praisonaippt -i deck.yaml --template sermon-dark
```

User overrides: `~/.praisonaippt/templates/*.yaml`

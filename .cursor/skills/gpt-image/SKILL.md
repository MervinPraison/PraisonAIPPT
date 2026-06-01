---
name: gpt-image
description: Generate and edit images with OpenAI gpt-image-2 for PraisonAI PPT slide assets. Use when creating diagrams, charts, or visuals for YAML decks (slide_type image), or any "generate/create/edit image" request for this repo.
disable-model-invocation: true
---

# GPT Image (PraisonAI PPT)

Generate and edit images via `gpt-image-2` CLI scripts in this repo. Pair with **ppt-yaml-deck-workflow** to embed results in decks.

**Skill root:** `.cursor/skills/gpt-image/`

## Setup

Scripts use PEP 723 metadata; run with `uv run` (installs `openai` on first use).

`OPENAI_API_KEY` from:

1. Shell export (`export OPENAI_API_KEY=sk-...`) — preferred
2. `.cursor/skills/gpt-image/.env` (copy from `.env.example`)

## Scripts

| Script | Use |
|--------|-----|
| `scripts/generate.py` | Text → image (no input file) |
| `scripts/edit.py` | Text + 1–10 images → image |
| `scripts/validate_skill.py` | Local checks (no API); optional `--generate` smoke test |

## Quick decision

- No input images → `generate.py`
- Has input image(s) → `edit.py`
- Slide asset for YAML → generate at **`1536x864`** (widescreen), save under `assets/generated/`

## Generate (slide diagram example)

```bash
cd /Users/praison/ppt-package

uv run .cursor/skills/gpt-image/scripts/generate.py \
  --prompt "Simple sermon diagram: two columns 'My Power' vs 'His Power', dark blue background, gold and green text labels only, no logos, no watermark, clean flat design for a PowerPoint slide." \
  --size 1536x864 \
  --quality medium \
  --output assets/generated/power_diagram.png
```

## Use in YAML deck

```yaml
- slide_type: image
  image_path: assets/generated/power_diagram.png
  image_fit: contain
  reference: 100% His Power
  text: Trust grace, not self-effort
```

Then regenerate the deck:

```bash
python3 -m praisonaippt.cli -i examples/how_to_prevent_delay.yaml -o examples/how_to_prevent_delay.pptx
```

## generate.py flags

| Flag | Default | Notes |
|------|---------|--------|
| `--prompt` | required | |
| `--output` | `output.png` | Use repo paths under `assets/generated/` |
| `--size` | `1024x1024` | Slides: `1536x864` (widescreen) |
| `--quality` | `medium` | `high` for dense text |
| `--output-format` | `png` | |
| `--n` | `1` | 1–4 variants |

## edit.py

```bash
uv run .cursor/skills/gpt-image/scripts/edit.py \
  --prompt "Instruction" \
  --images input.png \
  --output assets/generated/edited.png \
  --size 1536x864
```

## Validate skill (no API cost)

```bash
uv run .cursor/skills/gpt-image/scripts/validate_skill.py
```

## Validate with live generation

```bash
uv run .cursor/skills/gpt-image/scripts/validate_skill.py --generate
```

Expect `✓ Saved: assets/generated/skill_test.png` and a non-empty PNG.

## Prompting

Read `references/prompting-guide.md` before writing prompts. For slide diagrams: flat design, high contrast, **no logos/trademarks/watermarks**, legible text in quotes.

## Size reference (gpt-image-2)

| Use | Size |
|-----|------|
| Widescreen slide | `1536x864` |
| Portrait slide | `1024x1536` |
| Square | `1024x1024` |

Edges must be multiples of 16; ratio ≤ 3:1.

## Errors

Scripts print clear messages for missing API key, invalid size, or missing input files.

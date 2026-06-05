# Hero text panel calibration

Automatically pick a headline panel anchor on full-bleed `avatar_media_3` slides so the navy text box avoids dense UI text in hero screenshots.

**See also:** [Avatar layouts](avatar-layouts.md) · [Avatar PiP calibration](avatar-calibration.md) · [Slide QA](slide-qa.md) · [Commands](commands.md)

## Quick start

```bash
pip install -e ".[hero-text-detect]"
praisonaippt hero-panel-place -i examples/heygen-50590-video-audio-heygen-images.yaml --force
```

Enable auto placement on build:

```yaml
hero_text_placement:
  auto: true
  method: hybrid
  detector: auto
  preferred_anchor: top_right
  fallback_anchor: top_left
  min_confidence: 0.55

sections:
  - verses:
      - slide_type: avatar_media_3
        headline: Outcomes
        media_path: slide_images/example.jpg
        media_fit: contain
        text_panel:
          anchor: auto
```

When `hero_text_placement.auto` is true, the build pipeline calls `maybe_auto_place_hero_text_deck` immediately after avatar PiP calibration.

## CLI

| Command | Purpose |
|---------|---------|
| `hero-panel-place -i deck.yaml` | Calibrate all `anchor: auto` hero slides |
| `hero-panel-place -i deck.yaml --slide 3` | Calibrate one slide |
| `hero-panel-place … --validation-image out.png` | Save annotated 1920×1080 diagram |
| `hero-panel-place … --write` | Write resolved anchors into deck (YAML or JSON) |
| `hero-panel-centre -i deck.yaml --slide 3` | Measure panel clearance vs UI text |
| `hero-panel-centre --hero-image screenshot.jpg` | Standalone screenshot measurement |
| `hero-panel-centre … --validation-image` | L/R/T/B pixel gaps to nearest UI text (like `pip-face-centre`) |

Validation PNG colours:

- **Red** — detected text regions (padded)
- **Green** — chosen panel
- **Grey** — rejected anchor candidates
- **Yellow** — PiP exclusion zone

## Detector chain

Offline `auto` order:

1. PaddleOCR `PP-OCRv5_mobile_det` (optional `[hero-text-paddle]`)
2. RapidOCR-onnx (if installed)
3. OpenCV EAST (`[hero-text-detect]`)
4. MSER variance heuristic (last resort)

Post-processing: NMS, 20 px hard + 8 px soft padding, drop tiny/huge boxes.

## Scoring

Six fixed anchors (`top_left` … `bottom`) are scored with IoA^1.8 against detected regions. Hard rejects:

- Panel overlaps PiP exclusion zone
- Overlap sum &gt; 15% of panel area

Lower score wins. `preferred_anchor` adds a soft bias via `anchor_weight`.

`media_fit: contain` letterboxing is modelled when mapping detections to 1920×1080 slide space.

## Vision fallback (optional)

Set `vision_fallback: true` and:

```bash
export PRAISONAIPPT_VISION_PROVIDER=openai   # or anthropic
export OPENAI_API_KEY=...
pip install -e ".[slide-vision]"
```

Vision suggests an anchor name only (JSON); offline scorer re-validates before use.

## Cache

Results cache under `.praisonaippt/hero-text-placement/` (or `hero_text_placement.cache_dir`). Invalidated by image mtime, panel dimensions, headline/subheader, and detector config.

## Pipeline QA

When `hero_text_placement.auto` is true, the pipeline runs `check_hero_text_placement` and fails if any slide confidence is below `min_confidence`.

## Python API

```python
from praisonaippt import maybe_auto_place_hero_text_deck, calibrate_hero_panel
from praisonaippt.hero_panel_measure import (
    measure_hero_panel_image,
    format_hero_panel_measure_report,
    save_hero_panel_validation_diagram,
)

data = maybe_auto_place_hero_text_deck(data, source_file="deck.yaml")
metrics, result = measure_hero_panel_image(
    "slide_images/hero.jpg",
    style=data["slide_style"],
    data=data,
    verse=verse,
)
print(format_hero_panel_measure_report(metrics, result=result))
```

## Optional dependencies

| Extra | Purpose |
|-------|---------|
| `[hero-text-detect]` | OpenCV EAST + MSER (lightweight) |
| `[hero-text-paddle]` | PaddleOCR primary detector |
| `[slide-vision]` | OpenAI / Anthropic vision fallback |

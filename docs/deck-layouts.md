# HeyGen-style deck layouts

Designed sales-deck slide types (`deck_*`) are defined in `praisonaippt/deck_slides.py` and registered via `DeckKindRenderer`.

## Build gallery

```bash
python examples/build_showcase_examples.py
```

Or individually:

```bash
praisonaippt -i examples/deck_template_gallery.yaml -o examples/deck_template_gallery.pptx --convert-video
```

## Protocol (verse fields)

| `slide_type` | Required | Collection / fields |
|--------------|----------|---------------------|
| `deck_title_split` | `text` or `headline` | `reference` subtitle; `avatar_video_path` |
| `deck_exec_summary` | `items` | `badge`, `heading`/`label`, `text` (max 3) |
| `deck_split_performance` | `rows` | `badge`, `number`, `text`; optional `header` |
| `deck_region_grid` | `cells` or `columns` | `number`, `label`, `text` (max 4) |
| `deck_product_columns` | `columns` | `number`, `label`, `text` (max 4) |
| `deck_channel_analysis` | `rows` | `number`, `label`, `text`; optional `header` |
| `deck_customer_segments` | `columns` | `number`, `label`, `text` (max 3) |
| `deck_thank_you` | `text` or `headline` | `reference`/`subheader`; `contact` or `email` |
| `deck_agenda` | `items` or `agenda` | strings auto-number `01`, `02`, … |
| `deck_intro_split` | `text` or `headline` | body: `reference`/`body`/`description`; `media_path`/`image_path` |
| `deck_opportunity_cards` | `columns` or `items` | `badge`, `heading`, `text`, `image_path` (max 3) |
| `deck_forecast_split` | `items` | `badge`, `text` (max 3); `media_path`/`image_path` |

## Colour presets

Set `color_scheme` on a verse (e.g. `sales_blue`, `agenda_periwinkle`). Presets live in `DECK_COLOR_PRESETS`.

## Video export

- **Avatar shape:** set `slide_style.layouts.pip.shape` to `circle` (default) or `square` / `rect` for a rectangular PiP.
- **Size:** `width_ratio` (default **0.20**) and `margin_in` (default **0.38**).
- **Framing:** `crop_y_ratio` (default **0.06**, lower = face higher) and `zoom_ratio` (default **1.45**).
- **Timeline:** `avatar_timeline: auto` uses continuous playback when one HeyGen file is shared across slides (reduces blink between slides).
- **Media:** deck slides bake images in PPTX; the compositor skips duplicate media overlays (`skip_media_overlay`).

See also `docs/video-export.md` for narration modes and compositor options.

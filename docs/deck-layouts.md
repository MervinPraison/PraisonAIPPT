# HeyGen-style deck layouts (`deck_*`)

Designed sales-deck slide types live in `praisonaippt/deck_slides.py` and register via `DeckKindRenderer`. There are **12** types in `DECK_SLIDE_TYPES`.

For standard content slides (`list`, `table`, `verse`), see [Standard slide layouts](slide-layouts.md). For global PiP tokens, see [Slide style reference](slide-style-reference.md).

---

## Build gallery

```bash
python examples/build_showcase_examples.py
```

Or individually:

```bash
praisonaippt -i examples/deck_template_gallery.yaml -o examples/deck_template_gallery.pptx --convert-video
```

Gallery source: `examples/deck_template_gallery.yaml` (one slide per `deck_*` type with matching `color_scheme`).

---

## Protocol (verse fields)

| `slide_type` | Required | Collection / fields | Notes |
|--------------|----------|---------------------|-------|
| `deck_title_split` | `text` or `headline` | `reference` / `subheader`; `avatar_video_path` | 50/50 — title left, avatar right |
| `deck_exec_summary` | `items` | `badge`, `heading`/`label`, `text` (max **3**) | Circular PiP top-right |
| `deck_split_performance` | `rows` | `badge`, `number`, `text`; optional `header` | Left panel + avatar strip; metrics right |
| `deck_region_grid` | `cells` or `columns` | `number`, `label`, `text` (max **4**); optional `map_path` | 2×2 grid; PiP bottom-left |
| `deck_product_columns` | `columns` | `number`, `label`, `text` (max **4**) | Four columns; PiP top-right |
| `deck_channel_analysis` | `rows` | `number`, `label`, `text`; optional `header` | Badges on white panel; avatar bottom-left |
| `deck_customer_segments` | `columns` | `number`, `label`, `text` (max **3**) | Three segments; PiP top-right |
| `deck_thank_you` | `text` or `headline` | `reference`/`subheader`; `contact` or `email` | Dual-tone thank you + contact bar |
| `deck_agenda` | `items` or `agenda` | strings → auto `01`, `02`, … | Two-column list; **no avatar** |
| `deck_intro_split` | `text` or `headline` | `reference`/`body`/`description`; `media_path`/`image_path` | Top text; bottom hero image (baked) |
| `deck_opportunity_cards` | `columns` or `items` | `badge`, `heading`, `text`, `image_path` (max **3**) | Card images baked; **no avatar** |
| `deck_forecast_split` | `items` | `badge`, `text` (max **3**); `media_path`/`image_path` | Top badges; bottom hero (baked) |

String list entries (agenda) normalise to dicts with auto `badge` values.

Set **`color_scheme`** on a verse to apply a named preset. Per-verse `slide_style` merges over deck defaults.

---

## Colour presets (`DECK_COLOR_PRESETS`)

| Preset | Typical gallery slide |
|--------|----------------------|
| `sales_blue` | `deck_title_split` |
| `exec_grey` | `deck_exec_summary` |
| `split_blue` | `deck_split_performance` |
| `region_navy` | `deck_region_grid` |
| `product_lavender` | `deck_product_columns` |
| `channel_violet` | `deck_channel_analysis` |
| `segments_sky` | `deck_customer_segments` |
| `thank_you_blue` | `deck_thank_you` |
| `agenda_periwinkle` | `deck_agenda` |
| `intro_grey` | `deck_intro_split` |
| `opportunity_grey` | `deck_opportunity_cards` |
| `forecast_grey` | `deck_forecast_split` |

Each preset merges hex keys such as `background_color`, `text_color`, `title_color`, `accent_color`, `badge_color`, `panel_color`, and layout-specific `left_panel_color` / `metric_color` where defined.

You may override individual colours in `slide_style` without using a preset name.

---

## Avatar shape per deck

Video mask from `deck_avatar_shape()`:

| Category | `slide_type` values | Default shape |
|----------|---------------------|---------------|
| **Rectangular full-bleed** | `deck_title_split`, `deck_thank_you`, `deck_split_performance`, `deck_channel_analysis` | `rect` — video fills the panel edge-to-edge (horizontal crop), **not** a large PiP circle |
| **Circular PiP** | `deck_exec_summary`, `deck_region_grid`, `deck_product_columns`, `deck_customer_segments` | `circle` — small corner overlay only |
| **No avatar region** | `deck_agenda`, `deck_intro_split`, `deck_opportunity_cards`, `deck_forecast_split` | — |

Override: per-kind `slide_style.layouts` + `avatar_shape`, or `video_export.avatar.shape`. PiP sizing uses `layouts.pip` (`width_ratio` 0.20, `margin_in` 0.38, `shape`, `crop_y_ratio`, `zoom_ratio`).

---

## Export regions (`export_deck_slide_regions`)

Inch-based `RegionBox` values for FFmpeg overlays:

| `slide_type` | `avatar` | `media` | `text_panel` | `content` |
|--------------|----------|---------|--------------|-----------|
| `deck_title_split` | right half | — | left title | — |
| `deck_exec_summary` | PiP top-right | — | title | three columns |
| `deck_split_performance` | bottom strip on left | — | left title | right metrics |
| `deck_region_grid` | PiP bottom-left | — | title | 2×2 grid |
| `deck_product_columns` | PiP top-right | — | title + subtitle | columns |
| `deck_channel_analysis` | bottom strip on left | — | dual-tone title | right rows |
| `deck_customer_segments` | PiP top-right | — | title | three columns |
| `deck_thank_you` | right half | — | left + contact | — |
| `deck_agenda` | — | — | title | numbered list |
| `deck_intro_split` | — | bottom half | top title + body | — |
| `deck_opportunity_cards` | — | — | title | card row |
| `deck_forecast_split` | — | bottom half | top badges | — |

Tune geometry via `slide_style.layouts` keys per deck kind (e.g. `avatar_width_ratio`, `left_width_ratio`, `columns_top_in`).

---

## `skip_media_overlay`

All `deck_*` types are in `DECK_BAKED_MEDIA_TYPES` — hero images and card photos are **embedded in the PPTX**. Video export sets `skip_media_overlay: true` so FFmpeg does not duplicate media on the LibreOffice PNG.

Avatar video is still overlaid when `avatar_video_path` is set and an `avatar` region exists.

---

## Minimal example

```text
presentation_title: Q1 review
sections:
  - section: Deck
    verses:
      - slide_type: deck_title_split
        color_scheme: sales_blue
        headline: Quarterly results
        avatar_video_path: assets/speaker.mp4
video_export:
  backend: compositor
  preset: standard
  avatar_timeline: auto
```

---

## Related

- [Video export](video-export.md) — compositor, narration, HeyGen workflow
- [Avatar layouts & PiP](avatar-layouts.md) — non-deck avatar `slide_type`s
- [YAML deck reference](yaml-reference.md)

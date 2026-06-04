# Slide style and layout tokens

PraisonAI PPT resolves styling from the deck’s `slide_style` object (and template layers). **Colours and fonts** live at the top level; **font sizes** use `typography.*` (points); **geometry** uses `layouts.<kind>.*` (inches, ratios, or hex).

Source: `praisonaippt/layout_tokens.py`, `praisonaippt/core.py` (`_resolve_theme`, `_table_palette`).

For a shorter colour-only table, see also `docs/snippets/slide_style_table.md`.

---

## Top-level `slide_style` colour keys

### Background triggers

| Key | Description |
|-----|-------------|
| `background_image` | Full-slide background image path |
| `background_color` | Hex background (e.g. `"#1A1A2E"`) |

If either is set, the deck enters **dark-background mode** unless `text_color` overrides detection.

### Colour keys

| Key | Light default | Auto-dark default |
|-----|---------------|-------------------|
| `text_color` | `#1A1A2E` | `#FFFFFF` |
| `reference_color` | `#404040` | `#CCCCCC` |
| `title_color` | `#1A1A2E` | `#FFFFFF` |
| `subtitle_color` | `#505050` | `#AAAAAA` |
| `section_title_color` | `#003366` | `#FFFFFF` |
| `highlight_color` | `#FF8C00` | `#FFD700` |
| `annotation_color` | `#1E50C8` | `#1E50C8` |

Explicit values always win over auto-dark for that key only.

### Dark-mode detection

| Condition | `dark_mode` |
|-----------|-------------|
| `text_color` is `white` / `#ffffff` | **true** |
| `text_color` set to another value | **false** |
| `text_color` omitted + dark background | **true** |
| Otherwise | **false** (light) |

### Other top-level keys

| Key | Default | Description |
|-----|---------|-------------|
| `font_name` | `Palatino` | Font family |
| `alignment` | `left` | `left`, `center`, `right` |
| `reference_position` | `bottom` | Verse/list: `bottom`, `below`, `top` |
| `split_max_length` | `200` | Verse split threshold (min 50) |
| `avatar_pip` | — | Enable floating PiP layout |

PiP also enables when `slide_style.layouts.pip` is a non-empty object.

---

## `typography.*` (pt)

| Key | Default | Used by |
|-----|---------|---------|
| `title_size_pt` | 44 | Title slide |
| `subtitle_size_pt` | 28 | Title slide |
| `section_title_size_pt` | 44 | Section slides |
| `section_subtitle_size_pt` | 24 | Section slides |
| `body_size_pt` | 32 | Verse / list (verse `font_size` overrides) |
| `reference_size_pt` | 28 | Verse reference (top) |
| `reference_size_small_pt` | 24 | Large-reference variant |
| `reference_size_list_top_pt` | 26 | List, ref at top |
| `reference_size_list_bottom_pt` | 22 | List, ref at bottom |
| `reference_size_bottom_pt` | 22 | Verse/list foot reference |
| `leading_title_size_pt` | 38 | Verse `leading_title` |
| `annotation_size_pt` | 46 | Annotation bubbles |
| `caption_ref_size_pt` | 22 | Image reference |
| `caption_body_size_pt` | 18 | Image caption |
| `big_number_size_pt` | 120 | Big number |
| `big_number_label_size_pt` | 32 | Big number label |
| `quote_size_pt` | 36 | Quote slide |
| `comparison_heading_size_pt` | 28 | Comparison headings |

```yaml
slide_style:
  typography:
    body_size_pt: 30
```

---

## `layouts.*` by kind

Read with `layout_in(style, kind, key)` from `slide_style.layouts.<kind>.<key>`. Null in YAML means “use package default”.

### `layouts.title`

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `title_top_in` | 2.5 |
| `subtitle_gap_in` | 0.25 |
| `custom_subtitle_min_len` | 40 |

### `layouts.section`

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `subtitle_dim_factor` | 0.76 |

### `layouts.verse`

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `ref_top_in` | 0.3 |
| `ref_height_in` | 0.7 |
| `ref_height_large_in` | 0.95 |
| `body_gap_in` | 0.15 |
| `leading_title_top_in` | 0.35 |
| `leading_title_ref_gap_in` | 0.2 |
| `bottom_ref_top_in` | 6.0 |
| `bottom_ref_height_in` | 0.7 |
| `default_body_height_in` | 4.5 |
| `no_ref_body_top_in` | 1.5 |
| `no_ref_body_height_in` | 3.8 |
| `bottom_margin_in` | 0.15 |
| `extra_ref_reserve_in` | 1.32 |

Content width: `min(9.0, slide_width − margins)` on widescreen (PiP-aware).

### `layouts.list`

| Key | Default |
|-----|---------|
| `margin_in` | 0.75 |
| `list_bottom_margin_in` | 1.0 |
| `ref_gap_in` | 0.18 |

### `layouts.image`

| Key | Default |
|-----|---------|
| `margin_in` | 0.35 |
| `caption_height_in` | 0.9 |

### `layouts.table`

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `top_in` | 0.75 |
| `bottom_in` | 0.35 |
| `ref_gap_in` | 0.15 |
| `min_font_pt` | 11 |

**Table colour overrides** (via `layout_in`, not in `LAYOUT_DEFAULTS`):

| Key | Light | Dark |
|-----|-------|------|
| `header_fill` | `#1E40AF` | `#2563EB` |
| `header_text` | `#FFFFFF` | `#FFFFFF` |
| `row_fill` | `#F3F4F6` | `#1F2937` |
| `row_alt_fill` | `#E5E7EB` | `#374151` |
| `body_text` | `#111827` | theme `body` |

### `layouts.pip`

| Key | Default |
|-----|---------|
| `width_ratio` | 0.20 |
| `margin_in` | 0.38 |
| `text_gap_in` | 0.35 |
| `shape` | `circle` |
| `crop_y_ratio` | 0.02 (circle PiP; per `layouts.<slide_type>` for avatar slides) |
| `zoom_ratio` | 1.45 |
| `border_color` | `#FFFFFF` |
| `border_width_pt` | 2.5 |

### `layouts.two_column` / `comparison` / `quote` / `picture_text`

| Kind | Notable defaults |
|------|------------------|
| `two_column` | `top_in` 0.9, `column_gap_in` 0.4, `bottom_reserve_in` 0.5 |
| `comparison` | `top_in` 0.75, `heading_height_in` 0.55, `column_gap_in` 0.4 |
| `quote` | `margin_in` 0.8, `top_in` 2.0 |
| `picture_text` | `margin_in` 0.35, `image_width_ratio` 0.48 |

### `layouts.hebrew_rename`

| Key | Default |
|-----|---------|
| `row_y_in` | `[1.15, 4.05]` |
| `box_height_in` | 1.35 |
| `reference_width_in` | 10.0 |
| `left_x_factor` | 0.35 |
| `right_x_factor` | 5.15 |
| `box_width_factor` | 4.2 |

### `layouts.title_only` / `big_number`

| Kind | Default |
|------|---------|
| `title_only` | `margin_in` 0.6 |
| `big_number` | `margin_in` 0.6 |

### Avatar layouts

| Block | Notable defaults |
|-------|------------------|
| `avatar_media_1` | `media_width_ratio` 0.50 |
| `avatar_media_2` | `media_width_ratio` 0.40 |
| `avatar_media_3` | `pip_width_ratio` 0.14, `pip_margin_in` 0.45 |
| `avatar_name_card` | `panel_width_ratio` 0.42, pill heights |
| `avatar_headline` | `panel_margin_in` 0.75 |
| `avatar_headline_full` | `panel_width_ratio` 0.48, `panel_height_in` 1.45 |
| `avatar_quote` | `quote_bg_color` `#1E3A5F`, `top_in` 1.4 |
| `avatar_outro` | `diamond_size_in` 1.85 |
| `avatar_border` / `media_border` | `border_inset_in` 0.25, `border_width_pt` 8 |
| `avatar_media_border_1` | `media_width_ratio` 0.60 |
| `avatar_media_border_2` | `media_width_ratio` 0.40 |
| `avatar_media_border_3` | `pip_width_ratio` 0.18 |

Full list: [Avatar layouts & PiP](avatar-layouts.md).

### Deck layouts (`deck_*`)

Each `deck_*` kind has `margin_in`, often `color_scheme`, and layout-specific keys (`avatar_width_ratio`, `pip_position`, `columns_top_in`, …). See [Deck layouts](deck-layouts.md).

---

## How `layout_in` merge works

```text
slide_style.layouts.<kind>.<key>  →  override
LAYOUT_DEFAULTS[kind][key]        →  fallback when YAML omits key
```

`typography_pt(style, key)` reads `slide_style.typography.<key>` against `TYPOGRAPHY_DEFAULTS`.

**Template merge order** (low → high): template `extends` → `template:` / `--template` → deck `extends:` → `slide_style.preset` → `slide_style.overrides` → inline `slide_style`. See [Theme templates](templates.md).

---

## Table colours on dark backgrounds

`add_table_slide` sets explicit cell fills from `_table_palette` so PowerPoint’s default light stripes never produce white-on-pale text.

```yaml
slide_style:
  background_color: "#1A1A2E"
  layouts:
    table:
      header_fill: "#2563EB"
      row_fill: "#1F2937"
      row_alt_fill: "#374151"
      bottom_in: 0.4
      min_font_pt: 11
```

Vertical budget: `pip_top − top_in − reference − bottom_in`. Font shrinks from slide `font_size` down to `min_font_pt`.

---

## Quick reference

| Namespace | Unit | Purpose |
|-----------|------|---------|
| Top-level colour keys | hex / names | Theme and dark mode |
| `typography.*` | pt | Font sizes |
| `layouts.<kind>.*` | in, ratio, hex | Position, PiP, table colours |

Omitting `slide_style` entirely keeps package defaults.

---

## SDK validation

On load (`load_verses_from_file`, `load_verses_from_dict`, CLI build), `validate_verses()` checks:

- **Enums** — `alignment`, `reference_position`, `list_type`, `image_fit`, `media_fit`, `narration_mode`, `sync_mode`, `color_scheme`, `video_export.*`, `layouts.pip.shape`
- **Shapes** — `slide_size`, `table_rows`, `header_row`, font sizes, timing numbers
- **Unknown keys** — warning with “did you mean …?” for top-level, `slide_style`, `typography`, `layouts.<kind>`, and `video_export`

Implementation: `praisonaippt/yaml_validate.py` (called from `praisonaippt/schema.py`).

---

## Related

- [Layouts overview](layouts-overview.md)
- [Theme templates](templates.md)

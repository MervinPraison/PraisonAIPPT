| Field / Key | Type | Default (light) | Auto-dark default | Description |
|-----------|------|-----------------|-------------------|-------------|
| `background_image` | string | — | — | Path to a background image file |
| `background_color` | string | — | — | Hex background color e.g. `"#1A1A2E"` |
| `text_color` | string | `#1A1A2E` dark | `#FFFFFF` white | Body / verse text |
| `reference_color` | string | `#404040` gray | `#CCCCCC` light gray | Verse reference line |
| `title_color` | string | theme default | `#FFFFFF` white | Title slide title |
| `subtitle_color` | string | theme default | `#AAAAAA` | Title slide subtitle |
| `section_title_color` | string | `#003366` dark blue | `#FFFFFF` white | Section heading slides |
| `highlight_color` | string | `#FF8C00` orange | `#FFD700` yellow | Default color for simple string highlights |
| `annotation_color` | string | `#1E50C8` blue | `#1E50C8` blue | Numbered bubble annotations (❶❷❸…) |
| `font_name` | string | **`Palatino`** | **`Palatino`** | Font family for all text |
| `alignment` | string | **`"left"`** | **`"left"`** | Default text alignment (`"left"`, `"center"`, `"right"`) |
| `reference_position` | string | **`"top"`** | **`"top"`** | `"top"` or `"bottom"` for verse reference line |
| `split_max_length` | integer | **`200`** | **`200`** | Deck-level default max characters before verse text splits |

### `typography.*` (pt sizes)

| Key | Default | Used by |
|-----|---------|---------|
| `title_size_pt` | 44 | Title slide |
| `subtitle_size_pt` | 28 | Title slide |
| `section_title_size_pt` | 44 | Section slides |
| `section_subtitle_size_pt` | 24 | Section slides |
| `body_size_pt` | 32 | Verse / list body (overridden by per-verse `font_size`) |
| `reference_size_pt` | 28 | Verse reference (top) |
| `reference_size_small_pt` | 24 | Large-reference variant |
| `reference_size_bottom_pt` | 22 | Reference at bottom |
| `reference_size_list_top_pt` | 26 | List slide, ref at top |
| `reference_size_list_bottom_pt` | 22 | List slide, ref at bottom |
| `leading_title_size_pt` | 38 | Verse `leading_title` |
| `annotation_size_pt` | 46 | Highlight annotation bubbles |
| `caption_ref_size_pt` | 22 | Image slide reference line |
| `caption_body_size_pt` | 18 | Image slide caption |

### `layouts.title` (inches)

| Key | Default | Notes |
|-----|---------|-------|
| `margin_in` | 0.6 | Horizontal margin |
| `content_width_in` | slide − 2×margin | Optional fixed width |
| `title_top_in` | 2.5 | Title textbox top |
| `subtitle_gap_in` | 0.25 | Gap below title |
| `custom_subtitle_min_len` | 40 | Subtitle length threshold for custom layout |

### `layouts.section` (inches)

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `subtitle_dim_factor` | 0.76 |

Sizes use `typography.section_title_size_pt` / `section_subtitle_size_pt`.

### `layouts.verse` (inches)

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `content_width_in` | min(9.0, slide − 2×margin) on widescreen |
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

### `layouts.list` (inches)

| Key | Default |
|-----|---------|
| `margin_in` | 0.6 |
| `list_top_in` | 0.35 |
| `list_bottom_margin_in` | 0.4 |
| `list_bottom_reserve_in` | 6.0 |
| `ref_gap_in` | 0.12 |
| `ref_bottom_offset_in` | 0.35 |

### `layouts.image` (inches)

| Key | Default |
|-----|---------|
| `margin_in` | 0.35 |
| `caption_height_in` | 0.9 |

### `layouts.hebrew_rename` (inches)

| Key | Default |
|-----|---------|
| `row_y_in` | `[1.15, 4.05]` |
| `box_height_in` | 1.35 |
| `reference_width_in` | 10.0 |
| `left_x_factor` | 0.35 |
| `right_x_factor` | 5.15 |
| `box_width_factor` | 4.2 |
| `caption_height_in` | 0.85 |
| `caption_bottom_in` | 0.45 |
| `caption_margin_in` | 0.5 |

See [templates.md](../templates.md) for merge priority, examples, and custom slide types.

!!! note
    **Package defaults**: When `background_image` or `background_color` is set, all text colors automatically default to white/light variants. Individual color keys override these auto-defaults. `font_name`, `alignment`, and `reference_position` have opinionated defaults (Palatino / left / top).

!!! tip
    **Zero regression**: If you omit `slide_style` entirely, all slides retain their standard default parameters automatically.

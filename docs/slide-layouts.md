# Standard slide layouts

PraisonAI PPT builds slides from a YAML/JSON deck: a **title slide**, optional **section slides**, then one slide per entry under `sections[].verses[]`. Each verse is routed to a renderer that calls the matching `add_*_slide` function in `praisonaippt/core.py`.

For rich text (`highlights`, alignment, fonts), see [Rich text formatting](formatting.md). For avatar and `deck_*` layouts, see [Avatar layouts & PiP](avatar-layouts.md) and [Deck layouts](deck-layouts.md).

---

## How slides are chosen

Renderer resolution (`resolve_renderer` in `praisonaippt/slide_renderers.py`):

1. **`slide_type`** — If set and registered, that renderer runs (e.g. `table`, `quote`, `image`).
2. **`list_type`** — If `slide_type` is omitted and `list_type` is `"bullet"` or `"numbered"`, the **list** renderer runs.
3. **Default verse** — Otherwise the **verse** renderer runs (title + body + reference, with optional auto-splitting).

Explicit `slide_type: verse` is valid but rarely needed.

**Structural slides (not `slide_type` on a verse):**

| Source | Function | YAML location |
|--------|----------|----------------|
| Opening title | `add_title_slide` | `presentation_title`, optional `presentation_subtitle` |
| Section divider | `add_section_slide` | Per section: `section`, optional `section_subtitle` |

---

## Standard `slide_type` reference

| `slide_type` | Required | Optional (common) |
|--------------|----------|-------------------|
| *(omit)* / `verse` | `reference` **or** `text` | `highlights`, `large_text`, `alignment`, `font_size`, `reference_position`, `leading_title`, `text_below_reference`, `split_max_length`, `notes`, `avatar_video_path`, timing fields |
| `list` | `reference` **or** `text` | `list_type` (`bullet` / `numbered`), `alignment`, `font_size`, `notes`, `avatar_video_path` |
| `title_only` | `text` **or** `reference` | `reference` as subtitle when `text` is set, `font_size`, `notes` |
| `two_column` | `columns` (≥2) **or** `left` / `right` | Per-column `highlights`, `alignment`, `font_size` |
| `comparison` | `columns` (≥2) with `heading` / `text` | `reference`, `highlights` per column (first **two** columns rendered) |
| `big_number` | `number` (or non-empty `text` as fallback) | `label`, `reference` |
| `quote` | `text` | `reference` (attribution with —), `font_size`, `alignment` (default `center`) |
| `picture_text` | `image_path`, `text` | `image_side` (`left`/`right`), `image_fit` (`contain`/`cover`/`fill`) |
| `table` | `table_rows` **or** `rows` | `header_row` (default `true`), `reference`, `font_size` |
| `image` | `image_path` | `image_fit`, `reference`, `text` (second caption line) |
| `hebrew_rename` | `hebrew_rows` | `hebrew_font_size`, `hebrew_highlight_color`, `reference`, `text` (caption) |

**`list_type` without `slide_type`:** set `list_type: bullet` or `numbered` with newline-separated `text`.

**`columns` shapes:**

- **Two column:** `[{text: "…", highlights: [...]}, …]` or `left` / `right`.
- **Comparison:** `[{heading: "…", text: "…"}, …]`.

**`hebrew_rows`:** up to two objects: `left`, `right`, `highlight_in_right`.

---

## Table slides

### Data

```yaml
table_rows:
  - [Column A, Column B]
  - [Row 1, Value 1]
```

Alias: `rows:` with the same structure.

### `header_row`

Default **`true`**. Row 0 uses header fill and bold text.

### Dark theme cell fills

When the theme is in **dark mode** (`background_image` / `background_color` or white `text_color`), cells use explicit fills — not PowerPoint’s default light zebra stripes:

| Role | Default hex (dark) |
|------|-------------------|
| Header background | `#2563EB` |
| Header text | `#FFFFFF` |
| Body row | `#1F2937` |
| Alternating body row | `#374151` |

Override via `slide_style.layouts.table`: `header_fill`, `header_text`, `row_fill`, `row_alt_fill`, `body_text`. See [Slide style reference](slide-style-reference.md).

### Reference and PiP fit

- Optional `reference` is drawn **below the table** (italic, `reference_color`).
- Table height respects **`pip_top_inches`** when PiP is enabled; font shrinks to `layouts.table.min_font_pt` (default **11**) so rows and reference fit above the avatar.

---

## Common verse fields

Recognised keys (`schema.py` `_VERSE_KEYS`). Unknown keys log a warning.

### Content and typography

| Field | Used by |
|-------|---------|
| `reference`, `text` | Most layouts |
| `highlights`, `large_text` | Verse, columns |
| `alignment`, `font_size`, `reference_font_size`, `reference_position` | Verse, list, quote, … |
| `leading_title`, `text_below_reference` (+ highlights / large_text) | Verse (first split only) |
| `split_max_length` | Verse auto-split (deck default 200) |
| `notes` | Presenter notes |

### Layout-specific

| Field | Types |
|-------|-------|
| `list_type` | List routing |
| `columns`, `left`, `right`, `heading` | `two_column`, `comparison` |
| `number`, `label` | `big_number` |
| `image_path`, `image_fit`, `image_side` | `image`, `picture_text` |
| `table_rows`, `rows`, `header_row` | `table` |
| `hebrew_rows`, … | `hebrew_rename` |

### Avatar overlay on standard slides

| Field | Behaviour |
|-------|-----------|
| `avatar_video_path` | Floating PiP after slide build (`place_floating_avatar_pip`) |
| `avatar_poster_path` | Poster frame for PiP |

Dedicated `avatar_*` / `deck_*` types handle layout internally.

### Video export (optional)

| Field | Purpose |
|-------|---------|
| `duration_sec`, `audio_start_sec`, `audio_path` | Slide timing |
| `narration_mode`, `sync_mode` | Per-slide narration |

Deck-wide: `video_export`, `slide_timestamps`. See [Video export](video-export.md). For JPEG golden tests and MP4 frame QA, see [Slide QA](slide-qa.md).

---

## Minimal YAML examples

### Default verse

```yaml
- reference: John 3:16 (NKJV)
  text: For God so loved the world that he gave his only Son.
  highlights:
    - God so loved
```

### List

```yaml
- reference: Key points
  text: |
    First point
    Second point
  list_type: bullet
```

### Table (dark deck + PiP)

```yaml
slide_style:
  background_color: "#000000"
  text_color: white
  layouts:
    pip:
      width_ratio: 0.20
      shape: circle

- slide_type: table
  header_row: true
  table_rows:
    - [Capability, Status, What it means]
    - [Dreaming, Research preview, Background memory curation between sessions]
    - [Outcomes, Public beta, Rubric grader]
  reference: Code with Claude SF · 6 May 2026
  avatar_video_path: examples/heygen-article-50590.mp4
```

### Comparison

```yaml
- slide_type: comparison
  columns:
    - heading: Before
      text: The law condemns sin.
    - heading: After
      text: Grace brings salvation through faith.
```

---

## Behaviour notes

- **Long verse text:** Splits when length exceeds `split_max_length` (default 200).
- **`title_only`:** With both `text` and `reference`, `text` is the title and `reference` the subtitle.
- **`image`:** `reference` is first caption line (bold); `text` is optional second line.
- **Assets:** Paths resolve relative to the YAML file when loaded from disk.
- **Registry:** `praisonaippt.cli list-slides` / `list_renderers()` includes avatar and `deck_*` types.

---

## Related

- [Slide style reference](slide-style-reference.md)
- [Avatar layouts & PiP](avatar-layouts.md)
- [YAML deck reference](yaml-reference.md)

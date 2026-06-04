# Avatar layouts and PiP

Speaking-head layouts (`avatar_*`, `media_*`) place HeyGen or other avatar video in fixed regions. Standard slides (`list`, `table`, `verse`, …) can add a **floating** picture-in-picture (PiP) in the bottom-right when `avatar_video_path` is set. Video export uses the same geometry via the compositor; see [Video export](video-export.md).

---

## Avatar `slide_type` values

Sixteen kinds are registered in `AVATAR_SLIDE_TYPES`. Set `slide_type` on a verse.

| `slide_type` | Layout | Required fields | Typical optional fields |
|--------------|--------|-----------------|-------------------------|
| `avatar_only` | Full-slide avatar | — | `avatar_video_path`, `avatar_poster_path`, `notes` |
| `media_only` | Full-slide media | `media_path` | `media_fit`, `media_poster_path` |
| `avatar_media_1` | 50/50: media left, avatar right | — | `avatar_video_path`, `media_path`, `media_fit` |
| `avatar_media_2` | 40/60 split | — | same as `avatar_media_1` |
| `avatar_media_3` | Full media + corner PiP | — | `avatar_video_path`, `media_path` |
| `avatar_name_card` | Avatar + name/title pills | `headline` | `subheader`, `avatar_video_path` |
| `avatar_headline` | Headline + corner PiP | `headline` | `subheader`, `avatar_video_path` |
| `avatar_headline_full` | Full avatar + top panel | `headline` | `subheader`, `avatar_video_path` |
| `avatar_quote` | Quote slide + PiP | `text` | `reference`, `alignment`, `font_size` |
| `avatar_border` | Bordered avatar inset | — | `avatar_video_path` |
| `media_border` | Bordered media inset | `media_path` | `media_fit` |
| `avatar_media_border_1` | Bordered 60/40 split | — | `avatar_video_path`, `media_path` |
| `avatar_media_border_2` | Bordered 40/60 split | — | same |
| `avatar_media_border_3` | Bordered full media + PiP | — | same |
| `avatar_intro` | Decorative intro | — | `notes` |
| `avatar_outro` | Full avatar + centre diamond | — | `avatar_video_path` |

Validation enforces `media_path` on `media_only` / `media_border`, `headline` on name/headline layouts, and `text` on `avatar_quote`. `media_fit` must be `contain`, `cover`, or `fill` when set.

Without `avatar_video_path`, avatar regions render as grey placeholders in PPTX; the compositor skips missing files.

### `avatar_quote` and double avatar

For **`avatar_quote`**, the PPTX intentionally **does not** embed a second headshot shape — only the quote layout is drawn. The HeyGen PiP is added in **MP4 export** so you do not get two avatars on screen. Slide JPEG previews may show no face on that slide; compare the MP4. Tune PiP framing with [Avatar PiP calibration](avatar-calibration.md).

---

## `slide_style.layouts.pip`

Global PiP defaults (inches unless noted). Per-layout blocks (e.g. `layouts.avatar_media_3`) may override `pip_width_ratio`, `pip_margin_in`, or `pip_position`.

| Key | Default | Role |
|-----|---------|------|
| `shape` | `circle` | PiP mask when `avatar_shape` is `circle` (legacy alias) |
| `avatar_shape` | `auto` | `auto`, `circle`, `square`, `h_rect`, `v_rect` — see below |

### `avatar_shape` (per verse or `layouts.<kind>`)

| Value | Use |
|-------|-----|
| `auto` (default) | Layout picks shape: half-slide → `h_rect`/`v_rect`; bottom strip → `h_rect`; corner PiP → `circle` |
| `circle` | Round mask (small PiP) |
| `square` | Square mask |
| `h_rect` / `horizontal` / `wide` | Wide rectangle, cover crop (no black bars) |
| `v_rect` / `vertical` / `tall` | Tall rectangle, cover crop |

```yaml
- slide_type: deck_split_performance
  avatar_shape: h_rect
  avatar_video_path: examples/heygen-article-50590.mp4
```
| `width_ratio` | `0.20` | PiP edge length as fraction of slide width |
| `margin_in` | `0.38` | Inset from anchor corner |
| `text_gap_in` | `0.35` | Horizontal reserve so list/verse/table text clears the PiP |
| `crop_y_ratio` | `0.06` | Vertical crop bias (lower → face higher) |
| `zoom_ratio` | `1.45` | Scale before centre crop |
| `border_color` | `#FFFFFF` | PiP ring in PPTX |
| `border_width_pt` | `2.5` | PiP ring width |

**Enable PiP reserve on standard slides:** set `slide_style.avatar_pip: true`, or define a non-empty `slide_style.layouts.pip` object.

`VideoOptions.from_dict` merges `layouts.pip` `crop_y_ratio`, `zoom_ratio`, and `shape` into compositor options.

---

## Per-layout defaults (`layouts.<slide_type>`)

Overrides merge via `layout_in(style, kind, key)` — layout-specific keys win; shared keys fall back to `layouts.pip`.

| Block | Notable keys (defaults) |
|-------|-------------------------|
| `avatar_media_1` | `media_width_ratio` 0.50, `gap_in` 0 |
| `avatar_media_2` | `media_width_ratio` 0.40, `gap_in` 0 |
| `avatar_media_3` | `pip_width_ratio` 0.14, `pip_margin_in` 0.45 |
| `avatar_headline` | `panel_margin_in` 0.75, `pip_width_ratio` 0.14 |
| `avatar_headline_full` | `panel_width_ratio` 0.48, `panel_height_in` 1.45 |
| `avatar_name_card` | `panel_width_ratio` 0.42, pill heights, `pill_gap_in` |
| `avatar_quote` | `quote_bg_color` `#1E3A5F`, `top_in` 1.4 |
| `avatar_media_border_1` | `media_width_ratio` 0.60, border tokens |
| `avatar_media_border_2` | `media_width_ratio` 0.40 |
| `avatar_media_border_3` | `pip_width_ratio` 0.18 |
| `avatar_border` / `media_border` | `border_inset_in` 0.25, `border_width_pt` 8 |

`pip_position`: `bottom_right` (default), `top_right`, `bottom_left`, `top_left`.

---

## `avatar_timeline`

Set on `video_export` or `VideoOptions`:

| Value | Behaviour |
|-------|-----------|
| `per_slide` | Each slide’s avatar overlay starts at 0 s in the source file |
| `continuous` | One shared file: `video_start_sec` advances by each slide’s duration |
| `auto` (default) | `continuous` when all content slides share one `avatar_video_path`; else `per_slide` |

Use `continuous` with one HeyGen MP4 and per-verse `audio_start_sec` / `duration_sec` (or `slide_timestamps`) to avoid blink between slides.

---

## Video compositor

- **Shape:** `video_export.avatar.shape` or `layouts.pip.shape`. Circle values apply an alpha mask; `square`/`rect` use rectangular overlays.
- **Framing:** `avatar.fit` (`cover` default) with `crop_y_ratio` and `zoom_ratio`.
- **Continuous trim:** FFmpeg `trim` with start offset and slide duration per slide when timeline is continuous.
- **Floating PiP:** manifest uses `export_floating_pip_box`; shape from pip settings.

---

## Floating PiP on standard slides

When `avatar_video_path` is set on a verse whose `slide_type` is **not** in `AVATAR_SLIDE_TYPES` or `deck_*`, `_finish_slide` calls `place_floating_avatar_pip` after the body. Applies to `list`, `table`, `verse`, `quote`, `two_column`, etc.

```yaml
slide_style:
  layouts:
    pip:
      width_ratio: 0.20
      margin_in: 0.38
      shape: circle
      crop_y_ratio: 0.06
      zoom_ratio: 1.45

sections:
  - verses:
      - slide_type: list
        text: "Point one\nPoint two"
        reference: Demo
        avatar_video_path: examples/heygen-article-50590.mp4
```

---

## Gallery YAML

`examples/avatar_layouts.yaml` lists all sixteen layouts. Build:

```bash
praisonaippt -i examples/avatar_layouts.yaml -o examples/avatar_layouts_built.pptx --convert-video
```

Or: `python examples/build_showcase_examples.py`.

### Example `video_export` block

```yaml
video_export:
  backend: compositor
  narration_mode: fixed
  preset: draft
  slide_duration_sec: 3
  avatar_timeline: auto
  avatar:
    fit: cover
    shape: circle
    crop_y_ratio: 0.06
    zoom_ratio: 1.45
  captions:
    enabled: false
```

---

## Related

- [Video export](video-export.md)
- [Deck layouts](deck-layouts.md)
- [Slide style reference](slide-style-reference.md)

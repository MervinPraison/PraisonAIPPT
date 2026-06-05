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
| `avatar_media_3` | Hero screenshot + corner PiP | `headline`, `media_path` | `text_panel`, `hero_layout`, `text_style`, `media_fit` |
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

For **`avatar_quote`**, the PPTX intentionally **does not** embed a second headshot shape — only the quote layout is drawn. The HeyGen PiP is added in **MP4 export** so you do not get two avatars on screen. Slide JPEG previews may show no face on that slide unless `jpeg_show_pip_preview: true` (grey placeholder only); compare the MP4 or `mp4-frames/`. Tune PiP framing with [Avatar PiP calibration](avatar-calibration.md).

For **`avatar_media_3`**, media is baked into the slide PNG for MP4 export (`skip_media_overlay`); the live PiP is composited in FFmpeg. JPEGs may show a still/grey ring in the PiP corner — use [Slide QA — MP4 frames](slide-qa.md) for PiP truth.

---

<a id="avatar_media_3-full-bleed-hero"></a>

## `avatar_media_3` — stacked vs full-bleed hero

Two layout modes controlled by `slide_style.layouts.avatar_media_3.hero_layout` (or per-verse `text_panel.hero_layout`):

| Mode | Media region | Text | Default |
|------|--------------|------|---------|
| **`stacked`** | Band **below** a fixed top-left navy panel | Opaque panel (`text_style: navy_panel`) | Yes (backward compatible) |
| **`full_bleed`** | **Full slide** (`cover` / `contain` on entire content area) | Floating panel at a chosen **anchor** | HeyGen images variant |

### `text_panel` (per verse or layout defaults)

```yaml
slide_style:
  layouts:
    avatar_media_3:
      hero_layout: full_bleed
      text_style: semi_panel      # navy_panel | semi_panel | overlay
      panel_width_ratio: 0.38
      panel_height_in: 0.82
      panel_margin_in: 0.32
      text_pip_gap_in: 0.14       # clearance from PiP box

sections:
  - verses:
      - slide_type: avatar_media_3
        headline: Dreaming
        subheader: Persistent, proactive agents — work between sessions
        media_path: slide_images/HHt8A9BbYAAUfvZ.jpg
        media_fit: cover
        text_panel:
          anchor: top_right       # top_left | top_right | … | auto (see hero-text-calibration.md)
          width_ratio: 0.38       # optional override
        avatar_video_path: examples/heygen-article-50590.mp4
        video_overlay: *pip_hero_overlay
```

| `text_style` | Rendering |
|--------------|-----------|
| `navy_panel` / `semi_panel` | Opaque navy box + white headline/subheader (`_add_text_panel`) |
| `overlay` | Text only, no fill (`_add_headline_content`) — use on dark hero regions |

Text boxes are **shifted** when they would overlap the bottom-right PiP region (`text_pip_gap_in`).

**Reference deck:** `examples/heygen-50590-video-audio-heygen-images.yaml` — full-bleed product screenshots with `text_panel.anchor: auto` and [Hero text panel calibration](hero-text-calibration.md). See [HeyGen examples](heygen-examples.md) and [Slide QA](slide-qa.md).

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
| `crop_y_ratio` | `0.02` | Vertical crop (lower → less headspace above face in circle) |
| `zoom_ratio` | `1.47` | Scale before centre crop |
| `border_color` | `#FFFFFF` | PiP ring in PPTX |
| `border_width_pt` | `2.5` | PiP ring width |

**Enable PiP reserve on standard slides:** set `slide_style.avatar_pip: true`, or define a non-empty `slide_style.layouts.pip` object.

`VideoOptions.from_dict` merges `layouts.pip` `crop_y_ratio`, `zoom_ratio`, and `shape` into compositor options.

---

## Per-layout defaults (`layouts.<slide_type>`)

Overrides merge via `layout_in(style, kind, key)` — layout-specific keys win; shared keys fall back to `layouts.pip`.

| Block | Headspace (`crop_y` / `zoom`) | Notes |
|-------|-------------------------------|--------|
| `pip` (circle) | `0.02` / `1.47` (+ circle trim) | Floating PiP on list/verse slides |
| `avatar_only` | `0.09` / `1.38` | Full-bleed headshot |
| `avatar_media_1` / `_2` | `0.07` / `1.40` | Split columns |
| `avatar_media_3` | `0.025` / `1.46` | Corner PiP; optional `hero_layout`, `text_style`, `text_anchor`, `text_pip_gap_in` |
| `avatar_headline` / `avatar_quote` | `0.025` / `1.46` | Corner PiP |
| `avatar_headline_full` | `0.10` / `1.36` | Top panel + avatar |
| `avatar_name_card` | `0.09` / `1.38` | Name card |
| `avatar_media_border_*` | `0.07`–`0.025` | Bordered splits / corner PiP |
| `avatar_border` | `0.08` / `1.40` | Inset frame |

Lower `crop_y_ratio` = less empty space above the head. Circular masks also apply a small extra trim in code.

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

- [Slide QA (golden, MP4 frames)](slide-qa.md)
- [Video export](video-export.md)
- [Deck layouts](deck-layouts.md)
- [Slide style reference](slide-style-reference.md)

# Deck reference (YAML or JSON)

Quick reference for top-level deck keys, sections, verses, and video export. Use `.yaml`, `.yml`, or `.json` with the same schema; `praisonaippt -i deck.json` runs the same validation and pipeline as YAML. HeyGen variant outputs remain `.yaml` after `sync-variants`.

For layout-specific fields see [Standard slide layouts](slide-layouts.md), [Avatar layouts](avatar-layouts.md), and [Deck layouts](deck-layouts.md).

Source: `praisonaippt/schema.py`, `praisonaippt/yaml_validate.py`, `praisonaippt/video_exporter.py`, `praisonaippt/deck_pipeline.py`.

---

## Top-level keys

| Key | Required | Description |
|-----|----------|-------------|
| `presentation_title` | recommended | Opening title slide |
| `presentation_subtitle` | optional | Title slide subtitle |
| `sections` | yes (auto `[]` if omitted) | List of section objects |
| `slide_style` | optional | Colours, typography, `layouts.*` — see [Slide style reference](slide-style-reference.md) |
| `slide_size` | optional | e.g. `widescreen` |
| `template` | optional | Named theme template |
| `extends` | optional | Parent template chain |
| `auto_upload_gdrive` | optional | Upload after build |
| `video_export` | optional | MP4 compositor options — see [Video export](video-export.md) |
| `pipeline` | optional | CI gates, sync, and orchestration — see below |
| `avatar_calibration` | optional | PiP framing — see below |
| `hero_text_placement` | optional | Hero headline anchor — see below |
| `slide_transitions` | optional | MP4 slide transitions — [Slide transitions](slide-transitions.md) |
| `slide_timestamps` | optional | Wall-clock start (seconds) per slide for video timing |
| `slide_images_dir` | optional | Export `slide-NNN.jpg` after build — [Slide JPEG export](slide-images.md) |
| `skip_title_slide` | optional | Omit auto title slide (`presentation_title` / `presentation_subtitle`) |
| `jpeg_show_pip_preview` | optional | Grey PiP placeholder on `avatar_quote` in PPTX/JPEG (MP4 still uses live overlay) |
| `slide_qa` | optional | Deck-wide QA manifest defaults — [Slide QA](slide-qa.md) |

Keys starting with `x-` are ignored (YAML anchors). Unknown keys log a warning; invalid enum values (e.g. `narration_mode`, `color_scheme`, `layouts.pip.shape`) raise `SchemaError` at load time via `validate_verses()` / `load_verses_from_file()`.

---

## Section object

| Key | Description |
|-----|-------------|
| `section` | Section title (creates a section slide when non-empty) |
| `section_subtitle` | Optional subtitle on section slide |
| `verses` | List of verse/slide objects |

---

## Verse keys (shared)

| Key | Type | Description |
|-----|------|-------------|
| `slide_type` | string | Renderer choice (`table`, `avatar_headline`, `deck_agenda`, …) |
| `reference` | string | Footline, caption, or subtitle depending on layout |
| `text` | string | Body, list items (`\n`-separated), or headline |
| `notes` | string | Presenter notes (also used for captions / TTS) |
| `highlights` | list | Rich text highlights — [Formatting](formatting.md) |
| `font_size` | int | Body pt size (overrides `typography.body_size_pt`) |
| `alignment` | string | `left`, `center`, `right` |
| `avatar_video_path` | string | HeyGen MP4 or other avatar file |
| `avatar_poster_path` | string | Still frame for PiP |
| `media_path` | string | Image or video for media regions |
| `media_fit` | string | `contain`, `cover`, `fill` |
| `duration_sec` | float | Video slide duration override |
| `audio_start_sec` | float | Offset into shared audio/avatar file |
| `audio_path` | string | External narration MP3 |
| `narration_mode` | string | `fixed`, `audio_file`, `avatar`, `tts`, `auto` |
| `audio_source` | string | Optional alias: `heygen_video`, `external`, `tts` (used when `narration_mode` omitted) |
| `sync_mode` | string | `avatar_lead`, `notes_lead`, `longest` |
| `color_scheme` | string | Deck colour preset name (`deck_*` slides) |
| `text_panel` | object | Hero text placement (`anchor`, `style`, `hero_layout`, …) — [Avatar layouts](avatar-layouts.md#avatar_media_3-full-bleed-hero) |
| `qa` | object | Per-slide QA rules merged over `slide_qa` — [Slide QA](slide-qa.md) |
| `jpeg_show_pip_preview` | bool | Override deck `jpeg_show_pip_preview` for one slide |

Additional keys depend on `slide_type` — see the layout pages above.

### `text_panel` object

| Key | Type | Description |
|-----|------|-------------|
| `anchor` | string | `top_left`, `top_right`, `bottom_left`, `bottom_right`, `top`, `bottom` |
| `style` | string | `navy_panel`, `semi_panel`, `overlay` |
| `hero_layout` | string | `stacked` or `full_bleed` (overrides layout default) |
| `width_ratio` | float | Panel width as fraction of content width |
| `height_in` | float | Panel height in inches |
| `margin_in` | float | Inset from content edges |
| `max_width_ratio` | float | Cap on panel width |

### `qa` object (verse or `slide_qa` deck block)

| Key | Type | Description |
|-----|------|-------------|
| `expect_pip` | bool | Require PiP-capable slide + `avatar_video_path` |
| `expect_media` | bool | Require `media_path` file |
| `min_media_width_ratio` | float | 0–1; legacy left-band heuristic |
| `min_hero_coverage_ratio` | float | 0–1; full-slide non-background coverage (skipped for `media_fit: contain`) |

---

## `video_export` block

```yaml
video_export:
  backend: compositor
  narration_mode: fixed          # fixed | audio_file | avatar | tts | auto
  output_path: output/deck.mp4
  preset: standard               # draft | standard | high | 4k
  resolution: { width: 1920, height: 1080 }
  fps: 30
  dpi: 192
  slide_duration_sec: 5
  avatar_timeline: auto          # per_slide | continuous | auto
  avatar:
    fit: cover
    shape: circle
    crop_y_ratio: 0.06
    zoom_ratio: 1.45
    loop_if_shorter: true
  tts:
    provider: edge
    voice: en-GB-RyanNeural
  captions:
    enabled: true
  slide_cache: true
  transitions:
    default: none
    duration_sec: 0.30
  video_crf: 23
```

Per-edge and verse overrides: see [Slide transitions](slide-transitions.md).

CLI overrides: `--video-output`, `--video-preset`, `--narration-mode`, `--video-options` (JSON), `--slide-range`, `--keep-temp`. See [Video export](video-export.md).

---

## Minimal deck skeleton

```yaml
presentation_title: My presentation
presentation_subtitle: June 2026

slide_style:
  background_color: "#1A1A2E"
  text_color: white

sections:
  - section: Introduction
    verses:
      - reference: Opening
        text: First point.

  - section: Main
    verses:
      - slide_type: table
        table_rows:
          - [A, B]
          - [1, 2]
        reference: Source line
        avatar_video_path: assets/speaker.mp4

video_export:
  backend: compositor
  preset: standard
  narration_mode: avatar
  avatar_timeline: auto
```

---

## `pipeline` (QA orchestration)

Optional in **YAML or JSON** (same keys). Drives `praisonaippt pipeline` and `validate-deck` (validate-only: no PPTX/MP4). Build and export are separate stages wired via protocols (`pipeline_protocols.py`); defaults call `create_presentation` and `convert_deck_to_video`.

| Key | Type | Description |
|-----|------|-------------|
| `content_master` | string | Master YAML for `sync-variants` / drift checks |
| `transcript_path` | string | Whisper JSON for timing / A-V sync gates |
| `auto_sync` | bool | Sync variants from master before build |
| `variant_prefix` | string | Filename prefix for variant YAMLs (default `heygen-50590`) |
| `validate_pip` | bool | Run PiP centring QA (multi-seek) |
| `strict_pip` | bool | All calibration seeks must pass |
| `golden_slide_dir` | string | Golden JPEG directory for slide hash gate |
| `export_mp4_frames` | bool | Export MP4 seek frames per verse (`audio_start_sec`) |
| `mp4_frames_dir` | string | Output folder for `mp4-slide-NNN.jpg` (default `mp4-frames`) |
| `validate_slide_qa` | bool | Run `slide_qa` manifest gate on JPEGs (default true when `slide_qa` set) |
| `require_rights_ack` | bool | Block until `rights_acknowledged` |
| `rights_acknowledged` | bool | Manual rights checklist clearance |
| `content_approved` | bool | Content sign-off |
| `plan_approved` / `plan_draft` | bool / string | Plan-slides workflow |
| `export_mp4` | bool | Export MP4 in `pipeline` command (or use CLI `--convert-video`) |
| `export_slide_jpegs` | bool | Export slide JPEGs after PPTX |
| `post_render_qc` | bool | ffprobe post-render checks (default true) |
| `strict_post_render` | bool | Fail pipeline when post-render QC fails |
| `fail_fast` | bool | Stop on first failed gate (default true) |
| `validate_plan` / `validate_rights` | bool | Toggle plan / rights gates |
| `seed_timing` | bool | Seed `audio_start_sec` from transcript |
| `report_path` | string | Override `report.json` path |

CLI flags override YAML where both are set. Full gate matrix: [Video → deck workflow](workflow-video-transcript-to-deck.md).

---

## `avatar_calibration` (PiP framing)

Optional top-level block. When `auto: true`, runs before PPTX/video build and merges `crop_x_ratio` / `crop_y_ratio` into `slide_style.layouts.pip`.

| Key | Type | Description |
|-----|------|-------------|
| `auto` | bool | Run calibration when building (default false if block omitted) |
| `method` | string | `hybrid`, `balance`, `mediapipe`, `fixed`, `yolo` |
| `crop_x_preferred` | float | Visual anchor (e.g. `0.53`) |
| `crop_x_window` | `[lo, hi]` | Allowed `crop_x` range |
| `crop_y_preferred` | float | Default vertical crop |
| `anchor_weight` | float | Penalty for drifting from `crop_x_preferred` |
| `detector` | string | `auto`, `mediapipe`, `yunet`, `yolo` |
| `min_detection_confidence` | float | Face detector threshold |
| `force` | bool | Ignore cache |

Cache directory: `.praisonaippt/avatar-framing/` beside the deck (gitignored). See [Avatar PiP calibration](avatar-calibration.md).

---

## `hero_text_placement` (hero headline anchor)

Optional top-level block. When `auto: true`, runs after avatar calibration and sets `_hero_panel_anchor` on verses with `text_panel.anchor: auto`.

| Key | Type | Description |
|-----|------|-------------|
| `auto` | bool | Run placement when building (default false) |
| `method` | string | `hybrid`, `east`, `paddle`, `rapidocr`, `mser`, `heuristic`, `vision` |
| `detector` | string | `auto`, `paddle`, `rapidocr`, `east`, `mser`, `heuristic` |
| `min_confidence` | float | Minimum offline score (default `0.55`) |
| `preferred_anchor` | string | Soft bias for scoring |
| `fallback_anchor` | string | Used when all anchors rejected |
| `pad_hard_px` / `pad_soft_px` | float | OCR box padding |
| `vision_fallback` | bool | Optional LLM anchor suggester |
| `anchor_weight` | float | Penalty for non-preferred anchors |
| `force` | bool | Ignore cache |

Cache: `.praisonaippt/hero-text-placement/`. See [Hero text panel calibration](hero-text-calibration.md).

---

## `slide_transitions` (MP4 slide joins)

Optional top-level block. Default is **`none`** (hard cut). Resolved before video export into `_slide_transitions` sidecar.

| Key | Type | Description |
|-----|------|-------------|
| `enabled` | bool | When `false`, all edges resolve to `none` |
| `default` | string | Global fallback: `none`, `segment_fade`, `crossfade`, `wipeleft`, `wiperight`, `slideleft`, `slideright` |
| `duration_sec` | float | Default blend/fade duration |
| `min_slide_sec` | float | Skip transition when slide shorter |
| `max_fade_ratio` | float | Cap duration vs slide length (0–1) |
| `edges` | list | Per-edge overrides — see below |

Per-edge entry:

| Key | Type | Description |
|-----|------|-------------|
| `after_slide` | int | Transition leaving slide N → N+1 (1-based) |
| `type` | string | Transition type |
| `duration_sec` | float | Optional override |

Verse-level: `transition_out`, `transition_duration_sec` on the outgoing slide.

Nested under `video_export`:

```yaml
video_export:
  transitions:
    default: none
    duration_sec: 0.30
  transition_fade_sec: 0.28   # deprecated → segment_fade
  video_crf: 23
```

Showcase: `examples/slide-transitions-showcase.yaml` (GitHub: [showcase YAML](https://github.com/MervinPraison/PraisonAIPPT/blob/main/examples/slide-transitions-showcase.yaml)). Full guide: [Slide transitions](slide-transitions.md).

Pipeline: `pipeline.validate_transitions` (default true), `pipeline.strict_transitions`.

---

## HeyGen 50590 workflow

1. Edit `examples/heygen-50590-content.yaml`
2. `python examples/sync_heygen_variants.py`
3. `praisonaippt -i examples/<variant>.yaml -o examples/<variant>.pptx --convert-video`

Details: [HeyGen article examples](heygen-examples.md).

---

## Related

- [Layouts overview](layouts-overview.md)
- [Slide QA](slide-qa.md)
- [Configuration file](configuration.md) — `~/.praisonaippt/config.yaml` (Drive, PDF defaults)

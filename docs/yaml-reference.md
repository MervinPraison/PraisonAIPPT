# YAML deck reference

Quick reference for top-level deck keys, sections, verses, and video export. For layout-specific fields see [Standard slide layouts](slide-layouts.md), [Avatar layouts](avatar-layouts.md), and [Deck layouts](deck-layouts.md).

Source: `praisonaippt/schema.py`, `praisonaippt/video_exporter.py`.

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
| `slide_timestamps` | optional | Wall-clock start (seconds) per slide for video timing |

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

Additional keys depend on `slide_type` — see the layout pages above.

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
```

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

## HeyGen 50590 workflow

1. Edit `examples/heygen-50590-content.yaml`
2. `python examples/sync_heygen_variants.py`
3. `praisonaippt -i examples/<variant>.yaml -o examples/<variant>.pptx --convert-video`

Details: [HeyGen article examples](heygen-examples.md).

---

## Related

- [Layouts overview](layouts-overview.md)
- [Configuration file](configuration.md) — `~/.praisonaippt/config.yaml` (Drive, PDF defaults)

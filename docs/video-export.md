# Video export (PPTX → MP4)

PraisonAIPPT can export presentations to MP4 on **Mac and Linux** using a **compositor**
backend: LibreOffice rasterises slides to PNG, then FFmpeg overlays avatar and media
regions using geometry from `avatar_layouts` and `deck_slides` YAML. See [deck-layouts.md](deck-layouts.md) for `deck_*` slide types.

PowerPoint `CreateVideo` (Windows, on-prem) is **Phase 3** and not implemented in v1.

## Requirements

| Tool | Role | macOS install |
|------|------|---------------|
| FFmpeg + ffprobe | Encode and probe | `brew install ffmpeg` |
| poppler (`pdftoppm`) | PDF → PNG | `brew install poppler` |
| LibreOffice | PPTX → PDF | `brew install --cask libreoffice` |

Check dependencies:

```bash
praisonaippt convert-video --check
```

On macOS the default H.264 encoder is **`h264_videotoolbox`** when available; otherwise
`libx264` is used.

## CLI

```bash
# Build deck and export video (shares one LibreOffice PDF run when combined)
praisonaippt -i examples/avatar_layouts.yaml -o deck.pptx --convert-video

# Both PDF and video — single LO PDF internally
praisonaippt -i deck.yaml -o deck.pptx --convert-pdf --convert-video

# Standalone PPTX → MP4 (loads deck.yaml sidecar when present)
praisonaippt convert-video deck.pptx
# deck.yaml beside deck.pptx supplies avatar/media paths for PiP overlays --video-preset draft --slide-range 1-5

# Preflight
praisonaippt convert-video --check
```

Flags: `--convert-video`, `--video-output`, `--video-backend`, `--video-preset`,
`--narration-mode`, `--video-options` (JSON), `--slide-range`, `--keep-temp`.

## YAML configuration

Top-level `video_export` block:

```yaml
video_export:
  backend: compositor
  narration_mode: fixed          # fixed | audio_file | avatar | tts | auto
  output_path: output/deck.mp4
  resolution: { width: 1920, height: 1080 }
  fps: 30
  dpi: 192
  preset: standard               # draft | standard | high
  slide_duration_sec: 5
  avatar_timeline: per_slide     # per_slide | continuous
  avatar:
    fit: stretch                 # matches PPTX add_movie stretch
    loop_if_shorter: true
  tts:                           # requires pip install praisonaippt[video-tts]
    provider: edge
    voice: en-GB-RyanNeural
  captions:
    enabled: true                # writes .srt sidecar when notes/TTS used
```

Per-verse overrides:

```yaml
- slide_type: avatar_media_1
  avatar_video_path: assets/speaker.mp4
  media_path: assets/diagram.png
  notes: Narration text.
  duration_sec: 12
  narration_mode: avatar
```

Schema keys: `duration_sec`, `audio_start_sec`, `audio_path`, `narration_mode`, `sync_mode` (verse level);
`video_export`, `slide_timestamps` (deck level).

When `duration_sec` and `audio_start_sec` are set on a verse, they take precedence over
`ffprobe` on shared HeyGen MP4 or MP3 files. Use `avatar_timeline: continuous` with per-slide
`audio_start_sec` to slice one narration track across many slides.

## Transcript-driven HeyGen decks

Generate YAML from Whisper JSON:

```bash
praisonaippt transcript-to-yaml \
  -i examples/short-script-50590_timestamps.json \
  -o examples/heygen-article-50590 \
  --transcript-mode both \
  --transcript-audio examples/short-script-50590.mp3 \
  --align silence,karaoke
```

| Flag | Effect |
|------|--------|
| `--transcript-mode` | `full`, `thematic`, or `both` deck variants |
| `--transcript-audio` | MP3 for silence/RMS alignment |
| `--align` | `silence`, `emphasis`, `karaoke` (comma-separated) |
| `--variants all` | Write media combination YAMLs (see [heygen-50590-examples.md](../examples/heygen-50590-examples.md)) |

Example deck: `examples/heygen-article-50590-short.yaml`. See
`examples/heygen-50590-examples.md` for all audio/video combinations.

**Timing:** use wall-clock merge (`last_segment.end - first_segment.start`) so pauses between
Whisper segments are held on the correct slide. Sum of segment durations alone is shorter than
total audio length.

**Warning:** with `narration_mode: auto`, if both `audio_path` and `avatar_video_path` are set,
`audio_path` wins. Use explicit `avatar` or `audio_file` for HeyGen article exports.

## Narration modes

| Mode | Duration source | Primary audio |
|------|-----------------|---------------|
| `fixed` | `slide_duration_sec` / `duration_sec` | none |
| `audio_file` | verse `duration_sec`, else `slide_timestamps`, else ffprobe | external file (trimmed with `audio_start_sec`) |
| `avatar` | verse `duration_sec`, else `slide_timestamps`, else ffprobe | avatar track |
| `tts` | ffprobe on generated MP3 | TTS (avatar muted) |
| `auto` | precedence: audio_path → avatar (if audio) → notes→TTS → fixed | per rules |

Avatar video audio is muted when TTS or `audio_file` is primary to avoid double narration.

### sync_mode (per verse, optional)

When set explicitly on a verse, adjusts slide duration across sources:

| Value | Behaviour |
|-------|-----------|
| `avatar_lead` | Duration follows avatar video (skipped when verse has explicit `duration_sec`) |
| `notes_lead` | Duration follows TTS of notes |
| `longest` | Maximum of resolved sources (skipped when verse has explicit `duration_sec`) |

### Slide raster cache

PNG pages are cached under `~/.praisonaippt/video_cache/` keyed by PPTX mtime and DPI.
Disable with `slide_cache: false` in `video_export` (via JSON `--video-options`).

## Compositor behaviour

LibreOffice PNG is **static chrome only** (text, borders, placeholders). For every avatar
layout slide, FFmpeg overlays:

- `avatar_video_path` → `regions["avatar"]` box
- `media_path` → `regions["media"]` box when present

Split layouts (`avatar_media_1` vs `avatar_media_2`) use distinct width ratios from
`layout_tokens.py`, visible in both PPTX and video.

Z-order: media → avatar → text (already in PNG).

## Fidelity matrix (Phase 0 — LibreOffice vs PowerPoint)

Measured on Mac with LO headless PDF → `pdftoppm` vs PowerPoint slide view for avatar
layouts. Use this when judging export quality.

| Layout | LO static chrome | Embedded movies in LO PNG | FFmpeg overlay fix | Known delta |
|--------|------------------|---------------------------|--------------------|-------------|
| `avatar_only` | Good | Grey placeholder only | Avatar video in region | LO placeholder colour may differ slightly |
| `media_only` | Good | Image OK; video not played | Media file overlaid | Video must be overlaid, not embedded |
| `avatar_media_1` (50/50) | Good split geometry | Placeholders only | Both regions overlaid | Split ratio matches YAML (~50/50) |
| `avatar_media_2` (40/60) | Good | Placeholders only | Both regions overlaid | Wider media column vs `_1` |
| `avatar_media_3` (PiP) | Good | Placeholders only | PiP boxes overlaid | PiP position from `_slide_regions` |
| `avatar_name_card` | Good | Avatar placeholder | Avatar in region | Navy text panel may sit above avatar in PPTX; v1 square overlays |
| `avatar_headline` | Good | Same as name card | Same | Panel text in PNG only |
| `avatar_quote` | **Moderate** | Navy fill approximate | Avatar overlaid on quote area | LO may shift quote typography; use `raster_mode: native` (future) if drift matters |
| `avatar_border` / `media_border` | Good borders | Placeholders | Overlays in bordered rects | Rounded inner corners: **square overlays in v1** |
| `avatar_media_border_*` | Good | Placeholders | Overlays | 60/40 vs 40/60 ratios preserved |

**Invariants enforced:** `len(slides) == pdf_pages == png_count` — export fails fast on mismatch.

**Not in v1:** slide transitions, rounded overlay masks, Windows CreateVideo animations.

## Python API

```python
from praisonaippt import (
    create_presentation,
    load_verses_from_file,
    VideoOptions,
    convert_deck_to_video,
)

data = load_verses_from_file("deck.yaml")
pptx = create_presentation(data, "deck.pptx")
convert_deck_to_video(data, pptx, video_options=VideoOptions(preset="draft"))
```

## Optional extras

```bash
pip install praisonaippt[video-tts]      # edge-tts for narration_mode: tts
pip install praisonaippt[video-windows]  # Phase 3 stub only
```

## Windows worker (deferred)

Phase 3 adds an on-prem FastAPI worker calling PowerPoint `CreateVideo`. It is **not**
multi-tenant SaaS-ready without Microsoft Office licensing review. See
`praisonaippt/workers/ppt_com.py`.

## Legal note

SaaS redistributors using `libx264` should review H.264 patent obligations. macOS
VideoToolbox is preferred where available.

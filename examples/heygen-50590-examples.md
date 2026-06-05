# HeyGen 50590 — media combination examples

> **Published docs:** [HeyGen article examples](https://ppt.praison.ai/heygen-examples/) (MkDocs: `docs/heygen-examples.md`). Edit this file or the doc page; keep workflow in sync.

**Step 1 — content:** edit [`heygen-50590-content.yaml`](heygen-50590-content.yaml) with all slide copy,
formats (`list`, `two_column`, `table`, `big_number`, `avatar_quote`, `avatar_headline`, …), and timing.

**Step 2 — sync variants:**

```bash
python examples/sync_heygen_variants.py
```

This propagates content to [`heygen-50590-video-audio-heygen.yaml`](heygen-50590-video-audio-heygen.yaml)
and the other variant YAMLs (audio paths, narration mode).

**Step 3 — build PPTX/MP4** (see below).

Slide **headlines, bullets, tables, and quotes** in the content file come from the Claude Managed Agents
article (May 2026). Presenter narration lives in each verse `notes` field (synced to captions).

Shared assets (same ~57 s narration):

| File | Role |
|------|------|
| [heygen-article-50590.mp4](heygen-article-50590.mp4) | HeyGen headshot video (embedded audio) |
| [short-script-50590.mp3](short-script-50590.mp3) | Separate narration MP3 |
| [short-script-50590_timestamps.json](short-script-50590_timestamps.json) | Whisper transcript (timing + text) |
| [short-script-50590_timestamps.txt](short-script-50590_timestamps.txt) | Word-level timestamps (reference) |
| [heygen-article-50590-words.srt](heygen-article-50590-words.srt) | Karaoke-style word captions |

## Generate all combination YAMLs

```bash
python -m praisonaippt.cli transcript-to-yaml \
  -i examples/short-script-50590_timestamps.json \
  -o examples/heygen-article-50590 \
  --variants all
```

## Narration source (pick one)

1. **Default — HeyGen video audio** (`narration_mode: avatar` or `audio_source: heygen_video`): AAC from [heygen-article-50590.mp4](heygen-article-50590.mp4) (~57 s).
2. **Optional — video + separate MP3** (`narration_mode: audio_file` or `audio_source: external`): PiP from HeyGen; timing/voice from [short-script-50590.mp3](short-script-50590.mp3).
3. **TTS** (`narration_mode: tts`): synthesise from verse `notes` (avatar muted).

With `narration_mode: auto`, HeyGen embedded audio wins when the avatar file has a track, even if `audio_path` is also set.

## Variant matrix

| YAML | Video (HeyGen PiP) | Audio source | `narration_mode` | Use case |
|------|-------------------|--------------|------------------|----------|
| [heygen-50590-video-audio-heygen.yaml](heygen-50590-video-audio-heygen.yaml) | Yes | HeyGen MP4 track | `avatar` | **Default talking-head** — video + lip-sync audio from HeyGen |
| [heygen-50590-video-visual-mp3.yaml](heygen-50590-video-visual-mp3.yaml) | Yes (muted) | MP3 file | `audio_file` | Headshot visual only; external/studio MP3 drives timing |
| [heygen-50590-audio-only.yaml](heygen-50590-audio-only.yaml) | No | MP3 file | `audio_file` | Podcast-style — slides + voiceover, no avatar file |
| [heygen-50590-video-only-silent.yaml](heygen-50590-video-only-silent.yaml) | Yes | None | `fixed` | B-roll / preview — avatar scrubs on slides, silent |
| [heygen-50590-slides-silent.yaml](heygen-50590-slides-silent.yaml) | No | None | `fixed` | Slide timing demo — no media files required |
| [heygen-50590-video-audio-heygen-images.yaml](heygen-50590-video-audio-heygen-images.yaml) | Yes | HeyGen MP4 track | `avatar` | **Full-bleed hero screenshots** + `hero_text_placement.auto` / `text_panel.anchor: auto`; [Hero text calibration](../docs/hero-text-calibration.md) |

## Images variant (full-bleed heroes)

Same HeyGen MP4, Whisper timings, and narration as [`heygen-50590-video-audio-heygen.yaml`](heygen-50590-video-audio-heygen.yaml), with product screenshots as full-slide heroes and auto headline placement (`hero_text_placement.auto`, `text_panel.anchor: auto`).

```bash
VARIANT=heygen-50590-video-audio-heygen-images

praisonaippt hero-panel-place -i examples/${VARIANT}.yaml --force

python -m praisonaippt.cli \
  -i examples/${VARIANT}.yaml \
  -o examples/${VARIANT}.pptx \
  --convert-video \
  --video-output examples/${VARIANT}.mp4 \
  --no-list-slides

praisonaippt validate-deck -i examples/${VARIANT}.yaml
```

| Output | Path |
|--------|------|
| Deck YAML | `examples/heygen-50590-video-audio-heygen-images.yaml` |
| Layout JPEGs | `examples/slide_images/heygen-50590-images/slide-001.jpg` … `slide-007.jpg` |
| Golden baselines | `examples/slide_images/heygen-50590-images/golden/` |
| MP4 seek frames | `examples/slide_images/heygen-50590-images/mp4-frames/` |

Docs: [Hero text calibration](../docs/hero-text-calibration.md) · [HeyGen examples](../docs/heygen-examples.md) · [Avatar layouts — full-bleed](../docs/avatar-layouts.md#avatar_media_3-full-bleed-hero) · [Slide QA](../docs/slide-qa.md)

## Build and export (replace `VARIANT` with yaml stem)

```bash
VARIANT=heygen-50590-audio-only

python -m praisonaippt.cli \
  -i examples/${VARIANT}.yaml \
  -o examples/${VARIANT}.pptx \
  --convert-video \
  --video-output examples/${VARIANT}.mp4 \
  --no-list-slides
```

For `audio-only`, narration mode is already set in YAML (`audio_file`). For others, the YAML `video_export.narration_mode` is used automatically.

## Showcase galleries (avatar + deck layouts)

Rebuild **all** advanced showcase PPTX + MP4 outputs in one step:

```bash
python examples/build_showcase_examples.py
```

This syncs HeyGen variants from [`heygen-50590-content.yaml`](heygen-50590-content.yaml) and builds:

| Output stem | YAML | Features |
|-------------|------|----------|
| `avatar_layouts_built` | [`avatar_layouts.yaml`](avatar_layouts.yaml) | 16 avatar types, HeyGen PiP, circle overlay |
| `deck_template_gallery` | [`deck_template_gallery.yaml`](deck_template_gallery.yaml) | 12 HeyGen deck layouts, colour presets |
| `heygen-50590-*` | Five variant YAMLs | Article deck, transcript timing, captions |

See also [deck layouts](../docs/deck-layouts.md) and [HeyGen examples](../docs/heygen-examples.md) in `docs/`.

## Legacy filenames

| File | Same as |
|------|---------|
| `heygen-article-50590-short.yaml` | `video-audio-heygen` (hand-tuned headlines) |
| `heygen-article-50590-short-audio-only.yaml` | `audio-only` |

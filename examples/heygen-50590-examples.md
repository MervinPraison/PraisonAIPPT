# HeyGen 50590 — media combination examples

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

## Variant matrix

| YAML | Video (HeyGen PiP) | Audio source | `narration_mode` | Use case |
|------|-------------------|--------------|------------------|----------|
| [heygen-50590-video-audio-heygen.yaml](heygen-50590-video-audio-heygen.yaml) | Yes | HeyGen MP4 track | `avatar` | **Default talking-head** — video + lip-sync audio from HeyGen |
| [heygen-50590-video-visual-mp3.yaml](heygen-50590-video-visual-mp3.yaml) | Yes (muted) | MP3 file | `audio_file` | Headshot visual only; external/studio MP3 drives timing |
| [heygen-50590-audio-only.yaml](heygen-50590-audio-only.yaml) | No | MP3 file | `audio_file` | Podcast-style — slides + voiceover, no avatar file |
| [heygen-50590-video-only-silent.yaml](heygen-50590-video-only-silent.yaml) | Yes | None | `fixed` | B-roll / preview — avatar scrubs on slides, silent |
| [heygen-50590-slides-silent.yaml](heygen-50590-slides-silent.yaml) | No | None | `fixed` | Slide timing demo — no media files required |

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

## Legacy filenames

| File | Same as |
|------|---------|
| `heygen-article-50590-short.yaml` | `video-audio-heygen` (hand-tuned headlines) |
| `heygen-article-50590-short-audio-only.yaml` | `audio-only` |

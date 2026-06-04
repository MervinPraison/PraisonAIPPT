# HeyGen article 50590 — video export scenarios

Assets:

- `heygen-article-50590.mp4` — HeyGen headshot (~57 s)
- `short-script-50590.mp3` — narration audio
- `short-script-50590_timestamps.json` — Whisper transcript

## Generate YAML from transcript

```bash
python -m praisonaippt.cli transcript-to-yaml \
  -i examples/short-script-50590_timestamps.json \
  -o examples/heygen-article-50590 \
  --transcript-mode both \
  --transcript-audio examples/short-script-50590.mp3 \
  --align silence,karaoke
```

## Build PPTX

```bash
python -m praisonaippt.cli \
  -i examples/heygen-article-50590-short.yaml \
  -o examples/heygen-article-50590-short.pptx \
  --no-list-slides
```

## Scenario A — avatar + continuous HeyGen (primary)

```bash
python -m praisonaippt.cli \
  -i examples/heygen-article-50590-short.yaml \
  -o examples/heygen-article-50590-short.pptx \
  --convert-video \
  --video-output examples/heygen-article-50590-short_avatar.mp4 \
  --no-list-slides
```

## Scenario B — audio_file + MP3 trim + muted PiP

```bash
python -m praisonaippt.cli \
  -i examples/heygen-article-50590-short.yaml \
  -o examples/heygen-article-50590-short.pptx \
  --convert-video \
  --narration-mode audio_file \
  --video-output examples/heygen-article-50590-short_audio.mp4 \
  --no-list-slides
```

## Scenario C — audio only (no avatar video)

Remove `avatar_video_path` from content slides, then export with `--narration-mode audio_file`.

**Note:** Do not use `narration_mode: auto` when both `audio_path` and `avatar_video_path` are set.

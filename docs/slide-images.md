# Slide JPEG export

Export each slide as a PNG/JPEG image for previews, thumbnails, social posts, or vision checks — without running full video export.

## YAML

Set a directory next to your deck (paths are relative to the YAML file):

```yaml
slide_images_dir: slide_images
```

After a normal build, JPEGs are written as `slide-001.jpg`, `slide-002.jpg`, … under that folder.

## Commands

| Command | Purpose |
|---------|---------|
| `praisonaippt build-slide-images -i deck.yaml` | Build PPTX (with [auto calibration](avatar-calibration.md) when enabled) and export JPEGs |
| `praisonaippt export-slide-jpegs deck.pptx` | Export JPEGs from an existing PPTX only |
| `praisonaippt -i deck.yaml -o deck.pptx` | Same as build when `slide_images_dir` is set |

### Build from YAML (PPTX + JPEGs)

```bash
python -m praisonaippt.cli build-slide-images \
  -i examples/heygen-50590-video-audio-heygen.yaml \
  -o examples/heygen-50590-video-audio-heygen.pptx
```

Equivalent to:

```bash
praisonaippt -i examples/heygen-50590-video-audio-heygen.yaml \
  -o examples/heygen-50590-video-audio-heygen.pptx
```

### Export from existing PPTX

```bash
praisonaippt export-slide-jpegs examples/heygen-50590-video-audio-heygen.pptx \
  --slide-images-dir examples/slide_images
```

### Main build flag

During a standard presentation build you can request JPEG export without a separate subcommand:

```bash
praisonaippt -i deck.yaml -o deck.pptx --export-slide-jpegs
```

## HeyGen 50590 example

The article deck uses `slide_images_dir: slide_images` in `examples/heygen-50590-content.yaml`. A full showcase rebuild updates:

`examples/slide_images/slide-001.jpg` … `slide-008.jpg`

!!! note "Avatar on quote slides"
    For `avatar_quote`, the PPTX may show **no baked headshot** (video PiP only in MP4). JPEG previews can differ from the final MP4 — see [Avatar layouts — `avatar_quote`](avatar-layouts.md).

## Requirements

Uses the same LibreOffice → PDF → image pipeline as [video export](video-export.md) (LibreOffice + poppler). No FFmpeg is required for JPEG export alone.

## Related

- [Recent features](recent-features.md)
- [HeyGen examples](heygen-examples.md)
- [Video export](video-export.md)
- [Avatar PiP calibration](avatar-calibration.md)
- [Commands reference](commands.md#video-avatar-and-heygen-commands)

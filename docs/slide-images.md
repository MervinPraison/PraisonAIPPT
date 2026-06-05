# Slide JPEG export

Export each slide as a JPEG for previews, thumbnails, social posts, vision checks, or **golden regression** — without running full video export.

For automated QA (manifest rules, golden MD5, MP4 seek frames), see **[Slide QA](slide-qa.md)**.

---

## YAML

Set a directory relative to the deck YAML file:

```yaml
slide_images_dir: slide_images/heygen-50590-images
skip_title_slide: true    # optional: no auto title slide (hook opens at t=0)
```

After a normal build, JPEGs are written as `slide-001.jpg`, `slide-002.jpg`, … under that folder.

Use a **variant-specific** folder (as above) when multiple decks share `examples/` so golden sets do not overwrite each other.

---

## Commands

| Command | Purpose |
|---------|---------|
| `praisonaippt build-slide-images -i deck.yaml` | Build PPTX (with [auto calibration](avatar-calibration.md) when enabled) and export JPEGs |
| `praisonaippt export-slide-jpegs deck.pptx` | Export JPEGs from an existing PPTX only |
| `praisonaippt -i deck.yaml -o deck.pptx` | Exports JPEGs automatically when `slide_images_dir` is set |
| `praisonaippt -i deck.yaml -o deck.pptx --export-slide-jpegs` | Force JPEG export even without `slide_images_dir` |

### Build from YAML (PPTX + JPEGs)

```bash
praisonaippt -i examples/heygen-50590-video-audio-heygen-images.yaml \
  -o examples/heygen-50590-video-audio-heygen-images.pptx
```

### Export from existing PPTX

```bash
praisonaippt export-slide-jpegs examples/heygen-50590-video-audio-heygen-images.pptx \
  --slide-images-dir examples/slide_images/heygen-50590-images
```

---

## HeyGen 50590 examples

| Deck | `slide_images_dir` | Slide count |
|------|-------------------|-------------|
| Content master (with title) | `slide_images` | 8+ |
| **Images variant** (full-bleed heroes) | `slide_images/heygen-50590-images` | 7 (`skip_title_slide: true`) |

Images variant build:

```bash
praisonaippt -i examples/heygen-50590-video-audio-heygen-images.yaml \
  -o examples/heygen-50590-video-audio-heygen-images.pptx \
  --convert-video --video-output examples/heygen-50590-video-audio-heygen-images.mp4
```

Outputs:

- `examples/slide_images/heygen-50590-images/slide-001.jpg` … `slide-007.jpg`
- Golden reference: `…/golden/` (for CI MD5 gate)
- MP4 truth frames: `…/mp4-frames/mp4-slide-*.jpg` when `pipeline.export_mp4_frames: true`

---

## JPEG vs MP4 preview

| Slide type | JPEG | MP4 |
|------------|------|-----|
| `avatar_quote` | Quote only, or grey PiP if `jpeg_show_pip_preview: true` | Live HeyGen PiP |
| `avatar_media_3` | Full-bleed media + floating text panel; PiP may be placeholder | Live PiP over composited slide |
| `big_number`, `deck_*` | Baked layout | Same + live PiP when `avatar_video_path` set |

Always review **`mp4-slide-*.jpg`** for PiP-centric QA — see [Slide QA](slide-qa.md).

---

## Golden regression

Commit reference JPEGs under `pipeline.golden_slide_dir`. CI compares MD5 on each build:

```yaml
pipeline:
  golden_slide_dir: slide_images/heygen-50590-images/golden
```

Rebaseline after intentional visual changes:

```bash
cp examples/slide_images/heygen-50590-images/slide-*.jpg \
   examples/slide_images/heygen-50590-images/golden/
```

---

## Requirements

Uses the same LibreOffice → PDF → `pdftoppm` pipeline as [video export](video-export.md) (LibreOffice + poppler). FFmpeg is **not** required for JPEG export alone (FFmpeg is used for [MP4 frame QA](slide-qa.md#mp4-frame-export)).

---

## Related

- [Slide QA (golden, MP4 frames)](slide-qa.md)
- [Recent features](recent-features.md)
- [HeyGen examples](heygen-examples.md)
- [Avatar layouts — full-bleed hero](avatar-layouts.md#avatar_media_3-full-bleed-hero)
- [Video export](video-export.md)
- [Avatar PiP calibration](avatar-calibration.md)
- [Commands reference](commands.md#video-avatar-and-heygen-commands)

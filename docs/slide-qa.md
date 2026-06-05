# Slide QA (JPEG, golden, MP4 frames)

Automated checks for **layout stills** (PPTX → JPEG) and **composed video** (MP4 seek frames). Used by `praisonaippt pipeline`, `praisonaippt validate-deck`, and CI via `report.json`.

Implementation: `praisonaippt/slide_qa.py`, `praisonaippt/deck_pipeline.py` (`check_slide_jpegs`, `check_slide_qa_manifest`, `check_mp4_plan_frames`, `check_hero_text_placement`).

---

## Three-layer review model

| Layer | Input | What it validates |
|-------|--------|-------------------|
| **Layout JPEGs** | `slide_images_dir/slide-NNN.jpg` | PPTX raster (text panels, baked media, PiP placeholders) |
| **Golden regression** | `pipeline.golden_slide_dir` | MD5 match vs committed reference JPEGs |
| **MP4 frames** | `mp4_frames_dir/mp4-slide-NNN.jpg` | FFmpeg grab at each verse `audio_start_sec` (live PiP, compositor truth) |
| **Hero text placement** | `hero_text_placement.auto` | Offline anchor confidence gate when auto placement enabled — [Hero text calibration](hero-text-calibration.md) |
| **Slide transitions** | `slide_transitions` / `pipeline.validate_transitions` | Resolved edge plan valid; unknown types fail when strict — [Slide transitions](slide-transitions.md) |

!!! tip "JPEG ≠ MP4 for PiP"
    Slides in `_AVATAR_PIP_VIDEO_OVERLAY_ONLY` (`avatar_quote`, `avatar_media_3`) may show **no face** or a **grey PiP placeholder** in JPEGs while the MP4 shows the live HeyGen overlay. Always spot-check **`mp4-slide-*.jpg`** for PiP slides.

---

## YAML configuration

```yaml
slide_images_dir: slide_images/heygen-50590-images
skip_title_slide: true          # omit auto title slide (hook opens at t=0)
jpeg_show_pip_preview: true     # grey circle on avatar_quote in JPEG/PPTX only

slide_qa:                       # deck-wide defaults (merged with verse qa)
  expect_pip: true
  min_hero_coverage_ratio: 0.62  # full-slide non-background pixels (cover heroes)

pipeline:
  validate_slide_qa: true
  validate_transitions: true
  golden_slide_dir: slide_images/heygen-50590-images/golden
  export_mp4_frames: true
  mp4_frames_dir: slide_images/heygen-50590-images/mp4-frames
```

### Per-verse `qa` block

Merged over `slide_qa` (verse wins):

```yaml
- slide_type: avatar_media_3
  headline: Webhooks
  media_path: slide_images/HHpoqNAXcAcHY8h.jpg
  media_fit: contain
  qa:
    expect_media: true
    min_hero_coverage_ratio: 0.55   # lower threshold for letterboxed assets
```

| Key | Type | Description |
|-----|------|-------------|
| `expect_pip` | bool | Verse must have `avatar_video_path` and a PiP-capable `slide_type` |
| `expect_media` | bool | Verse must have `media_path` and file must exist |
| `min_media_width_ratio` | 0–1 | Legacy heuristic: left-band content width (stacked layout) |
| `min_hero_coverage_ratio` | 0–1 | Fraction of slide pixels ≠ deck background (`#121212`); **skipped** when `media_fit: contain` |

Requires **Pillow** for ratio checks (`pip install praisonaippt[avatar-calibrate]` or `pillow`).

---

## CI gates (`report.json`)

| Gate key | Step name | Pass criteria |
|----------|-----------|---------------|
| `hero_text` | `hero_text` | Auto hero panel anchors meet `min_confidence` |
| `slide_transitions` | `slide_transitions` | Resolved transition plan; optional strict mode |
| `slide_jpeg_golden` | `slide_jpegs` | JPEGs exist, min size, optional golden MD5 |
| `slide_qa` | `slide_qa` | Manifest rules (`expect_*`, coverage ratios) |
| `mp4_frames` | `mp4_frames` | One frame per verse at `audio_start_sec + 0.35s` |

```bash
praisonaippt validate-deck -i examples/heygen-50590-video-audio-heygen-images.yaml
echo $?   # 0 = all gates pass
```

Report path (default): `examples/.praisonaippt/{deck-stem}.pipeline-report.json`

### Rebaseline golden JPEGs

After an intentional layout change:

```bash
praisonaippt -i deck.yaml -o deck.pptx
cp slide_images/my-deck/slide-*.jpg slide_images/my-deck/golden/
praisonaippt validate-deck -i deck.yaml
```

Golden paths are resolved **relative to the deck YAML directory** (same as `slide_images_dir`).

---

## MP4 frame export

When `pipeline.export_mp4_frames: true` and the MP4 exists (or after `--convert-video` in pipeline):

- Writes `mp4-slide-001.jpg`, … under `mp4_frames_dir`
- One frame per plan slide at `audio_start_sec + 0.35` seconds
- Uses `ffmpeg -ss` (requires FFmpeg on PATH)

Validate-only (`validate-deck`) exports/refreshes frames if `{deck-stem}.mp4` is beside the YAML.

---

## HeyGen 50590 images variant

Reference deck: `examples/heygen-50590-video-audio-heygen-images.yaml`

| Setting | Value |
|---------|--------|
| Layout | `avatar_media_3` with `hero_layout: full_bleed` |
| Text | Floating `text_panel.anchor` per slide |
| Timings | Same as base HeyGen variant (unchanged) |
| Outputs | `heygen-50590-video-audio-heygen-images.pptx`, `.mp4`, `.srt` |
| JPEGs | `examples/slide_images/heygen-50590-images/` |
| Golden | `…/golden/` |
| MP4 frames | `…/mp4-frames/` |

See [Avatar layouts — full-bleed hero](avatar-layouts.md#avatar_media_3-full-bleed-hero) and [HeyGen examples](heygen-examples.md).

---

## Python API

```python
from praisonaippt.slide_qa import (
    check_slide_qa_manifest,
    check_mp4_plan_frames,
    export_mp4_plan_frames,
)

step = check_slide_qa_manifest(data, source_file="deck.yaml", jpeg_dir="slide_images/out")
assert step.ok, step.detail
```

---

## Related

- [Slide JPEG export](slide-images.md)
- [Avatar layouts](avatar-layouts.md)
- [Pipeline architecture](architecture-pipeline.md)
- [Video + transcript workflow — CI matrix](workflow-video-transcript-to-deck.md#ci-gates-validation-matrix)
- [Deck reference — `pipeline`](yaml-reference.md#pipeline-qa-orchestration)

# Recent features (video, HeyGen, PiP calibration)

Summary of capabilities added for **HeyGen talking-head decks**, **MP4 export**, **PiP framing**, and **visual validation**. Each item links to the full guide.

---

## Narration and audio sources

Choose where slide audio comes from in `video_export`:

| Priority | `narration_mode` | `audio_source` alias | Behaviour |
|----------|------------------|----------------------|-----------|
| **Default** | `avatar` | `heygen_video` | AAC from HeyGen MP4 (lip-sync voice) |
| Optional | `audio_file` | `external` | Separate MP3; PiP video muted for narration |
| Optional | `tts` | `tts` | Synthesise from verse `notes` |

With `narration_mode: auto`, **HeyGen embedded audio wins** when the avatar file has a track, even if `audio_path` is also set on verses.

```yaml
video_export:
  narration_mode: avatar
  audio_source: heygen_video   # optional alias when narration_mode omitted
```

**Docs:** [Video export — narration modes](video-export.md#narration-modes) · [HeyGen examples](heygen-examples.md#narration-source-pick-one) · [YAML reference](yaml-reference.md)

---

## HeyGen 50590 article workflow

One **content** YAML drives five **media variant** decks (video+audio, video+MP3, audio-only, silent variants).

```bash
# 1. Edit content
# examples/heygen-50590-content.yaml

# 2. Sync variants
python examples/sync_heygen_variants.py

# 3. Build + MP4 (default = HeyGen audio)
VARIANT=heygen-50590-video-audio-heygen
praisonaippt -i examples/${VARIANT}.yaml -o examples/${VARIANT}.pptx \
  --convert-video --video-output examples/${VARIANT}.mp4
```

**Docs:** [HeyGen article examples](heygen-examples.md) · [Video + transcript workflow](workflow-video-transcript-to-deck.md) (full pipeline and automation plan)

---

## Avatar PiP auto-calibration

Centres the presenter face in the circular PiP using **hybrid** calibration:

1. MediaPipe (or YuNet) estimates face position → `crop_x` seed  
2. **Face-centred refine** — sweeps `crop_x` / `crop_y` to minimise L/R/T/B margin asymmetry (same metric as the validation diagram)  
3. Results cached under `.praisonaippt/avatar-framing/` next to the deck YAML (gitignored)

```yaml
avatar_calibration:
  auto: true
  method: hybrid
  crop_x_preferred: 0.53
  crop_x_window: [0.50, 0.56]
  detector: auto
```

```bash
pip install praisonaippt[avatar-calibrate]
praisonaippt calibrate-avatar examples/heygen-50590-video-audio-heygen.yaml --force --write
```

**Install extras (PyPI):**

| Extra | Purpose |
|-------|---------|
| `praisonaippt[avatar-calibrate]` | MediaPipe + OpenCV (Python ≥3.8 for mediapipe) |
| `praisonaippt[avatar-calibrate-yolo]` | Ultralytics YOLO (hard angles; AGPL) |

**Docs:** [Avatar PiP calibration](avatar-calibration.md)

---

## PiP face centre measurement and validation diagram

Measure whether the head is centred in the PiP circle and save an **annotated PNG** for visual QA.

```bash
praisonaippt pip-face-centre -i deck.yaml --slide 6 \
  --validation-image examples/heygen-pip-validation.png

praisonaippt calibrate-avatar deck.yaml --force --validation-image
```

The diagram shows:

- Green circle + centre crosshair  
- Yellow face box, blue face centre  
- **L / R / T / B** pixel gaps from each side of the head to the circle  
- Banner: `centred=yes/no` and suggested `crop_x` / `crop_y` adjustments  

CLI hints come from `centring_advice()` (e.g. *increase crop_x* when L ≫ R).

**Docs:** [Avatar calibration — validation diagram](avatar-calibration.md#validation-diagram-image) · [Commands](commands.md#video-avatar-and-heygen-commands)

---

## Slide JPEG export

Export per-slide JPEG previews while building (for thumbnails, vision checks, or social).

```yaml
slide_images_dir: slide_images
```

```bash
praisonaippt build-slide-images -i deck.yaml -o deck.pptx
praisonaippt export-slide-jpegs deck.pptx --slide-images-dir slide_images
```

**Docs:** [Slide JPEG export](slide-images.md)

---

## Layout and export fixes

| Feature | Detail |
|---------|--------|
| **`avatar_quote`** | No baked headshot in PPTX — PiP only in MP4 (avoids double avatar) |
| **Deck + avatar galleries** | `python examples/build_showcase_examples.py` rebuilds all showcase PPTX/MP4 |
| **Transcript → YAML** | `praisonaippt transcript-to-yaml` with `--variants all` |
| **Local cache dirs** | `.praisonaippt/` and `.praisonaippt-calibrate/` under the deck (see `.gitignore`) |

**Docs:** [Avatar layouts — avatar_quote](avatar-layouts.md) · [Layouts overview](layouts-overview.md)

---

## Python API (new symbols)

```python
from praisonaippt import (
    calibrate_avatar_framing,
    calibrate_deck_avatars,
    maybe_auto_calibrate_deck,
    AvatarFramingResult,
    export_pptx_slide_jpegs,
    SlideImageOptions,
    convert_deck_to_video,
    VideoOptions,
)
from praisonaippt.pip_face_measure import (
    measure_pip_video,
    measure_pip_image,
    centring_advice,
    save_pip_validation_diagram,
    PipFaceMetrics,
    PipCentringAdvice,
)

metrics, probe = measure_pip_video("speaker.mp4", crop_x=0.545, crop_y=0.07)
advice = centring_advice(metrics)
if not advice.is_centred:
    print(advice.summary, advice.crop_x_delta, advice.crop_y_delta)
```

**Docs:** [Python API — video and calibration](python-api.md#video-export-and-avatar-calibration)

---

## CLI commands (quick reference)

| Command | Purpose |
|---------|---------|
| `calibrate-avatar` | Auto-tune `crop_x` / `crop_y`; `--write` updates YAML |
| `pip-face-centre` | Measure offsets; `--validation-image` saves diagram |
| `build-slide-images` | PPTX + JPEGs from YAML |
| `export-slide-jpegs` | JPEGs from existing PPTX |
| `convert-video` | PPTX → MP4 (sidecar YAML for PiP) |
| `transcript-to-yaml` | Whisper JSON → deck + variants |

Full flags: [Commands — video, avatar, and HeyGen](commands.md#video-avatar-and-heygen-commands)

---

## MkDocs preview

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and use the **Video & media** section in the nav.

# Avatar PiP calibration

Automatically centres the presenter face in the circular picture-in-picture (PiP) overlay using your HeyGen (or other) avatar video.

**See also:** [HeyGen article examples](heygen-examples.md) · [Video export](video-export.md) · [Avatar layouts](avatar-layouts.md) · [Commands](commands.md#video-avatar-and-heygen-commands)

## Quick start

```bash
pip install -e ".[avatar-calibrate]"
python -m praisonaippt.cli calibrate-avatar examples/heygen-50590-video-visual-mp3.yaml --force
# or: calibrate-avatar -i examples/heygen-50590-video-visual-mp3.yaml --force
```

## CLI commands (parity)

| Command | Purpose |
|---------|---------|
| `build-slide-images -i deck.yaml` | Build PPTX (with auto-calibration) and export JPEGs to `slide_images_dir` |
| `export-slide-jpegs deck.pptx` | Export JPEGs from an existing PPTX only |
| `calibrate-avatar -i deck.yaml --force` | Tune `crop_x` and cache framing |
| `pip-face-centre --avatar-video path.mp4 --crop-x 0.53` | Measure face vs circle centre (offsets + border margins) |
| `pip-face-centre … --validation-image` | Save annotated PNG: L/R/T/B pixel gaps to the circle |
| `calibrate-avatar … --validation-image` | Same diagram using calibrated `crop_x` |

### Slide images from YAML

```bash
python -m praisonaippt.cli build-slide-images -i examples/heygen-50590-video-visual-mp3.yaml \
  -o examples/heygen-50590-video-visual-mp3.pptx
```

Same as `praisonaippt -i deck.yaml -o deck.pptx` with `slide_images_dir` set in YAML (exports to `examples/slide_images/`).

### Face centre measurement

```bash
python -m praisonaippt.cli pip-face-centre -i examples/heygen-50590-video-visual-mp3.yaml --slide 6
python -m praisonaippt.cli pip-face-centre --avatar-video examples/heygen-article-50590.mp4 \
  --seek 37 --crop-x 0.505 --crop-y 0.03 --zoom 1.45
python -m praisonaippt.cli pip-face-centre --pip-image path/to/probe.png
```

Output includes normalised offset from circle centre (`offset_x`, `offset_y`), luminance `balance`, and margin gaps to the circular border.

### Validation diagram (image)

```bash
praisonaippt pip-face-centre -i examples/heygen-50590-video-audio-heygen.yaml \
  --validation-image examples/heygen-pip-validation.png

praisonaippt calibrate-avatar examples/heygen-50590-video-audio-heygen.yaml --force \
  --validation-image
```

The PNG shows:

- **Green** circle outline and centre crosshair  
- **Yellow** face bounding box  
- **L / R / T / B** coloured lines with **pixel** labels — gap from each side of the head to the circle edge (equal L≈R when centred)  
- Banner with `offset_x`, margins, and `centred=yes/no`

Omit the path after `--validation-image` to write `{probe}_pip_validation.png` beside the probe frame.

### Reading the diagram / SDK

CLI output includes `centred: yes/no` and **adjust** hints from `centring_advice()`:

| Symptom on diagram | Meaning | Move |
|--------------------|---------|------|
| **L** much larger than **R** | Face too far right | **Increase** `crop_x_ratio` |
| **R** much larger than **L** | Face too far left | **Decrease** `crop_x_ratio` |
| **T** much larger than **B** | Face too low | **Decrease** `crop_y_ratio` |
| **B** much larger than **T** | Face too high | **Increase** `crop_y_ratio` |

When centred, L≈R and T≈B (within ~5% offset). Hybrid calibration optimises the same L/R/T/B symmetry score used in tests (`face_centre_symmetry_score`).

Build the deck as usual; when `avatar_calibration.auto` is true, framing is applied before export:

```bash
python -m praisonaippt.cli -i examples/heygen-50590-video-visual-mp3.yaml \
  -o examples/heygen-50590-video-visual-mp3.pptx --convert-video \
  --video-output examples/heygen-50590-video-visual-mp3.mp4
```

## YAML configuration

```yaml
avatar_calibration:
  auto: true
  method: hybrid              # hybrid | balance | mediapipe | fixed | yolo
  crop_x_preferred: 0.53      # visual anchor for horizontal crop
  crop_x_window: [0.50, 0.56]
  crop_y_preferred: 0.03
  anchor_weight: 0.15         # penalty for drifting from preferred crop_x
  detector: auto              # auto | mediapipe | yunet | yolo
  min_detection_confidence: 0.5
  force: false                # ignore cache
  # cache_dir: /custom/path
```

Results are cached under `.praisonaippt/avatar-framing/` next to your deck YAML (add `.praisonaippt/` to `.gitignore` — local cache, not source).

## Methods

| Method | Description |
|--------|-------------|
| `hybrid` | MediaPipe face seed → **face-centred refine** (minimise L/R/T/B on validation diagram), then `crop_y` refine (**default**) |
| `balance` | Anchored luminance balance sweep only (no ML); needs no extra packages |
| `mediapipe` | Face detector only; no balance refine |
| `fixed` | Use `crop_x_preferred` from YAML |
| `yolo` | Ultralytics face model (requires `avatar-calibrate-yolo`; **AGPL-3.0**) |

## Optional dependencies

| Extra | Packages | Use |
|-------|----------|-----|
| `avatar-calibrate` | mediapipe, opencv-python-headless, numpy, pillow | Recommended for `hybrid` |
| `avatar-calibrate-yolo` | ultralytics + above | Hard face angles only |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Face off-centre | `calibrate-avatar --force`; confirm `crop_x_preferred: 0.53` |
| `ImportError: mediapipe` | `pip install -e ".[avatar-calibrate]"` or `method: balance` |
| Stale crop from old cache | `--force` or delete `.praisonaippt/avatar-framing/*.json` |
| Known-good framing | `method: fixed` and set `layouts.pip.crop_x_ratio: 0.53` |

## Manual override

```yaml
avatar_calibration:
  auto: false
slide_style:
  layouts:
    pip:
      crop_x_ratio: 0.53
      crop_y_ratio: 0.03
```

Lower `crop_x_ratio` shifts the visible face **right** in the PiP; higher shifts **left**.

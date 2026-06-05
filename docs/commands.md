---
layout: default
title: "Commands - PraisonAI PPT"
description: "Complete command-line interface reference for PraisonAI PPT"
---

# Complete Command Reference

PraisonAI PPT is invoked as **`praisonaippt`**. Deck input may be **`.yaml`**, **`.yml`**, or **`.json`** (same schema). Run `praisonaippt --help` for the latest flag list.

## Command index

| Command | Purpose |
|---------|---------|
| *(default)* | Load deck → build PPTX → optional PDF / MP4 / Drive / slide JPEGs |
| `convert-pdf` | PPTX → PDF |
| `convert-video` | PPTX → MP4 (sidecar `deck.yaml` / `deck.json` beside PPTX) |
| `convert-json` | PPTX or YAML → JSON extract |
| `convert-yaml` | JSON verses file → YAML |
| `transcript-to-yaml` | Whisper JSON → thematic / HeyGen variant YAML |
| `list-slides` | Print slide outline from deck or PPTX |
| `export-slide-jpegs` | Rasterise PPTX slides to JPEGs |
| `build-slide-images` | Build PPTX (if needed) + export `slide_images_dir` |
| `calibrate-avatar` | PiP face framing; `--write` updates deck YAML or JSON |
| `hero-panel-place` | Calibrate anchors; `--write` updates deck YAML or JSON |
| `hero-panel-centre` | Measure panel vs UI text; `--validation-image` L/R/T/B diagram |
| `pip-face-centre` | Measure L/R/T/B margins on PiP probe PNG |
| `pipeline` | Unified sync → gates → build → MP4 → `report.json` |
| `sync-variants` | Copy content master → HeyGen media variant YAMLs |
| `plan-slides` | Draft slide plan from transcript JSON |
| `approve-plan` | Approve plan draft (clears `plan_approval` gate) |
| `validate-deck` | Gates only (no PPTX / MP4 build) |
| `transcribe` | Audio → Whisper JSON (requires `whisper` CLI) |
| `template` | Show resolved theme template style |
| `config` | Show or edit `~/.praisonaippt/config.yaml` |
| `setup-oauth` | Google Drive OAuth setup |
| `setup-credentials` | Service-account credentials setup |
| `secure-credentials` | Restrict credential file permissions |

**Architecture:** [Pipeline architecture](architecture-pipeline.md) · **HeyGen workflow:** [Video + transcript workflow](workflow-video-transcript-to-deck.md)

## JSON and YAML decks

```bash
# Same flags for JSON or YAML
praisonaippt -i examples/job_sickness.json -o out.pptx
praisonaippt -i examples/heygen-50590-video-audio-heygen.yaml --convert-video
praisonaippt validate-deck -i deck.json --validate-pip
praisonaippt calibrate-avatar deck.json --write --force
```

`calibrate-avatar --write` preserves the file format (`.json` vs `.yaml`). See [Deck reference](yaml-reference.md).

## Main build command (default)

## 🚀 Basic Commands

### Create Presentation

#### Default Usage
```bash
# Use default verses.yaml in current directory
praisonaippt
```

#### Specify Input File
```bash
# YAML or JSON format
praisonaippt -i my_verses.yaml

# YAML format (recommended)
praisonaippt -i my_verses.yaml
```

#### Specify Output File
```bash
# Custom output filename
praisonaippt -i verses.yaml -o my_presentation.pptx
```

#### Use Custom Title
```bash
# Override JSON title
praisonaippt -i verses.yaml -t "My Custom Title"
```

#### Use Built-in Examples
```bash
# List available examples
praisonaippt --list-examples

# Use a specific example
praisonaippt --use-example tamil_verses
praisonaippt --use-example sample_verses
```

### Help and Version
```bash
# Show help
praisonaippt --help

# Show version
praisonaippt --version
```

## 📄 PDF Conversion Commands

### Convert Existing PPTX to PDF

#### Basic Conversion
```bash
# Convert presentation to PDF
praisonaippt convert-pdf presentation.pptx

# Specify output filename
praisonaippt convert-pdf presentation.pptx --pdf-output output.pdf
```

#### Backend Selection
```bash
# Choose specific backend
praisonaippt convert-pdf presentation.pptx --pdf-backend libreoffice
praisonaippt convert-pdf presentation.pptx --pdf-backend aspose
praisonaippt convert-pdf presentation.pptx --pdf-backend auto
```

#### Advanced PDF Options
```bash
# High quality PDF
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"quality":"high","compression":false}'

# Password protected PDF
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"password_protect":true,"password":"secret123"}'

# Custom slide range
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[1,5]}'
```

### Create PPTX and Convert to PDF in One Step

#### Basic Integrated Conversion
```bash
# Create presentation and convert to PDF
praisonaippt -i verses.yaml --convert-pdf

# Custom PDF output filename
praisonaippt -i verses.yaml --convert-pdf --pdf-output custom.pdf
```

#### Advanced Integrated Conversion
```bash
# With custom PDF options
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"high","include_hidden_slides":true}'

# With backend selection
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-backend aspose \
  --pdf-options '{"quality":"high","compression":false}'
```

## 🔄 PPTX → JSON Extraction Command

Convert slide content from a `.pptx` file back into the praisonaippt JSON schema, or convert a `.yaml` verse file back into `.json`.

### Basic Extraction (PPTX → JSON)
```bash
# Auto-named output (<input>.json)
praisonaippt convert-json presentation.pptx

# Specify output file
praisonaippt convert-json presentation.pptx --json-output extracted.json

# Compact JSON (no indentation)
praisonaippt convert-json presentation.pptx --json-output data.json --no-pretty
```

### Basic Conversion (YAML → JSON)
```bash
# Converts verses.yaml into verses.json
praisonaippt convert-json verses.yaml
```

### Convert-JSON Command Options
```
Convert-JSON Command:
  positional arguments:
    input_file              Input file to extract (.pptx or .ppt)

  options:
    --json-output PATH      Output JSON file path (default: <input>.json)
    --pretty                Write indented JSON (default: enabled)
    --no-pretty             Write compact single-line JSON
```

### Batch Extraction
```bash
# Extract all PPTX files in the current directory
for file in *.pptx; do
  praisonaippt convert-json "$file"
done
```

> 📖 Full reference: [PPTX to JSON Guide]({{ '/pptx-to-json' | relative_url }})

## 🔄 JSON → YAML Conversion Command

Convert legacy `.json` verse files to the new `.yaml` default format natively.

### Basic Conversion
```bash
# Converts verses.json into verses.yaml
praisonaippt convert-yaml verses.json
```

### Convert-YAML Command Options
```
Convert-YAML Command:
  positional arguments:
    input_file              Input file to convert (.json)
```

### Batch Conversion
```bash
# Convert all JSON source files in the current directory to YAML
for file in *.json; do
  praisonaippt convert-yaml "$file"
done
```
## ⚙️ Command Options Reference

### Global Options
```bash
Options:
  -h, --help            Show help message
  -v, --version         Show version number
  -i INPUT, --input INPUT
                        Input JSON/YAML file (default: verses.yaml)
  -o OUTPUT, --output OUTPUT
                        Output PowerPoint file (auto-generated if not specified)
  -t TITLE, --title TITLE
                        Custom presentation title (overrides JSON title)
  --use-example NAME    Use a built-in example file
  --list-examples       List all available example files
```

### PDF Conversion Options
```bash
PDF Options:
  --convert-pdf         Convert the generated PowerPoint to PDF
  --pdf-backend {aspose,libreoffice,auto}
                        PDF conversion backend (default: auto)
  --pdf-options PDF_OPTIONS
                        PDF conversion options as JSON string
  --pdf-output PDF_OUTPUT
                        Custom PDF output filename
```

### Convert-PDF Command Options
```bash
Convert-PDF Command:
  positional arguments:
    input_file            Input PPTX file to convert

  options:
    -h, --help            Show help message
    --pdf-backend {aspose,libreoffice,auto}
                        PDF conversion backend (default: auto)
    --pdf-options PDF_OPTIONS
                        PDF conversion options as JSON string
    --pdf-output PDF_OUTPUT
                        Custom PDF output filename
```

## 📋 PDF Options Reference

### Available Options
```json
{
  "backend": "auto",                    // "aspose", "libreoffice", "auto"
  "quality": "high",                    // "low", "medium", "high"
  "include_hidden_slides": false,       // Include hidden slides in PDF
  "password_protect": false,            // Password protect PDF
  "password": null,                     // PDF password
  "compression": true,                  // Compress PDF images
  "notes_pages": false,                 // Include notes pages
  "slide_range": null,                  // [start, end] slide range
  "compliance": null                    // "PDF/A", "PDF/UA" compliance
}
```

### Quality Settings
- **"low"**: Smaller file size, lower quality
- **"medium"**: Balanced file size and quality
- **"high"**: Best quality, larger file size

### Backend Comparison
| Backend | Quality | Cost | Dependencies | Best For |
|---------|---------|------|--------------|----------|
| **Aspose.Slides** | Excellent | Commercial | Python package | Professional quality |
| **LibreOffice** | Good | Free | LibreOffice install | Free option |
| **Auto** | Varies | Varies | Auto-detected | Convenience |

## 🎯 Advanced Command Examples

### Batch Processing
```bash
# Create multiple presentations with PDF
for file in *.json; do
  praisonaippt -i "$file" --convert-pdf
done

# Convert all PPTX files to PDF
for file in *.pptx; do
  praisonaippt convert-pdf "$file"
done
```

### Custom Quality Settings
```bash
# High quality PDF (no compression)
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# Low quality PDF (smaller file size)
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"low","compression":true}'
```

### Password Protected PDF
```bash
# Create password-protected PDF
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"password_protect":true,"password":"secret123"}'
```

### Slide Range Export
```bash
# Export specific slides to PDF
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[1,5]}'

# Export slides 10-20
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[10,20]}'
```

### Compliance Standards
```bash
# PDF/A compliance (archival)
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"compliance":"PDF/A"}'

# PDF/UA compliance (accessibility)
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"compliance":"PDF/UA"}'
```

## 🔍 Command Examples by Use Case

### Quick Presentation Creation
```bash
# Fastest way to create presentation
praisonaippt

# With custom title
praisonaippt -t "Sunday Service"

# From specific file
praisonaippt -i easter_verses.yaml
```

### Professional PDF Export
```bash
# High quality PDF for printing
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# PDF for web (smaller file)
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"medium","compression":true}'
```

### Batch Processing
```bash
# Process all JSON files in directory
find . -name "*.json" -exec praisonaippt -i {} --convert-pdf \;

# Create presentations for multiple services
for service in morning evening; do
  praisonaippt -i "${service}_verses.yaml" -o "${service}_service.pptx"
done
```

### Development and Testing
```bash
# Use example for testing
praisonaippt --use-example tamil_verses

# Create test presentation with PDF
praisonaippt --use-example sample_verses --convert-pdf --pdf-output test.pdf

# List all available examples
praisonaippt --list-examples
```

## 🛠️ Troubleshooting Commands

### Check Installation
```bash
# Verify installation
praisonaippt --version

# Check available commands
praisonaippt --help

# Test PDF conversion availability
praisonaippt convert-pdf --help
```

### Debug PDF Issues
```bash
# Test with specific backend
praisonaippt convert-pdf test.pptx --pdf-backend libreoffice

# Check backend availability
python -c "from praisonaippt import PDFConverter; print(PDFConverter().get_available_backends())"
```

### File Path Issues
```bash
# Use absolute paths
praisonaippt -i /full/path/to/verses.yaml -o /full/path/to/output.pptx

# Handle spaces in filenames
praisonaippt -i "my verses.yaml" -o "my presentation.pptx"
```

## Main build flags (default command)

Used with `praisonaippt -i deck.yaml` (or `.json`):

| Flag | Purpose |
|------|---------|
| `-i`, `--input` | Deck file (default `verses.yaml`, falls back to `verses.json`) |
| `-o`, `--output` | Output `.pptx` path |
| `-t`, `--title` | Override `presentation_title` |
| `--template` | Theme template (`sermon-dark`, path, or `extends` chain) |
| `--list-templates` | List built-in / user templates |
| `--use-example` / `--list-examples` | Built-in example decks |
| `--convert-pdf` | Also export PDF |
| `--convert-video` | Also export MP4 |
| `--video-output` | MP4 path |
| `--video-preset` | `draft`, `standard`, `high`, `4k` |
| `--video-backend` | `compositor`, `auto`, `powerpoint` |
| `--narration-mode` | `fixed`, `audio_file`, `avatar`, `tts`, `auto` |
| `--video-options` | JSON merged into `video_export` |
| `--slide-range` | `START-END` (1-based slides in MP4) |
| `--export-slide-jpegs` | Export `slide_images_dir` JPEGs after build |
| `--sync-variants` | Sync from `pipeline.content_master` before build |
| `--seed-timing` | Update verse timings from `pipeline.transcript_path` |
| `--validate-deck` | Run validation gates only (no build) |
| `--validate-pip` | PiP face-centre QA (fails build if strict) |
| `--strict-pip` | All calibration seeks must pass PiP QA |
| `--strict-post-render` | Fail if post-render MP4 QC fails |
| `--force` | Force avatar re-calibration (`avatar_calibration.force`) |
| `--validation-image` | Save PiP centring diagram PNG |
| `--golden-slide-dir` | Golden JPEG MD5 compare for CI |
| `--rights-acknowledged` | Pass rights/licensing gate |
| `--content-master` | Override `pipeline.content_master` |
| `--transcript-json` | Override transcript path for timing / A-V gates |
| `--pipeline-report` | Write pipeline-style report JSON on preflight |
| `--no-list-slides` | Skip slide outline after build |
| `--no-upload` | Skip Google Drive upload |
| `-v` / `--verbose` / `-q` | Logging level |

## Video, avatar, and HeyGen commands

**Feature overview:** [Recent features](recent-features.md)

Full behaviour: [Video export](video-export.md) · [HeyGen examples](heygen-examples.md) · [Avatar calibration](avatar-calibration.md) · [Slide JPEGs](slide-images.md) · [Slide QA](slide-qa.md) · [Pipeline architecture](architecture-pipeline.md)

### Video export

```bash
# Build deck + MP4
praisonaippt -i deck.yaml -o deck.pptx --convert-video --video-output deck.mp4
praisonaippt -i deck.json -o deck.pptx --convert-video   # JSON deck — same schema

# PPTX only (loads deck.yaml / deck.json sidecar beside PPTX for PiP paths)
praisonaippt convert-video deck.pptx --video-output deck.mp4

# Dependency check (also: praisonaippt --check with no command)
praisonaippt convert-video --check

# Override narration
praisonaippt -i deck.yaml -o deck.pptx --convert-video --narration-mode avatar
```

| Flag | Values |
|------|--------|
| `--convert-video` | On main command: build and export MP4 |
| `--video-output` | Output path |
| `--video-preset` | `draft`, `standard`, `high`, `4k` |
| `--narration-mode` | `fixed`, `audio_file`, `avatar`, `tts`, `auto` |
| `--video-options` | JSON merged into `video_export` |
| `--slide-range` | `START-END` (1-based) |
| `--keep-temp` | With `convert-video`: keep temp PNG/segments |
| `--check` | With `convert-video`: preflight ffmpeg/LibreOffice tools |

### Slide JPEG export

```bash
praisonaippt build-slide-images -i deck.yaml -o deck.pptx
praisonaippt export-slide-jpegs deck.pptx --slide-images-dir slide_images
praisonaippt -i deck.yaml -o deck.pptx --export-slide-jpegs
```

### Avatar PiP calibration

```bash
praisonaippt calibrate-avatar examples/heygen-50590-video-audio-heygen.yaml --force
praisonaippt calibrate-avatar --avatar-video examples/heygen-article-50590.mp4 --seek 6.0
praisonaippt calibrate-avatar deck.yaml --write   # persist into deck YAML or JSON
```

| Flag | Purpose |
|------|---------|
| `--force` | Ignore `.praisonaippt/avatar-framing/` cache |
| `--write` | Write calibrated `crop_x` into deck YAML |
| `--seek-times` | Comma-separated probe times (seconds) |
| `--validation-image` | Save annotated centring diagram PNG (optional path) |

### Face centre probe

```bash
praisonaippt pip-face-centre -i deck.yaml --slide 6
praisonaippt pip-face-centre --avatar-video speaker.mp4 --crop-x 0.53 --zoom 1.45
praisonaippt pip-face-centre --pip-image probe.png
praisonaippt pip-face-centre -i deck.yaml --validation-image out.png
praisonaippt calibrate-avatar deck.yaml --force --validation-image
```

`--validation-image` saves an annotated PNG: green circle centre, yellow face box, **L/R/T/B** pixel gaps from each side of the head to the circle (see [Avatar calibration](avatar-calibration.md)).

### Transcript → YAML (HeyGen variants)

```bash
praisonaippt transcript-to-yaml -i timestamps.json -o examples/heygen-article-50590 --variants all
```

### Deck pipeline (sync, validate, build, report)

Unified orchestration — see [Pipeline architecture](architecture-pipeline.md).

```bash
# Full HeyGen build (recommended for CI)
praisonaippt pipeline -i examples/heygen-50590-video-audio-heygen.yaml \
  -o examples/heygen-50590-video-audio-heygen.pptx \
  --convert-video \
  --video-output examples/heygen-50590-video-audio-heygen.mp4 \
  --validate-pip \
  --export-slide-jpegs \
  --pipeline-report examples/.praisonaippt/heygen-50590-video-audio-heygen.pipeline-report.json

# Validate only (no PPTX / MP4) — JSON or YAML
praisonaippt validate-deck -i deck.json --validate-pip --transcript-json timestamps.json

# Sync five HeyGen variants from content master
praisonaippt sync-variants -i examples/heygen-50590-content.yaml

# Plan → approve → sync → build
praisonaippt plan-slides -i examples/short-script-50590_timestamps.json \
  -o examples/heygen-50590-draft.yaml \
  --content-master examples/heygen-50590-content.yaml
praisonaippt approve-plan -i examples/heygen-50590-draft.yaml

# Whisper transcript (input to plan-slides / pipeline.transcript_path)
praisonaippt transcribe -i examples/short-script-50590.mp3 \
  -o examples/short-script-50590_timestamps.json

# Skip PPTX build (gates + MP4 only)
praisonaippt pipeline -i deck.yaml --skip-build --convert-video
```

| Command | Builds PPTX | Builds MP4 | Writes `report.json` |
|---------|-------------|------------|----------------------|
| `pipeline` | Yes (unless `--skip-build`) | If `--convert-video` | Yes (default under `.praisonaippt/`) |
| `validate-deck` | No | No | If `--pipeline-report` |
| Main `-i` + `--validate-deck` | Yes | Optional | If `--pipeline-report` |

| Flag / YAML (`pipeline:`) | Purpose |
|---------------------------|---------|
| `content_master` | Master deck for `sync-variants` |
| `transcript_path` | Whisper JSON for timing / A-V sync |
| `auto_sync` | Sync variants before build |
| `variant_prefix` | HeyGen filename prefix (default `heygen-50590`) |
| `validate_pip` | Run PiP centring gate |
| `strict_pip` | CLI or YAML: all seeks must pass |
| `export_mp4` | YAML-only: export MP4 in `pipeline` without CLI flag |
| `post_render_qc` / `strict_post_render` | ffprobe QC after MP4 |
| `golden_slide_dir` | Golden JPEG MD5 folder |
| `export_mp4_frames` | Export MP4 seek frames per verse |
| `mp4_frames_dir` | Output dir for `mp4-slide-NNN.jpg` |
| `validate_slide_qa` | Run slide QA manifest gate |
| `require_rights_ack` / `rights_acknowledged` | Rights gate |
| `content_approved` / `plan_approved` / `plan_draft` | Plan / content gates |
| `fail_fast` | Stop on first failed gate (default true) |
| `--sync-variants` | Force variant sync |
| `--seed-timing` | Refresh verse timings from transcript |
| `--rights-acknowledged` | CLI override for rights gate |
| `--pipeline-report` | Report JSON path |
| `--skip-build` | Pipeline: validate + MP4 only |

See [Video + transcript workflow](workflow-video-transcript-to-deck.md).

### Other utility commands

```bash
# Slide outline
praisonaippt list-slides -i deck.yaml
praisonaippt list-slides deck.pptx

# Theme template preview
praisonaippt --list-templates
praisonaippt template sermon-dark

# Config (~/.praisonaippt/config.yaml)
praisonaippt config
praisonaippt --config-show

# Google Drive
praisonaippt setup-oauth
praisonaippt setup-credentials
praisonaippt secure-credentials
```

### Showcase rebuild (examples)

```bash
python examples/build_showcase_examples.py --heygen-only
python examples/sync_heygen_variants.py
```

## 📚 Related Documentation

- [Installation Guide](installation.md)
- [Python API Documentation](python-api.md)
- [PDF Conversion Guide](pdf-conversion.md)
- [Examples and Templates](examples.md)
- [Deck reference (YAML or JSON)](yaml-reference.md)
- [Pipeline architecture](architecture-pipeline.md)
- [Video export](video-export.md)
- [Video + transcript workflow](workflow-video-transcript-to-deck.md)
- [HeyGen article examples](heygen-examples.md)
- [Avatar PiP calibration](avatar-calibration.md)
- [Slide JPEG export](slide-images.md)

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

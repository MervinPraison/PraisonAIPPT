---
layout: default
title: "Home - PraisonAI PPT"
description: "Create beautiful PowerPoint presentations from Bible verses with integrated PDF conversion"
---

# PraisonAI PPT

**Create beautiful PowerPoint presentations from Bible verses in YAML or JSON format with integrated PDF conversion capabilities.**

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://pypi.org/project/praisonaippt/)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 📦 **Proper Python Package** - Installable via pip with entry points
- 📖 **Dynamic verse loading** from JSON or YAML files
- 🎨 **Professional slide formatting** with proper placeholders
- 🎨 **Text highlighting** - Highlight specific words or phrases
- 🔤 **Custom font sizes** - Set custom font sizes for specific words
- 📑 **Multi-part verse support** for long verses
- 🔧 **Command-line interface** with flexible options
- 🐍 **Python API** for programmatic use
- 📄 **PDF Conversion** - Convert presentations to PDF with multiple backends
- 🔄 **Multiple PDF Backends** - Support for Aspose.Slides and LibreOffice
- ⚙️ **Advanced PDF Options** - Quality settings, password protection, and more
- 🎬 **Video export** — PPTX → MP4 with avatar PiP and HeyGen timing
- 🎙️ **Flexible narration** — HeyGen MP4 audio (default), external MP3, or TTS
- 🎯 **PiP calibration** — hybrid face detect + validation diagram (`pip-face-centre`)
- 🖼️ **Slide JPEG export** — `slide_images_dir` and `build-slide-images`
- 📐 **Layout reference** — standard, avatar, and `deck_*` slide types with full `slide_style` tokens

!!! tip "New in recent releases"
    See **[Recent features](recent-features.md)** for HeyGen variants, `audio_source`, validation PNGs, and calibration SDK.

## Layout and video documentation

| Guide | Description |
|-------|-------------|
| [Layouts overview](layouts-overview.md) | Choose standard, avatar, or deck layouts |
| [Standard slide layouts](slide-layouts.md) | `verse`, `list`, `table`, `quote`, … |
| [Avatar layouts & PiP](avatar-layouts.md) | HeyGen regions, floating PiP, `avatar_timeline` |
| [Deck layouts](deck-layouts.md) | Twelve `deck_*` sales templates |
| [Slide style reference](slide-style-reference.md) | Colours, `typography.*`, `layouts.*` |
| [YAML deck reference](yaml-reference.md) | Top-level keys and `video_export` |
| [Video export](video-export.md) | Compositor, narration modes, CLI |
| [HeyGen article examples](heygen-examples.md) | Five media variants, assets, build workflow |
| [Avatar PiP calibration](avatar-calibration.md) | Auto `crop_x`, hybrid face detect, CLI |
| [Slide JPEG export](slide-images.md) | `slide_images_dir`, `build-slide-images` |

Preview all docs locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Site config: `mkdocs.yml` at the repo root.

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install praisonaippt

# With PDF conversion support
pip install praisonaippt[pdf-aspose]

# Or with all PDF features
pip install praisonaippt[pdf-all]
```

### Basic Usage

```bash
# Create presentation from default verses.yaml
praisonaippt

# Create presentation and convert to PDF
praisonaippt -i verses.yaml --convert-pdf

# Convert existing PPTX to PDF
praisonaippt convert-pdf presentation.pptx
```

### Python API

```python
from praisonaippt import create_presentation, convert_pptx_to_pdf

# Load verses and create presentation
data = load_verses_from_file("verses.yaml")
result = create_presentation(data, convert_to_pdf=True)

print(f"PPTX: {result['pptx']}")
print(f"PDF: {result['pdf']}")
```

## 📋 Key Commands

### Presentation Creation
```bash
# Basic usage
praisonaippt

# Specify input file
praisonaippt -i my_verses.yaml

# Custom title and output
praisonaippt -i verses.yaml -o output.pptx -t "My Title"

# Use built-in examples
praisonaippt --use-example tamil_verses
```

### PDF Conversion
```bash
# Convert existing PPTX to PDF
praisonaippt convert-pdf presentation.pptx

# Create PPTX and convert to PDF
praisonaippt -i verses.yaml --convert-pdf

# Advanced PDF options
praisonaippt -i verses.yaml --convert-pdf \
  --pdf-options '{"quality":"high","compression":true}'
```

## 📄 File Format

### JSON Format
```yaml
presentation_title: Your Presentation Title
presentation_subtitle: Your Subtitle
sections:
- section: Section Name
  verses:
  - reference: Book Chapter:Verse (Version)
    text: The actual verse text here.
    highlights:
    - word1
    - phrase to highlight
    large_text:
      special_word: 200
```

### YAML Format (Recommended)
```yaml
presentation_title: Your Presentation Title
presentation_subtitle: Your Subtitle

sections:
  - section: Section Name
    verses:
      - reference: Book Chapter:Verse (Version)
        text: The actual verse text here.
        highlights:
          - word1
          - phrase to highlight
        large_text:
          special_word: 200
```

## 🔧 PDF Conversion Options

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

## 📊 Output

The package creates a PowerPoint presentation with:
- **Title Slide**: Shows the presentation title and subtitle
- **Section Slides**: One for each section in your JSON
- **Verse Slides**: One slide per verse (or multiple if the verse is long)

### Slide Formatting:
- **Verse Text**: 24pt, centered, black
- **Reference**: 18pt, centered, gray, italic
- **Section Titles**: 36pt, blue (#003366)
- **Layout**: Professional blank layout with custom text boxes

## 🎯 Next Steps

- [Installation Guide](installation.md)
- [Quick Start Tutorial](quickstart.md)
- [Complete Command Reference](commands.md)
- [Python API Documentation](python-api.md)
- [PDF Conversion Guide](pdf-conversion.md)
- [Examples and Templates](examples.md)
- [Recent features](recent-features.md)
- [HeyGen article examples](heygen-examples.md)

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/MervinPraison/PraisonAIPPT/issues)
- **Documentation**: [Full documentation](https://mervinpraison.github.io/PraisonAIPPT/)
- **PyPI**: [Package page](https://pypi.org/project/praisonaippt/)

---

**Built with ❤️ for creating beautiful Bible verse presentations**

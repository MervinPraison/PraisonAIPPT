---
layout: default
title: "Home - PraisonAI PPT"
description: "Create beautiful PowerPoint presentations from Bible verses with integrated PDF conversion"
---

# PraisonAI PPT

**Create beautiful PowerPoint presentations from Bible verses in JSON format with integrated PDF conversion capabilities.**

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
# Create presentation from default verses.json
praisonaippt

# Create presentation and convert to PDF
praisonaippt -i verses.json --convert-pdf

# Convert existing PPTX to PDF
praisonaippt convert-pdf presentation.pptx
```

### Python API

```python
from praisonaippt import create_presentation, convert_pptx_to_pdf

# Load verses and create presentation
data = load_verses_from_file("verses.json")
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
praisonaippt -i my_verses.json

# Custom title and output
praisonaippt -i verses.json -o output.pptx -t "My Title"

# Use built-in examples
praisonaippt --use-example tamil_verses
```

### PDF Conversion
```bash
# Convert existing PPTX to PDF
praisonaippt convert-pdf presentation.pptx

# Create PPTX and convert to PDF
praisonaippt -i verses.json --convert-pdf

# Advanced PDF options
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":true}'
```

## 📄 File Format

### JSON Format
```json
{
  "presentation_title": "Your Presentation Title",
  "presentation_subtitle": "Your Subtitle",
  "sections": [
    {
      "section": "Section Name",
      "verses": [
        {
          "reference": "Book Chapter:Verse (Version)",
          "text": "The actual verse text here.",
          "highlights": ["word1", "phrase to highlight"],
          "large_text": {"special_word": 200}
        }
      ]
    }
  ]
}
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

- [Installation Guide]({{ '/installation' | relative_url }})
- [Quick Start Tutorial]({{ '/quickstart' | relative_url }})
- [Complete Command Reference]({{ '/commands' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})
- [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})
- [Examples and Templates]({{ '/examples' | relative_url }})

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/MervinPraison/PraisonAIPPT/issues)
- **Documentation**: [Full documentation](https://mervinpraison.github.io/PraisonAIPPT/)
- **PyPI**: [Package page](https://pypi.org/project/praisonaippt/)

---

**Built with ❤️ for creating beautiful Bible verse presentations**

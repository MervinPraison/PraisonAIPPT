---
layout: default
title: "Python API - PraisonAI PPT"
description: "Complete Python API reference for PraisonAI PPT with code examples"
---

# Python API Documentation

## 🐍 Overview

PraisonAI PPT provides a comprehensive Python API for creating presentations and converting them to PDF. All functionality is accessible from the main package import.

## 📦 Package Imports

### Basic Import
```python
import praisonaippt
```

### Specific Imports
```python
from praisonaippt import (
    create_presentation,      # Core presentation creation
    load_verses_from_file,    # Load verses from file
    load_verses_from_dict,    # Load verses from dictionary
    convert_pptx_to_pdf,      # PDF conversion
    PDFOptions,               # PDF configuration options
    pptx_to_json              # PPTX → JSON extraction
)
```

## 🎯 Core Functions

### create_presentation()

Create a PowerPoint presentation from Bible verses data.

#### Signature
```python
def create_presentation(
    data, 
    output_file=None, 
    custom_title=None, 
    convert_to_pdf=False, 
    pdf_options=None, 
    pdf_backend='auto'
):
```

#### Parameters
- `data` (dict): Verses data dictionary
- `output_file` (str, optional): Output filename
- `custom_title` (str, optional): Custom presentation title
- `convert_to_pdf` (bool, optional): Convert to PDF (default: False)
- `pdf_options` (PDFOptions, optional): PDF conversion options
- `pdf_backend` (str, optional): PDF backend ('aspose', 'libreoffice', 'auto')

#### Returns
- `str` or `dict`: Path to PPTX file, or dict with both PPTX and PDF paths

#### Examples

**Basic Usage**
```python
from praisonaippt import create_presentation, load_verses_from_file

# Load verses from file
data = load_verses_from_file("verses.yaml")

# Create presentation
output_file = create_presentation(data)
print(f"Created: {output_file}")
```

**With Custom Output and Title**
```python
output_file = create_presentation(
    data,
    output_file="my_presentation.pptx",
    custom_title="My Custom Title"
)
```

**With PDF Conversion**
```python
result = create_presentation(
    data,
    output_file="presentation.pptx",
    convert_to_pdf=True
)

if isinstance(result, dict):
    print(f"PPTX: {result['pptx']}")
    print(f"PDF: {result['pdf']}")
```

**Advanced PDF Options**
```python
from praisonaippt import PDFOptions

pdf_options = PDFOptions(
    quality='high',
    compression=True,
    include_hidden_slides=False
)

result = create_presentation(
    data,
    convert_to_pdf=True,
    pdf_options=pdf_options,
    pdf_backend='aspose'
)
```

**With Theming (Dark Background + Font)**
```python
data = {
    "presentation_title": "Great Faith",
    "presentation_subtitle": "Selected Scriptures",
    "slide_style": {
        "background_image": "assets/background_alt.jpg",
        "text_color": "#FFFFFF",
        "reference_color": "#CCCCCC",
        "title_color": "#FFFFFF",
        "subtitle_color": "#AAAAAA",
        "section_title_color": "#FFFFFF",
        "highlight_color": "#FFD700",
        "annotation_color": "#1E50C8",
        "font_name": "Palatino",
        "alignment": "left",
        "reference_position": "top"
    },
    "sections": [...]
}
result = create_presentation(data, output_file="themed.pptx")
```

#### slide_style Reference

--8<-- "docs/snippets/slide_style_table.md"


Load verses data from JSON or YAML file.

#### Signature
```python
def load_verses_from_file(file_path):
```

#### Parameters
- `file_path` (str): Path to JSON or YAML file

#### Returns
- `dict`: Verses data dictionary or None if error

#### Examples
```python
from praisonaippt import load_verses_from_file

# Load JSON file
data = load_verses_from_file("verses.yaml")

# Load YAML file
data = load_verses_from_file("verses.yaml")

# Handle errors
if data:
    print("Loaded successfully")
else:
    print("Failed to load file")
```

### load_verses_from_dict()

Create verses data from dictionary.

#### Signature
```python
def load_verses_from_dict(data_dict):
```

#### Parameters
- `data_dict` (dict): Dictionary with verses data

#### Returns
- `dict`: Validated verses data dictionary

#### Examples
```python
from praisonaippt import load_verses_from_dict

data = {
    "presentation_title": "My Presentation",
    "sections": [
        {
            "section": "Section 1",
            "verses": [
                {
                    "reference": "John 3:16",
                    "text": "For God so loved the world..."
                }
            ]
        }
    ]
}

validated_data = load_verses_from_dict(data)
```

## 🔁 PPTX → JSON Extraction

### pptx_to_json()

Extract slide content from an existing PPTX back into the praisonaippt JSON schema.
This is the **inverse of `create_presentation()`**.

#### Signature
```python
def pptx_to_json(
    pptx_path: str,
    output_path: Optional[str] = None,
    pretty: bool = True,
    images_dir: Optional[str] = None,
    output_format: str = 'json',
) -> dict:
```

#### Parameters
- `pptx_path` (str): Path to `.pptx` or `.ppt` file
- `output_path` (str, optional): If set, writes output to this file
- `pretty` (bool, optional): Indent JSON output (default: True)
- `images_dir` (str, optional): Optional directory to save extracted images
- `output_format` (str, optional): Output format ('json' or 'yaml', default: 'json')

#### Returns
- `dict`: conforms to the praisonaippt JSON schema

#### Raises
- `FileNotFoundError`: if `pptx_path` does not exist
- `ValueError`: if file is not `.pptx` or `.ppt`

#### Examples
```python
from praisonaippt import pptx_to_json

# In-memory dict
data = pptx_to_json("presentation.pptx")
print(data["presentation_title"])

# Save to file
pptx_to_json("presentation.pptx", output_path="output.json")

# Compact JSON
pptx_to_json("presentation.pptx", output_path="out.json", pretty=False)

# Error handling
try:
    data = pptx_to_json("missing.pptx")
except FileNotFoundError:
    print("File not found")
except ValueError:
    print("Not a PPTX file")
```

> 📖 Full reference: [PPTX to JSON Guide]({{ '/pptx-to-json' | relative_url }})

---

## 📄 PDF Conversion Functions

### convert_pptx_to_pdf()

Convert existing PPTX file to PDF.

#### Signature
```python
def convert_pptx_to_pdf(
    input_file, 
    output_file=None, 
    backend='auto', 
    options=None
):
```

#### Parameters
- `input_file` (str): Path to PPTX file
- `output_file` (str, optional): Output PDF filename
- `backend` (str, optional): PDF backend ('aspose', 'libreoffice', 'auto')
- `options` (PDFOptions, optional): PDF conversion options

#### Returns
- `str`: Path to created PDF file

#### Examples
```python
from praisonaippt import convert_pptx_to_pdf, PDFOptions

# Basic conversion
pdf_file = convert_pptx_to_pdf("presentation.pptx")

# With custom output
pdf_file = convert_pptx_to_pdf(
    "presentation.pptx", 
    "output.pdf"
)

# With options
options = PDFOptions(quality='high', compression=True)
pdf_file = convert_pptx_to_pdf(
    "presentation.pptx", 
    options=options
)

# With specific backend
pdf_file = convert_pptx_to_pdf(
    "presentation.pptx", 
    backend='libreoffice'
)
```

### PDFOptions Class

Configuration options for PDF conversion.

#### Constructor
```python
def __init__(
    backend='auto',
    quality='high',
    include_hidden_slides=False,
    password_protect=False,
    password=None,
    compression=True,
    notes_pages=False,
    slide_range=None,
    compliance=None
):
```

#### Parameters
- `backend` (str): PDF backend ('aspose', 'libreoffice', 'auto')
- `quality` (str): Quality setting ('low', 'medium', 'high')
- `include_hidden_slides` (bool): Include hidden slides
- `password_protect` (bool): Password protect PDF
- `password` (str): PDF password
- `compression` (bool): Compress PDF images
- `notes_pages` (bool): Include notes pages
- `slide_range` (list): [start, end] slide range
- `compliance` (str): PDF compliance ('PDF/A', 'PDF/UA')

#### Examples
```python
from praisonaippt import PDFOptions

# Default options
options = PDFOptions()

# High quality, no compression
options = PDFOptions(
    quality='high',
    compression=False
)

# Password protected
options = PDFOptions(
    password_protect=True,
    password='secret123'
)

# Slide range
options = PDFOptions(
    slide_range=[1, 5]
)

# PDF/A compliance
options = PDFOptions(
    compliance='PDF/A'
)
```

## 📋 Data Structure

### Input Data Format

#### JSON Structure
```python
data = {
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

#### YAML Structure
```python
data = {
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

### Verse Object Properties

#### Required Properties
- `reference` (str): Bible reference (e.g., `"John 3:16 (KJV)"`) — shown at slide bottom
- `text` (str): Verse text content. Use `\n` to separate items for list slides.

#### Optional Properties

| Field | Type | Default | Description |
|---|---|---|---|
| `highlights` | list | `[]` | Per-phrase formatting — strings or objects (see below) |
| `large_text` | dict | `{}` | `{"phrase": font_size_pt}` — enlarge specific words |
| `list_type` | string | `null` | `"bullet"` or `"numbered"` — renders `\n`-separated lines as a list |
| `alignment` | string | `"center"` | Text alignment: `"left"`, `"center"`, `"right"` |
| `font_size` | integer | `32` | Body text size in pt |

#### Highlight Formats

**String** (simple) — bold + orange:
```python
"highlights": ["God so loved", "only Son"]
```

**Object** (rich) — full per-phrase control:
```python
"highlights": [
    "simple phrase",                              # bold + orange (default)
    {
        "text": "faith to faith",
        "color": "#4A86E8",    # named or hex color
        "bold": True,
        "italic": False,
        "underline": True,
        "annotation": 2        # renders ❷ superscript bubble after phrase
    }
]
```

Named colors: `orange` (default), `yellow`, `red`, `green`, `blue`, `white`, `cyan`, `purple`

#### Example Verse Object
```python
verse = {
    "reference": "Romans 1:16–17 (NKJV)",
    "text": "For I am not ashamed of the gospel of Christ, for it is the power of God to salvation.",
    "highlights": [
        { "text": "the gospel",  "annotation": 1 },
        { "text": "the power",   "annotation": 2 },
        { "text": "salvation",   "color": "#4A86E8", "underline": True, "annotation": 3 },
        "for everyone who believes"
    ],
    "alignment": "center",
    "font_size": 32
}
```

#### Bullet List Verse
```python
verse = {
    "reference": "",
    "text": "Woman with the Issue of Blood\nCenturion\nCanaanite",
    "list_type": "bullet",
    "alignment": "center"
}
```

> 📖 See the [Rich Text Formatting Guide]({{ '/formatting' | relative_url }}) for the full feature reference.


## 🎯 Complete Examples

### Example 1: Basic Presentation Creation
```python
from praisonaippt import create_presentation, load_verses_from_file

# Load data from file
data = load_verses_from_file("verses.yaml")

# Create presentation
output_file = create_presentation(
    data,
    output_file="my_presentation.pptx",
    custom_title="My Custom Title"
)

print(f"Presentation created: {output_file}")
```

### Example 2: Presentation with PDF Conversion
```python
from praisonaippt import create_presentation, load_verses_from_file, PDFOptions

# Load data
data = load_verses_from_file("verses.yaml")

# Configure PDF options
pdf_options = PDFOptions(
    quality='high',
    compression=True,
    include_hidden_slides=False
)

# Create presentation with PDF
result = create_presentation(
    data,
    output_file="presentation.pptx",
    convert_to_pdf=True,
    pdf_options=pdf_options
)

# Handle result
if isinstance(result, dict):
    print(f"PPTX: {result['pptx']}")
    print(f"PDF: {result['pdf']}")
else:
    print(f"PPTX only: {result}")
```

### Example 3: Batch Processing
```python
from praisonaippt import create_presentation, load_verses_from_file
import os

# Process multiple JSON files
json_files = [f for f in os.listdir('.') if f.endswith('.json')]

for json_file in json_files:
    try:
        data = load_verses_from_file(json_file)
        if data:
            output_name = json_file.replace('.json', '.pptx')
            result = create_presentation(
                data,
                output_file=output_name,
                convert_to_pdf=True
            )
            print(f"Processed: {json_file}")
    except Exception as e:
        print(f"Error processing {json_file}: {e}")
```

### Example 4: Custom Data Creation
```python
from praisonaippt import create_presentation, load_verses_from_dict

# Create custom data structure
data = {
    "presentation_title": "Easter Sunday",
    "presentation_subtitle": "Celebrating the Resurrection",
    "sections": [
        {
            "section": "The Resurrection",
            "verses": [
                {
                    "reference": "Matthew 28:6 (KJV)",
                    "text": "He is not here: for he is risen, as he said. Come, see the place where the Lord lay.",
                    "highlights": ["risen", "Lord"]
                },
                {
                    "reference": "John 11:25 (KJV)",
                    "text": "Jesus said unto her, I am the resurrection, and the life: he that believeth in me, though he were dead, yet shall he live:",
                    "highlights": ["resurrection", "life"],
                    "large_text": {"resurrection": 200}
                }
            ]
        }
    ]
}

# Create presentation
output_file = create_presentation(data, output_file="easter.pptx")
print(f"Easter presentation created: {output_file}")
```

### Example 5: Advanced PDF Conversion
```python
from praisonaippt import convert_pptx_to_pdf, PDFOptions

# Convert existing presentation with advanced options
options = PDFOptions(
    quality='high',
    compression=False,
    include_hidden_slides=True,
    password_protect=True,
    password='secret123',
    compliance='PDF/A'
)

pdf_file = convert_pptx_to_pdf(
    "presentation.pptx",
    "secure_presentation.pdf",
    options=options,
    backend='aspose'
)

print(f"Secure PDF created: {pdf_file}")
```

## 🔍 Error Handling

### Common Error Patterns
```python
from praisonaippt import create_presentation, load_verses_from_file

try:
    # Load file with error handling
    data = load_verses_from_file("verses.yaml")
    if not data:
        print("Failed to load verses file")
        return
    
    # Create presentation with error handling
    result = create_presentation(
        data,
        output_file="output.pptx",
        convert_to_pdf=True
    )
    
    if not result:
        print("Failed to create presentation")
        return
    
    # Handle result
    if isinstance(result, dict):
        print(f"Success! PPTX: {result['pptx']}, PDF: {result['pdf']}")
    else:
        print(f"Success! PPTX: {result}")
        
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error: {e}")
```

### PDF Conversion Error Handling
```python
from praisonaippt import convert_pptx_to_pdf, PDFOptions, PDFConverter

# Check available backends
converter = PDFConverter()
backends = converter.get_available_backends()

if not backends:
    print("No PDF backends available")
    print("Please install Aspose.Slides or LibreOffice")
else:
    try:
        pdf_file = convert_pptx_to_pdf("presentation.pptx")
        print(f"PDF created: {pdf_file}")
    except Exception as e:
        print(f"PDF conversion failed: {e}")
```

## 📚 Related Documentation

- [Installation Guide]({{ '/installation' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})
- [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})
- [PPTX to JSON Guide]({{ '/pptx-to-json' | relative_url }})
- [Examples and Templates]({{ '/examples' | relative_url }})

---

## 📐 Slide Size (Widescreen)

Set the presentation dimensions at the top level of the data dict:

```python
data = {
    "presentation_title": "Great Faith",
    "slide_size": "widescreen",   # or "16:9", "standard", "4:3", "16:10"
    "slide_style": { ... },
    "sections": [ ... ]
}
```

| Value | Dimensions |
|---|---|
| `"widescreen"` / `"16:9"` | 13.33" × 7.5" |
| `"standard"` / `"4:3"` | 10" × 7.5" (default) |
| `"16:10"` | 12.8" × 8.0" |
| `{"width": W, "height": H}` | Custom inches |

---

## 🔢 Verse Number Superscripts

Start each line of a verse's `text` field with its verse number and a space to render small superscript numbers:

```python
{
    "reference": "Mark 5:27-29 (NKJV)",
    "text": (
        "27 When she heard about Jesus, she came behind Him in the crowd and touched His garment.\n"
        "28 For she said, 'If only I may touch His clothes, I shall be made well.'\n"
        "29 Immediately the fountain of her blood was dried up, and she felt in her body that she was healed."
    )
}
```

Numbers render as ~52% body-size superscripts with 30% raised baseline. Works with `highlights` too — verse numbers appear before any highlighted text.

---

## 🎨 Package-Level Defaults

`_resolve_theme()` now uses opinionated defaults. Any `slide_style` key overrides them:

| Key | Default |
|---|---|
| `font_name` | `"Palatino"` |
| `alignment` | `"left"` |
| `reference_position` | `"top"` |
| `highlight_color` (dark bg) | `#FFD700` yellow |
| `highlight_color` (light) | `#FF8C00` orange |

---

## 📤 PDF + Google Drive Upload

```python
from praisonaippt import create_presentation

# Generate PPTX; CLI handles PDF + upload via --convert-pdf flag
result = create_presentation(data, output_file="my.pptx")
```

Via CLI (recommended — handles GDrive fallback + auto-upload):
```bash
# Generates PPTX + PDF, uploads both to YYYY/MM folder on Google Drive
praisonaippt -i verses.yaml -o my.pptx --convert-pdf

# Convert existing PPTX
praisonaippt convert-pdf my.pptx --upload-gdrive
```

The CLI falls back automatically to Google Drive API for PDF conversion when LibreOffice is not available.

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

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
    PDFOptions                # PDF configuration options
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
data = load_verses_from_file("verses.json")

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

### load_verses_from_file()

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
data = load_verses_from_file("verses.json")

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
- `reference` (str): Bible reference (e.g., "John 3:16 (KJV)")
- `text` (str): Verse text content

#### Optional Properties
- `highlights` (list): Words/phrases to highlight in orange/bold
- `large_text` (dict): Custom font sizes for specific words

#### Example Verse Object
```python
verse = {
    "reference": "John 3:16 (KJV)",
    "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
    "highlights": ["God", "loved", "everlasting life"],
    "large_text": {"everlasting life": 200}
}
```

## 🎯 Complete Examples

### Example 1: Basic Presentation Creation
```python
from praisonaippt import create_presentation, load_verses_from_file

# Load data from file
data = load_verses_from_file("verses.json")

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
data = load_verses_from_file("verses.json")

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
    data = load_verses_from_file("verses.json")
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
- [Examples and Templates]({{ '/examples' | relative_url }})

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

---
layout: default
title: "PDF Conversion Guide - PraisonAI PPT"
description: "Complete guide to PDF conversion with multiple backends and advanced options"
---

# PDF Conversion Guide

## 📄 Overview

PraisonAI PPT provides comprehensive PDF conversion functionality with multiple backend support and advanced configuration options. PDF conversion is fully integrated into the SDK and accessible via both CLI and Python API.

## 🔄 Supported Backends

### Aspose.Slides (Commercial - Recommended)
- **Quality**: Excellent rendering
- **Features**: Full feature support
- **Dependencies**: Python package only
- **Cost**: Commercial license required
- **Best for**: Professional quality output

### LibreOffice (Free)
- **Quality**: Good rendering
- **Features**: Most features supported
- **Dependencies**: LibreOffice installation
- **Cost**: Free
- **Best for**: Budget-conscious projects

### Auto-Detection
- **Behavior**: Automatically selects best available backend
- **Priority**: Aspose.Slides → LibreOffice → Error
- **Recommendation**: Use for maximum compatibility

## 🚀 Installation for PDF Conversion

### Option 1: Aspose.Slides (Recommended)
```bash
pip install praisonaippt[pdf-aspose]
```

### Option 2: LibreOffice (Free)
```bash
# Install praisonaippt
pip install praisonaippt

# Install LibreOffice
# Ubuntu/Debian:
sudo apt-get install libreoffice

# macOS:
brew install --cask libreoffice

# Windows:
# Download from libreoffice.org
```

### Option 3: All PDF Features
```bash
pip install praisonaippt[pdf-all]
```

## 💻 CLI PDF Conversion

### Convert Existing PPTX to PDF

#### Basic Conversion
```bash
# Simple conversion
praisonaippt convert-pdf presentation.pptx

# Specify output filename
praisonaippt convert-pdf presentation.pptx --pdf-output output.pdf
```

#### Backend Selection
```bash
# Use specific backend
praisonaippt convert-pdf presentation.pptx --pdf-backend aspose
praisonaippt convert-pdf presentation.pptx --pdf-backend libreoffice
praisonaippt convert-pdf presentation.pptx --pdf-backend auto
```

#### Advanced Options
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

### Create PPTX and Convert to PDF

#### Basic Integrated Conversion
```bash
# Create and convert in one step
praisonaippt -i verses.json --convert-pdf

# Custom PDF output
praisonaippt -i verses.json --convert-pdf --pdf-output custom.pdf
```

#### Advanced Integrated Conversion
```bash
# With custom options
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","include_hidden_slides":true}'

# With backend selection
praisonaippt -i verses.json --convert-pdf \
  --pdf-backend aspose \
  --pdf-options '{"quality":"high","compression":false}'
```

## 🐍 Python API PDF Conversion

### Basic Conversion
```python
from praisonaippt import convert_pptx_to_pdf

# Simple conversion
pdf_file = convert_pptx_to_pdf("presentation.pptx")

# With custom output
pdf_file = convert_pptx_to_pdf("presentation.pptx", "output.pdf")
```

### Advanced Conversion
```python
from praisonaippt import convert_pptx_to_pdf, PDFOptions

# Configure options
options = PDFOptions(
    quality='high',
    compression=True,
    include_hidden_slides=False
)

# Convert with options
pdf_file = convert_pptx_to_pdf(
    "presentation.pptx",
    options=options,
    backend='aspose'
)
```

### Integrated Creation and Conversion
```python
from praisonaippt import create_presentation, load_verses_from_file, PDFOptions

# Load data
data = load_verses_from_file("verses.json")

# Configure PDF options
pdf_options = PDFOptions(
    quality='high',
    compression=True,
    password_protect=True,
    password='secret123'
)

# Create presentation with PDF
result = create_presentation(
    data,
    output_file="presentation.pptx",
    convert_to_pdf=True,
    pdf_options=pdf_options,
    pdf_backend='aspose'
)

print(f"PPTX: {result['pptx']}")
print(f"PDF: {result['pdf']}")
```

## ⚙️ PDF Options Reference

### Complete Options List
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
- **"low"**: Smallest file size, basic quality
- **"medium"**: Balanced file size and quality
- **"high"**: Best quality, larger file size

### Compliance Standards
- **"PDF/A"**: Archival standard for long-term preservation
- **"PDF/UA"**: Universal Accessibility standard

## 🎯 Use Case Examples

### High Quality Printing
```bash
# CLI
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# Python
options = PDFOptions(quality='high', compression=False)
result = create_presentation(data, convert_to_pdf=True, pdf_options=options)
```

### Web Distribution
```bash
# CLI
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"medium","compression":true}'

# Python
options = PDFOptions(quality='medium', compression=True)
result = create_presentation(data, convert_to_pdf=True, pdf_options=options)
```

### Secure Document
```bash
# CLI
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"password_protect":true,"password":"secret123"}'

# Python
options = PDFOptions(password_protect=True, password='secret123')
result = create_presentation(data, convert_to_pdf=True, pdf_options=options)
```

### Partial Slide Export
```bash
# CLI - Export slides 1-5
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[1,5]}'

# Python
options = PDFOptions(slide_range=[1, 5])
pdf_file = convert_pptx_to_pdf("presentation.pptx", options=options)
```

### Archival Quality
```bash
# CLI
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compliance":"PDF/A"}'

# Python
options = PDFOptions(quality='high', compliance='PDF/A')
result = create_presentation(data, convert_to_pdf=True, pdf_options=options)
```

## 🔍 Backend Detection and Troubleshooting

### Check Available Backends
```python
from praisonaippt.pdf_converter import PDFConverter

converter = PDFConverter()
backends = converter.get_available_backends()
print(f"Available backends: {backends}")
```

### Manual Backend Testing
```python
from praisonaippt import convert_pptx_to_pdf

# Test Aspose.Slides
try:
    pdf_file = convert_pptx_to_pdf("test.pptx", backend='aspose')
    print("Aspose.Slides backend working")
except Exception as e:
    print(f"Aspose.Slides failed: {e}")

# Test LibreOffice
try:
    pdf_file = convert_pptx_to_pdf("test.pptx", backend='libreoffice')
    print("LibreOffice backend working")
except Exception as e:
    print(f"LibreOffice failed: {e}")
```

### Common Issues and Solutions

#### Aspose.Slides Issues
```bash
# License error
pip install --upgrade aspose.slides

# Import error
pip uninstall aspose.slides
pip install aspose.slides>=24.0.0
```

#### LibreOffice Issues
```bash
# LibreOffice not found
# Ubuntu/Debian:
sudo apt-get install libreoffice

# macOS:
brew install --cask libreoffice

# Windows:
# Download and install from libreoffice.org

# Add to PATH (if needed)
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"
```

#### General PDF Issues
```python
# Test with simple presentation
from praisonaippt import create_presentation

test_data = {
    "presentation_title": "Test",
    "sections": [{
        "section": "Test",
        "verses": [{"reference": "Test 1:1", "text": "Test verse"}]
    }]
}

result = create_presentation(test_data, convert_to_pdf=True)
print(f"Test result: {result}")
```

## 📊 Performance Considerations

### File Size vs Quality
```python
# Small file (web)
options = PDFOptions(quality='low', compression=True)

# Balanced (general use)
options = PDFOptions(quality='medium', compression=True)

# Large file (printing)
options = PDFOptions(quality='high', compression=False)
```

### Processing Speed
- **Aspose.Slides**: Faster processing, better quality
- **LibreOffice**: Slower processing, free alternative
- **Large presentations**: Consider slide range limits

### Memory Usage
```python
# For large presentations, process in chunks
options = PDFOptions(slide_range=[1, 10])  # Process 10 slides at a time
```

## 🔧 Advanced Configuration

### Custom Backend Configuration
```python
from praisonaippt.pdf_converter import PDFConverter

# Create custom converter
converter = PDFConverter()

# Check specific backend availability
aspose_available = converter._check_aspose_available()
libreoffice_available = converter._check_libreoffice_available()

print(f"Aspose.Slides: {aspose_available}")
print(f"LibreOffice: {libreoffice_available}")
```

### Batch Processing
```python
import os
from praisonaippt import convert_pptx_to_pdf

# Convert all PPTX files in directory
pptx_files = [f for f in os.listdir('.') if f.endswith('.pptx')]

for pptx_file in pptx_files:
    try:
        pdf_file = convert_pptx_to_pdf(pptx_file)
        print(f"Converted: {pptx_file} -> {pdf_file}")
    except Exception as e:
        print(f"Failed to convert {pptx_file}: {e}")
```

### Error Handling Best Practices
```python
from praisonaippt import convert_pptx_to_pdf, PDFConverter

def safe_convert_to_pdf(input_file, output_file=None):
    """Convert PPTX to PDF with comprehensive error handling"""
    
    # Check backends
    converter = PDFConverter()
    backends = converter.get_available_backends()
    
    if not backends:
        raise Exception("No PDF backends available")
    
    # Try conversion with fallback
    for backend in backends:
        try:
            return convert_pptx_to_pdf(
                input_file, 
                output_file, 
                backend=backend
            )
        except Exception as e:
            print(f"Backend {backend} failed: {e}")
            continue
    
    raise Exception("All backends failed")

# Usage
try:
    pdf_file = safe_convert_to_pdf("presentation.pptx")
    print(f"Success: {pdf_file}")
except Exception as e:
    print(f"Conversion failed: {e}")
```

## 📚 Related Documentation

- [Installation Guide]({{ '/installation' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})
- [Examples and Templates]({{ '/examples' | relative_url }})

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

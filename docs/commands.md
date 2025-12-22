---
layout: default
title: "Commands - PraisonAI PPT"
description: "Complete command-line interface reference for PraisonAI PPT"
---

# Complete Command Reference

## 📋 Command Overview

PraisonAI PPT provides a comprehensive command-line interface for creating presentations and converting them to PDF.

### Main Commands
- `praisonaippt` - Create PowerPoint presentations
- `praisonaippt convert-pdf` - Convert existing PPTX to PDF

## 🚀 Basic Commands

### Create Presentation

#### Default Usage
```bash
# Use default verses.json in current directory
praisonaippt
```

#### Specify Input File
```bash
# JSON format
praisonaippt -i my_verses.json

# YAML format (recommended)
praisonaippt -i my_verses.yaml
```

#### Specify Output File
```bash
# Custom output filename
praisonaippt -i verses.json -o my_presentation.pptx
```

#### Use Custom Title
```bash
# Override JSON title
praisonaippt -i verses.json -t "My Custom Title"
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
praisonaippt -i verses.json --convert-pdf

# Custom PDF output filename
praisonaippt -i verses.json --convert-pdf --pdf-output custom.pdf
```

#### Advanced Integrated Conversion
```bash
# With custom PDF options
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","include_hidden_slides":true}'

# With backend selection
praisonaippt -i verses.json --convert-pdf \
  --pdf-backend aspose \
  --pdf-options '{"quality":"high","compression":false}'
```

## ⚙️ Command Options Reference

### Global Options
```bash
Options:
  -h, --help            Show help message
  -v, --version         Show version number
  -i INPUT, --input INPUT
                        Input JSON/YAML file (default: verses.json)
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
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# Low quality PDF (smaller file size)
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"low","compression":true}'
```

### Password Protected PDF
```bash
# Create password-protected PDF
praisonaippt -i verses.json --convert-pdf \
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
praisonaippt -i easter_verses.json
```

### Professional PDF Export
```bash
# High quality PDF for printing
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# PDF for web (smaller file)
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"medium","compression":true}'
```

### Batch Processing
```bash
# Process all JSON files in directory
find . -name "*.json" -exec praisonaippt -i {} --convert-pdf \;

# Create presentations for multiple services
for service in morning evening; do
  praisonaippt -i "${service}_verses.json" -o "${service}_service.pptx"
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
praisonaippt -i /full/path/to/verses.json -o /full/path/to/output.pptx

# Handle spaces in filenames
praisonaippt -i "my verses.json" -o "my presentation.pptx"
```

## 📚 Related Documentation

- [Installation Guide]({{ '/installation' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})
- [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})
- [Examples and Templates]({{ '/examples' | relative_url }})

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

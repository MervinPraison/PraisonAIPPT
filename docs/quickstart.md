---
layout: default
title: "Quick Start - PraisonAI PPT"
description: "Get started with PraisonAI PPT in minutes - Quick start guide"
---

# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Installation
```bash
# Install with PDF support
pip install praisonaippt[pdf-all]
```

### Step 2: Create Your First Verses File

Create `verses.json`:
```json
{
  "presentation_title": "My First Presentation",
  "presentation_subtitle": "Created with PraisonAI PPT",
  "sections": [
    {
      "section": "Introduction",
      "verses": [
        {
          "reference": "John 3:16 (KJV)",
          "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
          "highlights": ["God", "loved", "everlasting life"]
        }
      ]
    }
  ]
}
```

### Step 3: Create Your Presentation
```bash
# Basic presentation
praisonaippt

# With PDF conversion
praisonaippt --convert-pdf
```

### Step 4: View Your Results
- **PowerPoint**: `My_First_Presentation.pptx`
- **PDF**: `My_First_Presentation.pdf` (if `--convert-pdf` used)

## 📝 Alternative: Use Built-in Examples

```bash
# List available examples
praisonaippt --list-examples

# Use an example
praisonaippt --use-example tamil_verses --convert-pdf
```

## 🐍 Python API Quick Start

```python
from praisonaippt import create_presentation, load_verses_from_file

# Load your verses
data = load_verses_from_file("verses.json")

# Create presentation with PDF
result = create_presentation(data, convert_to_pdf=True)

print(f"PPTX: {result['pptx']}")
print(f"PDF: {result['pdf']}")
```

## ✅ You're Ready!

You've successfully created your first presentation with PraisonAI PPT. 

**Next Steps:**
- [Complete Command Reference]({{ '/commands' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})
- [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})

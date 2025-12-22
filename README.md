# PraisonAI PPT - PowerPoint Bible Verses Generator

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://pypi.org/project/praisonaippt/)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python package for creating beautiful PowerPoint presentations from Bible verses stored in JSON format. Each verse gets its own slide with proper formatting and styling.

## ✨ Features

- 📦 **Proper Python Package** - Installable via pip with entry points
- 📖 **Dynamic verse loading** from JSON or YAML files
- 🎨 **Professional slide formatting** with proper placeholders
- 🎨 **Text highlighting** - Highlight specific words or phrases in verses (bold + orange)
- 🔤 **Custom font sizes** - Set custom font sizes for specific words (large_text feature)
- 📑 **Multi-part verse support** for long verses
- 🔧 **Command-line interface** with flexible options
- 🐍 **Python API** for programmatic use
- 📁 **Built-in examples** included with the package
- 📝 **Template file** for quick start
- ✨ **Auto-generated filenames** or custom output names
- 🎯 **Error handling** and user-friendly feedback
- 📄 **YAML support** - User-friendly YAML format alongside JSON
- 📄 **PDF Conversion** - Convert presentations to PDF with multiple backends
- 🔄 **Multiple PDF Backends** - Support for Aspose.Slides (commercial) and LibreOffice (free)
- ⚙️ **Advanced PDF Options** - Quality settings, password protection, and more

## 📋 Requirements

- Python 3.7 or higher
- python-pptx library (automatically installed)
- PyYAML library (automatically installed)

### Optional for PDF Conversion

Choose one of the following:

- **Aspose.Slides (Recommended)**: Commercial library with high-quality conversion
  ```bash
  pip install praisonaippt[pdf-aspose]
  ```
- **LibreOffice (Free)**: Requires LibreOffice installation on your system
  - Download from [libreoffice.org](https://www.libreoffice.org/)
  - Works on Windows, macOS, and Linux

## 🚀 Installation

### Method 1: Install from PyPI (Recommended)

```bash
# Using pip
pip install praisonaippt

# Or using uv (faster)
uv pip install praisonaippt
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT

# Install with pip
pip install .

# Or with uv (faster)
uv pip install .
```

### Method 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT

# Install in editable mode
pip install -e .
# Or with uv
uv pip install -e .
```

## 📁 Package Structure

```
ppt-package/
├── praisonaippt/          # Main package
│   ├── __init__.py            # Package initialization
│   ├── core.py                # Presentation creation logic
│   ├── utils.py               # Utility functions
│   ├── loader.py              # JSON loading & validation
│   └── cli.py                 # Command-line interface
├── examples/                   # Example JSON files
│   ├── verses.json            # Default example
│   ├── tamil_verses.json      # Tamil verses example
│   ├── sample_verses.json     # Simple example
│   ├── only_one_reason_sickness.json
│   └── template.json          # Empty template
├── docs/                       # Documentation
├── tests/                      # Test suite (optional)
├── setup.py                    # Package setup
├── pyproject.toml             # Modern Python config
├── requirements.txt           # Dependencies
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## 📖 File Format (JSON or YAML)

### YAML Format (Recommended! 📄)

YAML is more user-friendly and easier to edit:

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
          special_word: 200  # Custom font size
```

### JSON Format

Traditional JSON format is also supported:

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

### Text Highlighting Feature 🎨

Highlight specific words or phrases in your verses:
- Add a `highlights` array to any verse (optional)
- Highlighted text appears in **bold orange** color
- Case-insensitive matching
- Supports both single words and phrases

### Large Text Feature 🔤 (New in v1.1.0!)

Set custom font sizes for specific words:
- Add a `large_text` dictionary mapping words to font sizes
- Text appears at the specified font size in **black** color
- Perfect for emphasizing Hebrew/Greek words or key terms
- Example: `large_text: {"לֶחֶם": 200}` (YAML) or `"large_text": {"לֶחֶם": 200}` (JSON)

**Example:**
```json
{
  "reference": "John 3:16 (NIV)",
  "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
  "highlights": ["loved", "eternal life"]
}
```

**See full documentation:** [docs/HIGHLIGHTS_FEATURE.md](docs/HIGHLIGHTS_FEATURE.md)

### Quick Start Template

Use the included template to get started:

```bash
# For YAML (recommended)
cp examples/template.yaml my_verses.yaml  # or create from scratch
nano my_verses.yaml  # Edit with your verses
praisonaippt -i my_verses.yaml  # Generate presentation

# For JSON
cp examples/template.json my_verses.json
nano my_verses.json
praisonaippt -i my_verses.json
```

## 💻 Usage

### Command-Line Interface

#### Basic Usage

Use default `verses.json` in current directory:
```bash
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
praisonaippt -i verses.json -o my_presentation.pptx
```

#### Use Custom Title

```bash
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

#### Show Version

```bash
praisonaippt --version
```

#### Show Help

```bash
praisonaippt --help
```

### PDF Conversion

#### Convert Existing PPTX to PDF

```bash
# Convert existing presentation to PDF
praisonaippt convert-pdf presentation.pptx

# Specify output filename
praisonaippt convert-pdf presentation.pptx --pdf-output output.pdf

# Choose backend
praisonaippt convert-pdf presentation.pptx --pdf-backend libreoffice
```

#### Generate PPTX and Convert to PDF in One Step

```bash
# Create presentation and convert to PDF
praisonaippt -i verses.json --convert-pdf

# Custom PDF output filename
praisonaippt -i verses.json --convert-pdf --pdf-output custom.pdf

# Advanced PDF options
praisonaippt -i verses.json --convert-pdf --pdf-options '{"quality":"high","include_hidden_slides":true}'
```

#### PDF Options

Available PDF conversion options:

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

#### PDF Backend Comparison

| Backend | Quality | Cost | Dependencies | Best For |
|---------|---------|------|--------------|----------|
| **Aspose.Slides** | Excellent | Commercial | Python package | Professional quality |
| **LibreOffice** | Good | Free | LibreOffice install | Free option |

### Python API

You can also use the package programmatically in your Python code:

```python
from praisonaippt import create_presentation, load_verses_from_file

# Load verses from file
data = load_verses_from_file("verses.json")

# Create presentation
if data:
    output_file = create_presentation(
        data,
        output_file="my_presentation.pptx",
        custom_title="My Custom Title"  # Optional
    )
    print(f"Created: {output_file}")
```

#### PDF Conversion with Python API

**PDF conversion is fully integrated into the SDK** - all functions accessible from main package import:

```python
# All PDF functions available from main package
from praisonaippt import (
    create_presentation,
    load_verses_from_file,
    convert_pptx_to_pdf,  # Integrated PDF conversion
    PDFOptions            # Integrated PDF options
)

# Method 1: Create presentation and convert to PDF in one step
data = load_verses_from_file("verses.json")
if data:
    result = create_presentation(
        data,
        output_file="my_presentation.pptx",
        convert_to_pdf=True  # PDF conversion integrated into core function
    )
    if isinstance(result, dict):
        print(f"PPTX: {result['pptx']}")
        print(f"PDF: {result['pdf']}")

# Method 2: Convert existing PPTX to PDF (standalone function)
pdf_file = convert_pptx_to_pdf("presentation.pptx", "output.pdf")

# Method 3: Advanced PDF options (integrated configuration)
pdf_options = PDFOptions(
    quality='high',
    include_hidden_slides=True,
    compression=True
)
pdf_file = convert_pptx_to_pdf(
    "presentation.pptx", 
    "output.pdf", 
    options=pdf_options,
    backend='aspose'
)
```

**Note**: No need to import from submodules - all PDF functionality is part of the main SDK.

#### Using Built-in Examples

```python
from praisonaippt import create_presentation
from praisonaippt.loader import get_example_path, load_verses_from_file

# Get path to example
example_path = get_example_path("tamil_verses")

# Load and create
data = load_verses_from_file(example_path)
create_presentation(data, output_file="tamil_presentation.pptx")
```

#### List Available Examples

```python
from praisonaippt.loader import list_examples

examples = list_examples()
for example in examples:
    print(f"- {example}")
```

### Advanced Usage

**Combine multiple options:**
```bash
praisonaippt -i verses.json -o output.pptx -t "Amazing Grace"
```

**Use example with custom output:**
```bash
praisonaippt --use-example tamil_verses -o tamil_output.pptx
```

## 📊 Output

The package creates a PowerPoint presentation with:
- **Title Slide**: Shows the presentation title and subtitle
- **Section Slides**: One for each section in your JSON (skipped if using custom title)
- **Verse Slides**: One slide per verse (or multiple if the verse is long)

### Slide Formatting:
- **Verse Text**: 24pt, centered, black
- **Reference**: 18pt, centered, gray, italic
- **Section Titles**: 36pt, blue (#003366)
- **Layout**: Professional blank layout with custom text boxes

## 🛡️ Error Handling
- ✅ Validates JSON file existence and format
- ✅ Provides helpful error messages
- ✅ Auto-generates output filename if not specified
- ✅ Handles long verses by splitting them across multiple slides
- ✅ Sanitizes filenames for cross-platform compatibility

## 📚 Examples

### Example 1: Quick Start
```bash
# Install the package with uv
uv pip install -e .

# Use built-in example
praisonaippt --use-example verses
```

### Example 2: Create from Template
```bash
# Copy template
cp examples/template.json my_verses.json

# Edit the file with your verses
# Then generate
praisonaippt -i my_verses.json
```

### Example 3: Custom Title
```bash
praisonaippt -i verses.json -t "God's Promises"
```

### Example 4: Python Script
```python
from praisonaippt import create_presentation, load_verses_from_file

# Load your verses
data = load_verses_from_file("my_verses.json")

# Create presentation
if data:
    create_presentation(data, output_file="output.pptx")
```

### Example 5: With Text Highlighting
```bash
# Use the highlights example
praisonaippt --use-example highlights_example

# Or create your own with highlights in the JSON
praisonaippt -i my_highlighted_verses.json
```

## 🔧 Development

### Running Tests

```bash
# Install development dependencies
uv pip install -e .[dev]

# Run tests (when implemented)
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues:

1. **"Command not found: praisonaippt"**
   - Make sure you installed the package: `uv pip install -e .` or `pip install -e .`
   - Check that your Python scripts directory is in PATH

2. **"File not found" error**
   - Verify the JSON file exists
   - Use absolute path if needed: `praisonaippt -i /full/path/to/verses.json`

3. **"Invalid JSON" error**
   - Validate your JSON syntax using a JSON validator
   - Ensure all quotes are properly closed
   - Check that commas are in the right places

4. **Empty presentation**
   - Verify your JSON has a "sections" array
   - Check that verses array is not empty

5. **Import errors**
   - Reinstall the package: `uv pip install -e .`
   - Check that python-pptx is installed: `uv pip install python-pptx`

---

## 🔧 SDK Integration Verification

### ✅ PDF Conversion Feature - Fully Integrated into praisonaippt SDK

The PDF conversion functionality is **fully integrated** into the praisonaippt SDK, not as separate files or external functionality.

#### Integration Architecture

**Package Structure:**
```
praisonaippt/
├── __init__.py           # Main package exports (includes PDF functions)
├── core.py               # Core presentation creation (with PDF support)
├── loader.py             # Verse loading utilities
├── utils.py              # Helper utilities
├── cli.py                # Command-line interface (with PDF commands)
└── pdf_converter.py      # PDF conversion module (integrated)
```

**SDK Exports (`__init__.py`):**
The PDF conversion functionality is **directly exported** from the main package:

```python
from praisonaippt import (
    create_presentation,      # Core function with PDF support
    convert_pptx_to_pdf,      # Standalone PDF conversion
    PDFOptions,               # PDF configuration options
    load_verses_from_file,    # Verse loading
    load_verses_from_dict     # Verse loading
)
```

**All functions are accessible from the main package import** - no need to import from submodules.

#### Verification Tests

**✅ Test 1: Main Package Import**
```python
import praisonaippt

# All PDF functions available at package level
assert 'convert_pptx_to_pdf' in praisonaippt.__all__
assert 'PDFOptions' in praisonaippt.__all__
```

**✅ Test 2: Integrated PDF Conversion**
```python
from praisonaippt import create_presentation

# PDF conversion integrated into core function
result = create_presentation(data, convert_to_pdf=True)

# Returns both PPTX and PDF paths
assert isinstance(result, dict)
assert 'pptx' in result
assert 'pdf' in result
```

**✅ Test 3: Standalone PDF Conversion**
```python
from praisonaippt import convert_pptx_to_pdf

# Direct PDF conversion accessible from main package
pdf_file = convert_pptx_to_pdf('presentation.pptx')
```

**✅ Test 4: PDF Options Configuration**
```python
from praisonaippt import PDFOptions

# PDF options accessible from main package
options = PDFOptions(quality='high', compression=True)
```

#### SDK Usage Examples

**Example 1: Simple Integrated Usage**
```python
import praisonaippt

# Load verses
data = praisonaippt.load_verses_from_file('verses.json')

# Create presentation with PDF in one step
result = praisonaippt.create_presentation(
    data,
    convert_to_pdf=True  # PDF conversion integrated
)

print(f"Created: {result['pptx']} and {result['pdf']}")
```

**Example 2: Advanced Integrated Usage**
```python
from praisonaippt import create_presentation, PDFOptions

# Configure PDF options
pdf_opts = PDFOptions(
    quality='high',
    compression=True,
    include_hidden_slides=False
)

# Create with custom PDF settings
result = create_presentation(
    data,
    output_file='presentation.pptx',
    convert_to_pdf=True,
    pdf_options=pdf_opts,
    pdf_backend='auto'
)
```

#### Integration Benefits

**✅ Seamless User Experience**
- **Single import**: All functionality from `praisonaippt` package
- **No submodule imports**: Users don't need to know internal structure
- **Consistent API**: PDF conversion follows same patterns as core functions

**✅ Backward Compatibility**
- **Existing code works**: `create_presentation()` still works without PDF
- **Optional feature**: PDF conversion is opt-in via `convert_to_pdf=True`
- **Graceful degradation**: Works without PDF backends installed

#### Backend Detection

The SDK automatically detects available PDF backends:

```python
from praisonaippt import convert_pptx_to_pdf

# Automatically uses best available backend
pdf_file = convert_pptx_to_pdf('presentation.pptx')

# Backend selection priority:
# 1. Aspose.Slides (if installed)
# 2. LibreOffice (if installed)
# 3. Error with helpful message
```

---

## 📋 Complete Command Reference

### Basic Commands

#### Create Presentation
```bash
# Use default verses.json
praisonaippt

# Specify input file
praisonaippt -i my_verses.json

# Specify output file
praisonaippt -i verses.json -o output.pptx

# Use custom title
praisonaippt -i verses.json -t "My Custom Title"

# Use built-in example
praisonaippt --use-example tamil_verses

# List available examples
praisonaippt --list-examples
```

### PDF Conversion Commands

#### Convert Existing PPTX to PDF
```bash
# Basic conversion
praisonaippt convert-pdf presentation.pptx

# Specify output filename
praisonaippt convert-pdf presentation.pptx --pdf-output output.pdf

# Choose backend
praisonaippt convert-pdf presentation.pptx --pdf-backend libreoffice

# Advanced options
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"quality":"high","compression":true}'
```

#### Create PPTX and Convert to PDF in One Step
```bash
# Basic integrated conversion
praisonaippt -i verses.json --convert-pdf

# Custom PDF output filename
praisonaippt -i verses.json --convert-pdf --pdf-output custom.pdf

# Advanced PDF options
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","include_hidden_slides":true}'

# Choose backend and options
praisonaippt -i verses.json --convert-pdf \
  --pdf-backend aspose \
  --pdf-options '{"quality":"high","compression":false}'
```

### PDF Options Reference

#### Available Options
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

#### PDF Backend Comparison
| Backend | Quality | Cost | Dependencies | Best For |
|---------|---------|------|--------------|----------|
| **Aspose.Slides** | Excellent | Commercial | Python package | Professional quality |
| **LibreOffice** | Good | Free | LibreOffice install | Free option |

### Advanced Command Examples

#### Batch Processing
```bash
# Create multiple presentations with PDF
for file in *.json; do
  praisonaippt -i "$file" --convert-pdf
done
```

#### Custom Quality Settings
```bash
# High quality PDF (no compression)
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# Low quality PDF (smaller file size)
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"low","compression":true}'
```

#### Password Protected PDF
```bash
# Create password-protected PDF
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"password_protect":true,"password":"secret123"}'
```

#### Slide Range Export
```bash
# Export specific slides to PDF
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[1,5]}'
```

### Help and Version Commands
```bash
# Show help
praisonaippt --help
praisonaippt convert-pdf --help

# Show version
praisonaippt --version
```

---

## 💡 Tips

- Keep verse text concise for better readability
- Use consistent reference formatting (e.g., "Book Chapter:Verse (Version)")
- Organize verses into logical sections
- Test with a small JSON file first
- Use the template file as a starting point
- Check available examples with `--list-examples`
- Long verses are automatically split across multiple slides
- For PDF conversion, ensure Aspose.Slides or LibreOffice is installed
- Use `--pdf-backend auto` for automatic backend detection
- High quality PDFs create larger files but better visual quality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [python-pptx](https://python-pptx.readthedocs.io/)
- Inspired by the need for easy Bible verse presentation creation

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the examples in the `examples/` directory
3. Open an issue on GitHub

## 🚀 Quick Reference

```bash
# Installation with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

# Basic usage
praisonaippt

# With custom file
praisonaippt -i my_verses.json

# Use example
praisonaippt --use-example tamil_verses

# List examples
praisonaippt --list-examples

# Help
praisonaippt --help
```

---

**Made with ❤️ for creating beautiful Bible verse presentations**

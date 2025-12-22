# PraisonAI PPT - PowerPoint Bible Verses Generator

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://pypi.org/project/praisonaippt/)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python package for creating beautiful PowerPoint presentations from Bible verses stored in JSON or YAML format. Each verse gets its own slide with proper formatting and styling.

## Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#️-configuration)
  - [Quick Setup](#quick-setup)
  - [Configuration Options](#configuration-options)
  - [Configuration Examples](#configuration-examples)
- [Usage Guide](#-usage-guide)
  - [File Format](#file-format-json-or-yaml)
  - [CLI Usage](#cli-usage)
  - [Python API](#python-api)
- [Advanced Features](#-advanced-features)
  - [PDF Conversion](#pdf-conversion)
  - [Google Drive Upload](#google-drive-upload)
  - [Text Highlighting](#text-highlighting)
  - [Lazy Loading](#lazy-loading)
- [Complete Reference](#-complete-reference)
  - [CLI Options](#complete-cli-options)
  - [PDF Options](#pdf-options-reference)
  - [Python API Reference](#python-api-reference)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Support](#-support)

---

## ✨ Features

### Core Features
- 📦 **Proper Python Package** - Installable via pip with entry points
- 📖 **Dynamic verse loading** from JSON or YAML files
- 🎨 **Professional slide formatting** with proper placeholders
- 📑 **Multi-part verse support** for long verses
- 🔧 **Command-line interface** with flexible options
- 🐍 **Python API** for programmatic use
- 📁 **Built-in examples** included with the package
- 📝 **Template file** for quick start
- ✨ **Auto-generated filenames** or custom output names
- 🎯 **Error handling** and user-friendly feedback

### Advanced Features
- 🎨 **Text highlighting** - Highlight specific words or phrases (bold + orange)
- 🔤 **Custom font sizes** - Set custom font sizes for specific words
- 📄 **YAML support** - User-friendly YAML format alongside JSON
- 📄 **PDF Conversion** - Convert presentations to PDF with multiple backends
- 🔄 **Multiple PDF Backends** - Support for Aspose.Slides (commercial) and LibreOffice (free)
- ⚙️ **Advanced PDF Options** - Quality settings, password protection, and more
- ☁️ **Google Drive Upload** - Upload presentations directly to Google Drive
- 🔌 **Lazy Loading** - Optional dependencies loaded only when needed

---

## 🚀 Quick Start

### 1. Install the Package

```bash
pip install praisonaippt
```

### 2. Create Your First Presentation

```bash
# Use a built-in example
praisonaippt --use-example verses

# Or create from your own JSON file
praisonaippt -i my_verses.json
```

### 3. Explore More Options

```bash
# List available examples
praisonaippt --list-examples

# Create with custom title
praisonaippt -i verses.json -t "Sunday Service"

# Convert to PDF
praisonaippt -i verses.json --convert-pdf

# Upload to Google Drive (requires setup)
praisonaippt -i verses.json --upload-gdrive --gdrive-credentials creds.json
```

---

## 📦 Installation

### Requirements

- Python 3.7 or higher
- python-pptx library (automatically installed)
- PyYAML library (automatically installed)

### Installation Methods

#### Method 1: Install from PyPI (Recommended)

```bash
# Basic installation
pip install praisonaippt

# Or using uv (faster)
uv pip install praisonaippt
```

#### Method 2: Install from Source

```bash
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT
pip install .
```

#### Method 3: Development Installation

```bash
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT
pip install -e .
```

### Optional Dependencies

Install additional features as needed:

```bash
# For PDF conversion (Aspose - commercial, high quality)
pip install praisonaippt[pdf-aspose]

# For PDF conversion (all backends)
pip install praisonaippt[pdf-all]

# For Google Drive upload
pip install praisonaippt[gdrive]

# Install everything
pip install praisonaippt[all]
```

**Note**: For LibreOffice PDF conversion (free), download LibreOffice from [libreoffice.org](https://www.libreoffice.org/)

---

## ⚙️ Configuration

PraisonAI PPT supports persistent configuration stored in `~/.praisonaippt/config.yaml`. This eliminates the need to specify credentials and settings every time you run commands.

### Quick Setup

Initialize your configuration interactively:

```bash
praisonaippt --config-init
```

Or use the config command:

```bash
praisonaippt config init
```

### Configuration File Location

- **Path**: `~/.praisonaippt/config.yaml`
- **Format**: YAML (user-friendly, easy to edit)
- **Auto-created**: On first `--config-init` run

### Configuration Structure

```yaml
gdrive:
  credentials_path: ~/gdrive-credentials.json
  folder_id: null
  folder_name: Bible Presentations
  use_date_folders: false
  date_format: YYYY/MM

pdf:
  backend: auto
  quality: high
  compression: true

defaults:
  output_format: pptx
  auto_convert_pdf: false
  auto_upload_gdrive: false
```

### Configuration Options

#### Google Drive Settings (`gdrive`)

| Option | Description | Example |
|--------|-------------|---------|
| `credentials_path` | Path to service account JSON | `"~/gdrive-credentials.json"` |
| `folder_id` | Google Drive folder ID | `"1a2b3c4d5e6f7g8h9i0j"` |
| `folder_name` | Folder name (auto-creates if missing) | `"Bible Presentations"` |
| `use_date_folders` | Create date-based subfolders | `true` or `false` |
| `date_format` | Date folder format pattern | `"YYYY/MM"`, `"YYYY-MM"`, `"YYYY/MM/DD"` |

#### PDF Settings (`pdf`)

| Option | Description | Values |
|--------|-------------|--------|
| `backend` | PDF conversion backend | `"aspose"`, `"libreoffice"`, `"auto"` |
| `quality` | PDF quality | `"low"`, `"medium"`, `"high"` |
| `compression` | Enable image compression | `true`, `false` |

#### Default Behaviors (`defaults`)

| Option | Description | Values |
|--------|-------------|--------|
| `auto_convert_pdf` | Auto-convert to PDF | `true`, `false` |
| `auto_upload_gdrive` | Auto-upload to Google Drive | `true`, `false` |

### Using Configuration

Once configured, commands become simpler:

#### Without Configuration
```bash
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials ~/gdrive-credentials.json \
  --gdrive-folder-name "Bible Presentations"
```

#### With Configuration
```bash
# Just this! Config handles the rest
praisonaippt -i verses.json --upload-gdrive
```

### Configuration Priority

Settings are applied in this order (later overrides earlier):

1. **Default values** (built-in)
2. **Configuration file** (`~/.praisonaippt/config.yaml`)
3. **Command-line arguments** (highest priority)

**Example:**
```bash
# Config has: "folder_name": "Bible Presentations"
# This command overrides it:
praisonaippt -i verses.json --upload-gdrive --gdrive-folder-name "Sunday Service"
```

### Configuration Commands

```bash
# Initialize configuration (interactive)
praisonaippt --config-init
praisonaippt config init

# Show current configuration
praisonaippt --config-show
praisonaippt config show

# Edit configuration manually (YAML is easy to edit!)
nano ~/.praisonaippt/config.yaml
vim ~/.praisonaippt/config.yaml
code ~/.praisonaippt/config.yaml
```

### Manual Configuration

Create `~/.praisonaippt/config.yaml` manually:

```bash
mkdir -p ~/.praisonaippt
cat > ~/.praisonaippt/config.yaml << 'EOF'
gdrive:
  credentials_path: ~/gdrive-credentials.json
  folder_name: Bible Presentations

pdf:
  backend: auto
  quality: high

defaults:
  auto_convert_pdf: false
  auto_upload_gdrive: false
EOF
```

**YAML Benefits:**
- ✅ No quotes needed for most values
- ✅ No commas or brackets
- ✅ Clean, readable format
- ✅ Easy to comment with `#`
- ✅ Indentation-based (like Python)

### Python API with Configuration

```python
from praisonaippt import create_presentation, load_config
from praisonaippt.gdrive_uploader import upload_to_gdrive

# Load configuration
config = load_config()

# Create presentation
data = load_verses_from_file("verses.json")
output = create_presentation(data)

# Upload using config credentials
if config.get_gdrive_credentials():
    result = upload_to_gdrive(
        output,
        credentials_path=config.get_gdrive_credentials(),
        folder_name=config.get_gdrive_folder_name()
    )
    print(f"Uploaded: {result['webViewLink']}")
```

### Configuration Examples

#### Example 1: Google Drive Only
```yaml
gdrive:
  credentials_path: ~/secrets/gdrive-creds.json
  folder_name: Church Presentations
```

#### Example 2: Auto-Convert to PDF
```yaml
pdf:
  backend: libreoffice
  quality: high
  compression: false

defaults:
  auto_convert_pdf: true
```

#### Example 3: Complete Automation
```yaml
gdrive:
  credentials_path: ~/gdrive-credentials.json
  folder_name: Bible Study

pdf:
  backend: auto
  quality: high

defaults:
  auto_convert_pdf: true
  auto_upload_gdrive: true
```

#### Example 4: With Date-Based Folders
```yaml
gdrive:
  credentials_path: ~/.praisonaippt/gdrive-credentials.json
  folder_name: Bible Presentations
  use_date_folders: true    # Creates subfolders like 2024/12
  date_format: YYYY/MM      # Format: YYYY/MM, YYYY-MM, YYYY/MM/DD, etc.

defaults:
  auto_upload_gdrive: true
```

**Result**: Files uploaded to `Bible Presentations/2024/12/presentation.pptx`

#### Example 5: With Comments (YAML supports comments!)
```yaml
# Google Drive Settings
gdrive:
  credentials_path: ~/gdrive-credentials.json  # Path to service account JSON
  folder_name: Bible Presentations             # Auto-creates if doesn't exist
  use_date_folders: false                      # Set to true for date organization
  date_format: YYYY/MM                         # Date folder pattern (YYYY/MM, YYYY/MM/DD, etc.)

# PDF Settings
pdf:
  backend: auto      # Options: aspose, libreoffice, auto
  quality: high      # Options: low, medium, high
  compression: true  # Reduce file size

# Automation
defaults:
  auto_convert_pdf: false     # Set to true for automatic PDF conversion
  auto_upload_gdrive: false   # Set to true for automatic upload
```

With this config, just run:
```bash
praisonaippt -i verses.json
# Automatically creates PPTX, converts to PDF, and uploads to Google Drive!
```

### Benefits of Configuration

✅ **No Repetition** - Set credentials once, use everywhere  
✅ **Faster Commands** - Less typing, fewer arguments  
✅ **Consistent Settings** - Same quality/backend every time  
✅ **Secure** - Credentials stored in home directory (not in commands)  
✅ **Flexible** - Override config with CLI args when needed  

---

## 🚀 Quick Command Reference

```bash
# Setup
praisonaippt config init              # Initialize configuration
praisonaippt setup-oauth              # Setup OAuth (personal Drive)
praisonaippt setup-credentials        # Setup service account
praisonaippt secure-credentials       # Secure credential files

# Create Presentations
praisonaippt -i verses.json           # Create from JSON/YAML
praisonaippt --use-example verses     # Use built-in example
praisonaippt --list-examples          # List available examples

# With Features
praisonaippt -i verses.json --convert-pdf              # Create + PDF
praisonaippt -i verses.json --upload-gdrive            # Create + Upload
praisonaippt -i verses.json --convert-pdf --upload-gdrive  # All features

# Configuration
praisonaippt config show              # Show current config
praisonaippt --config-show            # Alternative syntax

# Convert Existing
praisonaippt convert-pdf input.pptx   # Convert PPTX to PDF
```

---

## 📖 Usage Guide

### File Format (JSON or YAML)

#### YAML Format (Recommended! 📄)

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

#### JSON Format

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

#### Quick Start Template

```bash
# For YAML (recommended)
cp examples/template.yaml my_verses.yaml
nano my_verses.yaml
praisonaippt -i my_verses.yaml

# For JSON
cp examples/template.json my_verses.json
nano my_verses.json
praisonaippt -i my_verses.json
```

### CLI Usage

#### Setup Commands

```bash
# Initialize configuration (interactive)
praisonaippt config init

# Show current configuration
praisonaippt config show

# Setup OAuth for personal Google Drive
praisonaippt setup-oauth

# Setup service account credentials
praisonaippt setup-credentials

# Secure credential files (move to ~/.praisonaippt and set permissions)
praisonaippt secure-credentials
```

#### Basic Commands

```bash
# Use default verses.json
praisonaippt

# Specify input file
praisonaippt -i my_verses.json
praisonaippt -i my_verses.yaml

# Specify output file
praisonaippt -i verses.json -o my_presentation.pptx

# Use custom title
praisonaippt -i verses.json -t "My Custom Title"

# Use built-in examples
praisonaippt --use-example tamil_verses

# List available examples
praisonaippt --list-examples
```

#### With PDF Conversion

```bash
# Create and convert to PDF in one step
praisonaippt -i verses.json --convert-pdf

# Convert existing PPTX to PDF
praisonaippt convert-pdf presentation.pptx

# With specific backend
praisonaippt -i verses.json --convert-pdf --pdf-backend aspose

# With custom options
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":true}'
```

#### With Google Drive Upload

```bash
# Upload to Google Drive
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-name "Presentations"

# Upload with date-based folders (e.g., Presentations/2024/12/)
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-name "Presentations" \
  --gdrive-date-folders

# Complete workflow: Create + PDF + Upload with date folders
praisonaippt -i verses.json \
  --convert-pdf \
  --upload-gdrive \
  --gdrive-credentials credentials.json \
  --gdrive-folder-name "Bible Study" \
  --gdrive-date-folders
```

### Python API

#### Basic Usage

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

#### With PDF Conversion

```python
from praisonaippt import (
    create_presentation,
    load_verses_from_file,
    convert_pptx_to_pdf,
    PDFOptions
)

# Method 1: Create and convert in one step
data = load_verses_from_file("verses.json")
result = create_presentation(
    data,
    output_file="my_presentation.pptx",
    convert_to_pdf=True
)
if isinstance(result, dict):
    print(f"PPTX: {result['pptx']}")
    print(f"PDF: {result['pdf']}")

# Method 2: Convert existing PPTX
pdf_file = convert_pptx_to_pdf("presentation.pptx", "output.pdf")

# Method 3: With advanced options
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

#### With Google Drive Upload

```python
from praisonaippt import create_presentation
from praisonaippt.gdrive_uploader import upload_to_gdrive, is_gdrive_available

# Create presentation
output = create_presentation(data)

# Basic upload
if is_gdrive_available():
    result = upload_to_gdrive(
        output,
        credentials_path='credentials.json',
        folder_name='Presentations'
    )
    print(f"Uploaded: {result['webViewLink']}")

# Upload with date-based folders (e.g., Presentations/2024/12/)
if is_gdrive_available():
    result = upload_to_gdrive(
        output,
        credentials_path='credentials.json',
        folder_name='Presentations',
        use_date_folders=True,
        date_format='YYYY/MM'  # Default format
    )
    print(f"Uploaded to date folder: {result['webViewLink']}")
```

#### Using Built-in Examples

```python
from praisonaippt import create_presentation
from praisonaippt.loader import get_example_path, load_verses_from_file, list_examples

# List available examples
examples = list_examples()
for example in examples:
    print(f"- {example}")

# Use an example
example_path = get_example_path("tamil_verses")
data = load_verses_from_file(example_path)
create_presentation(data, output_file="tamil_presentation.pptx")
```

---

## 🎯 Advanced Features

### PDF Conversion

Convert your presentations to PDF with multiple backend options.

#### Backends

| Backend | Quality | Cost | Dependencies | Best For |
|---------|---------|------|--------------|----------|
| **Aspose.Slides** | Excellent | Commercial | Python package | Professional quality |
| **LibreOffice** | Good | Free | LibreOffice install | Free option |
| **Auto** | Varies | Varies | Auto-detected | Convenience |

#### Quality Settings

- **"low"**: Smaller file size, basic quality
- **"medium"**: Balanced file size and quality
- **"high"**: Best quality, larger file size

#### Advanced Examples

```bash
# High quality PDF (no compression)
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"quality":"high","compression":false}'

# Password-protected PDF
praisonaippt -i verses.json --convert-pdf \
  --pdf-options '{"password_protect":true,"password":"secret123"}'

# Export specific slides
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"slide_range":[1,5]}'

# PDF/A compliance (archival)
praisonaippt convert-pdf presentation.pptx \
  --pdf-options '{"compliance":"PDF/A"}'
```

### Google Drive Upload

Upload presentations directly to Google Drive with service account authentication.

#### Features

- **Lazy Loading**: Dependencies only loaded when needed
- **Service Account Authentication**: Secure authentication
- **Folder Management**: Upload to specific folders or create new ones
- **Seamless Integration**: Works with PDF conversion

#### Quick Setup

1. **Install dependencies:**
   ```bash
   pip install praisonaippt[gdrive]
   ```

2. **Set up Google Drive credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a service account
   - Download credentials JSON
   - See [`docs/google-drive-upload.md`](docs/google-drive-upload.md) for detailed setup

3. **Upload:**
   ```bash
   praisonaippt -i verses.json \
     --upload-gdrive \
     --gdrive-credentials credentials.json \
     --gdrive-folder-name "Presentations"
   ```

**Full Documentation**: [`docs/google-drive-upload.md`](docs/google-drive-upload.md) | [`QUICKSTART_GDRIVE.md`](QUICKSTART_GDRIVE.md)

### Text Highlighting

Highlight specific words or phrases in your verses.

#### Features

- Add a `highlights` array to any verse (optional)
- Highlighted text appears in **bold orange** color
- Case-insensitive matching
- Supports both single words and phrases

#### Example

```json
{
  "reference": "John 3:16 (NIV)",
  "text": "For God so loved the world that he gave his one and only Son...",
  "highlights": ["loved", "eternal life"]
}
```

#### Large Text Feature

Set custom font sizes for specific words:

```yaml
large_text:
  special_word: 200  # Custom font size in points
```

Perfect for emphasizing Hebrew/Greek words or key terms.

**Full Documentation**: [`docs/HIGHLIGHTS_FEATURE.md`](docs/HIGHLIGHTS_FEATURE.md)

### Lazy Loading

Optional dependencies are loaded only when needed, providing:

- **Smaller Installation**: Core package has minimal dependencies
- **Faster Startup**: Only load what you use
- **No Import Errors**: Package works without optional features
- **Clear Feedback**: Helpful messages when features unavailable

#### Example

```python
from praisonaippt.lazy_loader import check_optional_dependency

if check_optional_dependency('google.oauth2.service_account'):
    # Google Drive upload available
    from praisonaippt.gdrive_uploader import upload_to_gdrive
    upload_to_gdrive('file.pptx', credentials_path='creds.json')
else:
    print("Install with: pip install praisonaippt[gdrive]")
```

**Full Documentation**: [`docs/lazy-loading.md`](docs/lazy-loading.md)

---

## 📚 Complete Reference

### Complete CLI Options

#### Global Options

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

#### PDF Conversion Options

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

#### Google Drive Upload Options

```bash
Google Drive Options:
  --upload-gdrive       Upload the generated PowerPoint to Google Drive
  --gdrive-credentials PATH
                        Path to Google Drive service account credentials JSON file
  --gdrive-folder-id ID
                        Google Drive folder ID to upload to (optional)
  --gdrive-folder-name NAME
                        Google Drive folder name to search/create (optional)
  --gdrive-date-folders
                        Create date-based subfolders (e.g., 2024/12) within target folder
```

#### Configuration Options

```bash
Configuration:
  --config-init         Initialize configuration file interactively
  --config-show         Show current configuration
```

#### Setup Commands

```bash
Setup Commands:
  praisonaippt config init              Initialize configuration
  praisonaippt config show              Show current configuration
  praisonaippt setup-oauth              Setup OAuth for personal Google Drive
  praisonaippt setup-credentials        Setup service account credentials
  praisonaippt secure-credentials       Secure credential files with proper permissions
```

#### Convert-PDF Command Options

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

### Python API Reference

#### Core Functions

```python
from praisonaippt import (
    create_presentation,      # Create PowerPoint presentation
    load_verses_from_file,    # Load verses from JSON/YAML file
    load_verses_from_dict,    # Load verses from dictionary
    convert_pptx_to_pdf,      # Convert PPTX to PDF
    PDFOptions,               # PDF configuration options
    lazy_import,              # Lazy import utility
    check_optional_dependency # Check if optional dependency is available
)
```

#### create_presentation()

```python
create_presentation(
    data,                    # Verses data dictionary
    output_file=None,        # Output filename (auto-generated if None)
    custom_title=None,       # Custom presentation title
    convert_to_pdf=False,    # Convert to PDF
    pdf_options=None,        # PDFOptions instance
    pdf_backend='auto'       # PDF backend ('aspose', 'libreoffice', 'auto')
)
```

#### convert_pptx_to_pdf()

```python
convert_pptx_to_pdf(
    pptx_file,              # Input PPTX file path
    pdf_file=None,          # Output PDF file path (auto-generated if None)
    backend='auto',         # Backend to use
    options=None            # PDFOptions instance
)
```

#### PDFOptions

```python
PDFOptions(
    quality='high',                    # Quality setting
    include_hidden_slides=False,       # Include hidden slides
    password_protect=False,            # Password protect
    password=None,                     # Password
    compression=True,                  # Compress images
    notes_pages=False,                 # Include notes
    slide_range=None,                  # Slide range [start, end]
    compliance=None                    # Compliance standard
)
```

---

## 💡 Examples

### Example 1: Quick Start

```bash
# Install and use built-in example
pip install praisonaippt
praisonaippt --use-example verses
```

### Example 2: Create from Template

```bash
# Copy template and customize
cp examples/template.json my_verses.json
nano my_verses.json
praisonaippt -i my_verses.json
```

### Example 3: Custom Title

```bash
praisonaippt -i verses.json -t "God's Promises"
```

### Example 4: Python Script

```python
from praisonaippt import create_presentation, load_verses_from_file

# Load and create
data = load_verses_from_file("my_verses.json")
if data:
    create_presentation(data, output_file="output.pptx")
```

### Example 5: With Text Highlighting

```bash
# Use the highlights example
praisonaippt --use-example highlights_example

# Or create your own
praisonaippt -i my_highlighted_verses.json
```

### Example 6: Batch Processing

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

### Example 7: Complete Workflow

```bash
# Create PPTX, convert to PDF, upload to Google Drive
praisonaippt -i verses.json \
  -t "Sunday Service - John 3:16" \
  --convert-pdf \
  --pdf-options '{"quality":"high"}' \
  --upload-gdrive \
  --gdrive-credentials ~/secrets/gdrive-credentials.json \
  --gdrive-folder-name "Bible Study"
```

---

## 📊 Output

The package creates a PowerPoint presentation with:

- **Title Slide**: Shows the presentation title and subtitle
- **Section Slides**: One for each section in your JSON (skipped if using custom title)
- **Verse Slides**: One slide per verse (or multiple if the verse is long)

### Slide Formatting

- **Verse Text**: 32pt, centered, black
- **Reference**: 22pt, centered, gray, italic
- **Section Titles**: 44pt, blue (#003366)
- **Layout**: Professional blank layout with custom text boxes

### Error Handling

- ✅ Validates JSON file existence and format
- ✅ Provides helpful error messages
- ✅ Auto-generates output filename if not specified
- ✅ Handles long verses by splitting them across multiple slides
- ✅ Sanitizes filenames for cross-platform compatibility

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Command not found: praisonaippt"

**Solution:**
- Make sure you installed the package: `pip install praisonaippt`
- Check that your Python scripts directory is in PATH

#### 2. "File not found" error

**Solution:**
- Verify the JSON file exists
- Use absolute path if needed: `praisonaippt -i /full/path/to/verses.json`

#### 3. "Invalid JSON" error

**Solution:**
- Validate your JSON syntax using a JSON validator
- Ensure all quotes are properly closed
- Check that commas are in the right places

#### 4. Empty presentation

**Solution:**
- Verify your JSON has a "sections" array
- Check that verses array is not empty

#### 5. Import errors

**Solution:**
- Reinstall the package: `pip install --force-reinstall praisonaippt`
- Check that python-pptx is installed: `pip install python-pptx`

#### 6. PDF conversion fails

**Solution:**
- For Aspose: `pip install praisonaippt[pdf-aspose]`
- For LibreOffice: Install LibreOffice from [libreoffice.org](https://www.libreoffice.org/)
- Check backend with: `praisonaippt convert-pdf --help`

#### 7. Google Drive upload not available

**Solution:**
- Install dependencies: `pip install praisonaippt[gdrive]`
- Set up service account credentials (see [`docs/google-drive-upload.md`](docs/google-drive-upload.md))

---

## 🔧 Development

### Project Structure

```
praisonaippt/
├── praisonaippt/                 # Main package
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # Command-line interface
│   ├── core.py                  # Core presentation creation logic
│   ├── loader.py                # JSON/YAML loading utilities
│   ├── pdf_converter.py         # PDF conversion functionality
│   ├── gdrive_uploader.py       # Google Drive upload
│   ├── lazy_loader.py           # Lazy loading utilities
│   └── utils.py                 # Helper functions
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_pdf_conversion.py
│   └── test_lazy_loading.py
├── examples/                    # Example files
├── docs/                        # Documentation
├── setup.py                     # Package setup
├── pyproject.toml              # Modern Python config
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run specific test file
pytest tests/test_lazy_loading.py -v
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

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
- For Google Drive upload, set up service account credentials first
- Use lazy loading to keep your installation lightweight

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [python-pptx](https://python-pptx.readthedocs.io/)
- Inspired by the need for easy Bible verse presentation creation
- Google Drive integration powered by Google Drive API
- PDF conversion powered by Aspose.Slides and LibreOffice

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the [documentation](docs/)
3. Check existing [GitHub Issues](https://github.com/MervinPraison/PraisonAIPPT/issues)
4. Open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)

---

## 🚀 Quick Reference Card

```bash
# Installation
pip install praisonaippt                    # Basic
pip install praisonaippt[gdrive]           # With Google Drive
pip install praisonaippt[all]              # Everything

# Basic Usage
praisonaippt                               # Use default verses.json
praisonaippt -i my_verses.json             # Custom input
praisonaippt -t "My Title"                 # Custom title
praisonaippt --use-example verses          # Use example

# PDF Conversion
praisonaippt -i verses.json --convert-pdf  # Create + convert
praisonaippt convert-pdf file.pptx         # Convert existing

# Google Drive Upload
praisonaippt -i verses.json \
  --upload-gdrive \
  --gdrive-credentials creds.json \
  --gdrive-folder-name "Folder"

# Help
praisonaippt --help                        # Show help
praisonaippt --version                     # Show version
praisonaippt --list-examples               # List examples
```

---

**Made with ❤️ for creating beautiful Bible verse presentations**

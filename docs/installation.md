---
layout: default
title: "Installation - PraisonAI PPT"
description: "Complete installation guide for PraisonAI PPT with PDF conversion support"
---

# Installation Guide

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

## 🚀 Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
# Using pip
pip install praisonaippt

# Or using uv (faster)
uv pip install praisonaippt
```

### Method 2: Install with PDF Support

```bash
# With Aspose.Slides (commercial, high quality)
pip install praisonaippt[pdf-aspose]

# With all PDF features
pip install praisonaippt[pdf-all]
```

### Optional: video export and avatar calibration

MP4 export uses **FFmpeg**, **LibreOffice**, and **poppler** on the system PATH (see [Video export](video-export.md)).

```bash
# TTS narration (edge-tts)
pip install praisonaippt[video-tts]

# Auto PiP face centre (MediaPipe + OpenCV; mediapipe requires Python >= 3.8)
pip install praisonaippt[avatar-calibrate]

# YOLO face detector (AGPL-3.0; hard angles only; Python >= 3.8)
pip install praisonaippt[avatar-calibrate-yolo]
```

See [Recent features](recent-features.md) and [Avatar PiP calibration](avatar-calibration.md) for CLI and validation diagram usage.

macOS example:

```bash
brew install ffmpeg poppler
brew install --cask libreoffice
```

### Method 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT

# Install in editable mode
pip install -e .

# Or with uv
uv install -e .
```

### Method 4: Install from Source

```bash
# Clone the repository
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT

# Install with pip
pip install .

# Or with uv
uv install .
```

## 🔧 Verification

After installation, verify everything is working:

```bash
# Check version
praisonaippt --version

# Test basic functionality
praisonaippt --help

# Test PDF conversion (if installed)
praisonaippt convert-pdf --help
```

### Python API Verification

```python
# Test import
import praisonaippt
print(f"PraisonAI PPT version: {praisonaippt.__version__}")

# Test PDF conversion availability
try:
    from praisonaippt import convert_pptx_to_pdf, PDFOptions
    print("✅ PDF conversion available")
except ImportError:
    print("❌ PDF conversion not available")
```

## 📦 Package Contents

When you install praisonaippt, you get:

- **CLI Tool**: `praisonaippt` command-line interface
- **Python API**: Full programmatic access
- **PDF Conversion**: Optional PDF export capabilities
- **Examples**: Built-in example files
- **Documentation**: Complete usage guides

## 🌍 Platform Support

### Supported Operating Systems
- ✅ **Windows** - Full support including PDF conversion
- ✅ **macOS** - Full support including PDF conversion
- ✅ **Linux** - Full support including PDF conversion

### Python Versions
- ✅ **Python 3.7** - Supported
- ✅ **Python 3.8** - Supported
- ✅ **Python 3.9** - Supported
- ✅ **Python 3.10** - Supported
- ✅ **Python 3.11** - Supported
- ✅ **Python 3.12** - Supported

## 🔍 Troubleshooting Installation

### Common Issues

#### 1. Permission Denied
```bash
# Use user installation
pip install --user praisonaippt

# Or use sudo (not recommended)
sudo pip install praisonaippt
```

#### 2. Python Not Found
```bash
# On macOS with Homebrew
brew install python3

# On Ubuntu/Debian
sudo apt-get install python3 python3-pip

# On Windows
# Download from python.org
```

#### 3. PDF Conversion Not Working
```bash
# Install LibreOffice (free option)
# Ubuntu/Debian:
sudo apt-get install libreoffice

# macOS:
brew install --cask libreoffice

# Windows:
# Download from libreoffice.org

# Or install Aspose.Slides (commercial)
pip install praisonaippt[pdf-aspose]
```

#### 4. Virtual Environment Issues
```bash
# Create new virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in clean environment
pip install praisonaippt[pdf-all]
```

## 📚 Dependencies

### Core Dependencies
- `python-pptx>=0.6.21` - PowerPoint file creation
- `PyYAML>=6.0` - YAML file support

### Optional PDF Dependencies
- `aspose.slides>=24.0.0` - Commercial PDF conversion
- `psutil>=5.9.0` - System utilities (for LibreOffice)
- `tqdm>=4.64.0` - Progress bars

### Optional video and QA dependencies

| Extra | Purpose |
|-------|---------|
| `praisonaippt[avatar-calibrate]` | Hybrid face detect for PiP `crop_x` — [Avatar PiP calibration](avatar-calibration.md) |
| System: `ffmpeg`, LibreOffice | MP4 export — [Video export](video-export.md) |
| System: `poppler` (`pdftoppm`) | Slide JPEG export from PPTX |

No extra pip package is required for [Slide QA](slide-qa.md) gates (`validate-deck`, golden JPEGs, MP4 seek frames).

```bash
brew install ffmpeg poppler
brew install --cask libreoffice
pip install praisonaippt[avatar-calibrate]
```

### Development Dependencies
- `pytest` - Testing framework
- `black` - Code formatting
- `flake8` - Linting

## 🎯 Next Steps

After successful installation:

1. [Quick Start Tutorial]({{ '/quickstart' | relative_url }})
2. [Complete Command Reference]({{ '/commands' | relative_url }})
3. [Python API Documentation]({{ '/python-api' | relative_url }})
4. [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})

## 💡 Pro Tips

- **Use virtual environments** to avoid conflicts
- **Install with `[pdf-all]`** for full functionality
- **Use `uv`** for faster installation (if available)
- **Check version** after installation to verify success
- **Test PDF conversion** before using in production

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

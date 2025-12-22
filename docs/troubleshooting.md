---
layout: default
title: "Troubleshooting - PraisonAI PPT"
description: "Common issues and solutions for PraisonAI PPT"
---

# Troubleshooting Guide

## 🔧 Common Issues and Solutions

### Installation Issues

#### Issue: "praisonaippt command not found"
```bash
# Solution 1: Reinstall
pip uninstall praisonaippt
pip install praisonaippt

# Solution 2: Check Python path
which python
which pip
echo $PATH

# Solution 3: Use user installation
pip install --user praisonaippt
```

#### Issue: "Permission denied"
```bash
# Solution: Use user installation
pip install --user praisonaippt

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install praisonaippt
```

#### Issue: "Python not found"
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# Windows
# Download from python.org
```

### File Issues

#### Issue: "verses.json not found"
```bash
# Create sample verses.json
cat > verses.json << EOF
{
  "presentation_title": "Sample Presentation",
  "sections": [
    {
      "section": "Sample Section",
      "verses": [
        {
          "reference": "John 3:16 (KJV)",
          "text": "For God so loved the world..."
        }
      ]
    }
  ]
}
EOF
```

#### Issue: "Invalid JSON format"
```bash
# Validate JSON
python -m json.tool verses.json

# Or use online validator
# https://jsonlint.com/
```

#### Issue: "Empty presentation created"
```json
// Check your JSON structure:
{
  "presentation_title": "Title",  // Required
  "sections": [                   // Required
    {
      "section": "Section Name",  // Required
      "verses": [                 // Required
        {
          "reference": "Book 1:1", // Required
          "text": "Verse text"     // Required
        }
      ]
    }
  ]
}
```

### PDF Conversion Issues

#### Issue: "No PDF backends available"
```bash
# Check available backends
python -c "from praisonaippt.pdf_converter import PDFConverter; print(PDFConverter().get_available_backends())"

# Install Aspose.Slides
pip install praisonaippt[pdf-aspose]

# Or install LibreOffice
# Ubuntu/Debian:
sudo apt-get install libreoffice

# macOS:
brew install --cask libreoffice

# Windows:
# Download from libreoffice.org
```

#### Issue: "LibreOffice not found"
```bash
# Check if LibreOffice is installed
libreoffice --version

# Add to PATH (macOS)
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"

# Add to PATH (Linux)
export PATH="/usr/bin/libreoffice:$PATH"
```

#### Issue: "Aspose.Slides license error"
```bash
# Update Aspose.Slides
pip install --upgrade aspose.slides

# Check version
python -c "import aspose.slides; print(aspose.slides.__version__)"
```

#### Issue: "PDF conversion failed"
```python
# Test with simple presentation
from praisonaippt import create_presentation

test_data = {
    "presentation_title": "Test",
    "sections": [{
        "section": "Test",
        "verses": [{"reference": "Test 1:1", "text": "Test"}]
    }]
}

result = create_presentation(test_data, convert_to_pdf=True)
print(f"Test result: {result}")
```

### Performance Issues

#### Issue: "Slow PDF conversion"
```python
# Use lower quality for faster conversion
from praisonaippt import PDFOptions

options = PDFOptions(quality='low', compression=True)
result = create_presentation(data, convert_to_pdf=True, pdf_options=options)
```

#### Issue: "Large file size"
```python
# Enable compression
options = PDFOptions(quality='medium', compression=True)

# Or reduce quality
options = PDFOptions(quality='low', compression=True)
```

### Python API Issues

#### Issue: "Import error"
```python
# Check installation
import praisonaippt
print(praisonaippt.__version__)

# Reinstall if needed
pip uninstall praisonaippt
pip install praisonaippt
```

#### Issue: "create_presentation returns None"
```python
# Check your data structure
from praisonaippt import load_verses_from_dict

try:
    data = load_verses_from_dict(your_data)
    result = create_presentation(data)
except Exception as e:
    print(f"Error: {e}")
```

## 🔍 Debugging Commands

### Check Installation
```bash
# Version check
praisonaippt --version

# Help check
praisonaippt --help

# PDF conversion check
praisonaippt convert-pdf --help
```

### Test Basic Functionality
```bash
# Use built-in example
praisonaippt --use-example sample_verses

# Test PDF conversion
praisonaippt --use-example sample_verses --convert-pdf
```

### Check Dependencies
```bash
# Check Python packages
pip list | grep praisonaippt
pip list | grep python-pptx
pip list | grep PyYAML

# Check optional PDF packages
pip list | grep aspose.slides
```

### Environment Check
```bash
# Python version
python --version
python3 --version

# Path check
which python
which praisonaippt
echo $PATH
```

## 🛠️ Advanced Troubleshooting

### Clean Reinstallation
```bash
# Complete cleanup
pip uninstall praisonaippt
pip uninstall python-pptx
pip uninstall PyYAML
pip uninstall aspose.slides

# Fresh installation
pip install praisonaippt[pdf-all]
```

### Virtual Environment Setup
```bash
# Create new environment
python3 -m venv praisonaippt_env
source praisonaippt_env/bin/activate  # Windows: praisonaippt_env\Scripts\activate

# Install in clean environment
pip install praisonaippt[pdf-all]

# Test
praisonaippt --version
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

from praisonaippt import create_presentation

# This will show detailed error messages
result = create_presentation(data, convert_to_pdf=True)
```

### Manual Backend Testing
```python
from praisonaippt.pdf_converter import PDFConverter

# Test each backend
converter = PDFConverter()

print("Testing backends:")
print(f"Aspose.Slides: {converter._check_aspose_available()}")
print(f"LibreOffice: {converter._check_libreoffice_available()}")
print(f"Available: {converter.get_available_backends()}")
```

## 📞 Getting Help

### Check Logs
```bash
# Enable verbose output
praisonaippt --help 2>&1 | tee debug.log

# Check system logs
# macOS: Console.app
# Linux: /var/log/syslog
# Windows: Event Viewer
```

### Report Issues
When reporting issues, include:
1. **Operating System** and version
2. **Python version** (`python --version`)
3. **PraisonAI PPT version** (`praisonaippt --version`)
4. **Error message** (full traceback)
5. **Steps to reproduce**
6. **Sample data** that causes the issue

### Sample Bug Report
```bash
# System info
python --version
praisonaippt --version
uname -a  # Linux/macOS
# or systeminfo on Windows

# Test case
echo '{"presentation_title":"Test","sections":[{"section":"Test","verses":[{"reference":"Test 1:1","text":"Test"}]}]}' > test.json
praisonaippt -i test.json --convert-pdf
```

## 📚 Additional Resources

- [GitHub Issues](https://github.com/MervinPraison/PraisonAIPPT/issues)
- [Installation Guide]({{ '/installation' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})
- [Python API Documentation]({{ '/python-api' | relative_url }})

---

**Still need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

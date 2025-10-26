# Quick Start Guide

Get started with PraisonAI PPT - PowerPoint Bible Verses Generator in 3 easy steps!

## 🚀 Installation (One Command)

```bash
# Install from PyPI (recommended)
pip install praisonaippt

# Or with uv (faster)
uv pip install praisonaippt
```

**For development:**

```bash
# Clone and install in editable mode
git clone https://github.com/MervinPraison/PraisonAIPPT.git
cd PraisonAIPPT
pip install -e .
```

## 📝 Create Your First Presentation

### Option 1: Use a Built-in Example (Fastest)

```bash
# List available examples
praisonaippt --list-examples

# Use an example
praisonaippt --use-example verses
```

### Option 2: Start from Template

```bash
# Copy the template
cp examples/template.json my_verses.json

# Edit with your favorite editor
nano my_verses.json  # or code, vim, etc.

# Generate presentation
praisonaippt -i my_verses.json
```

### Option 3: Use Existing JSON File

```bash
praisonaippt -i path/to/your/verses.json
```

## 🎨 Customization Options

### Custom Title
```bash
praisonaippt -i verses.json -t "My Custom Title"
```

### Custom Output Filename
```bash
praisonaippt -i verses.json -o my_presentation.pptx
```

### Combine Options
```bash
praisonaippt -i verses.json -t "God's Promises" -o promises.pptx
```

## 📖 JSON Format (Simple Example)

```json
{
  "presentation_title": "My Verses",
  "presentation_subtitle": "Selected Scriptures",
  "sections": [
    {
      "section": "Hope",
      "verses": [
        {
          "reference": "Jeremiah 29:11 (NIV)",
          "text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future."
        }
      ]
    }
  ]
}
```

## 🐍 Python API (Advanced)

```python
from praisonaippt import create_presentation, load_verses_from_file

# Load and create
data = load_verses_from_file("verses.json")
if data:
    create_presentation(data, output_file="output.pptx")
```

## 💡 Pro Tips

1. **Start Small**: Test with 2-3 verses first
2. **Use Template**: Copy `examples/template.json` as starting point
3. **Check Examples**: Look at `examples/` for inspiration
4. **Long Verses**: Automatically split across multiple slides
5. **Custom Titles**: Skip section slides with `-t` option

## 🆘 Need Help?

```bash
# Show all options
praisonaippt --help

# Check version
praisonaippt --version

# List examples
praisonaippt --list-examples
```

## 📚 More Information

- Full documentation: See [README.md](README.md)
- Examples directory: `examples/`
- Troubleshooting: Check README.md troubleshooting section

---

**That's it! You're ready to create beautiful Bible verse presentations! 🎉**

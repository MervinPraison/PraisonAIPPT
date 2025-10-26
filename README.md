# PraisonAI PPT - PowerPoint Bible Verses Generator

[![PyPI version](https://badge.fury.io/py/praisonaippt.svg)](https://pypi.org/project/praisonaippt/)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python package for creating beautiful PowerPoint presentations from Bible verses stored in JSON format. Each verse gets its own slide with proper formatting and styling.

## ✨ Features

- 📦 **Proper Python Package** - Installable via pip with entry points
- 📖 **Dynamic verse loading** from JSON files
- 🎨 **Professional slide formatting** with proper placeholders
- 🎨 **Text highlighting** - Highlight specific words or phrases in verses
- 📑 **Multi-part verse support** for long verses
- 🔧 **Command-line interface** with flexible options
- 🐍 **Python API** for programmatic use
- 📁 **Built-in examples** included with the package
- 📝 **Template file** for quick start
- ✨ **Auto-generated filenames** or custom output names
- 🎯 **Error handling** and user-friendly feedback

## 📋 Requirements

- Python 3.7 or higher
- python-pptx library (automatically installed)

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

## 📖 JSON File Format

Create your verses in JSON format following this structure:

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
          "highlights": ["word1", "phrase to highlight"]
        }
      ]
    }
  ]
}
```

### Highlighting Feature (New! 🎨)

You can now highlight specific words or phrases in your verses:
- Add a `"highlights"` array to any verse (optional)
- Highlighted text appears in **bold orange** color
- Case-insensitive matching
- Supports both single words and phrases

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
# Copy the template from examples
cp examples/template.json my_verses.json

# Edit with your verses
nano my_verses.json  # or use your favorite editor

# Generate presentation
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
praisonaippt -i my_verses.json
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

## 💡 Tips

- Keep verse text concise for better readability
- Use consistent reference formatting (e.g., "Book Chapter:Verse (Version)")
- Organize verses into logical sections
- Test with a small JSON file first
- Use the template file as a starting point
- Check available examples with `--list-examples`
- Long verses are automatically split across multiple slides

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

# Bible Verses PowerPoint Generator

A Python script that creates beautiful PowerPoint presentations from Bible verses stored in JSON format. Each verse gets its own slide with proper formatting and styling.

## Features

- 📖 **Dynamic verse loading** from JSON files
- 🎨 **Professional slide formatting** with proper placeholders
- 📑 **Multi-part verse support** for long verses
- 🔧 **Command-line interface** with flexible options
- 📁 **Multiple presentation support** from different JSON files
- ✨ **Auto-generated filenames** or custom output names
- 🎯 **Error handling** and user-friendly feedback

## Requirements

- Python 3.6+
- python-pptx library
- Conda environment (recommended)

## Installation

1. **Set up Conda environment:**
   ```bash
   conda create -n cursor python=3.11
   conda activate cursor
   ```

2. **Install required package:**
   ```bash
   pip install python-pptx
   ```

## File Structure

```
ppt-package/
├── app.py                             # Main script
├── verses.json                         # Default verses file
├── sample_verses.json                  # Example alternative verses
├── README.md                          # This file
└── *.pptx                            # Generated presentations
```

## JSON File Format

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
          "text": "The actual verse text here."
        }
      ]
    }
  ]
}
```

### Example verses.json:
```json
{
  "presentation_title": "Bible Verses Collection",
  "presentation_subtitle": "Selected Scriptures",
  "sections": [
    {
      "section": "Bible Verses",
      "verses": [
        {
          "reference": "Genesis 12:2 (KJV)",
          "text": "And I will make of thee a great nation, and I will bless thee, and make thy name great; and thou shalt be a blessing."
        },
        {
          "reference": "2 Corinthians 5:17 (KJV)",
          "text": "Therefore if any man be in Christ, he is a new creature: old things are passed away; behold, all things are become new."
        }
      ]
    }
  ]
}
```

## Usage

### Basic Usage

Run with default settings (uses `verses.json`):
```bash
python app.py
```

### Advanced Usage

**Specify input file:**
```bash
python app.py --input my_verses.json
```

**Specify both input and output:**
```bash
python app.py --input christmas_verses.json --output christmas_presentation.pptx
```

**Using short flags:**
```bash
python app.py -i easter_verses.json -o easter_presentation.pptx
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--verses` | `-v` | Input JSON file containing verses | `verses.json` |
| `--title` | `-t` | Custom title for the presentation | Uses JSON title |
| `--output` | `-o` | Output PowerPoint file name | Auto-generated from title or input filename |
| `--help` | `-h` | Show help message and examples | - |

### Auto-Generated Filenames

If you don't specify an output filename, the script automatically generates one:
- **With custom title**: `"Why Delay?"` → `Why_Delay.pptx`
- **Without custom title**: `my_verses.json` → `my_verses_presentation.pptx`

## Examples

### Example 1: Multiple Verse Collections
```bash
# Create Christmas presentation
python app.py -v christmas_verses.json -t "Christmas Joy" -o christmas_2024.pptx

# Create Easter presentation  
python app.py -v easter_verses.json -t "Resurrection Hope" -o easter_2024.pptx

# Create daily devotion presentation
python app.py -v daily_devotions.json -t "Daily Bread"
```

### Example 2: Organizing by Theme
Create separate JSON files for different themes:
- `hope_verses.json` - Verses about hope
- `faith_verses.json` - Verses about faith
- `love_verses.json` - Verses about love
- `comfort_verses.json` - Comforting verses

## Presentation Structure

The generated PowerPoint includes:

1. **Title Slide** - Uses presentation_title and presentation_subtitle from JSON
2. **Section Slides** - One for each section in your JSON
3. **Verse Slides** - Individual slides for each verse with:
   - Verse reference as the title
   - Verse text in quotes
   - Professional formatting and colors
   - Automatic text splitting for long verses

## Features Detail

### Long Verse Handling
Verses longer than 200 characters are automatically split into multiple slides:
- Original: `Romans 4:13-14 (KJV)`
- Split into: `Romans 4:13-14 (KJV) (Part 1/2)` and `Romans 4:13-14 (KJV) (Part 2/2)`

### Styling
- **Title color**: Navy blue (RGB: 0, 51, 102)
- **Text color**: Dark grey (RGB: 51, 51, 51)
- **Title font**: 28pt, bold, centered
- **Verse font**: 40pt, centered
- **Layout**: Professional Title and Content layout

### Error Handling
- ✅ Checks if input file exists
- ✅ Validates JSON format
- ✅ Provides helpful error messages
- ✅ Graceful failure with exit codes

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'pptx'"**
```bash
# Activate conda environment and install
conda activate cursor
pip install python-pptx
```

**"Error: Input file 'filename.json' not found"**
- Check the file path and name
- Make sure you're in the correct directory
- Use absolute path if needed

**"Error: Invalid JSON format"**
- Validate your JSON syntax
- Check for missing commas, brackets, or quotes
- Use a JSON validator online

### Running with Conda
Always activate your conda environment first:
```bash
zsh -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate cursor && python app.py -v verses.json -t 'My Title'"
```

## Tips

1. **Organize by theme** - Create separate JSON files for different occasions or themes
2. **Test with sample** - Use the included `sample_verses.json` to test functionality
3. **Backup your verses** - Keep your JSON files in version control
4. **Custom styling** - Modify the script's color and font settings as needed
5. **Batch processing** - Create a shell script to generate multiple presentations at once

## Contributing

Feel free to enhance this script by:
- Adding more slide layouts
- Implementing custom themes
- Adding image support
- Creating batch processing features
- Improving text formatting options

## License

This project is open source and available under the MIT License.

---

**Created with ❤️ for Bible study and presentation needs**

# Text Highlighting Feature

## Overview

The PraisonAI PPT - PowerPoint Bible Verses Generator now supports **highlighting specific words or phrases** within verses. Highlighted text appears in **bold orange color** to make key concepts stand out in your presentations.

---

## How to Use Highlights

### JSON Format

Add a `"highlights"` array to any verse in your JSON file:

```json
{
  "reference": "John 3:16 (NIV)",
  "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
  "highlights": ["loved", "eternal life"]
}
```

### Highlights Array

The `"highlights"` field is **optional** and accepts an array of strings:
- Each string can be a **single word** or a **phrase**
- Matching is **case-insensitive** (e.g., "loved" matches "loved" or "Loved")
- Multiple occurrences of the same word/phrase will all be highlighted
- Overlapping highlights are automatically handled

---

## Examples

### Example 1: Single Word Highlights

```json
{
  "reference": "Philippians 4:13 (NIV)",
  "text": "I can do all things through Christ who strengthens me.",
  "highlights": ["Christ", "strengthens"]
}
```

**Result**: "Christ" and "strengthens" appear in bold orange.

### Example 2: Phrase Highlights

```json
{
  "reference": "Jeremiah 29:11 (NIV)",
  "text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.",
  "highlights": ["hope and a future", "plans"]
}
```

**Result**: The phrase "hope and a future" and all occurrences of "plans" are highlighted.

### Example 3: Multiple Highlights

```json
{
  "reference": "Romans 8:28 (NIV)",
  "text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.",
  "highlights": ["all things", "good", "purpose"]
}
```

**Result**: Three different words/phrases are highlighted.

### Example 4: No Highlights (Optional)

```json
{
  "reference": "Psalm 23:1 (KJV)",
  "text": "The Lord is my shepherd; I shall not want."
}
```

**Result**: Normal text without any highlighting (highlights field is optional).

---

## Highlight Formatting

### Visual Appearance:
- **Font Weight**: Bold
- **Color**: Orange (RGB: 255, 140, 0)
- **Font Size**: Same as regular text (24pt)
- **Case**: Preserves original case from the verse

### Non-Highlighted Text:
- **Font Weight**: Regular
- **Color**: Black (RGB: 0, 0, 0)
- **Font Size**: 24pt

---

## Complete Example JSON

```json
{
  "presentation_title": "Faith and Hope",
  "presentation_subtitle": "Key Verses",
  "sections": [
    {
      "section": "Hope",
      "verses": [
        {
          "reference": "Jeremiah 29:11 (NIV)",
          "text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.",
          "highlights": ["plans", "hope and a future"]
        },
        {
          "reference": "Romans 15:13 (NIV)",
          "text": "May the God of hope fill you with all joy and peace as you trust in him, so that you may overflow with hope by the power of the Holy Spirit.",
          "highlights": ["hope", "joy and peace"]
        }
      ]
    },
    {
      "section": "Faith",
      "verses": [
        {
          "reference": "Hebrews 11:1 (NIV)",
          "text": "Now faith is confidence in what we hope for and assurance about what we do not see.",
          "highlights": ["faith", "confidence", "assurance"]
        }
      ]
    }
  ]
}
```

---

## Usage with CLI

```bash
# Create presentation with highlights
praisonaippt -i my_verses_with_highlights.json

# Use the built-in highlights example
praisonaippt --use-example highlights_example

# Combine with other options
praisonaippt -i verses.json -t "Key Concepts" -o highlighted.pptx
```

---

## Usage with Python API

```python
from praisonaippt import create_presentation, load_verses_from_file

# Load JSON file with highlights
data = load_verses_from_file("verses_with_highlights.json")

# Create presentation (highlights are automatically applied)
create_presentation(data, output_file="highlighted_presentation.pptx")
```

---

## Tips and Best Practices

### ✅ Do:
- Highlight **key theological terms** (e.g., "grace", "faith", "love")
- Highlight **important phrases** (e.g., "eternal life", "born again")
- Use highlights **sparingly** (2-4 per verse maximum)
- Highlight **consistent themes** across multiple verses

### ❌ Don't:
- Highlight too many words (reduces impact)
- Highlight entire sentences (defeats the purpose)
- Use highlights for every verse (makes them less special)
- Highlight common words like "the", "and", "is"

---

## Technical Details

### Case-Insensitive Matching
The highlighting system uses case-insensitive matching:
- `"love"` will match "love", "Love", "LOVE"
- Original case from the verse is preserved in the output

### Overlapping Highlights
If highlights overlap, the first occurrence takes precedence:
- Highlights: `["all things", "things"]`
- Text: "all things work together"
- Result: Only "all things" is highlighted (not "things" separately)

### Special Characters
Special regex characters in highlights are automatically escaped:
- You can highlight phrases with punctuation: `"God's love"`
- Parentheses, brackets, etc. are handled correctly

### Long Verses
Highlights work seamlessly with split verses:
- If a verse is split across multiple slides, highlights apply to each part
- The same highlight rules apply to all parts

---

## Example Files

Check these example files in the `examples/` directory:

1. **`highlights_example.json`** - Demonstrates various highlighting techniques
2. **`template.json`** - Shows the highlights field in the template
3. **`only_one_reason_sickness.json`** - Can be updated to include highlights

---

## Customization (Advanced)

If you want to customize the highlight color or style, edit `praisonaippt/core.py`:

```python
# In the _apply_highlights function, find this line:
run.font.color.rgb = RGBColor(255, 140, 0)  # Orange

# Change to your preferred color:
run.font.color.rgb = RGBColor(255, 0, 0)    # Red
run.font.color.rgb = RGBColor(0, 128, 0)    # Green
run.font.color.rgb = RGBColor(0, 0, 255)    # Blue
```

---

## Troubleshooting

### Highlights Not Appearing
- ✅ Check JSON syntax (highlights must be an array)
- ✅ Verify the text matches exactly (case-insensitive)
- ✅ Ensure the word/phrase exists in the verse text

### Wrong Text Highlighted
- ✅ Check for typos in the highlights array
- ✅ Remember matching is case-insensitive
- ✅ Use exact phrases (including spaces)

### Too Many Highlights
- ✅ Reduce the number of highlights per verse
- ✅ Focus on the most important concepts
- ✅ Consider splitting into multiple slides

---

## Version History

- **v1.0.0** - Initial release with highlighting support

---

**Happy highlighting! 🎨✨**

---
layout: default
title: "PPTX to JSON - PraisonAI PPT"
description: "Extract slide content from a PPTX file back into the praisonaippt JSON schema"
---

# PPTX → JSON Extraction

## 📄 Overview

`pptx_to_json` is the **inverse of `create_presentation()`**. It reads an existing `.pptx` file
and extracts its content as a dict that conforms to the praisonaippt JSON schema — the same
format used to create presentations.

This enables round-trip workflows:

```
JSON  ──create_presentation()──►  PPTX  ──pptx_to_json()──►  JSON
```

No new dependencies are required beyond `python-pptx`, which is already a core dependency.

---

## 🚀 Quick Start

### Python API

```python
from praisonaippt import pptx_to_json

# Returns a dict
data = pptx_to_json("presentation.pptx")

# Save to file (pretty-printed)
pptx_to_json("presentation.pptx", output_path="output.json")

# Compact JSON (no indentation)
pptx_to_json("presentation.pptx", output_path="output.json", pretty=False)
```

### CLI

```bash
# Saves to presentation.json (auto-named)
praisonaippt convert-json presentation.pptx

# Specify output file
praisonaippt convert-json presentation.pptx --json-output output.json

# Compact JSON
praisonaippt convert-json presentation.pptx --json-output out.json --no-pretty
```

---

## 💻 CLI Reference

### Command

```
praisonaippt convert-json <input_file> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `input_file` | Path to `.pptx` or `.ppt` file to extract (**required**) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--json-output PATH` | `<input>.json` | Output JSON file path |
| `--output-format FORMAT` | `"json"` | Output format (`"json"` or `"yaml"`) |
| `--pretty` | `True` | Write indented, human-readable JSON |
| `--no-pretty` | — | Write compact single-line JSON |

### Examples

```bash
# Basic extraction (auto output path)
praisonaippt convert-json my_presentation.pptx
# → writes my_presentation.json

# Named output
praisonaippt convert-json my_presentation.pptx --json-output extracted.json

# Compact JSON for embedding in scripts
praisonaippt convert-json my_presentation.pptx --json-output data.json --no-pretty
```

### Error Handling

```bash
# File not found
praisonaippt convert-json missing.pptx
# Error: Input file not found: missing.pptx

# Wrong file type
praisonaippt convert-json slides.pdf
# Error: Input file must be a PowerPoint file (.pptx or .ppt)
```

---

## 🐍 Python API Reference

### `pptx_to_json()`

```python
def pptx_to_json(
    pptx_path: str,
    output_path: Optional[str] = None,
    pretty: bool = True,
    images_dir: Optional[str] = None,
    output_format: str = 'json',
) -> dict:
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pptx_path` | `str` | *(required)* | Path to `.pptx` or `.ppt` file |
| `output_path` | `str` or `None` | `None` | If set, writes output to this path |
| `pretty` | `bool` | `True` | Indent output JSON (set `False` for compact) |
| `images_dir` | `str` or `None` | `None` | Optional directory to save extracted images |
| `output_format` | `str` | `"json"` | Output format (`"json"` or `"yaml"`) |

#### Returns

`dict` — conforms to the praisonaippt JSON schema (same structure as input files for `create_presentation`).

#### Raises

| Exception | When |
|-----------|------|
| `ValueError` | Input file has a non-PPTX extension |
| `FileNotFoundError` | Input file does not exist |

#### Examples

```python
from praisonaippt import pptx_to_json

# --- In-memory ---
data = pptx_to_json("presentation.pptx")
print(data["presentation_title"])
print(len(data["sections"]))

# --- Save to file ---
pptx_to_json("presentation.pptx", output_path="output.json")

# --- Compact JSON ---
pptx_to_json("presentation.pptx", output_path="data.json", pretty=False)

# --- Error handling ---
try:
    data = pptx_to_json("missing.pptx")
except FileNotFoundError as e:
    print(f"File missing: {e}")
except ValueError as e:
    print(f"Wrong type: {e}")
```

### `PPTXToJSONConverter` Class

For advanced use cases, use the converter class directly:

```python
from praisonaippt.pptx_to_json import PPTXToJSONConverter

converter = PPTXToJSONConverter("presentation.pptx")
data = converter.convert()
```

---

## 📋 Output JSON Schema

The output dict mirrors the praisonaippt input schema exactly, plus two metadata fields:

```yaml
_source: extracted
_extraction_warnings:
- 'background_image: file path not recoverable from PPTX binary'
presentation_title: Great Faith
presentation_subtitle: Mark 10:30 (NKJV)
slide_size: widescreen
slide_style:
  text_color: white
  reference_position: top
  alignment: left
  font_name: Palatino
  highlight_color: '#FF8C00'
  annotation_color: '#1E50C8'
sections:
- section: 1. Centurion
  verses:
  - reference: Matthew 8:5-10 (NKJV)
    text: 10 When Jesus heard it, He marveled...
    highlights:
    - I have not found such great faith
- section: To Be Victorious
  verses: []
- section: 1. They Didn't Wait for God
  verses:
  - reference: ''
    text: 'Woman with the Issue of Blood

      Centurion

      Canaanite'
    list_type: bullet
- section: 1. Tithe
  verses:
  - reference: ''
    text: 'מַעֲשֵׂר (maʿăśēr) – tithe


      עָשַׁר (ʿāšar) – to be rich'
    highlights:
    - מַעֲשֵׂר
    - עָשַׁר
    large_text:
      מַעֲשֵׂר: 80
      עָשַׁר: 80
```

### Metadata Fields

| Field | Value | Description |
|-------|-------|-------------|
| `_source` | `"extracted"` | Always present; marks this was extracted (not hand-authored) |
| `_extraction_warnings` | list of strings | Populated when features could not be fully recovered |

> **Note**: The `_source` and `_extraction_warnings` keys are ignored by `create_presentation()` — strip them or leave them in for a round-trip; both work.

---

## ✅ Feature Extraction Table

All features from the praisonaippt JSON schema are handled:

| Feature | Extraction | Notes |
|---------|-----------|-------|
| `presentation_title` | ✅ Lossless | Largest font run on slide 0 |
| `presentation_subtitle` | ✅ Lossless | Second text block on slide 0 (may be a Bible ref) |
| `slide_size` | ✅ Lossless | Mapped from slide dimensions |
| `slide_style.background_color` | ✅ Lossless | Extracted from solid fill |
| `slide_style.background_image` | ⚠️ Lossy | Image detected but **path not recoverable**; noted in `_extraction_warnings` |
| `slide_style.text_color` | ✅ Best-effort | Most common run color |
| `slide_style.reference_position` | ✅ Lossless | Inferred from textbox vertical position |
| `slide_style.alignment` | ✅ Best-effort | Most frequent paragraph alignment |
| `slide_style.font_name` | ✅ Lossless | Most common `run.font.name` |
| `slide_style.highlight_color` | ✅ Best-effort | Most common non-body run color |
| `slide_style.annotation_color` | ✅ Best-effort | Superscript-baseline run color |
| `sections[].section` | ✅ Lossless | Single bold block on section slide |
| `sections[].verses = []` | ✅ Lossless | Empty sections preserved |
| `verses[].reference` | ✅ Lossless | Detected via Unicode-aware regex |
| `verses[].reference = ""` | ✅ Lossless | Empty reference emitted correctly |
| `verses[].text` | ✅ Lossless | Body content including verse numbers |
| `verses[].text = ""` | ✅ Lossless | Empty text preserved |
| `verses[].highlights` (strings) | ✅ Best-effort | Colored runs matching highlight color |
| `verses[].highlights` (objects with `color`/`bold`/`underline`) | ✅ Lossless | Run color/formatting extracted |
| `verses[].highlights[].annotation` number | ⚠️ Lossy | Bubble chars (❶❷) **not recoverable**; omitted from output |
| `verses[].large_text` | ✅ Lossless | Runs with font size ≥ 1.4× body size |
| `verses[].list_type` | ✅ Lossless | Bullet prefix `•` → `"bullet"`, `N.` → `"numbered"` |
| `verses[].font_size` | ✅ Lossless | Per-verse body font size |
| `verses[].alignment` | ✅ Lossless | Paragraph alignment |
| Tamil / Hebrew / Unicode text | ✅ Lossless | Full Unicode support throughout |

---

## 🔄 Round-Trip Workflow

```python
from praisonaippt import create_presentation, pptx_to_json

# 1. Create PPTX from JSON
data = {
    "presentation_title": "Great Faith",
    "sections": [
        {
            "section": "1. Centurion",
            "verses": [
                {
                    "reference": "Matthew 8:10 (NKJV)",
                    "text": "I have not found such great faith.",
                    "highlights": ["great faith"]
                }
            ]
        }
    ]
}
pptx_path = create_presentation(data, output_file="great_faith.pptx")

# 2. Extract JSON back
extracted = pptx_to_json(pptx_path)

# 3. Feed back into create_presentation (works without stripping _ keys)
roundtrip = create_presentation(extracted, output_file="roundtrip.pptx")
```

### Batch Extraction

```python
import os
from praisonaippt import pptx_to_json

pptx_files = [f for f in os.listdir('.') if f.endswith('.pptx')]
for pptx in pptx_files:
    json_out = pptx.replace('.pptx', '.json')
    pptx_to_json(pptx, output_path=json_out)
    print(f"Extracted: {pptx} → {json_out}")
```

---

## ⚠️ Known Limitations

| Limitation | Reason | Workaround |
|-----------|--------|-----------|
| `background_image` path not in output | Image bytes in ZIP — path metadata stripped by PowerPoint | Manually add the path back to `slide_style.background_image` |
| `annotation` numbers (❶❷) not recovered | Bubble chars are rendered glyphs with no metadata | Re-add annotation numbers manually if needed |
| Style heuristics are best-effort | No semantic metadata in PPTX format | Visual inspection recommended for complex slides |
| Externally-authored PPTX may differ | Non-praisonaippt PPTX may use different layouts | Heuristics handle most cases; failures produce per-slide warnings |

---

## 📚 Related Documentation

- [Python API Reference]({{ '/python-api' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})
- [PDF Conversion Guide]({{ '/pdf-conversion' | relative_url }})
- [Rich Text Formatting Guide]({{ '/formatting' | relative_url }})
- [Examples and Templates]({{ '/examples' | relative_url }})

---

**Need help?** [Open an issue on GitHub](https://github.com/MervinPraison/PraisonAIPPT/issues)

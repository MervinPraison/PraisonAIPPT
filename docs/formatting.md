---
layout: default
title: "Rich Text Formatting - PraisonAI PPT"
description: "Complete guide to rich text formatting, bullet lists, annotations, alignment, and font options"
---

# Rich Text Formatting

PraisonAI PPT supports per-phrase rich text formatting directly in your JSON input — colors, bold, italic, underline, numbered annotations, bullet lists, text alignment, and custom font sizes.

---

## Highlights

The `highlights` field accepts a **mixed list** of strings and/or objects.

### String (Simple) Highlights

A plain string highlights the phrase in **bold orange** — the default style.

```yaml
reference: John 3:16 (NKJV)
text: For God so loved the world that he gave his only Son.
highlights:
- God so loved
- only Son
```

### Object (Rich) Highlights

Pass an object to control color, bold, italic, underline, and annotation independently.

```yaml
reference: Romans 1:17 (NKJV)
text: For in it the righteousness of God is revealed from faith to faith.
highlights:
- the righteousness of God is revealed from
- text: faith to faith
  color: '#4A86E8'
  bold: true
  underline: true
```

#### Object Highlight Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `text` | string | **required** | Phrase to match (case-insensitive) |
| `color` | string | `"orange"` | Named color or hex string |
| `bold` | boolean | `true` | Bold text |
| `italic` | boolean | `false` | Italic text |
| `underline` | boolean | `false` | Underline text (`true` auto-set when `annotation` is present) |
| `annotation` | integer | `null` | Numbered bubble annotation (1–9) |

---

## Colors

### Named Colors

| Name | Preview |
|---|---|
| `orange` | Default highlight color |
| `yellow` | Soft gold |
| `red` | Dark red |
| `green` | Mid green |
| `blue` | Dark blue |
| `white` | White (use on dark backgrounds) |
| `cyan` | Teal |
| `purple` | Violet |

### Hex Colors

Any 6-digit hex string works, with or without `#`:

```yaml
- text: faith
  color: '#4A86E8'
- text: hope
  color: 'FF8C00'
```

### Multi-Color Example

```yaml
highlights:
- text: the gospel
  annotation: 1
- text: the power
  annotation: 2
- text: salvation
  color: '#4A86E8'
  underline: true
  annotation: 3
- for everyone who believes
```

---

## Annotations (Numbered Bubbles)

Add `"annotation": N` (1–9) to any object highlight to render a **filled circle bubble** (❶❷❸…) as a superscript immediately after the phrase.

```yaml
reference: Romans 1:16–17 (NKJV)
text: For I am not ashamed of the gospel of Christ, for it is the power of God to
  salvation...
highlights:
- text: the gospel
  annotation: 1
- text: the power
  annotation: 2
- text: salvation
  color: '#4A86E8'
  underline: true
  annotation: 3
```

Renders as: **the gospel**❶ … **the power**❷ … **salvation**❸

!!! note
    Annotated phrases are automatically underlined unless you set `"underline": false` explicitly.

---

## Bullet and Numbered List Slides

Add `"list_type"` to a verse to render it as a bullet or numbered list instead of a plain text slide.
Items are split by newline characters (`\n`).

### Bullet List

```yaml
reference: ''
text: 'Woman with the Issue of Blood

  Centurion

  Canaanite'
list_type: bullet
```

Renders as:
```
• Woman with the Issue of Blood
• Centurion
• Canaanite
```

### Numbered List

```yaml
reference: ''
text: 'They heard about Jesus

  They knew the power of God

  They knew the heart of God'
list_type: numbered
```

Renders as:
```
1. They heard about Jesus
2. They knew the power of God
3. They knew the heart of God
```

---

## Text Alignment

Control per-verse text alignment with `"alignment"`:

| Value | Description |
|---|---|
| `"center"` | Default for verse slides |
| `"left"` | Default for list slides |
| `"right"` | Right-align |

```yaml
reference: Mark 16:20 (NKJV)
text: And they went out and preached everywhere...
alignment: left
```

---

## Custom Font Size

Override the default 32pt body text with `"font_size"`:

```yaml
reference: John 3:16 (NKJV)
text: For God so loved the world...
font_size: 28
```

Useful for longer verses that overflow a single slide, or for emphasis slides with large text.

---

## Complete Verse Object Reference

```yaml
reference: Romans 1:16–17 (NKJV)
text: For I am not ashamed of the gospel...
highlights:
- simple phrase (orange + bold)
- text: rich phrase
  color: yellow
  bold: true
  italic: false
  underline: true
  annotation: 1
large_text:
  gospel: 48
list_type: bullet
alignment: center
font_size: 32
```

| Field | Type | Default | Description |
|---|---|---|---|
| `reference` | string | `""` | Verse reference shown at bottom |
| `text` | string | **required** | Verse text (use `\n` for list items) |
| `highlights` | list | `[]` | Rich text formatting, see above |
| `large_text` | object | `{}` | `{"phrase": font_size_pt}` overrides |
| `list_type` | string | `null` | `"bullet"` or `"numbered"` |
| `alignment` | string | `"center"` | `"left"`, `"center"`, or `"right"` |
| `font_size` | integer | `32` | Body text size in pt |

---

## Slide Style (Background, Colors, Font)

Add a `"slide_style"` key at the **top level** of your JSON to control the appearance of every slide. All fields are optional. When a background is set, text colors automatically default to white.

```yaml
presentation_title: Great Faith
slide_style:
  background_image: assets/background_dark.png
  background_color: '#1A1A2E'
  text_color: '#FFFFFF'
  reference_color: '#CCCCCC'
  title_color: '#FFFFFF'
  subtitle_color: '#AAAAAA'
  section_title_color: '#FFFFFF'
  highlight_color: '#FF8C00'
  annotation_color: '#1E50C8'
  font_name: Spectral
  alignment: left
  reference_position: top
sections: [...]
```

### slide_style Fields

--8<-- "docs/snippets/slide_style_table.md"

### Dark Background — Quick Start

```yaml
slide_style:
  background_image: assets/background_alt.jpg
  text_color: white
  font_name: Palatino
```

### Custom Colors Only (No Background)

```yaml
slide_style:
  highlight_color: '#FFD700'
  annotation_color: '#E53935'
  font_name: Georgia
```

---

## Verse Number Superscripts

Display individual verse numbers as small superscripts before each verse line by starting each line with its verse number followed by a space.

```yaml
reference: Titus 2:11-13 (NKJV)
text: '11 For the grace of God that brings salvation has appeared to all men,

  12 teaching us that, denying ungodliness and worldly lusts, we should live soberly,

  13 looking for the blessed hope and glorious appearing of our great God and Savior
  Jesus Christ,'
```

The numbers render as small superscript characters (~52% of body size, raised baseline) before each line of text.

**Rules:**
- Each line in the `\n`-separated text must start with `1–3 digits + space` to trigger numbering
- Lines without a leading number are rendered as plain paragraphs (no superscript)
- Works alongside `highlights` — verse numbers appear before highlighted text without conflict
- Single-verse entries also support a number prefix: `"20 And they went out and preached…"`

---

## Slide Size (Widescreen)

Add a top-level `"slide_size"` key to change the presentation dimensions.

```yaml
presentation_title: Great Faith
slide_size: widescreen
slide_style: { ... }
sections: [ ... ]
```

### Presets

| Value | Dimensions | Use case |
|---|---|---|
| `"widescreen"` / `"16:9"` | 13.33" × 7.5" | Modern projectors / screens |
| `"standard"` / `"4:3"` | 10" × 7.5" | Classic slides (package default) |
| `"16:10"` | 12.8" × 8.0" | MacBook / older widescreen |
| `{"width": W, "height": H}` | Custom | Any size in inches |

```yaml
slide_size:
  width: 13.33
  height: 7.5
```

!!! note
    Omitting `slide_size` keeps the standard 4:3 default — no change to existing presentations.

---

## PDF Generation & Google Drive Upload

Generate a PDF alongside the PPTX and auto-upload both to Google Drive in a single command:

```bash
praisonaippt -i verses.yaml -o my_presentation.pptx --convert-pdf
```

- Creates `my_presentation.pptx` and `my_presentation.pdf`
- Automatically uploads **both** to the same Google Drive date folder (`YYYY/MM`)
- Falls back to Google Drive API for PDF conversion if LibreOffice is not installed

### Convert an Existing PPTX to PDF

```bash
praisonaippt convert-pdf my_presentation.pptx --upload-gdrive
```

Same GDrive fallback and auto-upload as the main flag.

---

## Related

- [Examples and Templates]({{ '/examples' | relative_url }})
- [Python API Reference]({{ '/python-api' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})

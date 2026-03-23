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

```json
{
    "reference": "John 3:16 (NKJV)",
    "text": "For God so loved the world that he gave his only Son.",
    "highlights": ["God so loved", "only Son"]
}
```

### Object (Rich) Highlights

Pass an object to control color, bold, italic, underline, and annotation independently.

```json
{
    "reference": "Romans 1:17 (NKJV)",
    "text": "For in it the righteousness of God is revealed from faith to faith.",
    "highlights": [
        "the righteousness of God is revealed from",
        {
            "text": "faith to faith",
            "color": "#4A86E8",
            "bold": true,
            "underline": true
        }
    ]
}
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

```json
{ "text": "faith", "color": "#4A86E8" }
{ "text": "hope",  "color": "FF8C00"  }
```

### Multi-Color Example

```json
"highlights": [
    { "text": "the gospel",   "annotation": 1 },
    { "text": "the power",    "annotation": 2 },
    { "text": "salvation",    "color": "#4A86E8", "underline": true, "annotation": 3 },
    "for everyone who believes"
]
```

---

## Annotations (Numbered Bubbles)

Add `"annotation": N` (1–9) to any object highlight to render a **filled circle bubble** (❶❷❸…) as a superscript immediately after the phrase.

```json
{
    "reference": "Romans 1:16–17 (NKJV)",
    "text": "For I am not ashamed of the gospel of Christ, for it is the power of God to salvation...",
    "highlights": [
        { "text": "the gospel",  "annotation": 1 },
        { "text": "the power",   "annotation": 2 },
        { "text": "salvation",   "color": "#4A86E8", "underline": true, "annotation": 3 }
    ]
}
```

Renders as: **the gospel**❶ … **the power**❷ … **salvation**❸

!!! note
    Annotated phrases are automatically underlined unless you set `"underline": false` explicitly.

---

## Bullet and Numbered List Slides

Add `"list_type"` to a verse to render it as a bullet or numbered list instead of a plain text slide.
Items are split by newline characters (`\n`).

### Bullet List

```json
{
    "reference": "",
    "text": "Woman with the Issue of Blood\nCenturion\nCanaanite",
    "list_type": "bullet"
}
```

Renders as:
```
• Woman with the Issue of Blood
• Centurion
• Canaanite
```

### Numbered List

```json
{
    "reference": "",
    "text": "They heard about Jesus\nThey knew the power of God\nThey knew the heart of God",
    "list_type": "numbered"
}
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

```json
{
    "reference": "Mark 16:20 (NKJV)",
    "text": "And they went out and preached everywhere...",
    "alignment": "left"
}
```

---

## Custom Font Size

Override the default 32pt body text with `"font_size"`:

```json
{
    "reference": "John 3:16 (NKJV)",
    "text": "For God so loved the world...",
    "font_size": 28
}
```

Useful for longer verses that overflow a single slide, or for emphasis slides with large text.

---

## Complete Verse Object Reference

```json
{
    "reference": "Romans 1:16–17 (NKJV)",
    "text": "For I am not ashamed of the gospel...",
    "highlights": [
        "simple phrase (orange + bold)",
        {
            "text": "rich phrase",
            "color": "yellow",
            "bold": true,
            "italic": false,
            "underline": true,
            "annotation": 1
        }
    ],
    "large_text": { "gospel": 48 },
    "list_type": "bullet",
    "alignment": "center",
    "font_size": 32
}
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

```json
{
    "presentation_title": "Great Faith",
    "slide_style": {
        "background_image": "assets/background_dark.png",
        "background_color": "#1A1A2E",
        "text_color": "#FFFFFF",
        "reference_color": "#CCCCCC",
        "title_color": "#FFFFFF",
        "subtitle_color": "#AAAAAA",
        "section_title_color": "#FFFFFF",
        "highlight_color": "#FF8C00",
        "annotation_color": "#1E50C8",
        "font_name": "Spectral",
        "alignment": "left",
        "reference_position": "top"
    },
    "sections": [...]
}
```

### slide_style Fields

| Field | Default (no bg) | Auto-dark default | Description |
|---|---|---|---|
| `background_image` | — | — | Path to a background image file |
| `background_color` | — | — | Hex background color e.g. `"#1A1A2E"` |
| `text_color` | `#1A1A2E` dark | `#FFFFFF` white | Body / verse text |
| `reference_color` | `#404040` gray | `#CCCCCC` light gray | Verse reference line |
| `title_color` | theme default | `#FFFFFF` white | Title slide title |
| `subtitle_color` | theme default | `#AAAAAA` | Title slide subtitle |
| `section_title_color` | `#003366` dark blue | `#FFFFFF` white | Section heading slides |
| `highlight_color` | `#FF8C00` orange | `#FF8C00` orange | Default color for simple string highlights |
| `annotation_color` | `#1E50C8` blue | `#1E50C8` blue | Numbered bubble annotations (❶❷❸…) |
| `font_name` | (system default) | (system default) | Font family for all text, e.g. `"Spectral"` |
| `alignment` | `"center"` (verses), `"left"` (lists) | same | Default text alignment |
| `reference_position` | `"bottom"` | `"bottom"` | `"top"` or `"bottom"` for verse reference |

!!! note
    **Font names**: any font installed on your system works (including Google Fonts after installation). The font name is stored in the PPTX file — PowerPoint will use it automatically.

!!! tip
    **Zero regression**: if you omit `slide_style` entirely, all slides use default styling (dark text, white background). `slide_style` only activates when present.

### Dark Background — Quick Start

```json
"slide_style": {
    "background_image": "assets/background_dark.png",
    "text_color": "white",
    "reference_position": "top",
    "font_name": "Spectral"
}
```

This will auto-set all text (body, reference, title, section) to white/light variants automatically.

### Custom Colors Only (No Background)

```json
"slide_style": {
    "highlight_color": "#FFD700",
    "annotation_color": "#E53935",
    "font_name": "Lato"
}
```

---

## Related

- [Examples and Templates]({{ '/examples' | relative_url }})
- [Python API Reference]({{ '/python-api' | relative_url }})
- [Command Reference]({{ '/commands' | relative_url }})

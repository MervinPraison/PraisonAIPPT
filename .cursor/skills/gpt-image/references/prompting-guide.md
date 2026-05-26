# GPT Image Prompting Reference

Condensed prompting patterns for `gpt-image-2`. Read this before writing any prompt.

## Prompt Structure

Write prompts in this order: **background/scene → subject → key details → constraints**.
Include the intended use (ad, UI mock, infographic) to set the visual "mode."
For complex prompts, use labeled segments or line breaks instead of one dense paragraph.

## Format

Use whatever format is easiest to maintain. All of these work:
- Minimal one-liners
- Descriptive paragraphs
- Labeled sections / bullet lists
- JSON-like structures

For production, prioritize a skimmable template over clever syntax.

## Specificity + Quality Cues

Be concrete about materials, shapes, textures, and the visual medium (photo, watercolor, 3D render).
Add targeted "quality levers" only when needed: *film grain*, *textured brushstrokes*, *macro detail*.

For photorealism, include the word **"photorealistic"** directly. Similar phrases like "real photograph,"
"taken on a real camera," "professional photography," or "iPhone photo" also help but are interpreted loosely.

## Composition

Specify:
- **Framing/viewpoint**: close-up, wide, top-down
- **Perspective/angle**: eye-level, low-angle
- **Lighting/mood**: soft diffuse, golden hour, high-contrast
- **Layout**: "logo top-right," "subject centered with negative space on left"

For cinematic, low-light, rain, or neon scenes, add extra detail about scale, atmosphere, and colour.

## People, Pose, and Action

Describe scale, body framing, gaze, and object interactions:
- "full body visible, feet included"
- "child-sized relative to the table"
- "looking down at the open book, not at the camera"
- "hands naturally gripping the handlebars"

## Constraints (Change vs Preserve)

State exclusions and invariants explicitly:
- "no watermark," "no extra text," "no logos/trademarks"
- "preserve identity/geometry/layout/brand elements"

For edits, use **"change only X" + "keep everything else the same"** and repeat the preserve list each iteration.

## Text in Images

- Put literal text in **quotes** or **ALL CAPS**
- Specify typography: font style, size, colour, placement
- For tricky words/brand names, spell letter-by-letter
- Use `medium` or `high` quality for small text, dense panels, multi-font layouts

## Multi-Image Inputs (Edit Mode)

Reference each input by index and description:
- "Image 1: product photo… Image 2: style reference…"
- Describe how they interact: "apply Image 2's style to Image 1"
- For compositing: "put the bird from Image 1 on the elephant in Image 2"

## Iteration Strategy

Start with a clean base prompt. Refine with small single-change follow-ups:
- "make lighting warmer"
- "remove the extra tree"
- "restore the original background"

Re-specify critical details if they start to drift.

---

## Use Case Prompt Patterns

### Infographics
Explain structured information for a specific audience. Include data hierarchy, labels, and layout.
Use `quality=high` for dense text or detailed diagrams.

### Photorealism
Prompt as if capturing a real photo. Use photography language (lens, lighting, framing).
Ask for real texture (pores, wrinkles, fabric wear). Avoid studio-polish language.

### Logo Generation
Describe brand personality and use case. Ask for clean vector-like shapes, strong silhouette,
balanced negative space. "Flat design, minimal strokes, no gradients unless essential."

### Ads
Write like a creative brief: brand positioning, desired vibe, target audience, scene, tagline.
Quote tagline text exactly. Ask for clean, legible typography.

### Style Transfer (Edit)
Describe what stays (style cues) and what changes (new content).
Add hard constraints: background, framing, "no extra elements."

### Virtual Try-On (Edit)
Lock the person (face, body shape, pose, hair, expression). Allow changes only to garments.
Require realistic fit (draping, folds, occlusion) plus consistent lighting/shadows.

### Product Mockups (Edit)
"Extract product, place on plain white opaque background."
Preserve product geometry and label legibility. Add only light polishing and contact shadow.

### Object Removal (Edit)
"Remove X. Do not change anything else." Use `input_fidelity=high` when identity matters.

### Scene Compositing (Edit)
Clearly specify what to transplant, where it goes, and what must remain unchanged.
Match lighting, perspective, scale, and shadows.

### Lighting/Weather Transformation (Edit)
Change only environmental conditions. Preserve identity, geometry, camera angle, object placement.

---

## Size Quick Reference

| Label | Resolution | Notes |
|-------|-----------|-------|
| HD portrait | 1024x1536 | Standard portrait |
| HD landscape | 1536x1024 | Standard landscape |
| Square | 1024x1024 | General-purpose default |
| 2K / QHD | 2560x1440 | Upper reliability boundary |
| Near-4K | 3824x2144 | Experimental upper end |

**Constraints**: both edges multiple of 16, max edge < 3840px, ratio ≤ 3:1,
total pixels between 655,360 and 8,294,400.

## Quality Guide

| Setting | When to use |
|---------|-------------|
| `low` | Speed/cost-sensitive, high-volume, experimentation, previews |
| `medium` | Default for most production work |
| `high` | Small/dense text, detailed infographics, close-up portraits, identity-sensitive edits, high-res |

---

## PraisonAI PPT slide assets

- Save outputs under `assets/generated/` in the ppt-package repo.
- Use **`1536x864`** for widescreen slide diagrams; match `slide_style` (dark background, gold/green accent text).
- Reference in YAML: `slide_type: image`, `image_path: assets/generated/your_file.png`, `image_fit: contain`.
- Regenerate deck: `python3 -m praisonaippt.cli -i examples/<deck>.yaml -o examples/<deck>.pptx`
- No logos, trademarks, or watermarks on slide art.


| Field / Key | Type | Default (light) | Auto-dark default | Description |
|-----------|------|-----------------|-------------------|-------------|
| `background_image` | string | — | — | Path to a background image file |
| `background_color` | string | — | — | Hex background color e.g. `"#1A1A2E"` |
| `text_color` | string | `#1A1A2E` dark | `#FFFFFF` white | Body / verse text |
| `reference_color` | string | `#404040` gray | `#CCCCCC` light gray | Verse reference line |
| `title_color` | string | theme default | `#FFFFFF` white | Title slide title |
| `subtitle_color` | string | theme default | `#AAAAAA` | Title slide subtitle |
| `section_title_color` | string | `#003366` dark blue | `#FFFFFF` white | Section heading slides |
| `highlight_color` | string | `#FF8C00` orange | `#FFD700` yellow | Default color for simple string highlights |
| `annotation_color` | string | `#1E50C8` blue | `#1E50C8` blue | Numbered bubble annotations (❶❷❸…) |
| `font_name` | string | **`Palatino`** | **`Palatino`** | Font family for all text |
| `alignment` | string | **`"left"`** | **`"left"`** | Default text alignment (`"left"`, `"center"`, `"right"`) |
| `reference_position` | string | **`"top"`** | **`"top"`** | `"top"` or `"bottom"` for verse reference line |

!!! note
    **Package defaults**: When `background_image` or `background_color` is set, all text colors automatically default to white/light variants. Individual color keys override these auto-defaults. `font_name`, `alignment`, and `reference_position` have opinionated defaults (Palatino / left / top).

!!! tip
    **Zero regression**: If you omit `slide_style` entirely, all slides retain their standard default parameters automatically.

"""
Core presentation creation logic for Bible verses PowerPoint generator.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from .utils import split_long_text, sanitize_filename, resolve_asset_path
from .pdf_converter import PDFOptions, convert_pptx_to_pdf


def _apply_slide_background(slide, style: dict, prs=None):
    """
    Apply background to a slide from a slide_style dict.

    Supported keys:
        background_color (str): Hex color e.g. '#1A1A2E'
        background_image (str): Absolute or relative path to an image file
    """
    if not style:
        return

    img_path = style.get('background_image')
    bg_color = style.get('background_color')
    source_file = style.get('_source_file')

    if img_path:
        import os
        resolved = resolve_asset_path(img_path, source_file=source_file)
        img_path = resolved if resolved else img_path
        if os.path.exists(img_path):
            # Use prs dimensions or fall back to standard 16:9 (13.33 x 7.5 in)
            if prs is not None:
                w, h = prs.slide_width, prs.slide_height
            else:
                w, h = Inches(13.33), Inches(7.5)
            pic = slide.shapes.add_picture(img_path, 0, 0, w, h)
            # Move picture to back
            sp_tree = slide.shapes._spTree
            sp_tree.remove(pic._element)
            sp_tree.insert(2, pic._element)
        elif bg_color:
            img_path = None
    if not img_path and bg_color:
        fill = slide.background.fill
        fill.solid()
        hex_c = bg_color.lstrip('#')
        r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        fill.fore_color.rgb = RGBColor(r, g, b)



def add_title_slide(prs, title, subtitle="", style=None):
    """
    Add a title slide. When slide_style contains a background, the slide uses
    a blank layout for full text-color control. Otherwise uses the default
    template layout (zero regression).
    """
    style = style or {}
    has_background = bool(style.get('background_image') or style.get('background_color'))

    if has_background:
        theme = _resolve_theme(style)
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
        _apply_slide_background(slide, style, prs)
        margin = Inches(_style_layout(style, 'title', 'margin_in', 0.6))
        width = Inches(_style_layout(style, 'title', 'content_width_in', 9.0))
        title_top = Inches(_style_layout(style, 'title', 'title_top_in', 2.5))
        title_h = Inches(_style_layout(style, 'title', 'title_height_in', 1.5))
        title_pt = _style_typography(style, 'title_size_pt', 44)
        tb = slide.shapes.add_textbox(margin, title_top, width, title_h)
        p = tb.text_frame.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(title_pt)
        p.font.bold = True
        p.font.color.rgb = theme['title']
        if theme['font_name']:
            p.font.name = theme['font_name']
        # Subtitle
        if subtitle:
            subtitle_top = Inches(_style_layout(style, 'title', 'subtitle_top_in', 4.2))
            subtitle_h = Inches(_style_layout(style, 'title', 'subtitle_height_in', 1.0))
            subtitle_pt = _style_typography(style, 'subtitle_size_pt', 28)
            tb2 = slide.shapes.add_textbox(margin, subtitle_top, width, subtitle_h)
            p2 = tb2.text_frame.paragraphs[0]
            p2.text = subtitle
            p2.alignment = PP_ALIGN.CENTER
            p2.font.size = Pt(subtitle_pt)
            p2.font.color.rgb = theme['subtitle']
            if theme['font_name']:
                p2.font.name = theme['font_name']
    else:
        theme = _resolve_theme(style)
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        _apply_slide_background(slide, style, prs)
        title_shape = slide.shapes.title
        title_shape.text = title
        if theme['font_name']:
            title_shape.text_frame.paragraphs[0].font.name = theme['font_name']
        if subtitle and len(slide.placeholders) > 1:
            sub = slide.placeholders[1]
            sub.text = subtitle
            if theme['font_name']:
                sub.text_frame.paragraphs[0].font.name = theme['font_name']

    return slide


def add_section_slide(prs, section_name, style=None, section_subtitle=None):
    """
    Add a section title slide — centred, same layout for all themes.
    Background image/color applied when present in slide_style.

    Optional ``section_subtitle`` (str): second line below the title, smaller type
    (e.g. ``Section 1``). Set from YAML as ``section_subtitle`` next to ``section``.
    """
    style = style or {}
    theme = _resolve_theme(style)

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank for full control
    _apply_slide_background(slide, style, prs)

    name = section_name or ''
    sub = (section_subtitle or '').strip()
    line_count = name.count('\n') + 1 if name else 1
    tb_h = Inches(1.5) if line_count <= 1 else Inches(min(1.2 + line_count * 0.55, 4.5))
    if sub:
        # Extra height for gap under title + subtitle paragraph
        tb_h += Inches(0.85)

    # Centre the title block vertically and horizontally on the slide
    margin = Inches(0.6)
    tb_w = prs.slide_width - 2 * margin
    left = (prs.slide_width - tb_w) / 2
    top = (prs.slide_height - tb_h) / 2

    tb = slide.shapes.add_textbox(left, top, tb_w, tb_h)
    tf = tb.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = section_name
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = theme['section']
    if theme['font_name']:
        p.font.name = theme['font_name']

    if sub:
        p.space_after = Pt(20)
        sr, sg, sb = list(theme['section'])
        dim = 0.76
        sub_rgb = RGBColor(
            max(0, min(255, int(sr * dim))),
            max(0, min(255, int(sg * dim))),
            max(0, min(255, int(sb * dim))),
        )
        sp = tf.add_paragraph()
        sp.text = sub
        sp.alignment = PP_ALIGN.CENTER
        sp.font.size = Pt(24)
        sp.font.bold = False
        sp.font.color.rgb = sub_rgb
        if theme['font_name']:
            sp.font.name = theme['font_name']

    return slide


def _parse_color(color_value):
    """Parse a color value (named string or hex) into RGBColor."""
    NAMED_COLORS = {
        'orange': RGBColor(255, 140, 0),
        'yellow': RGBColor(255, 215, 0),
        'red':    RGBColor(220, 50,  50),
        'green':  RGBColor(50,  180, 50),
        'blue':   RGBColor(30,  100, 220),
        'white':  RGBColor(255, 255, 255),
        'cyan':   RGBColor(0,   200, 200),
        'purple': RGBColor(150, 50,  200),
    }
    if not color_value:
        return NAMED_COLORS['orange']
    if isinstance(color_value, str):
        if color_value.lower() in NAMED_COLORS:
            return NAMED_COLORS[color_value.lower()]
        # Hex string e.g. "#FF8C00" or "FF8C00"
        lower = color_value.strip('#')
        if len(lower) == 6:
            try:
                r, g, b = int(lower[0:2], 16), int(lower[2:4], 16), int(lower[4:6], 16)
                return RGBColor(r, g, b)
            except ValueError:
                pass
    return NAMED_COLORS['orange']


def _resolve_theme(style: dict) -> dict:
    """
    Resolve all display colors from a slide_style dict with smart defaults.

    When background_image or background_color is set, text auto-defaults to
    white (dark-background mode). Any individual key in slide_style overrides
    the auto-default.

    JSON keys supported (all optional):
        text_color, reference_color, title_color, subtitle_color,
        section_title_color, highlight_color, annotation_color,
        reference_position, alignment
    """
    style = style or {}
    has_dark_bg = bool(style.get('background_image') or style.get('background_color'))
    raw_text = str(style.get('text_color') or '').lower().strip()
    if raw_text:
        dark_mode = raw_text in ('white', '#ffffff', 'ffffff')
    else:
        dark_mode = has_dark_bg  # auto: dark bg → white text

    def _rc(key, light, dark):
        raw = style.get(key, '')
        return _parse_color(raw) if raw else (_parse_color(dark) if dark_mode else _parse_color(light))

    return {
        'dark_mode':        dark_mode,
        'body':             _rc('text_color',          '#1A1A2E', '#FFFFFF'),
        'reference':        _rc('reference_color',     '#404040', '#CCCCCC'),
        'title':            _rc('title_color',         '#1A1A2E', '#FFFFFF'),
        'subtitle':         _rc('subtitle_color',      '#505050', '#AAAAAA'),
        'section':          _rc('section_title_color', '#003366', '#FFFFFF'),
        'highlight':        _rc('highlight_color',     '#FF8C00', '#FFD700'),
        'annotation':       _rc('annotation_color',    '#1E50C8', '#1E50C8'),
        'ref_position':     style.get('reference_position', 'top'),
        'global_alignment': style.get('alignment', 'left'),
        'font_name':        style.get('font_name') or 'Palatino',
    }


def _style_layout(style: dict, slide_type: str, key: str, default):
    """Optional SDK v2 layout token from slide_style.layouts."""
    layouts = (style or {}).get('layouts') or {}
    block = layouts.get(slide_type) or {}
    return block.get(key, default)


def _style_typography(style: dict, key: str, default):
    """Optional SDK v2 typography token from slide_style.typography."""
    typography = (style or {}).get('typography') or {}
    return typography.get(key, default)


def _normalise_highlights(highlights, highlight_rgb=None):
    """
    Normalise highlights list. highlight_rgb overrides the default orange.
    """
    default_hl = highlight_rgb or RGBColor(255, 140, 0)
    BUBBLES = {1: '\u2776', 2: '\u2777', 3: '\u2778', 4: '\u2779', 5: '\u277a',
                6: '\u277b', 7: '\u277c', 8: '\u277d', 9: '\u277e'}
    result = []
    for h in highlights:
        if isinstance(h, str):
            result.append({'text': h, 'color': default_hl,
                           'bold': True, 'italic': False,
                           'underline': False, 'annotation': None})
        elif isinstance(h, dict) and h.get('text'):
            ann = h.get('annotation', None)
            result.append({
                'text': h['text'],
                'color': _parse_color(h.get('color', 'orange')),
                'bold': h.get('bold', True),
                'italic': h.get('italic', False),
                'underline': h.get('underline', True if ann else False),
                'annotation': BUBBLES.get(ann) if ann else None,
            })
    return result


def _apply_highlights(paragraph, text, highlights, large_text=None,
                      body_rgb=None, highlight_rgb=None, annotation_rgb=None,
                      font_name=None, base_font_size=32):
    """
    Apply per-phrase rich text formatting.
    body_rgb, highlight_rgb, annotation_rgb, font_name all come from _resolve_theme.
    base_font_size: point size for normal body and highlight runs (``large_text`` overrides per match).
    """
    import re
    _body = body_rgb or RGBColor(26, 26, 46)
    _ann  = annotation_rgb or RGBColor(30, 80, 200)
    _base = int(base_font_size) if base_font_size else 32

    def _sf(run, size_pt):
        """Set font size and optional font name on a run."""
        run.font.size = Pt(size_pt)
        if font_name:
            run.font.name = font_name

    matches = []

    if highlights:
        for fmt in _normalise_highlights(highlights, highlight_rgb=highlight_rgb):
            pattern = re.escape(fmt['text'])
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append((match.start(), match.end(), match.group(), 'highlight', fmt))

    if large_text:
        for word, font_size in large_text.items():
            pattern = re.escape(word)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append((match.start(), match.end(), match.group(), 'large', font_size))

    matches.sort(key=lambda x: x[0])
    filtered, last_end = [], -1
    for m in matches:
        if m[0] >= last_end:
            filtered.append(m)
            last_end = m[1]

    _body = body_rgb or RGBColor(26, 26, 46)

    if not filtered:
        run = paragraph.add_run()
        run.text = text
        _sf(run, _base)
        run.font.color.rgb = _body
        if font_name:
            run.font.name = font_name
        return

    current_pos = 0

    for start, end, matched_text, fmt_type, fmt in filtered:
        # Plain text before this match
        if start > current_pos:
            run = paragraph.add_run()
            run.text = text[current_pos:start]
            _sf(run, _base)
            run.font.color.rgb = _body
            run.font.bold = False
            run.font.italic = False
            run.font.underline = False

        # Formatted run — always add_run() to preserve any pre-existing runs
        run = paragraph.add_run()
        run.text = matched_text

        if fmt_type == 'highlight':
            _sf(run, _base)
            run.font.color.rgb = fmt['color']
            run.font.bold = fmt['bold']
            run.font.italic = fmt['italic']
            run.font.underline = fmt['underline']
            if fmt.get('annotation'):
                ann_run = paragraph.add_run()
                ann_run.text = fmt['annotation']
                _sf(ann_run, 46)
                ann_run.font.bold = False
                ann_run.font.color.rgb = _ann
                rPr = ann_run._r.get_or_add_rPr()
                rPr.set('baseline', '30000')
        elif fmt_type == 'large':
            _sf(run, fmt)
            run.font.color.rgb = _body

        current_pos = end

    # Remaining plain text
    if current_pos < len(text):
        run = paragraph.add_run()
        run.text = text[current_pos:]
        _sf(run, _base)
        run.font.color.rgb = _body
        run.font.bold = False
        run.font.italic = False
        run.font.underline = False

def _resolve_alignment(align_str):
    """Convert alignment string to PP_ALIGN constant."""
    return {
        'left':   PP_ALIGN.LEFT,
        'right':  PP_ALIGN.RIGHT,
        'center': PP_ALIGN.CENTER,
    }.get((align_str or 'center').lower(), PP_ALIGN.CENTER)


def add_list_slide(prs, items, reference, list_type='bullet', font_size=32,
                   alignment='left', style=None):
    """
    Add a bullet/numbered list slide. Default alignment is left.
    All colors and font resolved via slide_style.
    """
    style = style or {}
    theme = _resolve_theme(style)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(slide, style, prs)

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(1.2), Inches(9), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    align = _resolve_alignment(alignment)

    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        prefix = f"{idx + 1}. " if list_type == 'numbered' else "\u2022  "
        p.text = prefix + item
        p.alignment = align
        p.font.size = Pt(font_size)
        p.font.color.rgb = theme['body']
        if theme['font_name']:
            p.font.name = theme['font_name']
        p.space_after = Pt(10)

    if reference:
        ref_tb = slide.shapes.add_textbox(Inches(0.6), Inches(6.3), Inches(9), Inches(0.6))
        ref_p = ref_tb.text_frame.paragraphs[0]
        ref_p.text = reference
        ref_p.alignment = PP_ALIGN.CENTER
        ref_p.font.size = Pt(22)
        ref_p.font.color.rgb = theme['reference']
        ref_p.font.italic = True
        if theme['font_name']:
            ref_p.font.name = theme['font_name']

    return slide


def add_image_slide(prs, image_path, style=None, caption=None, reference=None,
                    image_fit='contain', source_file=None):
    """
    Add a slide with an embedded image and optional caption.

    ``image_fit``: ``contain`` (default, keep aspect ratio), ``cover`` (fill area,
    keep ratio, may crop), or ``fill`` (stretch to content box).
    ``reference`` / ``caption`` appear below the image when provided.
    """
    import os
    style = dict(style or {})
    if source_file:
        style['_source_file'] = source_file

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(slide, style, prs)

    resolved = resolve_asset_path(image_path, source_file=source_file)
    path = resolved if resolved else image_path
    if not path or not os.path.exists(path):
        print(f"Warning: Image not found: {image_path}")
        return slide

    theme = _resolve_theme(style)
    slide_w = prs.slide_width
    slide_h = prs.slide_height
    caption_lines = []
    if reference and str(reference).strip():
        caption_lines.append(str(reference).strip())
    if caption and str(caption).strip():
        caption_lines.append(str(caption).strip())
    caption_h = Inches(0.9) if caption_lines else Inches(0)
    fit = (image_fit or 'contain').lower()
    margin = Inches(0) if not caption_lines and fit in ('cover', 'fill') else Inches(0.35)

    box_top = margin
    box_h = slide_h - margin * 2 - caption_h
    box_w = slide_w - margin * 2
    if fit not in ('contain', 'cover', 'fill'):
        fit = 'contain'

    if fit == 'fill':
        slide.shapes.add_picture(path, margin, box_top, width=box_w, height=box_h)
    else:
        pic = slide.shapes.add_picture(path, margin, box_top, width=box_w)
        scale_w = box_w / pic.width
        scale_h = box_h / pic.height
        if fit == 'contain':
            scale = min(scale_w, scale_h)
        else:  # cover
            scale = max(scale_w, scale_h)
        pic.width = int(pic.width * scale)
        pic.height = int(pic.height * scale)
        pic.left = margin + (box_w - pic.width) // 2
        pic.top = box_top + (box_h - pic.height) // 2

    if caption_lines:
        cap_top = slide_h - margin - caption_h
        cap_tb = slide.shapes.add_textbox(margin, cap_top, box_w, caption_h)
        cap_tf = cap_tb.text_frame
        cap_tf.word_wrap = True
        for i, line in enumerate(caption_lines):
            p = cap_tf.paragraphs[0] if i == 0 else cap_tf.add_paragraph()
            p.text = line
            p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(22 if i == 0 and reference else 18)
            p.font.bold = bool(i == 0 and reference)
            p.font.color.rgb = theme['reference'] if i == 0 and reference else theme['body']
            if theme['font_name']:
                p.font.name = theme['font_name']

    return slide


def _hebrew_font_name(style: dict) -> str:
    """Prefer a Hebrew-capable font when available."""
    custom = (style or {}).get("hebrew_font_name")
    if custom:
        return custom
    import os
    for path in (
        "/System/Library/Fonts/SFHebrew.ttf",
        "/System/Library/Fonts/Supplemental/Arial Hebrew.ttf",
        "/Library/Fonts/Arial Hebrew.ttf",
    ):
        if os.path.exists(path):
            return "Arial Hebrew" if "Arial" in path else "SF Hebrew"
    return (style or {}).get("font_name") or "Palatino"


def _fill_hebrew_runs(paragraph, text, highlight_substring, body_rgb, highlight_rgb, font_size_pt, font_name):
    """Write Hebrew text; colour ``highlight_substring`` in the right-hand name."""
    hl = highlight_substring or ""
    if not hl or hl not in text:
        run = paragraph.add_run()
        run.text = text
        run.font.size = Pt(font_size_pt)
        run.font.color.rgb = body_rgb
        if font_name:
            run.font.name = font_name
        return

    parts = text.split(hl, 1)
    before, after = parts[0], parts[1] if len(parts) > 1 else ""

    def _add(part, rgb):
        if not part:
            return
        r = paragraph.add_run()
        r.text = part
        r.font.size = Pt(font_size_pt)
        r.font.color.rgb = rgb
        if font_name:
            r.font.name = font_name

    _add(before, body_rgb)
    _add(hl, highlight_rgb)
    _add(after, body_rgb)


def add_hebrew_rename_slide(prs, rows, style=None, font_size=110, reference=None, caption=None,
                            highlight_color=None):
    """
    Slide matching the original Why Delay Hebrew layout: large names left/right,
    purple highlight on the changed letter in the new name (e.g. הָ in אַבְרָהָם).
    """
    from pptx.enum.shapes import MSO_CONNECTOR_TYPE

    style = style or {}
    theme = _resolve_theme(style)
    body_rgb = theme["body"]
    hl_hex = highlight_color or style.get("hebrew_highlight_color") or "#9900FF"
    hl_rgb = _parse_color(hl_hex) or RGBColor(153, 0, 255)
    hebrew_pt = int(font_size or style.get("hebrew_font_size") or 110)
    fn = _hebrew_font_name(style)

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(slide, style, prs)

    slide_w_in = prs.slide_width.inches
    sx = slide_w_in / 10.0
    row_y = [1.15, 4.05]
    left_x = 0.35 * sx
    right_x = 5.15 * sx
    box_w = 4.2 * sx
    box_h = 1.35

    for i, row in enumerate(rows[:2]):
        left = (row.get("left") or "").strip()
        right = (row.get("right") or "").strip()
        hl = (row.get("highlight_in_right") or "ה").strip()
        y = Inches(row_y[i] if i < len(row_y) else row_y[-1] + i * 2.9)

        lt = slide.shapes.add_textbox(Inches(left_x), y, Inches(box_w), Inches(box_h))
        lt_tf = lt.text_frame
        lt_tf.word_wrap = False
        lp = lt_tf.paragraphs[0]
        lp.alignment = PP_ALIGN.CENTER
        lr = lp.add_run()
        lr.text = left
        lr.font.size = Pt(hebrew_pt)
        lr.font.color.rgb = body_rgb
        if fn:
            lr.font.name = fn

        rt = slide.shapes.add_textbox(Inches(right_x), y, Inches(box_w), Inches(box_h))
        rt_tf = rt.text_frame
        rt_tf.word_wrap = False
        rp = rt_tf.paragraphs[0]
        rp.alignment = PP_ALIGN.CENTER
        _fill_hebrew_runs(rp, right, hl, body_rgb, hl_rgb, hebrew_pt, fn)

        y_mid = y.inches + box_h * 0.45
        x1 = left_x + box_w * 0.85
        x2 = right_x + box_w * 0.05
        conn = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.STRAIGHT,
            Inches(x1), Inches(y_mid), Inches(x2), Inches(y_mid),
        )
        conn.line.color.rgb = theme["highlight"]
        conn.line.width = Pt(2.5)

    cap_h = Inches(0.85)
    if reference or caption:
        cap_top = prs.slide_height - Inches(0.45) - cap_h
        cap_tb = slide.shapes.add_textbox(Inches(0.5), cap_top, prs.slide_width - Inches(1.0), cap_h)
        cap_tf = cap_tb.text_frame
        cap_tf.word_wrap = True
        lines = []
        if reference:
            lines.append(str(reference).strip())
        if caption:
            lines.append(str(caption).strip())
        for idx, line in enumerate(lines):
            p = cap_tf.paragraphs[0] if idx == 0 else cap_tf.add_paragraph()
            p.text = line
            p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(22 if idx == 0 and reference else 18)
            p.font.bold = bool(idx == 0 and reference)
            p.font.color.rgb = theme["reference"] if idx == 0 and reference else theme["body"]
            if theme["font_name"]:
                p.font.name = theme["font_name"]

    return slide


def _parse_verse_lines(text):
    """
    Parse verse text into [(verse_num_or_None, line_text), ...] pairs.
    Detects lines (or inline segments) starting with 1–3 digit verse numbers.
    e.g. '11 For the grace...\n12 Teaching us...' → [('11','For the grace...'),('12','Teaching us...')]
    e.g. '1 Therefore, holy brethren...' → [('1', 'Therefore, holy brethren...')]
    Returns [(None, full_text)] if no verse numbers detected.
    """
    import re
    VERSE_NUM_RE = re.compile(r"^(\d{1,3})\s+(.*)", re.DOTALL)

    # Books that appear with a numeric prefix (1/2/3 Timothy, etc.)
    NUMBERED_BOOKS = frozenset([
        "timothy", "corinthians", "thessalonians", "peter", "john",
        "chronicles", "samuel", "kings", "esdras", "maccabees",
    ])

    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
    result = []
    for line in raw_lines:
        m = VERSE_NUM_RE.match(line)
        if m:
            num_str = m.group(1)
            remainder = m.group(2)
            # If 1/2/3 followed by a numbered Bible book name -> plain text
            first_word = remainder.split()[0].lower().rstrip(",:)") if remainder.split() else ""
            if int(num_str) in (1, 2, 3) and first_word in NUMBERED_BOOKS:
                result.append((None, line))
            else:
                result.append((num_str, remainder))
        else:
            result.append((None, line))

    # If no verse numbers found at all, return original
    if not any(num for num, _ in result):
        return [(None, text)]
    return result


def _add_superscript_num_run(paragraph, num_str, font_size, body_rgb, font_name):
    """Add a small superscript verse-number run to a paragraph."""
    from pptx.oxml.ns import qn
    run = paragraph.add_run()
    run.text = num_str + '\u2009'  # narrow space after number
    run.font.size = Pt(int(font_size * 0.52))
    run.font.color.rgb = body_rgb
    run.font.bold = False
    if font_name:
        run.font.name = font_name
    # Set superscript baseline (30 000 = 30% above normal)
    rPr = run._r.get_or_add_rPr()
    rPr.set('baseline', '30000')


def add_verse_slide(prs, verse_text, reference, part_num=None, highlights=None,
                    large_text=None, alignment='left', font_size=32, style=None,
                    reference_font_size=None, leading_title=None,
                    text_below_reference=None, text_below_reference_highlights=None,
                    text_below_reference_large_text=None):
    """
    Add a verse slide. All colors and font resolved via slide_style.
    Supported slide_style keys: background_image, background_color,
    text_color, reference_color, highlight_color, annotation_color,
    title_color, section_title_color, font_name,
    reference_position ('top'/'bottom'), alignment.

    Optional verse YAML key ``leading_title`` (str): large line at the top of the
    slide; the reference is drawn directly under that title, then the verse body
    beneath the reference. Optional ``text_below_reference`` adds a further block
    below the verse body (e.g. a second passage on the same slide).
    Optional ``text_below_reference_highlights`` / ``text_below_reference_large_text``:
    same shape as ``highlights`` / ``large_text`` for that block.
    """
    style = style or {}
    theme = _resolve_theme(style)
    verse_slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(verse_slide, style, prs)
    align = _resolve_alignment(alignment)
    ref_position = theme['ref_position']
    fn = theme['font_name']
    leading = (leading_title or '').strip()
    extra_ref = (text_below_reference or '').strip()

    def _set_ref(tb_shape, text, align_const, size, bold=False, italic=False):
        rp = tb_shape.text_frame.paragraphs[0]
        rp.text = text
        rp.alignment = align_const
        rp.font.size = Pt(size)
        rp.font.bold = bold
        rp.font.italic = italic
        rp.font.color.rgb = theme['reference']
        if fn:
            rp.font.name = fn

    slide_h_in = prs.slide_height.inches
    bottom_margin_in = 0.15
    # Inches from top of slide to top of main verse body (used for text_below_reference placement)
    leading_verse_top_in = None
    leading_verse_h_in = None

    if leading:
        # Title at top; reference under title; verse body under reference
        lt_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(9), Inches(1.15))
        lt_tf = lt_tb.text_frame
        lt_tf.word_wrap = True
        lt_tf.vertical_anchor = MSO_ANCHOR.TOP
        lt_p = lt_tf.paragraphs[0]
        lt_p.text = leading
        lt_p.alignment = align
        lt_p.font.size = Pt(38)
        lt_p.font.bold = True
        lt_p.font.color.rgb = theme['body']
        if fn:
            lt_p.font.name = fn
        if reference:
            ref_text = reference + (f' (Part {part_num})' if part_num is not None else '')
            ref_pt = int(reference_font_size) if reference_font_size is not None else 24
            ref_h_in = 0.72 if extra_ref else 0.85
            # Gap below leading-title textbox before reference (title box ends 0.35 + 1.15)
            title_ref_gap_in = 0.2
            ref_y_in = 0.35 + 1.15 + title_ref_gap_in
            ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(ref_y_in), Inches(9), Inches(ref_h_in))
            _set_ref(ref_tb, ref_text, PP_ALIGN.LEFT, ref_pt, bold=True, italic=False)
            ref_tb.text_frame.paragraphs[0].font.color.rgb = theme['body']
            if fn:
                ref_tb.text_frame.paragraphs[0].font.name = fn
            vtop = ref_y_in + ref_h_in + 0.1
            if extra_ref:
                extra_reserve_in = 1.32
                vh = slide_h_in - vtop - extra_reserve_in - bottom_margin_in
            else:
                vh = slide_h_in - vtop - bottom_margin_in
            leading_verse_top_in = vtop
            leading_verse_h_in = max(vh, 2.0)
            verse_top = Inches(vtop)
            verse_height = Inches(leading_verse_h_in)
        else:
            leading_verse_top_in = 1.65
            leading_verse_h_in = 3.25 if extra_ref else 3.85
            verse_top = Inches(leading_verse_top_in)
            verse_height = Inches(leading_verse_h_in)
    elif ref_position == 'top' and reference:
        ref_text = reference + (f' (Part {part_num})' if part_num is not None else '')
        ref_pt = int(reference_font_size) if reference_font_size is not None else 28
        ref_h_in = 0.95 if ref_pt >= 36 else 0.7
        ref_h = Inches(ref_h_in)
        ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(9), ref_h)
        _set_ref(ref_tb, ref_text, PP_ALIGN.LEFT, ref_pt, bold=True)
        # Override body color for top reference (use body not reference)
        ref_tb.text_frame.paragraphs[0].font.color.rgb = theme['body']
        # Place body text below the reference box (avoid overlap when ref is large)
        verse_top = Inches(0.3 + ref_h_in + 0.15)
        verse_height = Inches(4.5)
    else:
        verse_top, verse_height = Inches(1.5), Inches(3.8)

    textbox = verse_slide.shapes.add_textbox(Inches(0.6), verse_top, Inches(9), verse_height)
    tf = textbox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = align

    verse_lines = _parse_verse_lines(verse_text)
    has_verse_nums = any(num for num, _ in verse_lines)

    first_para = True
    for v_num, v_text in verse_lines:
        if first_para:
            p = tf.paragraphs[0]
            first_para = False
        else:
            p = tf.add_paragraph()
        p.alignment = align

        if (highlights and len(highlights) > 0) or (large_text and len(large_text) > 0):
            if has_verse_nums and v_num:
                _add_superscript_num_run(p, v_num, font_size, theme['body'], fn)
            _apply_highlights(p, v_text, highlights, large_text,
                              body_rgb=theme['body'],
                              highlight_rgb=theme['highlight'],
                              annotation_rgb=theme['annotation'],
                              font_name=fn,
                              base_font_size=int(font_size))
        else:
            if has_verse_nums and v_num:
                _add_superscript_num_run(p, v_num, font_size, theme['body'], fn)
            run = p.add_run()
            run.text = v_text
            run.font.size = Pt(font_size)
            run.font.color.rgb = theme['body']
            if fn:
                run.font.name = fn

    if leading and extra_ref and leading_verse_top_in is not None and leading_verse_h_in is not None:
        below_top = leading_verse_top_in + leading_verse_h_in + 0.06
        below_fs = max(int(font_size) - 2, 22)
        ex_h_in = max(slide_h_in - below_top - bottom_margin_in, 0.5)
        ex_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(below_top), Inches(9), Inches(ex_h_in))
        ex_tf = ex_tb.text_frame
        ex_tf.word_wrap = True
        ex_tf.vertical_anchor = MSO_ANCHOR.TOP
        ex_p = ex_tf.paragraphs[0]
        ex_p.alignment = align
        hl2 = text_below_reference_highlights
        lt2 = text_below_reference_large_text
        if (hl2 and len(hl2) > 0) or (lt2 and len(lt2) > 0):
            _apply_highlights(ex_p, extra_ref, hl2, lt2,
                              body_rgb=theme['body'],
                              highlight_rgb=theme['highlight'],
                              annotation_rgb=theme['annotation'],
                              font_name=fn,
                              base_font_size=below_fs)
        else:
            ex_run = ex_p.add_run()
            ex_run.text = extra_ref
            ex_run.font.size = Pt(below_fs)
            ex_run.font.color.rgb = theme['body']
            if fn:
                ex_run.font.name = fn
    elif ref_position != 'top' and reference:
        ref_text = reference + (f' (Part {part_num})' if part_num is not None else '')
        ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(6.0), Inches(9), Inches(0.7))
        _set_ref(ref_tb, ref_text, PP_ALIGN.CENTER, 22, italic=True)

    return verse_slide


def create_presentation(data, output_file=None, custom_title=None, 
                        convert_to_pdf=False, pdf_options=None, pdf_backend='auto'):
    """
    Create a PowerPoint presentation from Bible verses data.
    
    Args:
        data (dict): Verses data dictionary with structure:
                     {
                         "presentation_title": "Title",
                         "presentation_subtitle": "Subtitle",
                         "sections": [
                             {
                                 "section": "Section Name",
                                 "verses": [
                                     {"reference": "Book 1:1", "text": "Verse text"}
                                 ]
                             }
                         ]
                     }
        output_file (str): Output filename (optional, auto-generated if not provided)
        custom_title (str): Custom presentation title (optional, overrides JSON title)
        convert_to_pdf (bool): Whether to also convert to PDF (default: False)
        pdf_options (PDFOptions): PDF conversion options (optional)
        pdf_backend (str): PDF conversion backend ('aspose', 'libreoffice', 'auto')
    
    Returns:
        str or dict: Path to the created presentation file, or dict with both PPTX and PDF paths
                    if convert_to_pdf is True, or None if error
    """
    if not data:
        print("Error: No data provided")
        return None
    
    # Create presentation
    prs = Presentation()

    # Apply slide size if specified in JSON
    # Supported: "widescreen"/"16:9", "standard"/"4:3", or {"width": W, "height": H} in inches
    slide_size = data.get("slide_size")
    if slide_size:
        from pptx.util import Inches as _Inches
        PRESETS = {
            "widescreen": (13.33, 7.5),
            "16:9":       (13.33, 7.5),
            "standard":   (10.0,  7.5),
            "4:3":        (10.0,  7.5),
            "16:10":      (12.8,  8.0),
        }
        if isinstance(slide_size, str) and slide_size.lower() in PRESETS:
            w, h = PRESETS[slide_size.lower()]
            prs.slide_width  = _Inches(w)
            prs.slide_height = _Inches(h)
        elif isinstance(slide_size, dict):
            if "width"  in slide_size: prs.slide_width  = _Inches(slide_size["width"])
            if "height" in slide_size: prs.slide_height = _Inches(slide_size["height"])

    # Get verses data from JSON
    verses_data = data.get("sections", [])
    # Presentation-level slide style (background, text color, alignment, etc.)
    slide_style = dict(data.get("slide_style", {}) or {})
    source_file = data.get("_source_file")
    if source_file:
        slide_style["_source_file"] = source_file

    # Add title slide
    if custom_title:
        title = custom_title
        subtitle = ""
    else:
        title = data.get("presentation_title", "Bible Verses Collection")
        subtitle = data.get("presentation_subtitle", "Selected Scriptures")
    
    add_title_slide(prs, title, subtitle, style=slide_style)
    
    # Add slides for each verse with section slides
    for section_data in verses_data:
        # Add section title slide if section name exists (skip if custom title is provided)
        if section_data.get("section") and not custom_title:
            add_section_slide(
                prs, section_data["section"], style=slide_style,
                section_subtitle=section_data.get("section_subtitle"),
            )

        # Add verse slides if there are any verses
        if section_data.get("verses") and len(section_data["verses"]) > 0:
            for verse in section_data["verses"]:
                # Get per-verse options
                highlights = verse.get('highlights', None)
                large_text = verse.get('large_text', None)
                list_type  = verse.get('list_type', None)
                list_alignment = verse.get('alignment', slide_style.get('alignment', 'left'))
                verse_alignment = verse.get('alignment', slide_style.get('alignment', 'left'))
                font_size  = verse.get('font_size', 32)

                if verse.get('slide_type') == 'image' and verse.get('image_path'):
                    add_image_slide(
                        prs,
                        verse['image_path'],
                        style=slide_style,
                        reference=verse.get('reference'),
                        caption=verse.get('text'),
                        image_fit=verse.get('image_fit', 'contain'),
                        source_file=source_file,
                    )
                elif verse.get('slide_type') == 'hebrew_rename' and verse.get('hebrew_rows'):
                    add_hebrew_rename_slide(
                        prs,
                        verse['hebrew_rows'],
                        style=slide_style,
                        font_size=verse.get('hebrew_font_size'),
                        reference=verse.get('reference'),
                        caption=verse.get('text'),
                        highlight_color=verse.get('hebrew_highlight_color'),
                    )
                elif list_type in ('bullet', 'numbered'):
                    items = [line.strip() for line in verse['text'].split('\n') if line.strip()]
                    add_list_slide(prs, items, verse['reference'],
                                   list_type=list_type,
                                   font_size=font_size,
                                   alignment=list_alignment,
                                   style=slide_style)
                else:
                    _max_len = int(verse.get('split_max_length') or 200)
                    verse_parts = split_long_text(verse['text'], max_length=max(_max_len, 50))
                    for i, part in enumerate(verse_parts):
                        part_num = None  # never show (Part N) on split slides
                        add_verse_slide(
                            prs, part, verse['reference'], part_num,
                            highlights, large_text,
                            alignment=verse_alignment,
                            font_size=font_size,
                            style=slide_style,
                            reference_font_size=verse.get('reference_font_size'),
                            leading_title=(verse.get('leading_title') if i == 0 else None),
                            text_below_reference=(verse.get('text_below_reference') if i == 0 else None),
                            text_below_reference_highlights=(
                                verse.get('text_below_reference_highlights') if i == 0 else None),
                            text_below_reference_large_text=(
                                verse.get('text_below_reference_large_text') if i == 0 else None),
                        )
    
    # Generate output filename if not provided
    if not output_file:
        if custom_title:
            base_name = sanitize_filename(custom_title)
        else:
            base_name = sanitize_filename(data.get("presentation_title", "presentation"))
        output_file = f"{base_name}.pptx"
    
    # Ensure .pptx extension
    if not output_file.endswith('.pptx'):
        output_file += '.pptx'
    
    # Save presentation
    try:
        prs.save(output_file)
        print(f"✓ Presentation created successfully: {output_file}")
        
        # Convert to PDF if requested
        if convert_to_pdf:
            try:
                # Use default PDF options if none provided
                if pdf_options is None:
                    pdf_options = PDFOptions()
                
                # Generate PDF filename
                from pathlib import Path
                pdf_file = str(Path(output_file).with_suffix('.pdf'))
                
                # Convert to PDF
                pdf_result = convert_pptx_to_pdf(
                    output_file, 
                    pdf_file, 
                    backend=pdf_backend, 
                    options=pdf_options
                )
                
                print(f"✓ PDF created successfully: {pdf_result}")
                
                # Return both files
                return {
                    'pptx': output_file,
                    'pdf': pdf_result
                }
                
            except Exception as e:
                print(f"Warning: PDF conversion failed: {e}")
                print("Presentation was created successfully at:", output_file)
                return output_file
        
        return output_file
        
    except Exception as e:
        print(f"Error saving presentation: {e}")
        return None

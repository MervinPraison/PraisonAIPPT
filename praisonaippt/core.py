"""
Core presentation creation logic for Bible verses PowerPoint generator.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from .utils import split_long_text, sanitize_filename
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

    if img_path:
        import os, pathlib
        if not os.path.isabs(img_path):
            img_path = str(pathlib.Path(img_path).resolve())
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
        # Title
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(2.5), Inches(9), Inches(1.5))
        p = tb.text_frame.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = theme['title']
        if theme['font_name']:
            p.font.name = theme['font_name']
        # Subtitle
        if subtitle:
            tb2 = slide.shapes.add_textbox(Inches(0.6), Inches(4.2), Inches(9), Inches(1.0))
            p2 = tb2.text_frame.paragraphs[0]
            p2.text = subtitle
            p2.alignment = PP_ALIGN.CENTER
            p2.font.size = Pt(28)
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


def add_section_slide(prs, section_name, style=None):
    """
    Add a section title slide — centered, same layout for all themes.
    Background image/color applied when present in slide_style.
    """
    style = style or {}
    theme = _resolve_theme(style)

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank for full control
    _apply_slide_background(slide, style, prs)

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(3.0), Inches(9), Inches(1.5))
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
    raw_text = style.get('text_color', '').lower().strip()
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
        'font_name':        style.get('font_name', 'Palatino'),
    }


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
                      font_name=None):
    """
    Apply per-phrase rich text formatting.
    body_rgb, highlight_rgb, annotation_rgb, font_name all come from _resolve_theme.
    """
    import re
    _body = body_rgb or RGBColor(26, 26, 46)
    _ann  = annotation_rgb or RGBColor(30, 80, 200)

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
        _sf(run, 32)
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
            _sf(run, 32)
            run.font.color.rgb = _body
            run.font.bold = False
            run.font.italic = False
            run.font.underline = False

        # Formatted run — always add_run() to preserve any pre-existing runs
        run = paragraph.add_run()
        run.text = matched_text

        if fmt_type == 'highlight':
            _sf(run, 32)
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
        _sf(run, 32)
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


def add_image_slide(prs, image_path, style=None, caption=None):
    """
    Add a slide containing an embedded image (e.g. a diagram extracted from a source PPTX).
    The background is applied from slide_style. The image is placed centred with small margins.
    """
    import os
    style = style or {}
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(slide, style, prs)

    if not os.path.exists(image_path):
        return slide  # image file missing — produce blank slide

    slide_w = prs.slide_width
    slide_h = prs.slide_height
    margin = Inches(0.2)
    img = slide.shapes.add_picture(
        image_path,
        left=margin,
        top=margin,
        width=slide_w - margin * 2,
        height=slide_h - margin * 2,
    )
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
                    large_text=None, alignment='left', font_size=32, style=None):
    """
    Add a verse slide. All colors and font resolved via slide_style.
    Supported slide_style keys: background_image, background_color,
    text_color, reference_color, highlight_color, annotation_color,
    title_color, section_title_color, font_name,
    reference_position ('top'/'bottom'), alignment.
    """
    style = style or {}
    theme = _resolve_theme(style)
    verse_slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(verse_slide, style, prs)
    align = _resolve_alignment(alignment)
    ref_position = theme['ref_position']
    fn = theme['font_name']

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

    if ref_position == 'top' and reference:
        ref_text = reference + (f' (Part {part_num})' if part_num is not None else '')
        ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(9), Inches(0.7))
        _set_ref(ref_tb, ref_text, PP_ALIGN.LEFT, 28, bold=True)
        # Override body color for top reference (use body not reference)
        ref_tb.text_frame.paragraphs[0].font.color.rgb = theme['body']
        verse_top, verse_height = Inches(1.2), Inches(4.5)
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
                              font_name=fn)
        else:
            if has_verse_nums and v_num:
                _add_superscript_num_run(p, v_num, font_size, theme['body'], fn)
            run = p.add_run()
            run.text = v_text
            run.font.size = Pt(font_size)
            run.font.color.rgb = theme['body']
            if fn:
                run.font.name = fn

    if ref_position != 'top' and reference:
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
    slide_style = data.get("slide_style", {})

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
            add_section_slide(prs, section_data["section"], style=slide_style)

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
                    # Image slide (diagram extracted from source PPTX)
                    add_image_slide(prs, verse['image_path'], style=slide_style)
                elif list_type in ('bullet', 'numbered'):
                    items = [line.strip() for line in verse['text'].split('\n') if line.strip()]
                    add_list_slide(prs, items, verse['reference'],
                                   list_type=list_type,
                                   font_size=font_size,
                                   alignment=list_alignment,
                                   style=slide_style)
                else:
                    verse_parts = split_long_text(verse['text'])
                    for i, part in enumerate(verse_parts):
                        part_num = None  # never show (Part N) on split slides
                        add_verse_slide(prs, part, verse['reference'], part_num,
                                        highlights, large_text,
                                        alignment=verse_alignment,
                                        font_size=font_size,
                                        style=slide_style)
    
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

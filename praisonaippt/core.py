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



def add_title_slide(prs, title, subtitle=""):
    """
    Add a title slide to the presentation.
    
    Args:
        prs: Presentation object
        title (str): Title text
        subtitle (str): Subtitle text (optional)
    
    Returns:
        Slide object
    """
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    
    title_shape = slide.shapes.title
    title_shape.text = title
    
    if subtitle and len(slide.placeholders) > 1:
        subtitle_shape = slide.placeholders[1]
        subtitle_shape.text = subtitle
    
    return slide


def add_section_slide(prs, section_name):
    """
    Add a section title slide to the presentation.
    
    Args:
        prs: Presentation object
        section_name (str): Section title text
    
    Returns:
        Slide object
    """
    section_slide_layout = prs.slide_layouts[1]
    section_slide = prs.slides.add_slide(section_slide_layout)
    section_title = section_slide.shapes.title
    section_title.text = section_name
    
    # Style section title
    section_title.text_frame.paragraphs[0].font.size = Pt(44)
    section_title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)
    
    return section_slide


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


def _normalise_highlights(highlights):
    """
    Normalise a mixed list of string/object highlight entries into dicts.

    String  -> {text, color=orange, bold=True, italic=False, underline=False}
    Object  -> {text, color, bold, italic, underline, annotation} with defaults applied
    """
    BUBBLES = {1: '❶', 2: '❷', 3: '❸', 4: '❹', 5: '❺',
                6: '❻', 7: '❼', 8: '❽', 9: '❾'}
    result = []
    for h in highlights:
        if isinstance(h, str):
            result.append({
                'text': h,
                'color': RGBColor(255, 140, 0),
                'bold': True,
                'italic': False,
                'underline': False,
                'annotation': None,
            })
        elif isinstance(h, dict) and h.get('text'):
            ann = h.get('annotation', None)
            result.append({
                'text': h['text'],
                'color': _parse_color(h.get('color', 'orange')),
                'bold': h.get('bold', True),
                'italic': h.get('italic', False),
                # auto-underline when annotation is set, unless explicitly set
                'underline': h.get('underline', True if ann else False),
                'annotation': BUBBLES.get(ann) if ann else None,
            })
    return result


def _apply_highlights(paragraph, text, highlights, large_text=None, body_rgb=None):
    """
    Apply per-phrase rich text formatting to a paragraph.

    Args:
        body_rgb (RGBColor): Color for non-highlighted runs (default dark charcoal)
    """
    import re

    matches = []

    if highlights:
        for fmt in _normalise_highlights(highlights):
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
        paragraph.text = text
        paragraph.font.size = Pt(32)
        paragraph.font.color.rgb = _body
        return

    current_pos = 0
    first_run = True

    for start, end, matched_text, fmt_type, fmt in filtered:
        # Plain text before this match
        if start > current_pos:
            if first_run:
                paragraph.text = text[current_pos:start]
                run = paragraph.runs[0]
                first_run = False
            else:
                run = paragraph.add_run()
                run.text = text[current_pos:start]
            run.font.size = Pt(32)
            run.font.color.rgb = _body
            run.font.bold = False
            run.font.italic = False
            run.font.underline = False

        # Formatted run
        if first_run:
            paragraph.text = matched_text
            run = paragraph.runs[0]
            first_run = False
        else:
            run = paragraph.add_run()
            run.text = matched_text

        if fmt_type == 'highlight':
            run.font.size = Pt(32)
            run.font.color.rgb = fmt['color']
            run.font.bold = fmt['bold']
            run.font.italic = fmt['italic']
            run.font.underline = fmt['underline']
            # Append filled-circle superscript annotation
            if fmt.get('annotation'):
                ann_run = paragraph.add_run()
                ann_run.text = fmt['annotation']
                ann_run.font.size = Pt(46)
                ann_run.font.bold = False
                ann_run.font.color.rgb = RGBColor(30, 80, 200)
                # XML superscript: raise 30% above baseline
                rPr = ann_run._r.get_or_add_rPr()
                rPr.set('baseline', '30000')
        elif fmt_type == 'large':
            run.font.size = Pt(fmt)
            run.font.color.rgb = RGBColor(26, 26, 46)

        current_pos = end

    # Remaining plain text
    if current_pos < len(text):
        run = paragraph.add_run()
        run.text = text[current_pos:]
        run.font.size = Pt(32)
        run.font.color.rgb = RGBColor(26, 26, 46)
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
    Add a bullet or numbered list slide.

    Args:
        style (dict): Optional slide_style dict (background_image, text_color, etc.)
    """
    style = style or {}
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(slide, style, prs)

    raw_text_color = style.get('text_color', '')
    body_rgb = RGBColor(255, 255, 255) if raw_text_color.lower() in ('white', '#ffffff', 'ffffff') else RGBColor(26, 26, 46)

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
        p.font.color.rgb = body_rgb
        from pptx.util import Pt as PtUtil
        p.space_after = PtUtil(10)

    if reference:
        ref_tb = slide.shapes.add_textbox(Inches(0.6), Inches(6.3), Inches(9), Inches(0.6))
        ref_p = ref_tb.text_frame.paragraphs[0]
        ref_p.text = reference
        ref_p.alignment = PP_ALIGN.CENTER
        ref_p.font.size = Pt(22)
        ref_p.font.color.rgb = RGBColor(200, 200, 200) if raw_text_color.lower() in ('white', '#ffffff', 'ffffff') else RGBColor(64, 64, 64)
        ref_p.font.italic = True

    return slide


def add_verse_slide(prs, verse_text, reference, part_num=None, highlights=None,
                    large_text=None, alignment='center', font_size=32, style=None):
    """
    Add a verse slide to the presentation.

    Args:
        style (dict): Optional slide_style dict with keys:
            background_color (str): Hex e.g. '#1A1A2E'
            background_image (str): Path to image file
            text_color (str): 'white' / hex (default dark charcoal)
            reference_position (str): 'top' or 'bottom' (default 'bottom')
    """
    style = style or {}
    verse_slide = prs.slides.add_slide(prs.slide_layouts[6])
    _apply_slide_background(verse_slide, style, prs)
    align = _resolve_alignment(alignment)

    # Resolve colors from style
    raw_text_color = style.get('text_color', '')
    if raw_text_color.lower() in ('white', '#ffffff', 'ffffff'):
        body_rgb = RGBColor(255, 255, 255)
    else:
        body_rgb = RGBColor(26, 26, 46)

    ref_position = style.get('reference_position', 'bottom')

    if ref_position == 'top' and reference:
        # Reference at top (bold, larger, white or styled)
        reference_text = reference
        if part_num is not None:
            reference_text += f' (Part {part_num})'
        ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(9), Inches(0.7))
        ref_p = ref_tb.text_frame.paragraphs[0]
        ref_p.text = reference_text
        ref_p.alignment = PP_ALIGN.LEFT
        ref_p.font.size = Pt(28)
        ref_p.font.bold = True
        ref_p.font.color.rgb = body_rgb
        verse_top = Inches(1.2)
        verse_height = Inches(4.5)
    else:
        verse_top = Inches(1.5)
        verse_height = Inches(3.8)

    # Verse text box
    textbox = verse_slide.shapes.add_textbox(Inches(0.6), verse_top, Inches(9), verse_height)
    tf = textbox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP

    p = tf.paragraphs[0]
    p.alignment = align

    if (highlights and len(highlights) > 0) or (large_text and len(large_text) > 0):
        _apply_highlights(p, verse_text, highlights, large_text, body_rgb=body_rgb)
    else:
        p.text = verse_text
        p.font.size = Pt(font_size)
        p.font.color.rgb = body_rgb

    # Reference at bottom
    if ref_position != 'top':
        reference_text = reference
        if part_num is not None:
            reference_text += f' (Part {part_num})'
        ref_tb = verse_slide.shapes.add_textbox(Inches(0.6), Inches(6.0), Inches(9), Inches(0.7))
        ref_p = ref_tb.text_frame.paragraphs[0]
        ref_p.text = reference_text
        ref_p.alignment = PP_ALIGN.CENTER
        ref_p.font.size = Pt(22)
        ref_p.font.color.rgb = RGBColor(200, 200, 200) if raw_text_color.lower() in ('white', '#ffffff', 'ffffff') else RGBColor(64, 64, 64)
        ref_p.font.italic = True

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
    
    add_title_slide(prs, title, subtitle)
    
    # Add slides for each verse with section slides
    for section_data in verses_data:
        # Add section title slide if section name exists (skip if custom title is provided)
        if section_data.get("section") and not custom_title:
            add_section_slide(prs, section_data["section"])

        # Add verse slides if there are any verses
        if section_data.get("verses") and len(section_data["verses"]) > 0:
            for verse in section_data["verses"]:
                # Get per-verse options
                highlights = verse.get('highlights', None)
                large_text = verse.get('large_text', None)
                list_type  = verse.get('list_type', None)
                alignment  = verse.get('alignment', slide_style.get('alignment', 'center'))
                font_size  = verse.get('font_size', 32)

                if list_type in ('bullet', 'numbered'):
                    items = [line.strip() for line in verse['text'].split('\n') if line.strip()]
                    add_list_slide(prs, items, verse['reference'],
                                   list_type=list_type,
                                   font_size=font_size,
                                   alignment=alignment,
                                   style=slide_style)
                else:
                    verse_parts = split_long_text(verse['text'])
                    for i, part in enumerate(verse_parts):
                        part_num = i + 1 if len(verse_parts) > 1 else None
                        add_verse_slide(prs, part, verse['reference'], part_num,
                                        highlights, large_text,
                                        alignment=alignment,
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

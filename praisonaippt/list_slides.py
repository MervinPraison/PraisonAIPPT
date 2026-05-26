"""Print a numbered outline of slides in a .pptx file."""

from pathlib import Path


def print_slide_outline(pptx_path, max_text_len=120):
    """
    Print slide count and a one-line summary per slide.

    Returns:
        int: 0 on success, 1 if the file is missing or unreadable.
    """
    path = Path(pptx_path)
    if not path.exists():
        print(f"MISSING: {path}")
        return 1

    from pptx import Presentation

    prs = Presentation(str(path))
    print(f"slides: {len(prs.slides)}")
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                line = shape.text.strip().replace("\n", " | ")
                if max_text_len:
                    line = line[:max_text_len]
                texts.append(line)
        title = texts[0] if texts else "(no text)"
        print(f"{i:2d}: {title}")
    return 0

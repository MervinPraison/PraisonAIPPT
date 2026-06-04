"""Export each slide from a PPTX deck as a JPEG image."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .ffmpeg_composer import check_video_tools, pdf_to_jpeg_pages
from .pdf_converter import PDFOptions, convert_pptx_to_pdf_with_fallback


@dataclass
class SlideImageOptions:
    """JPEG export settings."""

    dpi: int = 192
    jpeg_quality: int = 90
    keep_pdf: bool = False
    slide_range: Optional[Tuple[int, int]] = None  # 1-based inclusive


def default_slide_images_dir(pptx_path: str | Path) -> Path:
    """Default JPEG folder: ``examples/slide_images`` for decks under ``examples/``, else ``<stem>_slides``."""
    p = Path(pptx_path).resolve()
    if p.parent.name == "examples":
        return p.parent / "slide_images"
    return p.parent / f"{p.stem}_slides"


def resolve_slide_images_dir(
    deck: dict,
    *,
    pptx_path: str | Path,
    source_file: Optional[str] = None,
) -> Path:
    """Resolve ``slide_images_dir`` from deck YAML (relative to source file or PPTX parent)."""
    raw = (deck or {}).get("slide_images_dir")
    if not raw:
        return default_slide_images_dir(pptx_path)
    path = Path(str(raw))
    if path.is_absolute():
        return path
    base = Path(source_file).resolve().parent if source_file else Path(pptx_path).resolve().parent
    return (base / path).resolve()


def _parse_slide_range(slide_range: Optional[Tuple[int, int]]) -> tuple[Optional[int], Optional[int]]:
    if not slide_range:
        return None, None
    start, end = slide_range
    return int(start), int(end)


def _normalise_jpeg_names(raw_paths: List[str], out_dir: Path) -> List[str]:
    """Rename pdftoppm output (slide-1.jpg) to slide-001.jpg … slide-N.jpg."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(raw_paths, key=lambda p: Path(p).name)
    final: List[str] = []
    for i, src in enumerate(ordered, start=1):
        dest = out_dir / f"slide-{i:03d}.jpg"
        src_path = Path(src)
        if src_path.resolve() != dest.resolve():
            if dest.exists():
                dest.unlink()
            shutil.move(str(src_path), str(dest))
        final.append(str(dest))
    return final


def export_pptx_slide_jpegs(
    pptx_path: str,
    out_dir: Optional[str | Path] = None,
    *,
    pdf_path: Optional[str] = None,
    options: Optional[SlideImageOptions] = None,
    pdf_backend: str = "auto",
    pdf_options: Optional[PDFOptions] = None,
) -> List[str]:
    """
    Export one JPEG per slide from a PowerPoint file.

    Uses PPTX → PDF (LibreOffice / Aspose / GDrive fallback) then ``pdftoppm -jpeg``.

    Returns paths like ``…/slide-001.jpg``, ``slide-002.jpg``, …
    """
    opts = options or SlideImageOptions()
    pptx = Path(pptx_path)
    if not pptx.is_file():
        raise FileNotFoundError(f"PPTX not found: {pptx_path}")

    tools = check_video_tools()
    if not tools["pdftoppm"].found:
        raise RuntimeError(
            "pdftoppm (Poppler) is required for slide JPEG export. "
            "Install poppler — e.g. brew install poppler on macOS."
        )

    target_dir = Path(out_dir) if out_dir else default_slide_images_dir(pptx)
    target_dir.mkdir(parents=True, exist_ok=True)
    first_page, last_page = _parse_slide_range(opts.slide_range)

    def _rasterise(pdf_file: Path) -> List[str]:
        raw = pdf_to_jpeg_pages(
            str(pdf_file),
            target_dir,
            dpi=opts.dpi,
            jpeg_quality=opts.jpeg_quality,
            first_page=first_page,
            last_page=last_page,
        )
        if not raw:
            raise RuntimeError(f"No JPEG pages produced from {pdf_file}")
        return _normalise_jpeg_names(raw, target_dir)

    if pdf_path and Path(pdf_path).is_file():
        return _rasterise(Path(pdf_path))

    if pdf_path:
        pdf_file = Path(pdf_path)
        convert_pptx_to_pdf_with_fallback(
            str(pptx), str(pdf_file), backend=pdf_backend, options=pdf_options,
        )
        paths = _rasterise(pdf_file)
        if not opts.keep_pdf:
            pdf_file.unlink(missing_ok=True)
        return paths

    if opts.keep_pdf:
        pdf_file = pptx.with_suffix(".pdf")
        if not pdf_file.is_file():
            convert_pptx_to_pdf_with_fallback(
                str(pptx), str(pdf_file), backend=pdf_backend, options=pdf_options,
            )
        return _rasterise(pdf_file)

    with tempfile.TemporaryDirectory(prefix="praisonaippt-slides-") as tmp:
        pdf_file = Path(tmp) / f"{pptx.stem}.pdf"
        convert_pptx_to_pdf_with_fallback(
            str(pptx), str(pdf_file), backend=pdf_backend, options=pdf_options,
        )
        return _rasterise(pdf_file)

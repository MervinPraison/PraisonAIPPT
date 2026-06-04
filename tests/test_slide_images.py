"""Tests for PPTX slide JPEG export."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from praisonaippt.ffmpeg_composer import ToolCheck, pdf_to_jpeg_pages
from praisonaippt.slide_images import (
    SlideImageOptions,
    _normalise_jpeg_names,
    default_slide_images_dir,
    export_pptx_slide_jpegs,
)

PKG = Path(__file__).resolve().parent.parent


def test_default_slide_images_dir():
    assert default_slide_images_dir("/tmp/deck.pptx").resolve() == Path("/tmp/deck_slides").resolve()
    root = Path(__file__).resolve().parent.parent / "examples"
    assert default_slide_images_dir(root / "deck.pptx") == root / "slide_images"


def test_resolve_slide_images_dir_from_yaml():
    from praisonaippt.slide_images import resolve_slide_images_dir

    deck = {"slide_images_dir": "slide_images"}
    root = Path(__file__).resolve().parent.parent / "examples"
    out = resolve_slide_images_dir(
        deck, pptx_path=root / "heygen-50590-video-visual-mp3.pptx", source_file=str(root / "heygen-50590-content.yaml"),
    )
    assert out == (root / "slide_images").resolve()


def test_normalise_jpeg_names(tmp_path):
    raw = [str(tmp_path / "slide-2.jpg"), str(tmp_path / "slide-1.jpg")]
    for p in raw:
        Path(p).write_bytes(b"jpeg")
    out = _normalise_jpeg_names(raw, tmp_path)
    assert out == [str(tmp_path / "slide-001.jpg"), str(tmp_path / "slide-002.jpg")]


@patch("praisonaippt.slide_images.pdf_to_jpeg_pages")
@patch("praisonaippt.slide_images.convert_pptx_to_pdf_with_fallback")
@patch("praisonaippt.slide_images.check_video_tools")
def test_export_pptx_slide_jpegs(mock_tools, mock_pdf, mock_jpeg, tmp_path):
    pptx = tmp_path / "deck.pptx"
    pptx.write_bytes(b"pptx")
    mock_tools.return_value = {"pdftoppm": ToolCheck(name="pdftoppm", found=True)}
    jpg = tmp_path / "slides" / "slide-1.jpg"
    jpg.parent.mkdir(parents=True, exist_ok=True)
    jpg.write_bytes(b"jpeg")
    mock_jpeg.return_value = [str(jpg)]

    out_dir = tmp_path / "slides"
    paths = export_pptx_slide_jpegs(str(pptx), out_dir, options=SlideImageOptions(dpi=150, jpeg_quality=85))

    mock_pdf.assert_called_once()
    mock_jpeg.assert_called_once()
    assert mock_jpeg.call_args.kwargs["dpi"] == 150
    assert mock_jpeg.call_args.kwargs["jpeg_quality"] == 85
    assert paths == [str(out_dir / "slide-001.jpg")]


@patch("praisonaippt.slide_images.check_video_tools")
def test_export_requires_pdftoppm(mock_tools, tmp_path):
    pptx = tmp_path / "deck.pptx"
    pptx.write_bytes(b"pptx")
    mock_tools.return_value = {"pdftoppm": ToolCheck(name="pdftoppm", found=False)}
    with pytest.raises(RuntimeError, match="pdftoppm"):
        export_pptx_slide_jpegs(str(pptx), tmp_path / "out")


@patch("praisonaippt.ffmpeg_composer._run")
def test_pdf_to_jpeg_pages_invokes_pdftoppm(mock_run, tmp_path):
    out_dir = tmp_path / "pages"
    out_dir.mkdir()
    (out_dir / "slide-000.jpg").write_bytes(b"old")

    def _fake_pdftoppm(*_args, **_kwargs):
        (out_dir / "slide-1.jpg").write_bytes(b"j")
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = _fake_pdftoppm
    paths = pdf_to_jpeg_pages(str(tmp_path / "x.pdf"), out_dir, dpi=120, jpeg_quality=80)
    assert paths
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "pdftoppm"
    assert "-jpeg" in cmd
    assert "-jpegopt" in cmd
    assert "quality=80" in cmd

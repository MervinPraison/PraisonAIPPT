"""
PDF conversion tests.

These tests require a working PDF backend (Aspose.Slides or LibreOffice).
When no backend is available the tests are skipped (not failed), so the
suite remains green in minimal CI/dev environments.
"""

import os
from pathlib import Path

import pytest

from praisonaippt.pdf_converter import PDFConverter, PDFOptions, convert_pptx_to_pdf
from praisonaippt.core import create_presentation


def _has_backend() -> bool:
    try:
        return bool(PDFConverter().get_available_backends())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _has_backend(),
    reason="No PDF backend (Aspose.Slides/LibreOffice) available",
)


SAMPLE_DATA = {
    "presentation_title": "PDF Test Presentation",
    "presentation_subtitle": "Testing PDF Conversion",
    "sections": [
        {
            "section": "Test Section",
            "verses": [
                {
                    "reference": "Test 1:1",
                    "text": "This is a test verse for PDF conversion functionality.",
                    "highlights": ["test", "PDF"],
                }
            ],
        }
    ],
}


@pytest.fixture
def tmp_pptx(tmp_path):
    out = tmp_path / "deck.pptx"
    result = create_presentation(SAMPLE_DATA, output_file=str(out))
    pptx_path = result if isinstance(result, str) else result.get("pptx") if isinstance(result, dict) else os.fspath(result)
    assert pptx_path and Path(pptx_path).exists()
    return pptx_path


def test_backends_detected():
    converter = PDFConverter()
    backends = converter.get_available_backends()
    assert isinstance(backends, list) and backends, "expected at least one backend"


def test_convert_pptx_to_pdf_default(tmp_pptx, tmp_path):
    pdf_out = tmp_path / "out.pdf"
    result_path = convert_pptx_to_pdf(tmp_pptx, str(pdf_out))
    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0


def test_convert_pptx_to_pdf_with_options(tmp_pptx, tmp_path):
    pdf_out = tmp_path / "out_custom.pdf"
    options = PDFOptions(quality="medium", include_hidden_slides=False)
    result_path = convert_pptx_to_pdf(tmp_pptx, str(pdf_out), options=options)
    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0


def test_create_presentation_with_pdf_returns_dict(tmp_path):
    pptx_out = tmp_path / "api.pptx"
    result = create_presentation(SAMPLE_DATA, output_file=str(pptx_out), convert_to_pdf=True)
    # Backward-compat: dict return when convert_to_pdf=True
    assert isinstance(result, dict)
    assert "pptx" in result and "pdf" in result
    assert Path(result["pptx"]).exists()
    assert Path(result["pdf"]).exists()

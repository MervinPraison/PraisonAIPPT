"""
PraisonAI PPT - PowerPoint Bible Verses Generator

A Python package for creating beautiful PowerPoint presentations from Bible verses.
Includes built-in PDF conversion capabilities.
"""

__version__ = "1.2.0"
__author__ = "MervinPraison"
__license__ = "MIT"

from .core import create_presentation
from .loader import load_verses_from_file, load_verses_from_dict
from .pdf_converter import convert_pptx_to_pdf, PDFOptions

__all__ = [
    "create_presentation",
    "load_verses_from_file",
    "load_verses_from_dict",
    "convert_pptx_to_pdf",
    "PDFOptions",
]

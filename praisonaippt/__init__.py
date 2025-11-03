"""
PraisonAI PPT - PowerPoint Bible Verses Generator

A Python package for creating beautiful PowerPoint presentations from Bible verses.
"""

__version__ = "1.1.0"
__author__ = "MervinPraison"
__license__ = "MIT"

from .core import create_presentation
from .loader import load_verses_from_file, load_verses_from_dict

__all__ = [
    "create_presentation",
    "load_verses_from_file",
    "load_verses_from_dict",
]

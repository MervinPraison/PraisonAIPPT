"""
PraisonAI PPT - PowerPoint Bible Verses Generator

A Python package for creating beautiful PowerPoint presentations from Bible verses.
Includes built-in PDF conversion capabilities.

Single source of truth for version is ``pyproject.toml``. ``__version__`` is
read from installed package metadata, with a fallback that parses
``pyproject.toml`` for unbuilt source checkouts.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

from .core import create_presentation
from .loader import load_verses_from_file, load_verses_from_dict
from .pdf_converter import convert_pptx_to_pdf, PDFOptions, PDFConverter
from .lazy_loader import lazy_import, check_optional_dependency, LazyImportError
from .config import load_config, init_config, Config
from .pptx_to_json import pptx_to_json
# Note: gdrive_uploader uses lazy_import internally so importing the module
# (not the optional google-* deps) is always safe.
from .gdrive_uploader import upload_to_gdrive, is_gdrive_available, GDriveUploader
from .exceptions import (
    PraisonAIPPTError,
    LoaderError,
    SchemaError,
    BackendUnavailableError,
)


def _read_version() -> str:
    try:
        return _pkg_version("praisonaippt")
    except PackageNotFoundError:
        try:
            from pathlib import Path
            try:
                import tomllib  # py311+
            except ModuleNotFoundError:  # pragma: no cover - py<311
                import tomli as tomllib  # type: ignore[no-redef]
            pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
            with pyproject.open("rb") as f:
                return tomllib.load(f)["project"]["version"]
        except Exception:
            return "0.0.0"


__version__ = _read_version()
__author__ = "MervinPraison"
__license__ = "MIT"

__all__ = [
    "create_presentation",
    "load_verses_from_file",
    "load_verses_from_dict",
    "convert_pptx_to_pdf",
    "PDFConverter",
    "PDFOptions",
    "lazy_import",
    "check_optional_dependency",
    "LazyImportError",
    "load_config",
    "init_config",
    "Config",
    "pptx_to_json",
    "upload_to_gdrive",
    "is_gdrive_available",
    "GDriveUploader",
    "PraisonAIPPTError",
    "LoaderError",
    "SchemaError",
    "BackendUnavailableError",
]

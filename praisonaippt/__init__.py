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
from .loader import (
    load_deck_mapping,
    load_verses_from_file,
    load_verses_from_dict,
    write_deck_mapping,
)
from .template_resolver import list_templates, resolve_template_style, get_template_path
from .slide_renderers import register_renderer, list_renderers
from .pdf_converter import convert_pptx_to_pdf, PDFOptions, PDFConverter
from .slide_images import (
    SlideImageOptions,
    default_slide_images_dir,
    export_pptx_slide_jpegs,
    resolve_slide_images_dir,
)
from .video_exporter import VideoOptions, convert_pptx_to_video, convert_deck_to_video, resolve_video_backend
from .video_sidecar import load_deck_sidecar
from .lazy_loader import lazy_import, check_optional_dependency, LazyImportError
from .config import load_config, init_config, Config
from .pptx_to_json import pptx_to_json
from .deck_export import deck_to_markdown, write_deck_markdown
# Note: gdrive_uploader uses lazy_import internally so importing the module
# (not the optional google-* deps) is always safe.
from .gdrive_uploader import upload_to_gdrive, is_gdrive_available, GDriveUploader
from .exceptions import (
    PraisonAIPPTError,
    LoaderError,
    SchemaError,
    BackendUnavailableError,
)
from .utils import resolve_asset_path
from .avatar_calibrate import (
    AvatarFramingResult,
    calibrate_avatar_framing,
    calibrate_deck_avatars,
    maybe_auto_calibrate_deck,
)
from .hero_panel_calibrate import (
    HeroPanelResult,
    HeroTextConfig,
    calibrate_deck_hero_panels,
    calibrate_hero_panel,
    format_hero_panel_report,
    hero_text_deps_hint,
    maybe_auto_place_hero_text_deck,
)
from .slide_transition import (
    SlideTransitionConfig,
    format_transition_report,
    maybe_apply_slide_transitions_deck,
)
from .transition_backends import list_transition_backends
from .video_protocol import TransitionDefaults, resolve_edge_transitions
from .hero_panel_measure import (
    HeroPanelMetrics,
    format_hero_panel_measure_report,
    measure_hero_panel_image,
    panel_clearance_score,
    placement_advice,
    save_hero_panel_validation_diagram,
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
    "load_deck_mapping",
    "load_verses_from_file",
    "load_verses_from_dict",
    "write_deck_mapping",
    "list_templates",
    "resolve_template_style",
    "get_template_path",
    "register_renderer",
    "list_renderers",
    "convert_pptx_to_pdf",
    "PDFConverter",
    "PDFOptions",
    "SlideImageOptions",
    "export_pptx_slide_jpegs",
    "default_slide_images_dir",
    "resolve_slide_images_dir",
    "VideoOptions",
    "convert_pptx_to_video",
    "convert_deck_to_video",
    "resolve_video_backend",
    "load_deck_sidecar",
    "lazy_import",
    "check_optional_dependency",
    "LazyImportError",
    "load_config",
    "init_config",
    "Config",
    "pptx_to_json",
    "deck_to_markdown",
    "write_deck_markdown",
    "upload_to_gdrive",
    "is_gdrive_available",
    "GDriveUploader",
    "PraisonAIPPTError",
    "LoaderError",
    "SchemaError",
    "BackendUnavailableError",
    "resolve_asset_path",
    "AvatarFramingResult",
    "calibrate_avatar_framing",
    "calibrate_deck_avatars",
    "maybe_auto_calibrate_deck",
    "HeroPanelResult",
    "HeroTextConfig",
    "calibrate_deck_hero_panels",
    "calibrate_hero_panel",
    "maybe_auto_place_hero_text_deck",
    "format_hero_panel_report",
    "hero_text_deps_hint",
    "HeroPanelMetrics",
    "format_hero_panel_measure_report",
    "measure_hero_panel_image",
    "panel_clearance_score",
    "placement_advice",
    "save_hero_panel_validation_diagram",
    "SlideTransitionConfig",
    "format_transition_report",
    "maybe_apply_slide_transitions_deck",
    "list_transition_backends",
    "TransitionDefaults",
    "resolve_edge_transitions",
]

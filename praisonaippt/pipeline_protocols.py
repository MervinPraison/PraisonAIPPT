"""
Protocol-driven hooks for deck QA pipeline vs PPTX / MP4 implementations.

The pipeline orchestrates validation and optional build/export stages. Default
adapters delegate to ``core.create_presentation`` and
``video_exporter.convert_deck_to_video``; callers may inject alternates for tests
or custom backends.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, runtime_checkable

BuildFn = Callable[..., Optional[str]]
ExportFn = Callable[..., str]


@runtime_checkable
class DeckBuilder(Protocol):
    def __call__(
        self,
        data: dict,
        *,
        output_file: str,
        custom_title: Optional[str] = None,
    ) -> Optional[str]:
        ...


@runtime_checkable
class DeckVideoExporter(Protocol):
    def __call__(
        self,
        data: dict,
        pptx_path: str,
        *,
        video_options: Any,
    ) -> str:
        ...


def default_build_presentation(
    data: dict,
    *,
    output_file: str,
    custom_title: Optional[str] = None,
) -> Optional[str]:
    from .core import create_presentation

    return create_presentation(data, output_file=output_file, custom_title=custom_title)


def default_export_deck_video(
    data: dict,
    pptx_path: str,
    *,
    video_options: Any,
) -> str:
    from .video_exporter import convert_deck_to_video

    return convert_deck_to_video(data, pptx_path, video_options=video_options)

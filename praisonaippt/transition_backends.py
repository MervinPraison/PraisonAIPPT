"""Registry of slide transition backends (FFmpeg execution mapping)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class TransitionBackend(Protocol):
    name: str
    requires_reencode: bool

    def ffmpeg_xfade_name(self) -> Optional[str]:
        """FFmpeg xfade transition name, or None for segment-only backends."""
        ...


@dataclass(frozen=True)
class SegmentFadeBackend:
    name: str = "segment_fade"
    requires_reencode: bool = False

    def ffmpeg_xfade_name(self) -> Optional[str]:
        return None


@dataclass(frozen=True)
class XfadeBackend:
    name: str
    xfade_name: str
    requires_reencode: bool = True

    def ffmpeg_xfade_name(self) -> Optional[str]:
        return self.xfade_name


_REGISTRY: Dict[str, TransitionBackend] = {}


def register_transition_backend(backend: TransitionBackend) -> None:
    _REGISTRY[backend.name] = backend


def get_transition_backend(name: str) -> Optional[TransitionBackend]:
    return _REGISTRY.get(name)


def list_transition_backends() -> List[str]:
    return sorted(_REGISTRY.keys())


def known_transition_types() -> frozenset:
    return frozenset(_REGISTRY.keys()) | frozenset({"none"})


def ffmpeg_xfade_transition(edge_type: str) -> str:
    """Map YAML type to ffmpeg xfade transition= value."""
    backend = _REGISTRY.get(edge_type)
    if backend and backend.ffmpeg_xfade_name():
        return backend.ffmpeg_xfade_name()  # type: ignore[return-value]
    mapping = {
        "crossfade": "fade",
        "wipeleft": "wipeleft",
        "wiperight": "wiperight",
        "slideleft": "slideleft",
        "slideright": "slideright",
    }
    return mapping.get(edge_type, "fade")


def _register_builtins() -> None:
    _XFADE_MAP = {
        "crossfade": "fade",
        "wipeleft": "wipeleft",
        "wiperight": "wiperight",
        "slideleft": "slideleft",
        "slideright": "slideright",
    }
    register_transition_backend(SegmentFadeBackend())
    for name, xf in _XFADE_MAP.items():
        register_transition_backend(XfadeBackend(name=name, xfade_name=xf))


_register_builtins()

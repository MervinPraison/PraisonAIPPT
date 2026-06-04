"""Sync media-variant deck YAMLs from a content master."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

from .loader import load_deck_mapping
from .transcript_loader import MEDIA_VARIANTS, apply_media_variant, write_deck_yaml


def sync_variants_from_master(
    master_path: str | Path,
    output_dir: Optional[str | Path] = None,
    *,
    prefix: str = "heygen-50590",
    variants: Optional[Sequence[str]] = None,
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
) -> List[Path]:
    """Copy slide content from master YAML into variant decks with media flags."""
    master = Path(master_path)
    out_dir = Path(output_dir or master.parent)
    base = load_deck_mapping(master)
    names = list(variants or MEDIA_VARIANTS.keys())
    written: List[Path] = []
    for name in names:
        deck = apply_media_variant(
            base,
            name,
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
        )
        path = out_dir / f"{prefix}-{name}.yaml"
        write_deck_yaml(deck, path)
        written.append(path)
    return written


def _canonical_yaml(data: dict) -> str:
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=True)


def variants_drift(
    master_path: str | Path,
    output_dir: Optional[str | Path] = None,
    *,
    prefix: str = "heygen-50590",
    variants: Optional[Sequence[str]] = None,
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
) -> Tuple[bool, List[str]]:
    """Return (ok, messages). False when any variant file differs from a fresh sync."""
    master = Path(master_path)
    out_dir = Path(output_dir or master.parent)
    base = load_deck_mapping(master)
    names = list(variants or MEDIA_VARIANTS.keys())
    issues: List[str] = []
    for name in names:
        expected = apply_media_variant(
            base,
            name,
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
        )
        path = out_dir / f"{prefix}-{name}.yaml"
        if not path.is_file():
            issues.append(f"missing variant: {path.name}")
            continue
        actual = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if _canonical_yaml(expected) != _canonical_yaml(actual):
            issues.append(f"out of sync: {path.name} (run sync-variants)")
    return (len(issues) == 0, issues)

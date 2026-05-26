"""
Utility functions for the PowerPoint Bible Verses Generator.
"""

import os
import re
from pathlib import Path
from typing import Optional, Union


def resolve_asset_path(
    path: Union[str, Path],
    *,
    source_file: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """
    Resolve an image or asset path for deck YAML/JSON.

    Tries, in order: absolute path, path relative to the input file's directory,
    current working directory, then the package repo root (parent of ``praisonaippt``).
    """
    if not path:
        return None

    raw = Path(path).expanduser()
    if raw.is_absolute() and raw.is_file():
        return str(raw.resolve())

    candidates = []
    if source_file:
        candidates.append(Path(source_file).resolve().parent / raw)
    candidates.append(Path.cwd() / raw)
    pkg_root = Path(__file__).resolve().parent.parent
    candidates.append(pkg_root / raw)

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())

    # Last resort: return absolute-normalised path (caller may warn if missing)
    if raw.is_absolute():
        return str(raw)
    return str((Path.cwd() / raw).resolve())


def split_long_text(text, max_length=200):
    """
    Split long text into multiple parts at sentence boundaries.
    
    Args:
        text (str): The text to split
        max_length (int): Maximum length for each part (default: 200)
    
    Returns:
        list: List of text parts
    """
    if len(text) <= max_length:
        return [text]
    
    # Split at sentences first
    sentences = text.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
    parts = []
    current_part = ""
    
    for sentence in sentences:
        if len(current_part + sentence) <= max_length:
            current_part += sentence
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = sentence
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts if parts else [text]


def sanitize_filename(filename):
    """
    Clean filename by removing or replacing invalid characters.
    
    Args:
        filename (str): The filename to sanitize
    
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

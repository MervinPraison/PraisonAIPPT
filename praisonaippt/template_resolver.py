"""Resolve extendable YAML theme templates (SDK-style inheritance)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from .exceptions import SchemaError

_STYLE_KEYS = frozenset({"slide_style", "slide_size", "auto_upload_gdrive"})
_META_KEYS = frozenset({"name", "description", "source_example", "extends", "template"})
_MAX_EXTENDS_DEPTH = 32


def _package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _user_templates_dir() -> Path:
    return Path.home() / ".praisonaippt" / "templates"


def _builtin_templates_dir() -> Path:
    return _package_root() / "templates"


def _deep_merge(base: Any, override: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_mapping(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SchemaError(f"Template file must be a mapping: {path}")
    return data


def _style_slice(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: data[k] for k in _STYLE_KEYS if k in data}


def _resolve_path(ref: str, base_dir: Path) -> Path:
    candidate = Path(ref)
    if candidate.is_file():
        return candidate.resolve()
    from_base = (base_dir / ref).resolve()
    if from_base.is_file():
        return from_base
    name = candidate.stem if candidate.suffix else ref
    found = get_template_path(name, base_dir=base_dir)
    if found:
        return Path(found)
    raise SchemaError(f"Template not found: {ref}")


def get_template_path(name: str, base_dir: Optional[Path] = None) -> Optional[str]:
    """Resolve a template name or path to an existing file."""
    if not name:
        return None

    candidate = Path(name)
    if candidate.is_file():
        return str(candidate.resolve())

    # Explicit path next to the deck (e.g. ./themes/custom.yaml), not bare theme names.
    if base_dir is not None and (candidate.suffix or "/" in name or "\\" in name):
        from_base = (base_dir / name).resolve()
        if from_base.is_file():
            return str(from_base)

    for directory in (_user_templates_dir(), _builtin_templates_dir()):
        if not directory.is_dir():
            continue
        if candidate.suffix:
            path = directory / candidate.name
            if path.is_file():
                return str(path.resolve())
        for ext in (".yaml", ".yml", ".json"):
            path = directory / f"{name}{ext}"
            if path.is_file():
                return str(path.resolve())

    return None


def _resolve_theme_file(path: Path, visited: Optional[Set[Path]] = None) -> Dict[str, Any]:
    visited = visited or set()
    resolved = path.resolve()
    if resolved in visited:
        raise SchemaError(f"Circular template extends chain at: {path}")
    if len(visited) >= _MAX_EXTENDS_DEPTH:
        raise SchemaError("Template extends chain too deep")
    visited.add(resolved)

    data = _load_mapping(resolved)
    extends = data.get("extends")
    style_data = _style_slice(data)

    if extends:
        parent_path = _resolve_path(str(extends), resolved.parent)
        parent_style = _resolve_theme_file(parent_path, visited)
        style_data = _deep_merge(parent_style, style_data)

    return style_data


def resolve_template_style(name: str, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load a template by name and resolve its full style (extends chain)."""
    path_str = get_template_path(name, base_dir=base_dir)
    if not path_str:
        raise SchemaError(f"Template not found: {name}")
    return _resolve_theme_file(Path(path_str))


def _expand_slide_style_preset(slide_style: Dict[str, Any], base_dir: Optional[Path]) -> Dict[str, Any]:
    style = dict(slide_style or {})
    preset = style.pop("preset", None)
    overrides = style.pop("overrides", None)

    merged: Dict[str, Any] = {}
    if preset:
        preset_resolved = resolve_template_style(str(preset), base_dir=base_dir)
        merged = _deep_merge(merged, preset_resolved.get("slide_style") or {})

    merged = _deep_merge(merged, style)
    if overrides and isinstance(overrides, dict):
        merged = _deep_merge(merged, overrides)
    return merged


def apply_template_layers(
    data: Dict[str, Any],
    deck_path: Optional[Path] = None,
    cli_template: Optional[str] = None,
) -> Dict[str, Any]:
    """Merge template, extends, preset, and inline slide_style into deck data."""
    if not isinstance(data, dict):
        return data

    deck_dir = deck_path.parent if deck_path else Path.cwd()
    result = dict(data)

    file_style: Dict[str, Any] = {}

    deck_template = result.pop("template", None)
    template_ref = cli_template or deck_template
    if template_ref:
        tpl_path = get_template_path(str(template_ref), base_dir=deck_dir)
        if not tpl_path:
            raise SchemaError(f"Template not found: {template_ref}")
        file_style = _deep_merge(file_style, _resolve_theme_file(Path(tpl_path)))

    extends_ref = result.pop("extends", None)
    if extends_ref:
        ext_path = _resolve_path(str(extends_ref), deck_dir)
        file_style = _deep_merge(file_style, _resolve_theme_file(ext_path))

    merged_slide_style = False
    for key in _STYLE_KEYS:
        if key not in file_style:
            continue
        if key == "slide_style":
            merged_slide_style = True
            existing = result.get("slide_style")
            if isinstance(existing, dict):
                expanded = _expand_slide_style_preset(existing, deck_dir)
                result["slide_style"] = _deep_merge(file_style.get("slide_style") or {}, expanded)
            else:
                result["slide_style"] = dict(file_style.get("slide_style") or {})
        else:
            if key not in result:
                result[key] = file_style[key]

    if not merged_slide_style and isinstance(result.get("slide_style"), dict):
        result["slide_style"] = _expand_slide_style_preset(result["slide_style"], deck_dir)

    return result


def list_templates() -> List[Dict[str, str]]:
    """List discoverable templates (user dir first, then built-in)."""
    seen: Set[str] = set()
    entries: List[Dict[str, str]] = []

    for directory in (_user_templates_dir(), _builtin_templates_dir()):
        if not directory.is_dir():
            continue
        for path in (
            sorted(directory.glob("*.yaml"))
            + sorted(directory.glob("*.yml"))
            + sorted(directory.glob("*.json"))
        ):
            if path.name.lower() == "readme.md":
                continue
            stem = path.stem
            if stem in seen:
                continue
            seen.add(stem)
            meta: Dict[str, str] = {"name": stem, "path": str(path)}
            try:
                raw = _load_mapping(path)
                if raw.get("description"):
                    meta["description"] = str(raw["description"])
                if raw.get("extends"):
                    meta["extends"] = str(raw["extends"])
            except (SchemaError, OSError, yaml.YAMLError, json.JSONDecodeError):
                pass
            entries.append(meta)

    return entries

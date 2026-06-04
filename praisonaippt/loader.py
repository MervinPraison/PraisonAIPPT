"""
Data loading and validation functions for Bible verses.
"""

import json
import yaml
from pathlib import Path

from .exceptions import SchemaError
from .schema import validate_verses
from .template_resolver import apply_template_layers


def deck_file_format(filepath: str | Path) -> str:
    """Return ``json`` or ``yaml`` from the file suffix (default yaml)."""
    ext = Path(filepath).suffix.lower()
    return "json" if ext == ".json" else "yaml"


def load_deck_mapping(filepath: str | Path) -> dict:
    """
    Parse a deck file to a dict (no template merge or schema validation).

    Use :func:`load_verses_from_file` for full load + validate.
    """
    file_path = Path(filepath)
    with open(file_path, encoding="utf-8") as f:
        if file_path.suffix.lower() == ".json":
            data = json.load(f)
        elif file_path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            text = f.read()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Top level of '{filepath}' must be a mapping")
    return data


def write_deck_mapping(filepath: str | Path, data: dict) -> None:
    """Write deck dict using JSON or YAML based on the path suffix."""
    path = Path(filepath)
    payload = {k: v for k, v in data.items() if not str(k).startswith("_")}
    if path.suffix.lower() == ".json":
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        path.write_text(
            yaml.dump(payload, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )


def load_verses_from_file(filepath, template=None):
    """
    Load verses data from a JSON or YAML file.

    Args:
        filepath (str): Path to the JSON or YAML file
        template (str, optional): Theme template name or path (--template)

    Returns:
        dict: Verses data dictionary, or None if error
    """
    try:
        file_path = Path(filepath)
        file_extension = file_path.suffix.lower()

        try:
            data = load_deck_mapping(filepath)
        except ValueError as e:
            print(f"Error: Invalid format in '{filepath}': {e}")
            return None
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            print(f"Error: Invalid format in '{filepath}': {e}")
            return None

        if not isinstance(data, dict):
            print(f"Error: Invalid format in '{filepath}': top level must be a mapping")
            return None

        try:
            data = apply_template_layers(data, deck_path=file_path, cli_template=template)
        except SchemaError as e:
            print(f"Error: Template resolution failed for '{filepath}': {e}")
            return None

        # Validate (warns on unknown keys; raises SchemaError on hard issues)
        try:
            data = validate_verses(data)
        except SchemaError as e:
            print(f"Error: Invalid schema in '{filepath}': {e}")
            return None

        data["_source_file"] = str(file_path.resolve())
        return data

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"Error: Invalid format in '{filepath}': {e}")
        return None
    except Exception as e:
        print(f"Error loading file '{filepath}': {e}")
        return None


def load_verses_from_dict(data):
    """
    Load verses data from a dictionary (for programmatic use).

    Raises:
        SchemaError: If ``data`` does not match the verses schema.

    Args:
        data (dict): Verses data dictionary

    Returns:
        dict: Validated verses data dictionary
    """
    return validate_verses(data)


def get_example_path(example_name):
    """
    Get the full path to an example file.

    Args:
        example_name (str): Name of the example file (with or without extension)

    Returns:
        str: Full path to the example file, or None if not found
    """
    package_dir = Path(__file__).parent.parent
    examples_dir = package_dir / 'examples'

    if not any(example_name.endswith(ext) for ext in ['.json', '.yaml', '.yml']):
        for ext in ['.yaml', '.yml', '.json']:
            example_path = examples_dir / (example_name + ext)
            if example_path.exists():
                return str(example_path)
    else:
        example_path = examples_dir / example_name
        if example_path.exists():
            return str(example_path)

    return None


def list_examples():
    """
    List all available example files.

    Returns YAML files preferentially when both YAML and JSON exist for the same stem.

    Returns:
        list: List of example filenames (preferring .yaml over .json)
    """
    package_dir = Path(__file__).parent.parent
    examples_dir = package_dir / 'examples'

    if not examples_dir.exists():
        return []

    stems = {}
    for ext in ['.yaml', '.yml', '.json']:
        for f in examples_dir.glob(f'*{ext}'):
            if f.stem not in stems:
                stems[f.stem] = []
            stems[f.stem].append(ext)

    result = []
    for stem, exts in stems.items():
        if '.yaml' in exts:
            result.append(f"{stem}.yaml")
        elif '.yml' in exts:
            result.append(f"{stem}.yml")
        else:
            result.append(f"{stem}.json")

    return sorted(result)

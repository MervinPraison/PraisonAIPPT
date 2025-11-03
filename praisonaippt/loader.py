"""
Data loading and validation functions for Bible verses.
"""

import json
import yaml
from pathlib import Path


def load_verses_from_file(filepath):
    """
    Load verses data from a JSON or YAML file.
    
    Args:
        filepath (str): Path to the JSON or YAML file
    
    Returns:
        dict: Verses data dictionary, or None if error
    """
    try:
        file_path = Path(filepath)
        file_extension = file_path.suffix.lower()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            # Detect file format and load accordingly
            if file_extension in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif file_extension == '.json':
                data = json.load(f)
            else:
                # Try to auto-detect format
                content = f.read()
                f.seek(0)
                try:
                    # Try YAML first (more forgiving)
                    data = yaml.safe_load(content)
                except yaml.YAMLError:
                    # Fall back to JSON
                    data = json.loads(content)
        
        # Basic validation
        if not isinstance(data, dict):
            print("Error: File must contain an object/dictionary")
            return None
        
        if "sections" not in data:
            print("Warning: No 'sections' key found in file")
            data["sections"] = []
        
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
    
    Args:
        data (dict): Verses data dictionary
    
    Returns:
        dict: Validated verses data dictionary
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    if "sections" not in data:
        data["sections"] = []
    
    return data


def get_example_path(example_name):
    """
    Get the full path to an example file.
    
    Args:
        example_name (str): Name of the example file (with or without extension)
    
    Returns:
        str: Full path to the example file, or None if not found
    """
    # Get the package directory
    package_dir = Path(__file__).parent.parent
    examples_dir = package_dir / 'examples'
    
    # If no extension, try YAML first, then JSON
    if not any(example_name.endswith(ext) for ext in ['.json', '.yaml', '.yml']):
        # Try YAML first
        for ext in ['.yaml', '.yml', '.json']:
            example_path = examples_dir / (example_name + ext)
            if example_path.exists():
                return str(example_path)
    else:
        # Extension provided, use as-is
        example_path = examples_dir / example_name
        if example_path.exists():
            return str(example_path)
    
    return None


def list_examples():
    """
    List all available example files.
    
    Returns:
        list: List of example filenames
    """
    package_dir = Path(__file__).parent.parent
    examples_dir = package_dir / 'examples'
    
    if not examples_dir.exists():
        return []
    
    examples = [f.name for f in examples_dir.glob('*.json')]
    return sorted(examples)

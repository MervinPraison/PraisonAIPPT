"""
Data loading and validation functions for Bible verses.
"""

import json
from pathlib import Path


def load_verses_from_file(filepath):
    """
    Load verses data from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
    
    Returns:
        dict: Verses data dictionary, or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation
        if not isinstance(data, dict):
            print("Error: JSON file must contain an object/dictionary")
            return None
        
        if "sections" not in data:
            print("Warning: No 'sections' key found in JSON file")
            data["sections"] = []
        
        return data
    
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{filepath}': {e}")
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
        example_name (str): Name of the example file (with or without .json)
    
    Returns:
        str: Full path to the example file, or None if not found
    """
    # Add .json extension if not present
    if not example_name.endswith('.json'):
        example_name += '.json'
    
    # Get the package directory
    package_dir = Path(__file__).parent.parent
    examples_dir = package_dir / 'examples'
    
    example_path = examples_dir / example_name
    
    if example_path.exists():
        return str(example_path)
    else:
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

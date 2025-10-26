"""
Utility functions for the PowerPoint Bible Verses Generator.
"""

import re


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

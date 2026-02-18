"""
Module: filename
Purpose: Filename and path building utilities for YT Transcriber
Created: 2026-01-28
Session: yt_trans_20260128_001 | Context: 1
"""
import re
from pathlib import Path
from typing import Optional

# Import from shared utils - falls back to local implementation if not installed
try:
    from gzpqb_utils import sanitize_for_filename, expand_path
except ImportError:
    # Fallback implementations
    def sanitize_for_filename(text: str, max_length: int = 50, replacement: str = "_") -> str:
        if not text:
            return "untitled"
        clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)
        clean = re.sub(r'[^\w\s-]', '', clean)
        clean = re.sub(r'\s+', replacement, clean.strip())
        clean = re.sub(f'{re.escape(replacement)}+', replacement, clean)
        clean = clean.strip(replacement)
        if len(clean) > max_length:
            clean = clean[:max_length].rstrip(replacement)
        return clean or "untitled"
    
    def expand_path(path):
        import os
        path = str(path)
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        return Path(path).resolve()


def build_filename(author: str, topic: str, year: str, max_length: int = 50) -> str:
    """
    Build filename from author, topic, and year.
    
    Pattern: {Author}_{Topic}_{Year}
    
    Each component is sanitized individually, then combined.
    Total length is managed to stay under reasonable limits.
    
    Args:
        author: Author/speaker name
        topic: Video topic
        year: 4-digit year
        max_length: Max length for topic component (author and year not limited)
    
    Returns:
        Filename without extension, e.g. "Jordan_Peterson_Maps_of_Meaning_2017"
    """
    # Sanitize components
    clean_author = sanitize_for_filename(author, max_length=30)
    clean_topic = sanitize_for_filename(topic, max_length=max_length)
    clean_year = sanitize_for_filename(year, max_length=4)
    
    # Combine
    return f"{clean_author}_{clean_topic}_{clean_year}"


def build_output_path(
    base_dir: str | Path,
    author: str,
    filename: str,
    extension: str
) -> Path:
    """
    Build full output path with author subfolder.
    
    Structure: {base_dir}/{Author}/{filename}.{ext}
    
    Creates author subfolder if it doesn't exist.
    
    Args:
        base_dir: Base output directory (may contain ~)
        author: Author name (used for subfolder)
        filename: Base filename (without extension)
        extension: File extension (without dot)
    
    Returns:
        Full Path object, with parent directories created
    """
    # Expand base directory
    base = expand_path(base_dir)
    
    # Create author subfolder name
    author_folder = sanitize_for_filename(author, max_length=50)
    
    # Build path
    output_dir = base / author_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure extension doesn't have leading dot
    extension = extension.lstrip('.')
    
    return output_dir / f"{filename}.{extension}"


def generate_unique_filename(
    base_dir: str | Path,
    author: str,
    topic: str,
    year: str,
    extension: str
) -> Path:
    """
    Generate unique filename, adding suffix if file exists.
    
    If {Author}_{Topic}_{Year}.ext exists, tries:
        {Author}_{Topic}_{Year}_2.ext
        {Author}_{Topic}_{Year}_3.ext
        etc.
    
    Returns:
        Path to a non-existing file
    """
    filename = build_filename(author, topic, year)
    path = build_output_path(base_dir, author, filename, extension)
    
    if not path.exists():
        return path
    
    # Add numeric suffix
    counter = 2
    while True:
        numbered_filename = f"{filename}_{counter}"
        path = build_output_path(base_dir, author, numbered_filename, extension)
        if not path.exists():
            return path
        counter += 1
        if counter > 100:  # Safety limit
            raise ValueError(f"Too many files with same name: {filename}")

"""Utility functions used across the project."""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import yaml
import os


def ensure_directory(path: str) -> Path:
    """Ensure a directory exists, create if it doesn't."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_file_safe(path: str) -> Optional[str]:
    """Safely read a file, return None if it doesn't exist."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return None


def write_file_safe(path: str, content: str) -> bool:
    """Safely write to a file."""
    try:
        ensure_directory(str(Path(path).parent))
        with open(path, 'w') as f:
            f.write(content)
        return True
    except:
        return False


def load_json_safe(path: str) -> Optional[Dict]:
    """Safely load JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None


def load_yaml_safe(path: str) -> Optional[Dict]:
    """Safely load YAML file."""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except:
        return None


def list_files(directory: str, extension: Optional[str] = None) -> List[Path]:
    """List files in directory, optionally filtered by extension."""
    path = Path(directory)
    if not path.exists():
        return []
    if extension:
        return list(path.glob(f"*{extension}"))
    return list(path.iterdir())


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    value = os.environ.get(key, str(default)).lower()
    return value in ('true', 'yes', 'on', '1')


def get_env_int(key: str, default: int = 0) -> int:
    """Get integer from environment variable."""
    try:
        return int(os.environ.get(key, str(default)))
    except:
        return default


__all__ = [
    'ensure_directory',
    'read_file_safe',
    'write_file_safe',
    'load_json_safe',
    'load_yaml_safe',
    'list_files',
    'get_env_bool',
    'get_env_int',
]

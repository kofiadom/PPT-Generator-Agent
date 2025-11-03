"""
Utility functions for the PPTX workflow.

This module provides helper functions for file operations, path management,
and common workflow tasks.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def ensure_workspace(workspace_dir: str) -> Path:
    """
    Ensure workspace directory exists with all stage subdirectories.
    
    Args:
        workspace_dir: Path to workspace directory
    
    Returns:
        Path object for workspace directory
    """
    workspace = Path(workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create stage directories
    stage_dirs = [
        "stage0-template-intake",
        "stage0-source-intake",
        "stage1-extract",
        "stage2-analyze",
        "stage3-outline",
        "stage4-rearrange",
        "stage5-inventory",
        "stage6-replacement",
        "stage7-final",
    ]
    
    for stage_dir in stage_dirs:
        (workspace / stage_dir).mkdir(parents=True, exist_ok=True)
    
    return workspace


def copy_file(source: str, destination: str) -> None:
    """
    Copy a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
    """
    src = Path(source)
    dst = Path(destination)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    
    # Ensure destination directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    shutil.copy2(src, dst)


def read_json(file_path: str) -> Dict[str, Any]:
    """
    Read JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed JSON data
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """
    Write JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to write
        indent: JSON indentation level
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_text(file_path: str) -> str:
    """
    Read text file.
    
    Args:
        file_path: Path to text file
    
    Returns:
        File contents
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")
    
    return path.read_text(encoding='utf-8')


def write_text(file_path: str, content: str) -> None:
    """
    Write text file.
    
    Args:
        file_path: Path to text file
        content: Content to write
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def format_command(cmd: List[str], replacements: Dict[str, str]) -> List[str]:
    """
    Format command with placeholder replacements.
    
    Args:
        cmd: Command array with placeholders like {workspace}
        replacements: Dictionary of placeholder -> value mappings
    
    Returns:
        Formatted command array
    """
    formatted = []
    for part in cmd:
        for key, value in replacements.items():
            part = part.replace(f"{{{key}}}", str(value))
        formatted.append(part)
    return formatted


def get_stage_paths(workspace_dir: str) -> Dict[str, Path]:
    """
    Get paths for all stage directories.
    
    Args:
        workspace_dir: Workspace directory path
    
    Returns:
        Dictionary mapping stage names to Path objects
    """
    workspace = Path(workspace_dir)
    
    return {
        "template_intake": workspace / "stage0-template-intake",
        "source_intake": workspace / "stage0-source-intake",
        "extract": workspace / "stage1-extract",
        "analyze": workspace / "stage2-analyze",
        "outline": workspace / "stage3-outline",
        "rearrange": workspace / "stage4-rearrange",
        "inventory": workspace / "stage5-inventory",
        "replacement": workspace / "stage6-replacement",
        "final": workspace / "stage7-final",
    }


def log_stage_start(stage: str) -> None:
    """Log stage start."""
    timestamp = datetime.utcnow().isoformat()
    print(f"\n{'='*60}")
    print(f"[{timestamp}] Starting: {stage}")
    print(f"{'='*60}")


def log_stage_complete(stage: str) -> None:
    """Log stage completion."""
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] ✅ Completed: {stage}")


def log_stage_error(stage: str, error: str) -> None:
    """Log stage error."""
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] ❌ Failed: {stage}")
    print(f"Error: {error}")


def validate_file_exists(file_path: str, description: str = "File") -> None:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to file
        description: Description for error message
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in bytes
    """
    path = Path(file_path)
    if not path.exists():
        return 0
    return path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
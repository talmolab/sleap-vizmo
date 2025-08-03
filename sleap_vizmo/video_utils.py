"""Utility functions for extracting video metadata from SLEAP labeled frames."""

import re
from pathlib import Path, WindowsPath, PosixPath
from typing import Optional, Any


def extract_video_name(labeled_frame: Any) -> str:
    """
    Extract video name from a SLEAP labeled frame.

    Handles various formats of video.filename including:
    - Direct string paths
    - Path objects
    - Lists of Path objects
    - String representations of lists (e.g., "[WindowsPath('...'')]")

    Args:
        labeled_frame: A SLEAP labeled frame object

    Returns:
        The video name (stem without extension) or "unknown" if extraction fails
    """
    if not hasattr(labeled_frame, "video"):
        return "unknown"

    # Note: Don't check "if not labeled_frame.video" because Video objects might evaluate to False

    # Try to get filename from video object
    filename = None

    # Try direct filename attribute first
    if hasattr(labeled_frame.video, "filename"):
        filename = labeled_frame.video.filename
    # Try backend.filename as fallback
    elif hasattr(labeled_frame.video, "backend") and hasattr(
        labeled_frame.video.backend, "filename"
    ):
        filename = labeled_frame.video.backend.filename

    if not filename:
        return "unknown"

    # Now parse the filename which could be in various formats
    return parse_video_filename(filename)


def parse_video_filename(filename: Any) -> str:
    """
    Parse a filename that could be in various formats.

    Args:
        filename: The filename in any of these formats:
            - String path: "/path/to/video.mp4"
            - Path object: Path("/path/to/video.mp4")
            - List of paths: [Path("/path/to/video.mp4")]
            - String representation of list: "[WindowsPath('/path/to/video.mp4')]"

    Returns:
        The filename stem (without extension) or "unknown"
    """
    if not filename:
        return "unknown"

    # Check if it's a list first (before checking Path, since list might contain Path objects)
    if isinstance(filename, list):
        if len(filename) > 0:
            return parse_video_filename(filename[0])
        return "unknown"

    # If it's a Path object (including WindowsPath, PosixPath), extract stem
    if isinstance(filename, (Path, WindowsPath, PosixPath)):
        return filename.stem

    # Check if it's a string type
    if not isinstance(filename, str):
        # For non-string, non-Path types (like integers), return unknown
        return "unknown"

    # Convert to string for further processing
    filename_str = str(filename)

    # Check if it's a string representation of a list like "[WindowsPath('...')]"
    # This regex extracts the path from patterns like:
    # "[WindowsPath('C:/path/to/file.mp4')]"
    # "[PosixPath('/path/to/file.mp4')]"
    # "[Path('/path/to/file.mp4')]"
    list_pattern = r"\[(Windows|Posix)?Path\(['\"](.*?)['\"]\)\]"
    match = re.match(list_pattern, filename_str)
    if match:
        # Extract the actual path from the string representation
        path_str = match.group(2)
        return Path(path_str).stem

    # Check for malformed string representations
    if filename_str.startswith("[WindowsPath(") or filename_str.startswith(
        "[PosixPath("
    ):
        # Malformed representation without closing
        return "unknown"

    # If it's a regular string path, convert to Path and get stem
    try:
        path = Path(filename_str)
        if path.stem:  # Ensure there's actually a stem
            return path.stem
        return "unknown"
    except Exception:
        return "unknown"


def get_video_info(labeled_frame: Any) -> dict:
    """
    Extract comprehensive video information from a labeled frame.

    Args:
        labeled_frame: A SLEAP labeled frame object

    Returns:
        Dictionary containing:
            - name: Video name (stem)
            - full_path: Full path as POSIX string
            - filename_type: Type of filename format detected
            - frame_idx: Frame index if available
    """
    info = {
        "name": "unknown",
        "full_path": None,
        "filename_type": "unknown",
        "frame_idx": None,
    }

    if not hasattr(labeled_frame, "video"):
        return info

    # Note: Don't check "if not labeled_frame.video" because Video objects might evaluate to False

    # Get frame index if available
    if hasattr(labeled_frame, "frame_idx"):
        info["frame_idx"] = labeled_frame.frame_idx

    # Try to get filename
    filename = None
    source = None

    if hasattr(labeled_frame.video, "filename"):
        filename = labeled_frame.video.filename
        source = "video.filename"
    elif hasattr(labeled_frame.video, "backend") and hasattr(
        labeled_frame.video.backend, "filename"
    ):
        filename = labeled_frame.video.backend.filename
        source = "video.backend.filename"

    if not filename:
        return info

    # Determine filename type - check list first
    if isinstance(filename, list):
        info["filename_type"] = f"List of {len(filename)} items"
        if len(filename) > 0:
            info["name"] = parse_video_filename(filename[0])
            if isinstance(filename[0], (Path, WindowsPath, PosixPath)):
                info["full_path"] = filename[0].as_posix()
    elif isinstance(filename, (Path, WindowsPath, PosixPath)):
        info["filename_type"] = "Path object"
        info["full_path"] = filename.as_posix()
        info["name"] = filename.stem
    elif isinstance(filename, str):
        # Check if it's a string representation of a list
        if filename.startswith("[") and "Path(" in filename:
            info["filename_type"] = "String representation of Path list"
            info["name"] = parse_video_filename(filename)
            # Extract path for full_path
            match = re.search(r"Path\(['\"](.*?)['\"]\)", filename)
            if match:
                info["full_path"] = Path(match.group(1)).as_posix()
        else:
            info["filename_type"] = "String path"
            info["name"] = Path(filename).stem
            info["full_path"] = Path(filename).as_posix()
    else:
        info["filename_type"] = f"Unknown type: {type(filename)}"
        info["name"] = parse_video_filename(filename)

    return info

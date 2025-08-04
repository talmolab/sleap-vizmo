"""Utilities for SLEAP-roots pipeline detection and management."""
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import sleap_io as sio


def detect_root_types(file_configs: List[Dict]) -> Dict[str, bool]:
    """
    Detect which root types are present in the loaded files.
    
    Args:
        file_configs: List of dictionaries with 'root_type' key
        
    Returns:
        Dictionary with keys 'primary', 'lateral', 'crown' and boolean values
    """
    root_types = {"primary": False, "lateral": False, "crown": False}
    
    for config in file_configs:
        if "root_type" in config and config["root_type"] in root_types:
            root_types[config["root_type"]] = True
    
    return root_types


def get_compatible_pipelines(root_types: Dict[str, bool]) -> List[Tuple[str, str]]:
    """
    Determine compatible SLEAP-roots pipelines based on detected root types.
    
    Args:
        root_types: Dictionary with 'primary', 'lateral', 'crown' boolean values
        
    Returns:
        List of tuples (pipeline_class_name, description)
    """
    compatible_pipelines = []
    
    # Single root type pipelines
    if root_types["primary"] and not root_types["lateral"] and not root_types["crown"]:
        compatible_pipelines = [
            ("PrimaryRootPipeline", "Primary root analysis"),
        ]
    elif root_types["lateral"] and not root_types["primary"] and not root_types["crown"]:
        compatible_pipelines = [
            ("LateralRootPipeline", "Lateral roots only")
        ]
    elif root_types["crown"] and not root_types["primary"] and not root_types["lateral"]:
        compatible_pipelines = [
            ("OlderMonocotPipeline", "Older monocot (crown roots only)")
        ]
    # Multiple root type pipelines
    elif root_types["primary"] and root_types["lateral"] and not root_types["crown"]:
        compatible_pipelines = [
            ("DicotPipeline", "Single dicot plant (primary + lateral)"),
            ("MultipleDicotPipeline", "Multiple dicot plants (primary + lateral)"),
        ]
    elif root_types["primary"] and root_types["crown"] and not root_types["lateral"]:
        compatible_pipelines = [
            ("YoungerMonocotPipeline", "Young monocot (primary + crown)")
        ]
    
    return compatible_pipelines


def combine_labels_from_configs(file_configs: List[Dict]) -> Optional[sio.Labels]:
    """
    Combine labels from multiple file configurations into a single Labels object.
    
    Args:
        file_configs: List of dictionaries with 'labels' key containing sleap_io.Labels
        
    Returns:
        Combined Labels object or None if no valid labels
    """
    if not file_configs:
        return None
        
    all_labeled_frames = []
    all_videos = []
    skeleton = None
    all_tracks = []
    
    for config in file_configs:
        if "labels" not in config or config["labels"] is None:
            continue
            
        labels = config["labels"]
        
        # Get skeleton from first valid labels
        if skeleton is None and labels.skeleton:
            skeleton = labels.skeleton
        
        # Collect all labeled frames
        all_labeled_frames.extend(labels.labeled_frames)
        
        # Collect unique videos
        for video in labels.videos:
            if video not in all_videos:
                all_videos.append(video)
        
        # Collect unique tracks
        for track in labels.tracks:
            if track not in all_tracks:
                all_tracks.append(track)
    
    if not all_labeled_frames:
        return None
    
    # Create combined labels
    combined_labels = sio.Labels(
        labeled_frames=all_labeled_frames,
        videos=all_videos,
        skeletons=[skeleton] if skeleton else [],
        tracks=all_tracks
    )
    
    return combined_labels


def get_file_summary(file_configs: List[Dict]) -> Dict[str, List[str]]:
    """
    Generate a summary of loaded files grouped by root type.
    
    Args:
        file_configs: List of dictionaries with 'path' and 'root_type' keys
        
    Returns:
        Dictionary mapping root types to lists of file names
    """
    summary = {"primary": [], "lateral": [], "crown": []}
    
    for config in file_configs:
        if "root_type" in config and "path" in config:
            root_type = config["root_type"]
            if root_type in summary:
                file_name = Path(config["path"]).name if isinstance(config["path"], (str, Path)) else str(config["path"])
                summary[root_type].append(file_name)
    
    return summary


def validate_file_config(
    file_path: Union[str, Path], 
    root_type: str
) -> Tuple[bool, str, Optional[sio.Labels]]:
    """
    Validate a single file configuration.
    
    Args:
        file_path: Path to the .slp file
        root_type: Root type ('primary', 'lateral', or 'crown')
        
    Returns:
        Tuple of (is_valid, message, labels_or_none)
    """
    valid_root_types = {"primary", "lateral", "crown"}
    
    if not file_path:
        return False, "No file path provided", None
    
    if root_type not in valid_root_types:
        return False, f"Invalid root type: {root_type}", None
    
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {file_path}", None
        
        if path.suffix != ".slp":
            return False, f"Not a .slp file: {file_path}", None
        
        # Try to load the file
        labels = sio.load_slp(str(path))
        
        # Basic validation
        if not labels.labeled_frames:
            return False, f"No labeled frames in {path.name}", None
        
        return True, f"Valid file with {len(labels.labeled_frames)} frames", labels
        
    except Exception as e:
        return False, f"Error loading file: {str(e)}", None
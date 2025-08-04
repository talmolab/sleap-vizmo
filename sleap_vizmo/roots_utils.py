"""Utilities for SLEAP-roots Series compatibility and multi-video label handling."""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sleap_io as sio
from sleap_io.model.labels import Labels
from sleap_io.model.video import Video
from .video_utils import extract_video_name


def get_videos_in_labels(labels: Labels) -> List[Tuple[str, Video]]:
    """
    Get all unique videos in a labels object.

    Args:
        labels: SLEAP labels object

    Returns:
        List of tuples (video_name, video_object)
    """
    videos = []

    if hasattr(labels, "videos") and labels.videos:
        for video in labels.videos:
            # Create a mock labeled frame to use extract_video_name
            mock_lf = type("obj", (object,), {"video": video})()
            video_name = extract_video_name(mock_lf)
            videos.append((video_name, video))

    return videos


def split_labels_by_video(labels: Labels) -> Dict[str, Labels]:
    """
    Split multi-video labels into individual video labels.

    Args:
        labels: SLEAP labels object potentially containing multiple videos

    Returns:
        Dictionary mapping video names to Labels objects containing only
        frames from that video
    """
    video_labels = {}

    # Get all videos
    videos = get_videos_in_labels(labels)

    # If no videos or single video, return as-is
    if len(videos) <= 1:
        if videos:
            video_name = videos[0][0]
        else:
            video_name = "unknown"
        return {video_name: labels}

    # Create a mapping of video objects to names
    video_to_name = {video: name for name, video in videos}

    # Group labeled frames by video
    for video_name, video in videos:
        # Create new labels object for this video
        video_specific_labels = Labels()

        # Copy skeletons (all videos share the same skeletons)
        if hasattr(labels, "skeletons"):
            video_specific_labels.skeletons = labels.skeletons

        # Copy tracks if present
        if hasattr(labels, "tracks") and labels.tracks:
            video_specific_labels.tracks = labels.tracks

        # Add only this video
        video_specific_labels.videos = [video]

        # Filter labeled frames for this video
        video_frames = []
        if hasattr(labels, "labeled_frames"):
            for lf in labels.labeled_frames:
                if hasattr(lf, "video") and lf.video == video:
                    video_frames.append(lf)

        video_specific_labels.labeled_frames = video_frames

        # Copy provenance if exists
        if hasattr(labels, "provenance"):
            video_specific_labels.provenance = labels.provenance.copy()
            # Update filename in provenance to reflect the specific video
            if "filename" in video_specific_labels.provenance:
                orig_path = Path(video_specific_labels.provenance["filename"])
                new_filename = f"{orig_path.stem}_{video_name}{orig_path.suffix}"
                video_specific_labels.provenance["filename"] = str(new_filename)

        video_labels[video_name] = video_specific_labels

    return video_labels


def save_individual_video_labels(
    labels: Labels,
    output_dir: Path,
    prefix: str = "",
    suffix: str = "",
) -> Dict[str, Path]:
    """
    Save each video's labels as separate files.

    Args:
        labels: SLEAP labels object potentially containing multiple videos
        output_dir: Directory to save individual video files
        prefix: Prefix to add to filenames (e.g., "plant_")
        suffix: Suffix to add before extension (e.g., "_primary")

    Returns:
        Dictionary mapping video names to saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split labels by video
    video_labels = split_labels_by_video(labels)

    saved_paths = {}

    for video_name, video_specific_labels in video_labels.items():
        # Construct filename
        filename = f"{prefix}{video_name}{suffix}.slp"
        file_path = output_dir / filename

        # Save the labels
        sio.save_slp(video_specific_labels, str(file_path))

        saved_paths[video_name] = file_path

    return saved_paths


def validate_series_compatibility(labels: Labels) -> Dict[str, Any]:
    """
    Check if labels are compatible with sleap-roots Series class.

    Args:
        labels: SLEAP labels object to validate

    Returns:
        Dictionary with validation results:
        - is_compatible: bool
        - warnings: List[str]
        - errors: List[str]
        - video_count: int
        - frame_count: int
        - has_tracks: bool
        - skeleton_info: Dict
    """
    result = {
        "is_compatible": True,
        "warnings": [],
        "errors": [],
        "video_count": 0,
        "frame_count": 0,
        "has_tracks": False,
        "skeleton_info": {},
    }

    # Check for videos
    if hasattr(labels, "videos") and labels.videos:
        result["video_count"] = len(labels.videos)
    else:
        result["errors"].append("No videos found in labels")
        result["is_compatible"] = False

    # Check for labeled frames
    if hasattr(labels, "labeled_frames") and labels.labeled_frames:
        result["frame_count"] = len(labels.labeled_frames)
    else:
        result["errors"].append("No labeled frames found")
        result["is_compatible"] = False

    # Check for skeletons
    if hasattr(labels, "skeletons") and labels.skeletons:
        for i, skeleton in enumerate(labels.skeletons):
            nodes = []
            if hasattr(skeleton, "nodes"):
                nodes = [node.name for node in skeleton.nodes]
            result["skeleton_info"][f"skeleton_{i}"] = {
                "node_count": len(nodes),
                "node_names": nodes,
            }
    else:
        result["errors"].append("No skeletons found")
        result["is_compatible"] = False

    # Check for tracks
    if hasattr(labels, "tracks") and labels.tracks:
        result["has_tracks"] = True
    else:
        result["warnings"].append("No tracks found - Series may expect tracked data")

    # Check video references in frames
    frames_without_video = 0
    if hasattr(labels, "labeled_frames"):
        for lf in labels.labeled_frames:
            if not hasattr(lf, "video") or lf.video is None:
                frames_without_video += 1

    if frames_without_video > 0:
        result["warnings"].append(
            f"{frames_without_video} frames have no video reference"
        )

    # For multi-video files, warn about splitting
    if result["video_count"] > 1:
        result["warnings"].append(
            f"Labels contain {result['video_count']} videos. "
            "Series typically expects one video per file. "
            "Consider using split_labels_by_video()."
        )

    return result


def create_series_name_from_video(
    video_name: str, strip_extensions: bool = True
) -> str:
    """
    Create a series name from a video filename.

    Args:
        video_name: Video filename or path
        strip_extensions: Whether to remove common video extensions

    Returns:
        Clean series name suitable for Series class
    """
    if strip_extensions:
        name = Path(video_name).stem
    else:
        # Keep the full filename without path
        name = Path(video_name).name

    if strip_extensions:
        # Remove common video extensions that might be in stem
        for ext in [".avi", ".mp4", ".mov", ".tif", ".tiff", ".h5", ".hdf5"]:
            if name.lower().endswith(ext):
                name = name[: -len(ext)]

    # Replace problematic characters
    name = name.replace(" ", "_")
    name = name.replace("-", "_")

    return name

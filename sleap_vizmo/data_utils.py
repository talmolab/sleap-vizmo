"""Data export utility functions for SLEAP visualization."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pandas as pd
import numpy as np
from .video_utils import extract_video_name


def extract_instance_data(
    labeled_frame: Any,
    frame_idx: int,
    video_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract instance coordinate data from a labeled frame.

    Args:
        labeled_frame: SLEAP labeled frame object
        frame_idx: Index of the frame in the labels
        video_name: Optional video name override

    Returns:
        List of dictionaries with instance coordinate data
    """
    data = []

    # Get video name if not provided
    if video_name is None:
        video_name = extract_video_name(labeled_frame)

    # Get actual frame index in video
    actual_frame_idx = (
        labeled_frame.frame_idx if hasattr(labeled_frame, "frame_idx") else frame_idx
    )

    # Process each instance
    for instance_idx, instance in enumerate(labeled_frame.instances):
        instance_points = instance.numpy()
        
        # Skip if numpy() returns None
        if instance_points is None:
            continue
            
        instance_skeleton = instance.skeleton
        instance_node_names = [node.name for node in instance_skeleton.nodes]

        # Extract coordinates for each node
        for node_idx, (node_name, pt) in enumerate(
            zip(instance_node_names, instance_points)
        ):
            if not np.isnan(pt).any():
                data.append(
                    {
                        "Video": video_name,
                        "Frame_Index": actual_frame_idx,
                        "Labeled_Frame_Index": frame_idx,
                        "Instance": instance_idx,
                        "Node": node_name,
                        "X": pt[0],
                        "Y": pt[1],
                    }
                )

    return data


def export_labels_to_dataframe(labels: Any) -> pd.DataFrame:
    """
    Export all labeled frames to a pandas DataFrame.

    Args:
        labels: SLEAP labels object containing labeled frames

    Returns:
        DataFrame with columns: Video, Frame_Index, Labeled_Frame_Index,
        Instance, Node, X, Y
    """
    all_data = []

    for frame_idx, labeled_frame in enumerate(labels.labeled_frames):
        frame_data = extract_instance_data(labeled_frame, frame_idx)
        all_data.extend(frame_data)

    # Create DataFrame with explicit columns to handle empty case
    df = pd.DataFrame(all_data)
    if len(df) == 0:
        # Ensure empty DataFrame has the expected columns
        df = pd.DataFrame(
            columns=[
                "Video",
                "Frame_Index",
                "Labeled_Frame_Index",
                "Instance",
                "Node",
                "X",
                "Y",
            ]
        )

    return df


def save_labels_to_csv(
    labels: Any,
    output_path: Union[str, Path],
    include_metadata: bool = True,
) -> Path:
    """
    Save labeled frame data to CSV file.

    Args:
        labels: SLEAP labels object
        output_path: Path to save CSV file
        include_metadata: Whether to include metadata in filename

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export data
    df = export_labels_to_dataframe(labels)

    # Add metadata to filename if requested
    if include_metadata:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        n_frames = len(labels.labeled_frames)
        n_points = len(df)

        stem = output_path.stem
        suffix = output_path.suffix
        output_path = (
            output_path.parent
            / f"{stem}_{n_frames}frames_{n_points}pts_{timestamp}{suffix}"
        )

    # Save to CSV
    df.to_csv(output_path, index=False)

    return output_path


def summarize_labels(labels: Any) -> Dict[str, Any]:
    """
    Generate summary statistics for a labels object.

    Args:
        labels: SLEAP labels object

    Returns:
        Dictionary with summary statistics
    """
    summary = {
        "n_videos": len(labels.videos) if hasattr(labels, "videos") and labels.videos is not None else 0,
        "n_skeletons": len(labels.skeletons) if hasattr(labels, "skeletons") and labels.skeletons is not None else 0,
        "n_labeled_frames": (
            len(labels.labeled_frames) if hasattr(labels, "labeled_frames") and labels.labeled_frames is not None else 0
        ),
        "n_tracks": (
            len(labels.tracks)
            if hasattr(labels, "tracks") and labels.tracks is not None
            else 0
        ),
        "video_names": [],
        "nodes_per_skeleton": {},
        "instances_per_frame": [],
        "total_instances": 0,
        "total_points": 0,
    }

    # Get video names
    if hasattr(labels, "videos") and labels.videos is not None:
        for video in labels.videos:
            # Create a mock labeled frame with the video for extraction
            mock_lf = type("obj", (object,), {"video": video})()
            video_name = extract_video_name(mock_lf)
            summary["video_names"].append(video_name)

    # Get skeleton info
    if hasattr(labels, "skeletons") and labels.skeletons is not None:
        for i, skeleton in enumerate(labels.skeletons):
            if hasattr(skeleton, "nodes"):
                summary["nodes_per_skeleton"][f"skeleton_{i}"] = len(skeleton.nodes)

    # Analyze labeled frames
    if hasattr(labels, "labeled_frames") and labels.labeled_frames is not None:
        for lf in labels.labeled_frames:
            n_instances = len(lf.instances) if hasattr(lf, "instances") else 0
            summary["instances_per_frame"].append(n_instances)
            summary["total_instances"] += n_instances

            # Count valid points
            if hasattr(lf, "instances") and lf.instances is not None:
                for instance in lf.instances:
                    pts = instance.numpy()
                    valid_pts = ~np.isnan(pts).any(axis=1)
                    summary["total_points"] += np.sum(valid_pts)

    # Calculate statistics
    if summary["instances_per_frame"]:
        summary["avg_instances_per_frame"] = np.mean(summary["instances_per_frame"])
        summary["min_instances_per_frame"] = np.min(summary["instances_per_frame"])
        summary["max_instances_per_frame"] = np.max(summary["instances_per_frame"])

    return summary

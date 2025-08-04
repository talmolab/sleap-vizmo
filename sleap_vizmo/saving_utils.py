"""Utility functions for saving SLEAP visualization outputs."""

from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import plotly.graph_objects as go
from .plotting_utils import create_frame_figure
from .video_utils import extract_video_name
from .data_utils import save_labels_to_csv


def create_output_directory(base_dir: str = "./output") -> Path:
    """
    Create a timestamped output directory.

    Args:
        base_dir: Base directory for outputs

    Returns:
        Path to the created directory
    """
    # Include microseconds to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = Path(base_dir) / f"output_{timestamp}"

    # If directory already exists (very rare), add counter
    counter = 1
    while output_dir.exists():
        output_dir = Path(base_dir) / f"output_{timestamp}_{counter}"
        counter += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_frame_plots(
    labeled_frame: Any,
    frame_idx: int,
    output_dir: Path,
    video_name: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    scale: int = 2,
    **fig_kwargs,
) -> tuple[Path, Path]:
    """
    Save both PNG and HTML versions of a frame plot.

    Args:
        labeled_frame: SLEAP labeled frame
        frame_idx: Frame index for filename
        output_dir: Directory to save files
        video_name: Optional video name override
        width: Figure width in pixels
        height: Figure height in pixels
        scale: PNG export scale factor
        **fig_kwargs: Additional arguments for create_frame_figure

    Returns:
        Tuple of (png_path, html_path)
    """
    # Extract video name if not provided
    if video_name is None:
        video_name = extract_video_name(labeled_frame)
        if video_name == "unknown":
            video_name = "frame"

    # Create the figure
    fig = create_frame_figure(labeled_frame, **fig_kwargs)

    # Update layout with title
    fig.update_layout(
        title=f"{video_name} - Frame {frame_idx:04d}",
        width=width,
        height=height,
    )

    # Save as PNG
    png_filename = f"{video_name}_frame_{frame_idx:04d}.png"
    png_path = output_dir / png_filename
    fig.write_image(str(png_path), width=width, height=height, scale=scale)

    # Save as HTML (interactive)
    html_filename = f"{video_name}_frame_{frame_idx:04d}.html"
    html_path = output_dir / html_filename
    fig.write_html(
        str(html_path),
        include_plotlyjs="cdn",  # Use CDN to reduce file size
        config={"displayModeBar": True, "displaylogo": False},
    )

    return png_path, html_path


def save_all_frames(
    labels: Any,
    base_dir: str = "./output",
    progress_callback: Optional[callable] = None,
    **fig_kwargs,
) -> dict:
    """
    Save all labeled frames as PNG and HTML plots, plus a summary CSV.

    Args:
        labels: SLEAP labels object
        base_dir: Base directory for outputs
        progress_callback: Optional callback function(current, total, message)
        **fig_kwargs: Additional arguments for create_frame_figure

    Returns:
        Dictionary with:
            - output_dir: Path to output directory
            - png_files: List of saved PNG paths
            - html_files: List of saved HTML paths
            - csv_file: Path to saved CSV
            - errors: List of any errors encountered
    """
    # Create output directory
    output_dir = create_output_directory(base_dir)

    results = {
        "output_dir": output_dir,
        "png_files": [],
        "html_files": [],
        "csv_file": None,
        "errors": [],
    }

    total_frames = len(labels.labeled_frames)

    # Save each frame
    for idx, labeled_frame in enumerate(labels.labeled_frames):
        if progress_callback:
            progress_callback(idx + 1, total_frames, f"Processing frame {idx}")

        try:
            png_path, html_path = save_frame_plots(
                labeled_frame, idx, output_dir, **fig_kwargs
            )
            results["png_files"].append(png_path)
            results["html_files"].append(html_path)
        except Exception as e:
            error_msg = f"Error saving frame {idx}: {str(e)}"
            results["errors"].append(error_msg)
            print(error_msg)

    # Save CSV summary
    try:
        # Create descriptive CSV filename
        n_frames = len(labels.labeled_frames)

        # Try to get labels filename if available
        labels_name = "sleap_labels"

        # Check multiple sources for filename
        if hasattr(labels, "filename") and labels.filename:
            # Direct filename attribute
            labels_path = Path(labels.filename)
            labels_name = labels_path.stem
        elif hasattr(labels, "provenance") and isinstance(labels.provenance, dict):
            # Check provenance dictionary (where SLEAP typically stores it)
            if "filename" in labels.provenance and labels.provenance["filename"]:
                labels_path = Path(labels.provenance["filename"])
                labels_name = labels_path.stem

        # Count total instances
        total_instances = 0
        if hasattr(labels, "labeled_frames") and labels.labeled_frames is not None:
            for lf in labels.labeled_frames:
                if hasattr(lf, "instances") and lf.instances is not None:
                    total_instances += len(lf.instances)

        # Create descriptive filename
        csv_filename = f"{labels_name}_frames{n_frames}_instances{total_instances}.csv"
        csv_path = output_dir / csv_filename

        results["csv_file"] = save_labels_to_csv(
            labels, csv_path, include_metadata=False
        )

        if progress_callback:
            progress_callback(total_frames, total_frames, "Export complete!")

    except Exception as e:
        error_msg = f"Error saving CSV: {str(e)}"
        results["errors"].append(error_msg)
        print(error_msg)

    return results

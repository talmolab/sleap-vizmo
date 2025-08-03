"""Plotting utility functions for SLEAP visualization."""

from pathlib import Path
from typing import List, Optional, Any, Union, Tuple
import numpy as np
import plotly.graph_objects as go


def get_color_palette(name: str = "tab20", n_colors: int = 20) -> List[str]:
    """
    Get a color palette for plotting.

    Args:
        name: Name of the color palette. Currently supports "tab20" and "tab10".
        n_colors: Number of colors to generate.

    Returns:
        List of color strings in hex format.
    """
    if name == "tab20":
        # Plotly's default color sequence extended
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
            "#aec7e8",
            "#ffbb78",
            "#98df8a",
            "#ff9896",
            "#c5b0d5",
            "#c49c94",
            "#f7b6d2",
            "#c7c7c7",
            "#dbdb8d",
            "#9edae5",
        ]
    elif name == "tab10":
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
    else:
        # Default to a simple color cycle
        colors = [
            "red",
            "blue",
            "green",
            "orange",
            "purple",
            "brown",
            "pink",
            "gray",
            "olive",
            "cyan",
        ]

    # Repeat colors if needed
    while len(colors) < n_colors:
        colors.extend(colors)

    return colors[:n_colors]


def plot_instance_plotly(
    instance: Any,
    skeleton: Optional[Any] = None,
    cmap: Optional[List[str]] = None,
    color_by_node: bool = False,
    lw: int = 2,
    ms: int = 10,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    scale: float = 1.0,
    name_prefix: str = "Instance",
    show_edges: bool = True,
    show_labels: bool = True,
    **kwargs,
) -> List[go.Scatter]:
    """
    Plot a single instance with edge coloring using Plotly.

    Args:
        instance: SLEAP instance or numpy array of points.
        skeleton: Skeleton object for edge connections.
        cmap: Color map (list of colors) to use.
        color_by_node: If True, color by node instead of edge.
        lw: Line width for edges.
        ms: Marker size for nodes.
        bbox: Bounding box for cropping (y_min, x_min, y_max, x_max).
        scale: Scale factor for coordinates.
        name_prefix: Prefix for trace names.
        show_edges: Whether to show skeleton edges.
        show_labels: Whether to show node labels.
        **kwargs: Additional arguments passed to go.Scatter.

    Returns:
        List of Plotly trace objects.
    """
    if cmap is None:
        cmap = get_color_palette("tab20")

    if skeleton is None and hasattr(instance, "skeleton"):
        skeleton = instance.skeleton

    if skeleton is None or (hasattr(skeleton, "edges") and len(skeleton.edges) == 0):
        color_by_node = True
        show_edges = False

    if hasattr(instance, "numpy"):
        inst_pts = instance.numpy()
    else:
        inst_pts = instance

    traces = []

    # Get node names if available
    node_names = []
    if skeleton and hasattr(skeleton, "nodes"):
        node_names = [node.name for node in skeleton.nodes]
    else:
        node_names = [f"Point {i}" for i in range(len(inst_pts))]

    # Apply transformations
    pts_transformed = inst_pts.copy().astype(
        float
    )  # Ensure float type for transformations
    if bbox is not None:
        pts_transformed[:, 0] -= bbox[1]  # x
        pts_transformed[:, 1] -= bbox[0]  # y
    pts_transformed *= scale

    # Filter out NaN points
    valid_mask = ~np.isnan(pts_transformed).any(axis=1)

    if color_by_node:
        # Plot each node separately with its own color
        for k, (pt, name, is_valid) in enumerate(
            zip(pts_transformed, node_names, valid_mask)
        ):
            if not is_valid:
                continue

            trace = go.Scatter(
                x=[pt[0]],
                y=[pt[1]],
                mode="markers+text" if show_labels else "markers",
                marker=dict(size=ms, color=cmap[k % len(cmap)]),
                text=[str(k)] if show_labels else None,
                textposition="top center",
                name=f"{name_prefix} - {name}",
                hovertemplate=f"<b>{name_prefix}</b><br>"
                + f"Node: {name}<br>"
                + f"X: %{{x:.1f}}<br>"
                + f"Y: %{{y:.1f}}<br>"
                + "<extra></extra>",
                **kwargs,
            )
            traces.append(trace)

    else:
        # Plot with edge coloring
        if show_edges and skeleton and hasattr(skeleton, "edges"):
            edge_inds = []
            if hasattr(skeleton, "edge_inds"):
                edge_inds = skeleton.edge_inds
            else:
                # Try to get edge indices from edges
                for edge in skeleton.edges:
                    if hasattr(edge, "source") and hasattr(edge, "destination"):
                        src_idx = (
                            edge.source.idx
                            if hasattr(edge.source, "idx")
                            else edge.source
                        )
                        dst_idx = (
                            edge.destination.idx
                            if hasattr(edge.destination, "idx")
                            else edge.destination
                        )
                        edge_inds.append((src_idx, dst_idx))
                    elif isinstance(edge, (tuple, list)) and len(edge) == 2:
                        edge_inds.append(edge)

            # Plot edges
            for k, (src_ind, dst_ind) in enumerate(edge_inds):
                if src_ind >= len(pts_transformed) or dst_ind >= len(pts_transformed):
                    continue
                if not (valid_mask[src_ind] and valid_mask[dst_ind]):
                    continue

                src_pt = pts_transformed[src_ind]
                dst_pt = pts_transformed[dst_ind]

                # Edge line only (no markers on the line)
                edge_trace = go.Scatter(
                    x=[src_pt[0], dst_pt[0]],
                    y=[src_pt[1], dst_pt[1]],
                    mode="lines",
                    line=dict(width=lw, color=cmap[k % len(cmap)]),
                    name=f"{name_prefix} - Edge {k}",
                    hoverinfo="skip",  # Don't show hover for edge lines
                    showlegend=False,
                    **kwargs,
                )
                traces.append(edge_trace)

        # Always add nodes as separate traces with proper hover info
        for i, (pt, name, is_valid) in enumerate(
            zip(pts_transformed, node_names, valid_mask)
        ):
            if not is_valid:
                continue

            # Determine color based on edge association
            node_color = "gray"  # Default color
            if skeleton and hasattr(skeleton, "edges"):
                for k, (src_ind, dst_ind) in enumerate(edge_inds):
                    if i == src_ind or i == dst_ind:
                        node_color = cmap[k % len(cmap)]
                        break

            node_trace = go.Scatter(
                x=[pt[0]],
                y=[pt[1]],
                mode="markers+text" if show_labels else "markers",
                marker=dict(size=ms, color=node_color),
                text=[str(i)] if show_labels else None,
                textposition="top center",
                name=f"{name_prefix} - {name}",
                hovertemplate=f"<b>{name_prefix}</b><br>"
                + f"Node: {name} (index {i})<br>"
                + f"X: %{{x:.1f}}<br>"
                + f"Y: %{{y:.1f}}<br>"
                + "<extra></extra>",
                showlegend=False,
                **kwargs,
            )
            traces.append(node_trace)

    return traces


def plot_instances_plotly(
    instances: List[Any],
    skeleton: Optional[Any] = None,
    cmap: Optional[List[str]] = None,
    color_by_track: bool = False,
    tracks: Optional[List[Any]] = None,
    fig: Optional[go.Figure] = None,
    **kwargs,
) -> go.Figure:
    """
    Plot a list of instances with identity coloring using Plotly.

    Args:
        instances: List of instances to plot.
        skeleton: Skeleton to use for edge coloring.
        cmap: Color map to use for coloring.
        color_by_track: If True, color instances by track.
        tracks: List of tracks for coloring order.
        fig: Existing Plotly figure to add to. If None, creates new figure.
        **kwargs: Additional arguments passed to plot_instance_plotly.

    Returns:
        Plotly figure object.
    """
    if cmap is None:
        cmap = get_color_palette("tab10")

    if fig is None:
        fig = go.Figure()

    if color_by_track and tracks is None:
        # Infer tracks from instances
        tracks = set()
        for instance in instances:
            if hasattr(instance, "track") and instance.track is not None:
                tracks.add(instance.track)

        # Sort tracks by name or string representation
        try:
            tracks = sorted(
                list(tracks),
                key=lambda track: track.name if hasattr(track, "name") else str(track),
            )
        except TypeError:
            # If tracks can't be sorted (e.g., Mock objects), use them as-is
            tracks = list(tracks)

    for i, instance in enumerate(instances):
        if color_by_track:
            if not hasattr(instance, "track") or instance.track is None:
                raise ValueError("Instances must have tracks when color_by_track=True")

            if instance.track not in tracks:
                raise ValueError("Instance track not found in specified tracks")

            color = cmap[tracks.index(instance.track) % len(cmap)]
            instance_cmap = [color]
        else:
            # Color by instance order
            color = cmap[i % len(cmap)]
            instance_cmap = [color]

        traces = plot_instance_plotly(
            instance,
            skeleton=skeleton,
            cmap=instance_cmap,
            name_prefix=f"Instance {i}",
            **kwargs,
        )

        for trace in traces:
            fig.add_trace(trace)

    return fig


def create_frame_figure(
    labeled_frame: Any,
    skeleton: Optional[Any] = None,
    show_image: bool = True,
    color_by_track: bool = False,
    **kwargs,
) -> go.Figure:
    """
    Create a Plotly figure for a single labeled frame.

    Args:
        labeled_frame: SLEAP LabeledFrame object.
        skeleton: Skeleton to use (if None, uses from instances).
        show_image: Whether to show the frame image if available.
        color_by_track: Whether to color instances by track.
        **kwargs: Additional arguments passed to plot_instances_plotly.

    Returns:
        Plotly figure object.
    """
    fig = go.Figure()

    # Try to add image if requested
    if show_image:
        img = None
        try:
            if hasattr(labeled_frame, "image") and labeled_frame.image is not None:
                img = labeled_frame.image
            elif hasattr(labeled_frame, "video") and labeled_frame.video is not None:
                video_idx = labeled_frame.frame_idx
                if hasattr(labeled_frame.video, "get_frame"):
                    img = labeled_frame.video.get_frame(video_idx)

            if img is not None:
                fig.add_trace(go.Image(z=img))
        except Exception:
            pass

    # Plot instances
    if hasattr(labeled_frame, "instances") and len(labeled_frame.instances) > 0:
        # Get skeleton from first instance if not provided
        if skeleton is None and len(labeled_frame.instances) > 0:
            skeleton = labeled_frame.instances[0].skeleton

        fig = plot_instances_plotly(
            labeled_frame.instances,
            skeleton=skeleton,
            color_by_track=color_by_track,
            fig=fig,
            **kwargs,
        )

    # Update layout
    # Note: y-axis is reversed to match image coordinates (top-left origin)
    fig.update_layout(
        xaxis=dict(title="X coordinate", scaleanchor="y", constrain="domain"),
        yaxis=dict(title="Y coordinate", autorange="reversed", constrain="domain"),
        height=600,
        hovermode="closest",
    )

    return fig

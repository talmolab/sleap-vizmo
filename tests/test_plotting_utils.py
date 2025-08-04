"""Tests for plotting_utils module."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
import plotly.graph_objects as go
from sleap_vizmo.plotting_utils import (
    get_color_palette,
    plot_instance_plotly,
    plot_instances_plotly,
    create_frame_figure,
)


class TestGetColorPalette:
    """Test suite for get_color_palette function."""

    def test_tab20_palette(self):
        """Test tab20 color palette."""
        colors = get_color_palette("tab20", 20)
        assert len(colors) == 20
        assert all(isinstance(c, str) for c in colors)
        assert colors[0] == "#1f77b4"  # First color should be blue

    def test_tab10_palette(self):
        """Test tab10 color palette."""
        colors = get_color_palette("tab10", 10)
        assert len(colors) == 10
        assert all(isinstance(c, str) for c in colors)

    def test_default_palette(self):
        """Test default color palette."""
        colors = get_color_palette("unknown", 10)
        assert len(colors) == 10
        assert "red" in colors
        assert "blue" in colors

    def test_palette_extension(self):
        """Test that palette extends when more colors requested."""
        colors = get_color_palette("tab10", 25)
        assert len(colors) == 25
        # Check that colors repeat
        assert colors[0] == colors[10]
        assert colors[1] == colors[11]


class TestPlotInstancePlotly:
    """Test suite for plot_instance_plotly function."""

    def test_basic_instance_plotting(self):
        """Test basic instance plotting with numpy array."""
        # Create test data
        points = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]])

        traces = plot_instance_plotly(points)

        assert len(traces) > 0
        assert all(isinstance(t, go.Scatter) for t in traces)

    def test_instance_with_skeleton(self):
        """Test plotting instance with skeleton edges."""
        # Mock instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10.0, 20.0], [30.0, 40.0]])

        # Mock skeleton
        skeleton = Mock()
        skeleton.nodes = [Mock(name="node1"), Mock(name="node2")]
        skeleton.edges = [Mock()]
        skeleton.edge_inds = [(0, 1)]

        traces = plot_instance_plotly(instance, skeleton=skeleton, show_edges=True)

        assert len(traces) > 0
        # Should have both edge traces (lines) and node traces (markers or markers+text)
        edge_traces = [t for t in traces if t.mode == "lines"]
        node_traces = [t for t in traces if "markers" in t.mode]

        # Should have 1 edge trace and 2 node traces
        assert len(edge_traces) == 1
        assert len(node_traces) == 2

        # Edge traces should have hoverinfo="skip"
        for trace in edge_traces:
            assert trace.hoverinfo == "skip"

        # Node traces should have proper hover templates
        for trace in node_traces:
            assert "hovertemplate" in trace._props
            assert "Node:" in trace.hovertemplate

    def test_instance_with_nan_points(self):
        """Test plotting instance with NaN points."""
        points = np.array([[10.0, 20.0], [np.nan, np.nan], [30.0, 40.0]])

        traces = plot_instance_plotly(points, color_by_node=True)

        # Should skip NaN points
        valid_traces = [t for t in traces if len(t.x) > 0]
        assert len(valid_traces) == 2  # Only 2 valid points

    def test_color_by_node(self):
        """Test coloring by node."""
        points = np.array([[10.0, 20.0], [30.0, 40.0]])
        cmap = ["red", "blue", "green"]

        traces = plot_instance_plotly(points, cmap=cmap, color_by_node=True)

        # Each node should have its own trace with different color
        assert len(traces) == 2
        assert traces[0].marker.color == "red"
        assert traces[1].marker.color == "blue"

    def test_with_labels(self):
        """Test plotting with labels."""
        points = np.array([[10.0, 20.0], [30.0, 40.0]])

        traces = plot_instance_plotly(points, show_labels=True, color_by_node=False)

        # Should have traces with text
        label_traces = [t for t in traces if t.mode and "text" in t.mode]
        assert len(label_traces) > 0

    def test_with_transformations(self):
        """Test plotting with bbox and scale transformations."""
        points = np.array([[100.0, 200.0], [300.0, 400.0]])
        bbox = (10, 20, 50, 60)  # y_min, x_min, y_max, x_max
        scale = 0.5

        traces = plot_instance_plotly(
            points, bbox=bbox, scale=scale, color_by_node=True
        )

        # Check that transformations were applied
        # Original x=100, after bbox: 100-20=80, after scale: 80*0.5=40
        assert traces[0].x[0] == 40.0
        # Original y=200, after bbox: 200-10=190, after scale: 190*0.5=95
        assert traces[0].y[0] == 95.0


class TestPlotInstancesPlotly:
    """Test suite for plot_instances_plotly function."""

    def test_multiple_instances(self):
        """Test plotting multiple instances."""
        # Create mock instances
        instances = []
        for i in range(3):
            inst = Mock()
            inst.numpy.return_value = np.array([[i * 10, i * 20], [i * 30, i * 40]])
            inst.skeleton = None
            instances.append(inst)

        fig = plot_instances_plotly(instances)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_color_by_track(self):
        """Test coloring instances by track."""
        # Create mock instances with tracks
        track1 = Mock(name="track1")
        track2 = Mock(name="track2")

        instances = []
        for i, track in enumerate([track1, track2, track1]):
            inst = Mock()
            inst.numpy.return_value = np.array([[i * 10, i * 20]])
            inst.skeleton = None
            inst.track = track
            instances.append(inst)

        fig = plot_instances_plotly(instances, color_by_track=True)

        assert isinstance(fig, go.Figure)
        # All instances with same track should have same color

    def test_with_existing_figure(self):
        """Test adding to existing figure."""
        # Create initial figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0], y=[0], name="existing"))

        # Add instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10, 20]])
        instance.skeleton = None

        result_fig = plot_instances_plotly([instance], fig=fig)

        assert result_fig is fig  # Should be same figure object
        assert len(fig.data) > 1  # Should have added traces

    def test_no_track_error(self):
        """Test error when color_by_track but no tracks."""
        instance = Mock()
        instance.numpy.return_value = np.array([[10, 20]])
        instance.skeleton = None
        instance.track = None

        with pytest.raises(ValueError, match="must have tracks"):
            plot_instances_plotly([instance], color_by_track=True)


class TestCreateFrameFigure:
    """Test suite for create_frame_figure function."""

    def test_basic_frame_figure(self):
        """Test creating basic frame figure."""
        # Mock labeled frame
        labeled_frame = Mock()
        labeled_frame.instances = []
        labeled_frame.image = None
        labeled_frame.video = None

        fig = create_frame_figure(labeled_frame)

        assert isinstance(fig, go.Figure)
        assert fig.layout.xaxis.title.text == "X coordinate"
        assert fig.layout.yaxis.title.text == "Y coordinate"
        assert fig.layout.yaxis.autorange == "reversed"

    def test_frame_with_image(self):
        """Test frame with image."""
        # Mock labeled frame with image
        labeled_frame = Mock()
        labeled_frame.instances = []
        labeled_frame.image = np.zeros((100, 100, 3), dtype=np.uint8)

        fig = create_frame_figure(labeled_frame, show_image=True)

        # Should have image trace
        image_traces = [t for t in fig.data if isinstance(t, go.Image)]
        assert len(image_traces) == 1

    def test_frame_with_video(self):
        """Test frame with video."""
        # Mock labeled frame with video
        labeled_frame = Mock()
        labeled_frame.instances = []
        labeled_frame.image = None
        labeled_frame.video = Mock()
        labeled_frame.video.get_frame.return_value = np.zeros((100, 100, 3))
        labeled_frame.frame_idx = 5

        fig = create_frame_figure(labeled_frame, show_image=True)

        # Should have called get_frame
        labeled_frame.video.get_frame.assert_called_once_with(5)

    def test_frame_with_instances(self):
        """Test frame with instances."""
        # Mock instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10, 20], [30, 40]])
        instance.skeleton = Mock()
        node_a = Mock()
        node_a.name = "a"
        node_b = Mock()
        node_b.name = "b"
        instance.skeleton.nodes = [node_a, node_b]
        instance.skeleton.edges = []

        # Mock labeled frame
        labeled_frame = Mock()
        labeled_frame.instances = [instance]
        labeled_frame.image = None
        labeled_frame.video = None

        fig = create_frame_figure(labeled_frame)

        # Should have instance traces
        assert len(fig.data) > 0

    def test_frame_figure_layout(self):
        """Test frame figure layout settings."""
        labeled_frame = Mock()
        labeled_frame.instances = []
        labeled_frame.image = None
        labeled_frame.video = None

        fig = create_frame_figure(labeled_frame)

        # Check layout settings
        assert fig.layout.height == 600
        assert fig.layout.hovermode == "closest"
        assert fig.layout.xaxis.scaleanchor == "y"
        assert fig.layout.xaxis.constrain == "domain"


class TestHoverTemplates:
    """Test suite for hover templates in plotting functions."""

    def test_node_hover_template_with_color_by_node(self):
        """Test that node hover templates are properly formatted when color_by_node=True."""
        # Create skeleton with named nodes
        skeleton = Mock()
        node1 = Mock()
        node1.name = "root_tip"
        node2 = Mock()
        node2.name = "root_base"
        skeleton.nodes = [node1, node2]
        skeleton.edges = []

        # Create instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10.5, 20.3], [30.7, 40.9]])
        instance.skeleton = skeleton

        # Plot with color_by_node=True
        traces = plot_instance_plotly(
            instance, skeleton=skeleton, color_by_node=True, name_prefix="Instance 0"
        )

        # Should have one trace per node
        assert len(traces) == 2

        # Check hover template for first node
        hover_template = traces[0].hovertemplate
        assert "<b>Instance 0</b>" in hover_template
        assert "Node: root_tip" in hover_template
        assert "X: %{x:.1f}" in hover_template
        assert "Y: %{y:.1f}" in hover_template
        assert "<extra></extra>" in hover_template

        # Check hover template for second node
        hover_template = traces[1].hovertemplate
        assert "Node: root_base" in hover_template

    def test_node_hover_template_with_edge_coloring(self):
        """Test that nodes have proper hover templates when using edge coloring."""
        # Create skeleton with edges
        skeleton = Mock()
        node1 = Mock()
        node1.name = "node_a"
        node2 = Mock()
        node2.name = "node_b"
        skeleton.nodes = [node1, node2]
        skeleton.edges = [(0, 1)]
        skeleton.edge_inds = [(0, 1)]

        # Create instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10, 20], [30, 40]])
        instance.skeleton = skeleton

        # Plot with edge coloring (color_by_node=False)
        traces = plot_instance_plotly(
            instance,
            skeleton=skeleton,
            color_by_node=False,
            show_edges=True,
            name_prefix="Instance 0",
        )

        # Should have edge trace + node traces
        edge_traces = [t for t in traces if t.mode == "lines"]
        node_traces = [t for t in traces if t.mode in ["markers", "markers+text"]]

        assert len(edge_traces) == 1
        assert len(node_traces) == 2

        # Edge should not show hover
        assert edge_traces[0].hoverinfo == "skip"

        # Check node hover templates
        for i, node_trace in enumerate(node_traces):
            assert "<b>Instance 0</b>" in node_trace.hovertemplate
            assert "Node:" in node_trace.hovertemplate
            assert "(index" in node_trace.hovertemplate
            assert "X: %{x:.1f}" in node_trace.hovertemplate
            assert "Y: %{y:.1f}" in node_trace.hovertemplate

    def test_coordinate_display_accuracy(self):
        """Test that hover coordinates match the actual data points."""
        # Create instance with specific coordinates
        points = np.array([[12.345, 67.890], [23.456, 78.901]])
        skeleton = Mock()
        skeleton.nodes = [Mock(name="p1"), Mock(name="p2")]
        skeleton.edges = []

        instance = Mock()
        instance.numpy.return_value = points
        instance.skeleton = skeleton

        traces = plot_instance_plotly(
            instance, skeleton=skeleton, color_by_node=True, name_prefix="Test"
        )

        # Verify that the x,y data matches our input
        assert traces[0].x[0] == 12.345
        assert traces[0].y[0] == 67.890
        assert traces[1].x[0] == 23.456
        assert traces[1].y[0] == 78.901

        # Hover template should use these coordinates
        assert "X: %{x:.1f}" in traces[0].hovertemplate
        assert "Y: %{y:.1f}" in traces[0].hovertemplate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

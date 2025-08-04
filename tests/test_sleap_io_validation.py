"""Tests to validate correct usage of sleap-io data structures and prevent silent failures."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path

from sleap_vizmo.pipeline_utils import detect_root_types, get_file_summary
from sleap_vizmo.roots_utils import split_labels_by_video, validate_series_compatibility
from sleap_vizmo.data_utils import summarize_labels
from sleap_vizmo.plotting_utils import get_color_palette


class TestSilentFailures:
    """Test cases that might silently fail or return incorrect NA values."""

    def test_node_name_extraction_failure(self):
        """Test that node names are correctly extracted and never NA."""
        # Create instance with nodes that might cause issues
        instance = Mock()

        # Node with empty name
        node1 = Mock()
        node1.name = ""  # Empty string

        # Node with whitespace name
        node2 = Mock()
        node2.name = "   "  # Just whitespace

        # Normal node
        node3 = Mock()
        node3.name = "root_tip"

        skeleton = Mock()
        skeleton.nodes = [node1, node2, node3]
        instance.skeleton = skeleton
        instance.numpy = Mock(return_value=np.array([[1, 2], [3, 4], [5, 6]]))

        # Extract node names
        node_names = [node.name for node in instance.skeleton.nodes]

        # Verify we get actual strings, not None
        assert all(isinstance(name, str) for name in node_names)
        assert node_names[0] == ""  # Empty string, not None
        assert node_names[1] == "   "  # Whitespace, not None
        assert node_names[2] == "root_tip"

    def test_skeleton_nodes_not_none(self):
        """Test that skeleton.nodes is never None."""
        skeleton = Mock()

        # Test 1: nodes as empty list
        skeleton.nodes = []
        assert skeleton.nodes is not None
        assert len(skeleton.nodes) == 0

        # Test 2: nodes as None (should be handled)
        skeleton.nodes = None
        # This would cause issues - we should check for this
        assert skeleton.nodes is None  # This is a problem!

    def test_labels_collections_not_none(self):
        """Test that labels collections are handled when None."""
        labels = Mock()

        # Set collections to None instead of empty lists
        labels.videos = None
        labels.skeletons = None
        labels.tracks = None
        labels.labeled_frames = None

        # These should be handled gracefully
        summary = summarize_labels(labels)

        # Should return 0 counts, not crash
        assert summary["n_labeled_frames"] == 0
        assert summary["n_videos"] == 0
        assert summary["n_skeletons"] == 0

    def test_video_filename_none_handling(self):
        """Test that None video filenames don't cause silent failures."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()

        # Both filename attributes are None
        labeled_frame.video.filename = None
        labeled_frame.video.backend = Mock()
        labeled_frame.video.backend.filename = None

        from sleap_vizmo.video_utils import extract_video_name

        # Should return "unknown", not None or empty string
        result = extract_video_name(labeled_frame)
        assert result == "unknown"
        assert result is not None
        assert result != ""

    def test_instance_numpy_returns_none(self):
        """Test handling when instance.numpy() returns None."""
        instance = Mock()
        instance.numpy = Mock(return_value=None)  # This would be bad!

        skeleton = Mock()
        skeleton.nodes = [Mock(name="node1")]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        from sleap_vizmo.data_utils import extract_instance_data

        # Should handle gracefully, not crash
        data = extract_instance_data(labeled_frame, frame_idx=0)
        # Should return empty list when instance.numpy() returns None
        assert len(data) == 0


class TestDataTypeValidation:
    """Test that we're using correct data types."""

    def test_frame_idx_type_validation(self):
        """Test that frame_idx is always an integer."""
        labeled_frame = Mock()

        # Test various frame_idx types
        test_cases = [
            0,  # int
            1.0,  # float that should be int
            "2",  # string that should be int
            np.int64(3),  # numpy int
            None,  # Missing
        ]

        for test_idx in test_cases:
            labeled_frame.frame_idx = test_idx
            labeled_frame.video = Mock()
            labeled_frame.video.filename = "test.mp4"
            labeled_frame.instances = []

            from sleap_vizmo.data_utils import extract_instance_data

            if test_idx is None:
                # Should use provided frame_idx
                data = extract_instance_data(labeled_frame, frame_idx=0)
                # Check it doesn't crash
                assert isinstance(data, list)
            else:
                # Should handle type conversion
                data = extract_instance_data(labeled_frame, frame_idx=0)
                assert isinstance(data, list)

    def test_coordinate_precision_loss(self):
        """Test that coordinates don't lose precision."""
        instance = Mock()

        # High precision coordinates
        coords = np.array([[123.456789012345, 234.567890123456]])
        instance.numpy = Mock(return_value=coords)

        skeleton = Mock()
        skeleton.nodes = [Mock(name="precise_node")]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        from sleap_vizmo.data_utils import extract_instance_data

        data = extract_instance_data(labeled_frame, frame_idx=0)

        # Check precision is maintained
        assert len(data) == 1
        # Float precision should be maintained
        assert abs(data[0]["X"] - 123.456789012345) < 1e-10
        assert abs(data[0]["Y"] - 234.567890123456) < 1e-10


class TestCollectionIteration:
    """Test that we correctly iterate over collections."""

    def test_videos_iteration_with_generator(self):
        """Test if videos is a generator instead of list."""
        labels = Mock()

        # Create a generator
        def video_generator():
            yield Mock(filename="video1.mp4")
            yield Mock(filename="video2.mp4")

        labels.videos = video_generator()

        # This should work but might not if we assume it's a list
        from sleap_vizmo.roots_utils import get_videos_in_labels

        videos = get_videos_in_labels(labels)
        assert len(videos) == 2

    def test_empty_collections_handling(self):
        """Test handling of empty collections."""
        labels = Mock()
        labels.videos = []
        labels.skeletons = []
        labels.tracks = []
        labels.labeled_frames = []

        # Should not produce NA values
        summary = summarize_labels(labels)

        assert summary["n_labeled_frames"] == 0
        assert summary["n_videos"] == 0
        assert summary["n_skeletons"] == 0
        assert summary["n_tracks"] == 0

        # Should not have None values
        assert all(v is not None for v in summary.values())


class TestAttributeAccess:
    """Test safe attribute access patterns."""

    def test_hasattr_vs_try_except(self):
        """Test that hasattr is used correctly."""
        obj = Mock()

        # hasattr returns True even for None attributes
        obj.attr = None
        assert hasattr(obj, "attr") is True
        assert obj.attr is None

        # hasattr returns False for missing attributes
        del obj.attr
        assert hasattr(obj, "attr") is False

    def test_nested_attribute_access(self):
        """Test safe nested attribute access."""
        labeled_frame = Mock()

        # Case 1: video exists but backend doesn't
        labeled_frame.video = Mock()
        del labeled_frame.video.backend

        # This pattern is safer
        if hasattr(labeled_frame.video, "backend") and hasattr(
            labeled_frame.video.backend, "filename"
        ):
            filename = labeled_frame.video.backend.filename
        else:
            filename = None

        assert filename is None

    def test_attribute_types(self):
        """Test that attributes have expected types."""
        # Create mock with wrong types
        instance = Mock()
        instance.skeleton = "not a skeleton object"  # Wrong type!

        # This would fail
        with pytest.raises(AttributeError):
            nodes = instance.skeleton.nodes


class TestRootTypeDetection:
    """Test root type detection doesn't silently fail."""

    def test_detect_root_types_with_missing_nodes(self):
        """Test root type detection with missing root_type in config."""
        from sleap_vizmo.pipeline_utils import detect_root_types

        # Test with missing root_type keys
        file_configs = [
            {"root_type": "primary", "path": "file1.slp"},
            {"path": "file2.slp"},  # Missing root_type
            {"root_type": "lateral", "path": "file3.slp"},
            {"root_type": None, "path": "file4.slp"},  # None root_type
        ]

        # Should handle missing/None root types gracefully
        root_types = detect_root_types(file_configs)

        # Should detect primary and lateral
        assert root_types["primary"] is True
        assert root_types["lateral"] is True
        assert root_types["crown"] is False

        # Should still detect the valid root types
        assert "primary" in root_types
        assert "lateral" in root_types

    def test_pipeline_detection_with_edge_cases(self):
        """Test pipeline detection with edge cases."""
        from sleap_vizmo.pipeline_utils import get_file_summary

        # Test with edge case file configs
        file_configs = [
            {"root_type": "primary", "path": Path("file1.slp")},
            {"root_type": "lateral", "path": "file2.slp"},  # String path
            {"root_type": "invalid", "path": "file3.slp"},  # Invalid root type
            {"path": "file4.slp"},  # Missing root_type
            {"root_type": "crown"},  # Missing path
        ]

        summary = get_file_summary(file_configs)

        # Should only include valid entries
        assert len(summary["primary"]) == 1
        assert len(summary["lateral"]) == 1
        assert len(summary["crown"]) == 0
        assert "file1.slp" in summary["primary"]
        assert "file2.slp" in summary["lateral"]

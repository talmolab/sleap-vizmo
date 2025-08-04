"""Tests for safe handling of SLEAP data structures."""

import pytest
import numpy as np
from unittest.mock import Mock
import sleap_io as sio
from pathlib import Path

from sleap_vizmo.utils import safe_len, safe_iter, has_valid_attr, safe_get_attr
from sleap_vizmo.data_utils import extract_instance_data


class TestSafeUtilities:
    """Test safe utility functions."""

    def test_safe_len(self):
        """Test safe_len function."""
        obj = Mock()

        # Normal list
        obj.items = [1, 2, 3]
        assert safe_len(obj, "items") == 3

        # None attribute
        obj.items = None
        assert safe_len(obj, "items") == 0

        # Missing attribute
        del obj.items
        assert safe_len(obj, "items") == 0

    def test_safe_iter(self):
        """Test safe_iter function."""
        obj = Mock()

        # Normal list
        obj.items = [1, 2, 3]
        assert list(safe_iter(obj, "items")) == [1, 2, 3]

        # None attribute
        obj.items = None
        assert list(safe_iter(obj, "items")) == []

        # Missing attribute
        del obj.items
        assert list(safe_iter(obj, "items")) == []

    def test_has_valid_attr(self):
        """Test has_valid_attr function."""
        obj = Mock()

        # Valid attribute
        obj.attr = "value"
        assert has_valid_attr(obj, "attr") is True

        # None attribute
        obj.attr = None
        assert has_valid_attr(obj, "attr") is False

        # Missing attribute
        del obj.attr
        assert has_valid_attr(obj, "attr") is False

    def test_safe_get_attr(self):
        """Test safe_get_attr function."""
        obj = Mock()

        # Valid attribute
        obj.attr = "value"
        assert safe_get_attr(obj, "attr") == "value"
        assert safe_get_attr(obj, "attr", "default") == "value"

        # None attribute
        obj.attr = None
        assert safe_get_attr(obj, "attr") is None
        assert safe_get_attr(obj, "attr", "default") == "default"

        # Missing attribute
        del obj.attr
        assert safe_get_attr(obj, "attr") is None
        assert safe_get_attr(obj, "attr", "default") == "default"


class TestInstanceNumpyEdgeCases:
    """Test edge cases with instance.numpy() method."""

    def test_instance_numpy_empty_array(self):
        """Test handling of empty numpy array from instance."""
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([]))  # Empty array

        skeleton = Mock()
        skeleton.nodes = []  # No nodes
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        # Should handle empty array
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 0

    def test_instance_numpy_wrong_shape(self):
        """Test handling of wrong shape numpy array."""
        instance = Mock()
        # Wrong shape - 1D instead of 2D
        instance.numpy = Mock(return_value=np.array([1.0, 2.0, 3.0, 4.0]))

        skeleton = Mock()
        skeleton.nodes = [Mock(name="node1"), Mock(name="node2")]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        # Should fail with proper error
        with pytest.raises(Exception):  # Will fail on indexing
            data = extract_instance_data(labeled_frame, frame_idx=0)

    def test_instance_numpy_inf_values(self):
        """Test handling of infinity values in coordinates."""
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[np.inf, -np.inf], [1.0, 2.0]]))

        skeleton = Mock()
        node1 = Mock()
        node1.name = "node1"
        node2 = Mock()
        node2.name = "node2"
        skeleton.nodes = [node1, node2]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        # Currently extracts all coordinates including infinity values
        # This is probably fine as infinity might be a valid coordinate in some contexts
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 2  # Both points extracted
        assert data[0]["Node"] == "node1"
        assert data[0]["X"] == np.inf
        assert data[0]["Y"] == -np.inf
        assert data[1]["Node"] == "node2"
        assert data[1]["X"] == 1.0
        assert data[1]["Y"] == 2.0

    def test_instance_skeleton_mismatch(self):
        """Test when number of points doesn't match number of nodes."""
        instance = Mock()
        # 3 points
        instance.numpy = Mock(return_value=np.array([[1, 2], [3, 4], [5, 6]]))

        skeleton = Mock()
        # Only 2 nodes
        skeleton.nodes = [Mock(name="node1"), Mock(name="node2")]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        # This will fail in zip() - only processes min length
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 2  # Only 2 nodes processed


class TestNodeNameValidation:
    """Test node name handling."""

    def test_node_names_special_characters(self):
        """Test node names with special characters."""
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[1, 2], [3, 4]]))

        skeleton = Mock()
        # Special characters in node names
        node1 = Mock()
        node1.name = "node@#$%"
        node2 = Mock()
        node2.name = "node\nwith\nnewlines"
        skeleton.nodes = [node1, node2]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 2
        assert data[0]["Node"] == "node@#$%"
        assert data[1]["Node"] == "node\nwith\nnewlines"

    def test_duplicate_node_names(self):
        """Test handling of duplicate node names."""
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[1, 2], [3, 4]]))

        skeleton = Mock()
        # Duplicate names
        node1 = Mock()
        node1.name = "node"
        node2 = Mock()
        node2.name = "node"  # Same name!
        skeleton.nodes = [node1, node2]
        instance.skeleton = skeleton

        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = [instance]

        # Should extract both even with duplicate names
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 2
        assert all(d["Node"] == "node" for d in data)
        # But different coordinates
        assert data[0]["X"] != data[1]["X"]


class TestRealDataValidation:
    """Validate assumptions about real SLEAP data."""

    @pytest.fixture
    def real_labels(self):
        """Load real SLEAP data."""
        test_file = Path(
            "tests/data/one_vid_lateral_root_MK22_Day14_test_labels.v003.slp"
        )
        if test_file.exists():
            return sio.load_slp(test_file)
        pytest.skip("Test SLEAP file not found")

    def test_real_data_assumptions(self, real_labels):
        """Test our assumptions about real data structures."""
        # Check that collections are never None
        assert real_labels.videos is not None
        assert real_labels.skeletons is not None
        assert real_labels.labeled_frames is not None
        # tracks might be None

        # Check video filenames
        for video in real_labels.videos:
            assert hasattr(video, "filename") or (
                hasattr(video, "backend") and hasattr(video.backend, "filename")
            )

        # Check instances
        for lf in real_labels.labeled_frames:
            assert lf.instances is not None  # Should be list, possibly empty
            for instance in lf.instances:
                # Check numpy() returns correct shape
                coords = instance.numpy()
                assert coords.ndim == 2
                assert coords.shape[1] == 2

                # Check skeleton
                assert instance.skeleton is not None
                assert instance.skeleton.nodes is not None

                # Verify lengths match
                assert coords.shape[0] == len(instance.skeleton.nodes)

        # Check node names are strings
        for skeleton in real_labels.skeletons:
            assert skeleton.nodes is not None
            for node in skeleton.nodes:
                assert isinstance(node.name, str)
                assert node.name != ""  # Not empty

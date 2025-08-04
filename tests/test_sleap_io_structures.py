"""Comprehensive tests for sleap-io data structure usage."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
import sleap_io as sio
from pathlib import Path

from sleap_vizmo.video_utils import extract_video_name, parse_video_filename, get_video_info
from sleap_vizmo.data_utils import extract_instance_data, export_labels_to_dataframe
from sleap_vizmo.roots_utils import get_videos_in_labels, split_labels_by_video


class TestVideoObjectHandling:
    """Test handling of sleap-io Video objects."""

    def test_video_object_falsy_behavior(self):
        """Test that Video objects might evaluate to False."""
        # Create a mock video that evaluates to False
        video = Mock()
        video.__bool__ = Mock(return_value=False)
        video.__len__ = Mock(return_value=0)
        video.filename = "test.mp4"
        
        # This would fail if we used "if not video:"
        assert bool(video) is False
        assert hasattr(video, "filename")
        assert video.filename == "test.mp4"

    def test_video_filename_types(self):
        """Test different types of video.filename attributes."""
        labeled_frame = Mock()
        
        # Test 1: String filename
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "/path/to/video.mp4"
        assert extract_video_name(labeled_frame) == "video"
        
        # Test 2: Path object
        labeled_frame.video.filename = Path("/path/to/video.mp4")
        assert extract_video_name(labeled_frame) == "video"
        
        # Test 3: List of Path objects (real SLEAP behavior)
        labeled_frame.video.filename = [Path("/path/to/video.mp4")]
        assert extract_video_name(labeled_frame) == "video"
        
        # Test 4: String representation of list
        labeled_frame.video.filename = "[WindowsPath('/path/to/video.mp4')]"
        assert extract_video_name(labeled_frame) == "video"
        
        # Test 5: None
        labeled_frame.video.filename = None
        labeled_frame.video.backend = Mock()
        labeled_frame.video.backend.filename = "backup.mp4"
        assert extract_video_name(labeled_frame) == "backup"

    def test_video_backend_fallback(self):
        """Test fallback to video.backend.filename."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        
        # No direct filename attribute
        del labeled_frame.video.filename
        
        # But has backend.filename
        labeled_frame.video.backend = Mock()
        labeled_frame.video.backend.filename = "backend_video.mp4"
        
        assert extract_video_name(labeled_frame) == "backend_video"

    def test_missing_video_attribute(self):
        """Test handling of missing video attribute."""
        labeled_frame = Mock()
        del labeled_frame.video
        
        assert extract_video_name(labeled_frame) == "unknown"


class TestInstanceHandling:
    """Test handling of sleap-io Instance objects."""

    def test_instance_numpy_method(self):
        """Test that instances have numpy() method returning coordinates."""
        # Create mock instance
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[10.0, 20.0], [30.0, 40.0]]))
        
        # Create mock skeleton
        node1 = Mock()
        node1.name = "node1"
        node2 = Mock()
        node2.name = "node2"
        
        skeleton = Mock()
        skeleton.nodes = [node1, node2]
        instance.skeleton = skeleton
        
        # Test coordinate extraction
        coords = instance.numpy()
        assert coords.shape == (2, 2)
        assert coords[0, 0] == 10.0
        assert coords[0, 1] == 20.0

    def test_instance_with_nan_coordinates(self):
        """Test handling of NaN coordinates in instances."""
        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        
        # Create instance with some NaN coordinates
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[10.0, 20.0], [np.nan, np.nan], [30.0, 40.0]]))
        
        # Create skeleton
        nodes = []
        for i in range(3):
            node = Mock()
            node.name = f"node_{i}"
            nodes.append(node)
        
        skeleton = Mock()
        skeleton.nodes = nodes
        instance.skeleton = skeleton
        
        labeled_frame.instances = [instance]
        
        # Extract data
        data = extract_instance_data(labeled_frame, frame_idx=0)
        
        # Should have 2 points (excluding NaN)
        assert len(data) == 2
        assert all(d["Node"] in ["node_0", "node_2"] for d in data)

    def test_empty_instances_list(self):
        """Test handling of frames with no instances."""
        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = []
        
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 0


class TestSkeletonHandling:
    """Test handling of sleap-io Skeleton objects."""

    def test_skeleton_nodes_access(self):
        """Test accessing nodes from skeleton."""
        # Create nodes
        nodes = []
        for name in ["root_tip", "root_base", "lateral_1"]:
            node = Mock()
            node.name = name
            nodes.append(node)
        
        skeleton = Mock()
        skeleton.nodes = nodes
        
        # Test node access
        node_names = [n.name for n in skeleton.nodes]
        assert "root_tip" in node_names
        assert "root_base" in node_names
        assert "lateral_1" in node_names

    def test_instance_skeleton_relationship(self):
        """Test that each instance has its own skeleton reference."""
        # Create two different skeletons
        skeleton1 = Mock()
        node_a = Mock()
        node_a.name = "node_a"
        node_b = Mock()
        node_b.name = "node_b"
        skeleton1.nodes = [node_a, node_b]
        
        skeleton2 = Mock()
        node_x = Mock()
        node_x.name = "node_x"
        node_y = Mock()
        node_y.name = "node_y"
        skeleton2.nodes = [node_x, node_y]
        
        # Create instances with different skeletons
        instance1 = Mock()
        instance1.skeleton = skeleton1
        instance1.numpy = Mock(return_value=np.array([[1, 2], [3, 4]]))
        
        instance2 = Mock()
        instance2.skeleton = skeleton2
        instance2.numpy = Mock(return_value=np.array([[5, 6], [7, 8]]))
        
        # Verify each instance has correct skeleton
        assert len(instance1.skeleton.nodes) == 2
        assert instance1.skeleton.nodes[0].name == "node_a"
        
        assert len(instance2.skeleton.nodes) == 2
        assert instance2.skeleton.nodes[0].name == "node_x"


class TestLabelsStructure:
    """Test handling of sleap-io Labels object."""

    def test_labels_video_collection(self):
        """Test that labels.videos is a collection."""
        labels = Mock()
        
        # Create mock videos
        video1 = Mock()
        video1.filename = "video1.mp4"
        video2 = Mock()
        video2.filename = "video2.mp4"
        
        labels.videos = [video1, video2]
        
        # Test iteration
        video_names = []
        for video in labels.videos:
            if hasattr(video, "filename"):
                video_names.append(video.filename)
        
        assert len(video_names) == 2
        assert "video1.mp4" in video_names
        assert "video2.mp4" in video_names

    def test_labels_skeleton_collection(self):
        """Test that labels.skeletons is a collection."""
        labels = Mock()
        
        skeleton1 = Mock()
        skeleton1.nodes = [Mock(name="node1")]
        skeleton2 = Mock()
        skeleton2.nodes = [Mock(name="node2"), Mock(name="node3")]
        
        labels.skeletons = [skeleton1, skeleton2]
        
        # Test skeleton access
        assert len(labels.skeletons) == 2
        assert len(labels.skeletons[0].nodes) == 1
        assert len(labels.skeletons[1].nodes) == 2

    def test_labels_missing_attributes(self):
        """Test handling of labels with missing attributes."""
        labels = Mock()
        
        # Missing videos
        del labels.videos
        videos = get_videos_in_labels(labels)
        assert len(videos) == 0
        
        # Missing tracks
        del labels.tracks
        # Should not crash
        assert not hasattr(labels, "tracks")


class TestRealSLEAPData:
    """Test with real SLEAP data to catch actual structure issues."""

    @pytest.fixture
    def real_labels(self):
        """Load real SLEAP data."""
        test_file = Path("tests/data/one_vid_lateral_root_MK22_Day14_test_labels.v003.slp")
        if test_file.exists():
            return sio.load_slp(test_file)
        pytest.skip("Test SLEAP file not found")

    def test_real_video_structure(self, real_labels):
        """Test real video object structure."""
        assert hasattr(real_labels, "videos")
        assert len(real_labels.videos) > 0
        
        for video in real_labels.videos:
            # Check video attributes
            assert hasattr(video, "filename") or hasattr(video.backend, "filename")
            
            # Get filename safely
            if hasattr(video, "filename"):
                filename = video.filename
                # Could be string, Path, or list
                if isinstance(filename, list) and len(filename) > 0:
                    filename = filename[0]
                assert filename is not None

    def test_real_instance_structure(self, real_labels):
        """Test real instance structure."""
        assert len(real_labels) > 0  # Has labeled frames
        
        for lf in real_labels:
            assert hasattr(lf, "instances")
            assert hasattr(lf, "frame_idx")
            
            for instance in lf.instances:
                # Check instance has required methods/attributes
                assert hasattr(instance, "numpy")
                assert callable(instance.numpy)
                
                # Check skeleton
                assert hasattr(instance, "skeleton")
                assert hasattr(instance.skeleton, "nodes")
                
                # Get coordinates
                coords = instance.numpy()
                assert isinstance(coords, np.ndarray)
                assert coords.ndim == 2
                assert coords.shape[1] == 2  # x, y coordinates
                
                # Number of points should match number of nodes
                assert coords.shape[0] == len(instance.skeleton.nodes)

    def test_real_skeleton_structure(self, real_labels):
        """Test real skeleton structure."""
        assert hasattr(real_labels, "skeletons")
        assert len(real_labels.skeletons) > 0
        
        for skeleton in real_labels.skeletons:
            assert hasattr(skeleton, "nodes")
            assert len(skeleton.nodes) > 0
            
            for node in skeleton.nodes:
                assert hasattr(node, "name")
                assert isinstance(node.name, str)
                assert len(node.name) > 0

    def test_real_data_extraction(self, real_labels):
        """Test that our extraction functions work with real data."""
        # Test video name extraction
        for lf in real_labels:
            video_name = extract_video_name(lf)
            assert video_name != "unknown"
            assert isinstance(video_name, str)
            assert len(video_name) > 0
        
        # Test data extraction
        df = export_labels_to_dataframe(real_labels)
        assert not df.empty
        
        # Check for NA values that shouldn't be there
        assert not df["Video"].isna().any(), "Video names should not be NA"
        assert not df["Node"].isna().any(), "Node names should not be NA"
        assert df["X"].notna().sum() > 0, "Should have some valid X coordinates"
        assert df["Y"].notna().sum() > 0, "Should have some valid Y coordinates"
        
        # Check data types
        assert df["Frame_Index"].dtype in [int, np.int64, np.int32]
        assert df["Instance"].dtype in [int, np.int64, np.int32]
        assert df["X"].dtype in [float, np.float64, np.float32]
        assert df["Y"].dtype in [float, np.float64, np.float32]


class TestEdgeCases:
    """Test edge cases and potential silent failures."""

    def test_video_filename_edge_cases(self):
        """Test edge cases in video filename parsing."""
        # Empty list
        assert parse_video_filename([]) == "unknown"
        
        # List with None
        assert parse_video_filename([None]) == "unknown"
        
        # Malformed string representation
        assert parse_video_filename("[WindowsPath('incomplete") == "unknown"
        
        # Integer (non-string type)
        assert parse_video_filename(12345) == "unknown"
        
        # Very long path
        long_path = "/very/long/path/" + "subdir/" * 50 + "video.mp4"
        assert parse_video_filename(long_path) == "video"

    def test_coordinate_edge_cases(self):
        """Test edge cases in coordinate handling."""
        labeled_frame = Mock()
        labeled_frame.frame_idx = 0
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        
        # Instance with all NaN coordinates
        instance = Mock()
        instance.numpy = Mock(return_value=np.array([[np.nan, np.nan], [np.nan, np.nan]]))
        
        skeleton = Mock()
        skeleton.nodes = [Mock(name="node1"), Mock(name="node2")]
        instance.skeleton = skeleton
        
        labeled_frame.instances = [instance]
        
        # Should return empty list
        data = extract_instance_data(labeled_frame, frame_idx=0)
        assert len(data) == 0

    def test_missing_frame_idx(self):
        """Test handling of missing frame_idx attribute."""
        labeled_frame = Mock()
        del labeled_frame.frame_idx  # Remove attribute
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test.mp4"
        labeled_frame.instances = []
        
        # Should use provided frame_idx
        data = extract_instance_data(labeled_frame, frame_idx=42)
        # Even with no instances, should not crash
        assert isinstance(data, list)
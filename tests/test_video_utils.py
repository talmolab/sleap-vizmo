"""Tests for video_utils module."""

import pytest
from pathlib import Path, WindowsPath, PosixPath
from unittest.mock import Mock
from sleap_vizmo.video_utils import (
    extract_video_name,
    parse_video_filename,
    get_video_info,
)


class TestParseVideoFilename:
    """Test suite for parse_video_filename function."""

    def test_string_representation_of_windows_path_list(self):
        """Test parsing string representation of WindowsPath list (actual SLEAP format)."""
        filename = "[WindowsPath('Z:/Mikayla_Kappes/experiments/fungal_CLEs_exps/root_growth_assays/MK22_root_growth_assay_12_peptides_fresh_and_original/MK22_Scans/Day14_scans_MK22/S_Ri_set2_day14_20250527-103422_013.tif')]"
        result = parse_video_filename(filename)
        assert result == "S_Ri_set2_day14_20250527-103422_013"

    def test_string_representation_of_posix_path_list(self):
        """Test parsing string representation of PosixPath list."""
        filename = "[PosixPath('/home/user/data/video_001.mp4')]"
        result = parse_video_filename(filename)
        assert result == "video_001"

    def test_string_representation_of_generic_path_list(self):
        """Test parsing string representation of generic Path list."""
        filename = "[Path('/data/experiments/sample_video.avi')]"
        result = parse_video_filename(filename)
        assert result == "sample_video"

    def test_direct_path_object(self):
        """Test parsing direct Path object."""
        filename = Path("/path/to/test_video.mp4")
        result = parse_video_filename(filename)
        assert result == "test_video"

    def test_list_of_path_objects(self):
        """Test parsing list of Path objects."""
        filename = [Path("/path/to/video1.mp4"), Path("/path/to/video2.mp4")]
        result = parse_video_filename(filename)
        assert result == "video1"  # Should take first element

    def test_empty_list(self):
        """Test parsing empty list."""
        filename = []
        result = parse_video_filename(filename)
        assert result == "unknown"

    def test_simple_string_path(self):
        """Test parsing simple string path."""
        filename = "/home/user/data/my_video.mp4"
        result = parse_video_filename(filename)
        assert result == "my_video"

    def test_windows_string_path(self):
        """Test parsing Windows-style string path."""
        # Use forward slashes which work on all platforms
        filename = "C:/Users/test/Videos/experiment_01.avi"
        result = parse_video_filename(filename)
        assert result == "experiment_01"

    def test_none_input(self):
        """Test parsing None input."""
        result = parse_video_filename(None)
        assert result == "unknown"

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_video_filename("")
        assert result == "unknown"

    def test_path_with_multiple_dots(self):
        """Test parsing path with multiple dots in filename."""
        filename = "/data/test.video.v2.mp4"
        result = parse_video_filename(filename)
        assert result == "test.video.v2"

    def test_malformed_string_representation(self):
        """Test parsing malformed string representation."""
        filename = "[WindowsPath('incomplete"
        result = parse_video_filename(filename)
        assert result == "unknown"


class TestExtractVideoName:
    """Test suite for extract_video_name function."""

    def test_video_with_string_representation_filename(self):
        """Test extraction with string representation of Path list (actual SLEAP case)."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = (
            "[WindowsPath('Z:/path/to/S_Ri_set2_day14_20250527-103422_013.tif')]"
        )

        result = extract_video_name(labeled_frame)
        assert result == "S_Ri_set2_day14_20250527-103422_013"

    def test_video_with_direct_filename(self):
        """Test extraction with direct filename."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "/path/to/video.mp4"

        result = extract_video_name(labeled_frame)
        assert result == "video"

    def test_video_with_backend_filename(self):
        """Test extraction with backend filename."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = None
        del labeled_frame.video.filename  # Remove attribute
        labeled_frame.video.backend = Mock()
        labeled_frame.video.backend.filename = "/path/to/backend_video.mp4"

        result = extract_video_name(labeled_frame)
        assert result == "backend_video"

    def test_no_video_attribute(self):
        """Test extraction when no video attribute."""
        labeled_frame = Mock(spec=[])
        result = extract_video_name(labeled_frame)
        assert result == "unknown"

    def test_video_is_none(self):
        """Test extraction when video is None."""
        labeled_frame = Mock()
        labeled_frame.video = None
        result = extract_video_name(labeled_frame)
        assert result == "unknown"

    def test_no_filename_attributes(self):
        """Test extraction when no filename attributes exist."""
        labeled_frame = Mock()
        labeled_frame.video = Mock(spec=[])
        result = extract_video_name(labeled_frame)
        assert result == "unknown"


class TestGetVideoInfo:
    """Test suite for get_video_info function."""

    def test_string_representation_windows_path(self):
        """Test getting info from string representation of WindowsPath."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "[WindowsPath('Z:/data/S_Ri_set2_day14.tif')]"
        labeled_frame.frame_idx = 42

        info = get_video_info(labeled_frame)

        assert info["name"] == "S_Ri_set2_day14"
        assert info["full_path"] == "Z:/data/S_Ri_set2_day14.tif"
        assert info["filename_type"] == "String representation of Path list"
        assert info["frame_idx"] == 42

    def test_path_object(self):
        """Test getting info from Path object."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = Path("/home/user/video.mp4")

        info = get_video_info(labeled_frame)

        assert info["name"] == "video"
        assert info["full_path"] == "/home/user/video.mp4"
        assert info["filename_type"] == "Path object"

    def test_list_of_paths(self):
        """Test getting info from list of Path objects."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = [
            Path("/data/video1.mp4"),
            Path("/data/video2.mp4"),
        ]

        info = get_video_info(labeled_frame)

        assert info["name"] == "video1"
        assert info["full_path"] == "/data/video1.mp4"
        assert info["filename_type"] == "List of 2 items"

    def test_string_path(self):
        """Test getting info from string path."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "/path/to/test.avi"

        info = get_video_info(labeled_frame)

        assert info["name"] == "test"
        assert info["full_path"] == "/path/to/test.avi"
        assert info["filename_type"] == "String path"

    def test_no_frame_idx(self):
        """Test when frame_idx is not available."""
        labeled_frame = Mock(spec=["video"])
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "video.mp4"

        info = get_video_info(labeled_frame)

        assert info["frame_idx"] is None

    def test_backend_filename(self):
        """Test getting info from backend filename."""
        labeled_frame = Mock()
        labeled_frame.video = Mock(spec=["backend"])
        labeled_frame.video.backend = Mock()
        labeled_frame.video.backend.filename = "/backend/video.mp4"

        info = get_video_info(labeled_frame)

        assert info["name"] == "video"
        assert info["full_path"] == "/backend/video.mp4"

    def test_unknown_type(self):
        """Test with unknown filename type."""
        labeled_frame = Mock()
        labeled_frame.video = Mock()
        labeled_frame.video.filename = 12345  # Invalid type

        info = get_video_info(labeled_frame)

        assert info["name"] == "unknown"
        assert info["filename_type"].startswith("Unknown type:")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

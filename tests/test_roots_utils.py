"""Tests for SLEAP-roots compatibility utilities."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import sleap_io as sio

from sleap_vizmo.roots_utils import (
    get_videos_in_labels,
    split_labels_by_video,
    save_individual_video_labels,
    validate_series_compatibility,
    create_series_name_from_video,
)


class TestGetVideosInLabels:
    """Test suite for get_videos_in_labels function."""

    def test_single_video(self):
        """Test with single video."""
        labels = Mock()
        video = Mock()
        video.filename = "test_video.mp4"
        labels.videos = [video]

        videos = get_videos_in_labels(labels)

        assert len(videos) == 1
        assert videos[0][0] == "test_video"
        assert videos[0][1] == video

    def test_multiple_videos(self):
        """Test with multiple videos."""
        labels = Mock()
        video1 = Mock()
        video1.filename = "video1.mp4"
        video2 = Mock()
        video2.filename = "video2.mp4"
        labels.videos = [video1, video2]

        videos = get_videos_in_labels(labels)

        assert len(videos) == 2
        assert videos[0][0] == "video1"
        assert videos[1][0] == "video2"

    def test_no_videos(self):
        """Test with no videos."""
        labels = Mock()
        labels.videos = []

        videos = get_videos_in_labels(labels)

        assert len(videos) == 0

    def test_no_videos_attribute(self):
        """Test when labels has no videos attribute."""
        labels = Mock()
        del labels.videos

        videos = get_videos_in_labels(labels)

        assert len(videos) == 0


class TestSplitLabelsByVideo:
    """Test suite for split_labels_by_video function."""

    def test_single_video_labels(self):
        """Test splitting labels with single video."""
        labels = Mock()
        video = Mock()
        video.filename = "single_video.mp4"
        labels.videos = [video]
        labels.labeled_frames = []
        labels.skeletons = []
        labels.tracks = []

        result = split_labels_by_video(labels)

        assert len(result) == 1
        assert "single_video" in result
        assert result["single_video"] == labels

    def test_multi_video_split(self):
        """Test splitting labels with multiple videos."""
        labels = Mock()

        # Create two videos
        video1 = Mock()
        video1.filename = "video1.mp4"
        video2 = Mock()
        video2.filename = "video2.mp4"
        labels.videos = [video1, video2]

        # Create frames for each video
        frame1 = Mock()
        frame1.video = video1
        frame2 = Mock()
        frame2.video = video2
        frame3 = Mock()
        frame3.video = video1

        labels.labeled_frames = [frame1, frame2, frame3]
        labels.skeletons = ["skeleton1"]
        labels.tracks = ["track1"]
        labels.provenance = {"filename": "original.slp"}

        result = split_labels_by_video(labels)

        assert len(result) == 2
        assert "video1" in result
        assert "video2" in result

        # Check video1 labels
        video1_labels = result["video1"]
        assert len(video1_labels.labeled_frames) == 2
        assert video1_labels.labeled_frames[0] == frame1
        assert video1_labels.labeled_frames[1] == frame3
        assert len(video1_labels.videos) == 1
        assert video1_labels.videos[0] == video1

        # Check video2 labels
        video2_labels = result["video2"]
        assert len(video2_labels.labeled_frames) == 1
        assert video2_labels.labeled_frames[0] == frame2
        assert len(video2_labels.videos) == 1
        assert video2_labels.videos[0] == video2

        # Check both have skeletons and tracks
        assert video1_labels.skeletons == labels.skeletons
        assert video2_labels.skeletons == labels.skeletons
        assert video1_labels.tracks == labels.tracks
        assert video2_labels.tracks == labels.tracks

    def test_no_videos_fallback(self):
        """Test when no videos are present."""
        labels = Mock()
        labels.videos = []

        result = split_labels_by_video(labels)

        assert len(result) == 1
        assert "unknown" in result
        assert result["unknown"] == labels


class TestSaveIndividualVideoLabels:
    """Test suite for save_individual_video_labels function."""

    @patch("sleap_vizmo.roots_utils.sio.save_slp")
    def test_save_slp_format(self, mock_save_slp):
        """Test saving in SLP format."""
        labels = Mock()
        video = Mock()
        video.filename = "test_video.mp4"
        labels.videos = [video]
        labels.labeled_frames = []
        labels.skeletons = []
        labels.tracks = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            result = save_individual_video_labels(
                labels, output_dir, prefix="plant_", suffix="_primary"
            )

            assert len(result) == 1
            assert "test_video" in result
            expected_path = output_dir / "plant_test_video_primary.slp"
            assert result["test_video"] == expected_path

            # Check save was called
            mock_save_slp.assert_called_once()
            # Check the path argument matches
            saved_path = Path(mock_save_slp.call_args[0][1])
            assert saved_path.name == expected_path.name

    @patch("sleap_vizmo.roots_utils.split_labels_by_video")
    @patch("sleap_vizmo.roots_utils.sio.save_slp")
    def test_multi_video_save(self, mock_save_slp, mock_split):
        """Test saving multiple videos."""
        # Mock split to return two video labels
        video1_labels = Mock()
        video2_labels = Mock()
        mock_split.return_value = {
            "video1": video1_labels,
            "video2": video2_labels,
        }

        labels = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            result = save_individual_video_labels(labels, output_dir)

            assert len(result) == 2
            assert "video1" in result
            assert "video2" in result
            assert mock_save_slp.call_count == 2


class TestValidateSeriesCompatibility:
    """Test suite for validate_series_compatibility function."""

    def test_valid_labels(self):
        """Test with valid labels for Series."""
        labels = Mock()
        labels.videos = [Mock()]
        labels.labeled_frames = [Mock(), Mock()]
        labels.tracks = [Mock()]

        skeleton = Mock()
        node1 = Mock()
        node1.name = "root_tip"
        node2 = Mock()
        node2.name = "root_base"
        skeleton.nodes = [node1, node2]
        labels.skeletons = [skeleton]

        # All frames have video references
        for lf in labels.labeled_frames:
            lf.video = labels.videos[0]

        result = validate_series_compatibility(labels)

        assert result["is_compatible"] is True
        assert len(result["errors"]) == 0
        assert result["video_count"] == 1
        assert result["frame_count"] == 2
        assert result["has_tracks"] is True
        assert "skeleton_0" in result["skeleton_info"]
        assert result["skeleton_info"]["skeleton_0"]["node_count"] == 2

    def test_no_videos(self):
        """Test labels with no videos."""
        labels = Mock()
        labels.videos = []
        labels.labeled_frames = [Mock()]

        # Create proper mock skeleton
        skeleton = Mock()
        skeleton.nodes = []
        labels.skeletons = [skeleton]

        result = validate_series_compatibility(labels)

        assert result["is_compatible"] is False
        assert "No videos found" in str(result["errors"])

    def test_no_frames(self):
        """Test labels with no frames."""
        labels = Mock()
        labels.videos = [Mock()]
        labels.labeled_frames = []

        # Create proper mock skeleton
        skeleton = Mock()
        skeleton.nodes = []
        labels.skeletons = [skeleton]

        result = validate_series_compatibility(labels)

        assert result["is_compatible"] is False
        assert "No labeled frames found" in str(result["errors"])

    def test_no_skeletons(self):
        """Test labels with no skeletons."""
        labels = Mock()
        labels.videos = [Mock()]
        labels.labeled_frames = [Mock()]
        labels.skeletons = []

        result = validate_series_compatibility(labels)

        assert result["is_compatible"] is False
        assert "No skeletons found" in str(result["errors"])

    def test_multi_video_warning(self):
        """Test warning for multi-video labels."""
        labels = Mock()
        labels.videos = [Mock(), Mock()]
        labels.labeled_frames = [Mock()]

        # Create proper mock skeleton
        skeleton = Mock()
        skeleton.nodes = []
        labels.skeletons = [skeleton]
        labels.tracks = []

        result = validate_series_compatibility(labels)

        assert result["video_count"] == 2
        assert any("2 videos" in w for w in result["warnings"])
        assert any("split_labels_by_video" in w for w in result["warnings"])

    def test_frames_without_video_warning(self):
        """Test warning for frames without video reference."""
        labels = Mock()
        labels.videos = [Mock()]

        frame1 = Mock()
        frame1.video = labels.videos[0]
        frame2 = Mock()
        frame2.video = None

        labels.labeled_frames = [frame1, frame2]

        # Create proper mock skeleton
        skeleton = Mock()
        skeleton.nodes = []
        labels.skeletons = [skeleton]
        labels.tracks = []

        result = validate_series_compatibility(labels)

        assert any("1 frames have no video reference" in w for w in result["warnings"])


class TestCreateSeriesNameFromVideo:
    """Test suite for create_series_name_from_video function."""

    def test_simple_name(self):
        """Test with simple filename."""
        assert create_series_name_from_video("test_video.mp4") == "test_video"

    def test_path_extraction(self):
        """Test extracting name from path."""
        assert create_series_name_from_video("/path/to/video.mp4") == "video"

    def test_strip_extensions(self):
        """Test stripping common extensions."""
        assert create_series_name_from_video("data.avi") == "data"
        assert create_series_name_from_video("scan.tif") == "scan"
        assert create_series_name_from_video("tracking.h5") == "tracking"

    def test_keep_extensions(self):
        """Test keeping extensions when requested."""
        assert (
            create_series_name_from_video("data.avi", strip_extensions=False)
            == "data.avi"
        )
        assert (
            create_series_name_from_video("data.custom", strip_extensions=False)
            == "data.custom"
        )

    def test_character_replacement(self):
        """Test problematic character replacement."""
        assert create_series_name_from_video("my video.mp4") == "my_video"
        assert create_series_name_from_video("scan-001.mp4") == "scan_001"
        assert create_series_name_from_video("my-video 2.mp4") == "my_video_2"


class TestIntegrationWithRealData:
    """Integration tests with real SLEAP data."""

    def test_real_labels_validation(self, test_labels):
        """Test validation with real SLEAP labels."""
        result = validate_series_compatibility(test_labels)

        assert result["is_compatible"] is True
        assert result["video_count"] >= 1
        assert result["frame_count"] >= 1
        assert result["skeleton_info"]  # Should have skeleton info

    def test_real_labels_split(self, test_labels):
        """Test splitting real labels (even if single video)."""
        result = split_labels_by_video(test_labels)

        assert len(result) >= 1
        # Each split should have frames
        for video_name, video_labels in result.items():
            assert hasattr(video_labels, "labeled_frames")
            assert hasattr(video_labels, "videos")
            assert len(video_labels.videos) == 1

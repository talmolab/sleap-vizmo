"""Tests for data_utils module."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from sleap_vizmo.data_utils import (
    extract_instance_data,
    export_labels_to_dataframe,
    save_labels_to_csv,
    summarize_labels,
)


class TestExtractInstanceData:
    """Test suite for extract_instance_data function."""

    def test_basic_extraction(self):
        """Test basic instance data extraction."""
        # Mock instance
        instance = Mock()
        instance.numpy.return_value = np.array([[10.0, 20.0], [30.0, 40.0]])
        instance.skeleton = Mock()
        node1 = Mock()
        node1.name = "root_tip"
        node2 = Mock()
        node2.name = "root_base"
        instance.skeleton.nodes = [node1, node2]

        # Mock labeled frame
        labeled_frame = Mock()
        labeled_frame.instances = [instance]
        labeled_frame.frame_idx = 5
        labeled_frame.video = Mock()
        labeled_frame.video.filename = "test_video.mp4"

        data = extract_instance_data(labeled_frame, frame_idx=0)

        assert len(data) == 2  # Two nodes
        assert data[0]["Video"] == "test_video"
        assert data[0]["Frame_Index"] == 5  # actual frame index
        assert data[0]["Labeled_Frame_Index"] == 0
        assert data[0]["Instance"] == 0
        assert data[0]["Node"] == "root_tip"
        assert data[0]["X"] == 10.0
        assert data[0]["Y"] == 20.0

    def test_with_nan_points(self):
        """Test extraction with NaN points."""
        # Mock instance with NaN
        instance = Mock()
        instance.numpy.return_value = np.array(
            [[10.0, 20.0], [np.nan, np.nan], [30.0, 40.0]]
        )
        instance.skeleton = Mock()
        node_a = Mock()
        node_a.name = "a"
        node_b = Mock()
        node_b.name = "b"
        node_c = Mock()
        node_c.name = "c"
        instance.skeleton.nodes = [node_a, node_b, node_c]

        labeled_frame = Mock()
        labeled_frame.instances = [instance]
        labeled_frame.frame_idx = 0

        data = extract_instance_data(labeled_frame, frame_idx=0, video_name="test")

        assert len(data) == 2  # Only 2 valid points (skips NaN)
        node_names = [d["Node"] for d in data]
        assert "b" not in node_names  # Middle node with NaN should be skipped

    def test_multiple_instances(self):
        """Test extraction with multiple instances."""
        # Create two instances
        instances = []
        for i in range(2):
            inst = Mock()
            inst.numpy.return_value = np.array([[i * 10, i * 20]])
            inst.skeleton = Mock()
            node = Mock()
            node.name = f"node_{i}"
            inst.skeleton.nodes = [node]
            instances.append(inst)

        labeled_frame = Mock()
        labeled_frame.instances = instances
        labeled_frame.frame_idx = 3

        data = extract_instance_data(labeled_frame, frame_idx=0, video_name="multi")

        assert len(data) == 2
        assert data[0]["Instance"] == 0
        assert data[1]["Instance"] == 1

    def test_no_frame_idx_attribute(self):
        """Test when labeled_frame has no frame_idx attribute."""
        instance = Mock()
        instance.numpy.return_value = np.array([[10.0, 20.0]])
        instance.skeleton = Mock()
        node = Mock()
        node.name = "node"
        instance.skeleton.nodes = [node]

        labeled_frame = Mock(spec=["instances"])  # No frame_idx
        labeled_frame.instances = [instance]

        data = extract_instance_data(labeled_frame, frame_idx=7, video_name="test")

        assert data[0]["Frame_Index"] == 7  # Falls back to provided frame_idx
        assert data[0]["Labeled_Frame_Index"] == 7


class TestExportLabelsToDataframe:
    """Test suite for export_labels_to_dataframe function."""

    def test_basic_export(self):
        """Test basic export to dataframe."""
        # Mock labels with 2 frames
        labels = Mock()
        labeled_frames = []

        for i in range(2):
            inst = Mock()
            inst.numpy.return_value = np.array([[i * 10, i * 20]])
            inst.skeleton = Mock()
            node = Mock()
            node.name = "node"
            inst.skeleton.nodes = [node]

            lf = Mock()
            lf.instances = [inst]
            lf.frame_idx = i * 5
            lf.video = Mock()
            lf.video.filename = f"video_{i}.mp4"
            labeled_frames.append(lf)

        labels.labeled_frames = labeled_frames

        df = export_labels_to_dataframe(labels)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # 2 frames, 1 point each
        assert list(df.columns) == [
            "Video",
            "Frame_Index",
            "Labeled_Frame_Index",
            "Instance",
            "Node",
            "X",
            "Y",
        ]
        assert df.iloc[0]["Video"] == "video_0"
        assert df.iloc[1]["Video"] == "video_1"

    def test_empty_labels(self):
        """Test export with no labeled frames."""
        labels = Mock()
        labels.labeled_frames = []

        df = export_labels_to_dataframe(labels)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == [
            "Video",
            "Frame_Index",
            "Labeled_Frame_Index",
            "Instance",
            "Node",
            "X",
            "Y",
        ]


class TestSaveLabelsToCSV:
    """Test suite for save_labels_to_csv function."""

    @patch("sleap_vizmo.data_utils.export_labels_to_dataframe")
    def test_basic_save(self, mock_export):
        """Test basic CSV save."""
        # Mock the export function
        mock_df = pd.DataFrame(
            {
                "Video": ["test"],
                "Frame_Index": [0],
                "Labeled_Frame_Index": [0],
                "Instance": [0],
                "Node": ["node"],
                "X": [10.0],
                "Y": [20.0],
            }
        )
        mock_export.return_value = mock_df

        # Mock labels
        labels = Mock()
        labels.labeled_frames = [Mock()]

        # Save to temporary path
        output_path = Path("test_output.csv")

        with patch.object(Path, "mkdir"):
            with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
                result = save_labels_to_csv(labels, output_path, include_metadata=False)

        assert result == output_path
        mock_to_csv.assert_called_once()

    @patch("sleap_vizmo.data_utils.export_labels_to_dataframe")
    def test_save_with_metadata(self, mock_export):
        """Test CSV save with metadata in filename."""
        # Mock the export function
        mock_df = pd.DataFrame(
            {
                "Video": ["test"] * 5,
                "Frame_Index": list(range(5)),
                "Labeled_Frame_Index": list(range(5)),
                "Instance": [0] * 5,
                "Node": ["node"] * 5,
                "X": list(range(5)),
                "Y": list(range(5)),
            }
        )
        mock_export.return_value = mock_df

        # Mock labels
        labels = Mock()
        labels.labeled_frames = [Mock(), Mock()]  # 2 frames

        output_path = Path("test_output.csv")

        with patch.object(Path, "mkdir"):
            with patch.object(pd.DataFrame, "to_csv"):
                result = save_labels_to_csv(labels, output_path, include_metadata=True)

        # Check that metadata was added to filename
        assert "2frames" in str(result)
        assert "5pts" in str(result)
        # Should have timestamp in filename
        assert result.stem != output_path.stem  # Filename was modified


class TestSummarizeLabels:
    """Test suite for summarize_labels function."""

    def test_basic_summary(self):
        """Test basic label summary."""
        # Mock skeleton
        skeleton = Mock()
        tip_node = Mock()
        tip_node.name = "tip"
        base_node = Mock()
        base_node.name = "base"
        skeleton.nodes = [tip_node, base_node]

        # Mock instances
        inst1 = Mock()
        inst1.numpy.return_value = np.array([[10, 20], [30, 40]])
        inst1.skeleton = skeleton

        inst2 = Mock()
        inst2.numpy.return_value = np.array([[50, 60], [np.nan, np.nan]])  # One NaN
        inst2.skeleton = skeleton

        # Mock frames
        lf1 = Mock()
        lf1.instances = [inst1, inst2]

        lf2 = Mock()
        lf2.instances = [inst1]

        # Mock video
        video = Mock()
        video.filename = "test_video.mp4"

        # Mock labels
        labels = Mock()
        labels.videos = [video]
        labels.skeletons = [skeleton]
        labels.labeled_frames = [lf1, lf2]
        labels.tracks = []

        summary = summarize_labels(labels)

        assert summary["n_videos"] == 1
        assert summary["n_skeletons"] == 1
        assert summary["n_labeled_frames"] == 2
        assert summary["n_tracks"] == 0
        assert summary["video_names"] == ["test_video"]
        assert summary["nodes_per_skeleton"]["skeleton_0"] == 2
        assert summary["instances_per_frame"] == [2, 1]
        assert summary["total_instances"] == 3
        assert summary["total_points"] == 5  # 6 total minus 1 NaN
        assert summary["avg_instances_per_frame"] == 1.5
        assert summary["min_instances_per_frame"] == 1
        assert summary["max_instances_per_frame"] == 2

    def test_empty_labels(self):
        """Test summary with empty labels."""
        labels = Mock()
        labels.videos = []
        labels.skeletons = []
        labels.labeled_frames = []
        labels.tracks = None

        summary = summarize_labels(labels)

        assert summary["n_videos"] == 0
        assert summary["n_skeletons"] == 0
        assert summary["n_labeled_frames"] == 0
        assert summary["n_tracks"] == 0
        assert summary["total_instances"] == 0
        assert summary["total_points"] == 0
        assert "avg_instances_per_frame" not in summary

    def test_labels_without_attributes(self):
        """Test summary when labels object lacks some attributes."""
        labels = Mock(spec=["labeled_frames"])
        labels.labeled_frames = []

        summary = summarize_labels(labels)

        assert summary["n_videos"] == 0
        assert summary["n_skeletons"] == 0
        assert summary["n_labeled_frames"] == 0
        assert summary["n_tracks"] == 0


class TestWithRealData:
    """Test suite using real SLEAP data from fixtures."""

    def test_extract_instance_data_real(self, first_labeled_frame):
        """Test instance data extraction with real SLEAP data."""
        data = extract_instance_data(first_labeled_frame, frame_idx=0)

        # Should have extracted data for all valid points
        assert len(data) > 0

        # Check data structure
        first_point = data[0]
        assert "Video" in first_point
        assert "Frame_Index" in first_point
        assert "Instance" in first_point
        assert "Node" in first_point
        assert "X" in first_point
        assert "Y" in first_point

        # Video name should be extracted correctly
        assert first_point["Video"] == "F_Ac_set1_day14_20250527-102755_001"

        # Check coordinates are reasonable
        assert isinstance(first_point["X"], (int, float))
        assert isinstance(first_point["Y"], (int, float))

    def test_export_labels_to_dataframe_real(self, test_labels):
        """Test dataframe export with real SLEAP labels."""
        df = export_labels_to_dataframe(test_labels)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert list(df.columns) == [
            "Video",
            "Frame_Index",
            "Labeled_Frame_Index",
            "Instance",
            "Node",
            "X",
            "Y",
        ]

        # Check video names are extracted
        assert not all(df["Video"] == "unknown")
        assert "F_Ac_set1_day14_20250527-102755_001" in df["Video"].values

    def test_summarize_labels_real(self, test_labels):
        """Test label summary with real SLEAP data."""
        summary = summarize_labels(test_labels)

        assert summary["n_labeled_frames"] > 0
        assert summary["total_instances"] > 0
        assert summary["total_points"] > 0
        assert len(summary["video_names"]) > 0
        assert "F_Ac_set1_day14_20250527-102755_001" in summary["video_names"]

        # Check skeleton info
        assert summary["n_skeletons"] > 0
        assert len(summary["nodes_per_skeleton"]) > 0

        # Check frame statistics
        assert len(summary["instances_per_frame"]) == summary["n_labeled_frames"]
        assert summary["avg_instances_per_frame"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for saving_utils module."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import tempfile
import shutil
from src.saving_utils import (
    create_output_directory,
    save_frame_plots,
    save_all_frames,
)


class TestCreateOutputDirectory:
    """Test suite for create_output_directory function."""

    def test_creates_directory_with_timestamp(self):
        """Test that directory is created with timestamp format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "test_output"

            # Create directory
            output_dir = create_output_directory(str(base_dir))

            # Check it exists
            assert output_dir.exists()
            assert output_dir.is_dir()

            # Check name format
            dir_name = output_dir.name
            assert dir_name.startswith("output_")

            # Verify timestamp format (now includes microseconds)
            # May have additional counter suffix if collision occurs
            timestamp_part = dir_name.replace("output_", "")
            # Remove any counter suffix
            if "_" in timestamp_part.split("_")[-1]:
                # Has counter, remove it
                parts = timestamp_part.split("_")
                if parts[-1].isdigit():
                    timestamp_part = "_".join(parts[:-1])

            # Should be able to parse as timestamp with microseconds
            datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S_%f")

    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "nested" / "dirs" / "output"

            # Create directory
            output_dir = create_output_directory(str(base_dir))

            # Check entire path exists
            assert output_dir.exists()
            assert base_dir.exists()

    def test_unique_timestamps(self):
        """Test that multiple calls create unique directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "test_output"

            # Create multiple directories
            dirs = []
            for _ in range(3):
                output_dir = create_output_directory(str(base_dir))
                dirs.append(output_dir)

            # All should be unique (now using millisecond precision)
            assert len(set(dirs)) == 3

            # All should exist
            for d in dirs:
                assert d.exists()


class TestSaveFramePlots:
    """Test suite for save_frame_plots function."""

    @pytest.fixture
    def mock_labeled_frame(self):
        """Create a mock labeled frame."""
        frame = Mock()
        frame.video = Mock()
        frame.video.filename = "test_video.mp4"
        frame.instances = []
        frame.image = None
        return frame

    @patch("src.saving_utils.create_frame_figure")
    def test_saves_png_and_html(self, mock_create_figure, mock_labeled_frame):
        """Test that both PNG and HTML files are saved."""
        # Mock the figure
        mock_fig = MagicMock()
        mock_create_figure.return_value = mock_fig

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Save plots
            png_path, html_path = save_frame_plots(
                mock_labeled_frame,
                frame_idx=5,
                output_dir=output_dir,
                video_name="test_video",
            )

            # Check paths
            assert png_path.name == "test_video_frame_0005.png"
            assert html_path.name == "test_video_frame_0005.html"
            assert png_path.parent == output_dir
            assert html_path.parent == output_dir

            # Check figure methods were called
            mock_fig.update_layout.assert_called_once()
            mock_fig.write_image.assert_called_once_with(
                str(png_path), width=1200, height=800, scale=2
            )
            mock_fig.write_html.assert_called_once()

    @patch("src.saving_utils.create_frame_figure")
    def test_uses_extracted_video_name(self, mock_create_figure, mock_labeled_frame):
        """Test that video name is extracted when not provided."""
        mock_fig = MagicMock()
        mock_create_figure.return_value = mock_fig

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Save without providing video name
            png_path, html_path = save_frame_plots(
                mock_labeled_frame, frame_idx=0, output_dir=output_dir
            )

            # Should use extracted name
            assert png_path.name == "test_video_frame_0000.png"
            assert html_path.name == "test_video_frame_0000.html"

    @patch("src.saving_utils.extract_video_name")
    @patch("src.saving_utils.create_frame_figure")
    def test_handles_unknown_video_name(self, mock_create_figure, mock_extract_name):
        """Test handling when video name extraction returns 'unknown'."""
        mock_fig = MagicMock()
        mock_create_figure.return_value = mock_fig
        mock_extract_name.return_value = "unknown"

        frame = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Save with unknown video name
            png_path, html_path = save_frame_plots(
                frame, frame_idx=0, output_dir=output_dir
            )

            # Should use "frame" as fallback
            assert png_path.name == "frame_frame_0000.png"
            assert html_path.name == "frame_frame_0000.html"


class TestSaveAllFrames:
    """Test suite for save_all_frames function."""

    @pytest.fixture
    def mock_labels(self):
        """Create mock labels with multiple frames."""
        labels = Mock()
        labels.filename = "test_labels.slp"  # Add filename attribute

        # Create mock frames
        frames = []
        for i in range(3):
            frame = Mock()
            frame.video = Mock()
            frame.video.filename = f"video_{i}.mp4"
            frame.instances = []
            frame.image = None
            frames.append(frame)

        labels.labeled_frames = frames
        return labels

    @patch("src.saving_utils.save_frame_plots")
    @patch("src.saving_utils.save_labels_to_csv")
    def test_saves_all_frames(self, mock_save_csv, mock_save_plots, mock_labels):
        """Test that all frames are saved."""
        # Mock return values
        mock_save_plots.side_effect = [
            (
                Path(f"video_{i}_frame_{i:04d}.png"),
                Path(f"video_{i}_frame_{i:04d}.html"),
            )
            for i in range(3)
        ]
        mock_save_csv.return_value = Path("sleap_labels_frames3_instances0.csv")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Save all frames
            results = save_all_frames(mock_labels, base_dir=temp_dir)

            # Check results
            assert results["output_dir"].exists()
            assert len(results["png_files"]) == 3
            assert len(results["html_files"]) == 3
            assert results["csv_file"] is not None
            assert len(results["errors"]) == 0

            # Check save_frame_plots was called for each frame
            assert mock_save_plots.call_count == 3

            # Check CSV was saved
            mock_save_csv.assert_called_once()

    def test_handles_errors_gracefully(self, mock_labels):
        """Test that errors are handled and reported."""
        with patch("src.saving_utils.save_frame_plots") as mock_save_plots:
            # Make first frame fail
            mock_save_plots.side_effect = [
                Exception("Test error"),
                (Path("frame_1.png"), Path("frame_1.html")),
                (Path("frame_2.png"), Path("frame_2.html")),
            ]

            with tempfile.TemporaryDirectory() as temp_dir:
                results = save_all_frames(mock_labels, base_dir=temp_dir)

                # Should have 2 successful saves and 1 error
                assert len(results["png_files"]) == 2
                assert len(results["html_files"]) == 2
                assert len(results["errors"]) == 1
                assert "Error saving frame 0" in results["errors"][0]

    def test_progress_callback(self, mock_labels):
        """Test that progress callback is called correctly."""
        progress_calls = []

        def track_progress(current, total, message):
            progress_calls.append((current, total, message))

        with patch("src.saving_utils.save_frame_plots") as mock_save_plots:
            mock_save_plots.side_effect = [
                (Path(f"frame_{i}.png"), Path(f"frame_{i}.html")) for i in range(3)
            ]

            with patch("src.saving_utils.save_labels_to_csv") as mock_save_csv:
                mock_save_csv.return_value = Path("instances.csv")

                with tempfile.TemporaryDirectory() as temp_dir:
                    save_all_frames(
                        mock_labels, base_dir=temp_dir, progress_callback=track_progress
                    )

                    # Should have progress calls for each frame + completion
                    assert len(progress_calls) >= 4
                    assert progress_calls[-1][2] == "Export complete!"

    def test_empty_labels(self):
        """Test handling of empty labels."""
        labels = Mock()
        labels.labeled_frames = []
        labels.filename = "empty_labels.slp"  # Add filename attribute

        with tempfile.TemporaryDirectory() as temp_dir:
            results = save_all_frames(labels, base_dir=temp_dir)

            # Should create directory but no files
            assert results["output_dir"].exists()
            assert len(results["png_files"]) == 0
            assert len(results["html_files"]) == 0
            # CSV should still be created (even if empty)
            assert results["csv_file"] is not None


class TestIntegration:
    """Integration tests with real SLEAP data."""

    def test_save_all_with_real_data(self, test_labels):
        """Test save_all_frames with real SLEAP data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # This test requires kaleido for image export
            try:
                import kaleido

                results = save_all_frames(test_labels, base_dir=temp_dir)

                # Should have saved at least one frame
                assert len(results["png_files"]) > 0
                assert len(results["html_files"]) > 0
                assert results["csv_file"] is not None

                # Check files actually exist
                for png_file in results["png_files"]:
                    assert png_file.exists()

                for html_file in results["html_files"]:
                    assert html_file.exists()

                assert results["csv_file"].exists()

            except ImportError:
                pytest.skip("kaleido not installed, skipping image export test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

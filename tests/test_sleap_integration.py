"""Integration tests with actual SLEAP files."""

import pytest
from pathlib import Path
from src.video_utils import extract_video_name, get_video_info, parse_video_filename
from src.data_utils import export_labels_to_dataframe


class TestSLEAPIntegration:
    """Test suite for actual SLEAP file integration."""

    def test_actual_sleap_file_exists(self, test_sleap_file_path):
        """Test that the test SLEAP file exists."""
        assert (
            test_sleap_file_path.exists()
        ), f"Test file should exist at {test_sleap_file_path}"
        assert test_sleap_file_path.suffix == ".slp"

    def test_load_sleap_labels(self, test_labels):
        """Test loading SLEAP labels."""
        assert test_labels is not None
        assert hasattr(test_labels, "labeled_frames")
        assert len(test_labels.labeled_frames) > 0

    def test_video_name_extraction_from_real_data(self, first_labeled_frame):
        """Test video name extraction from real SLEAP data."""
        # Debug: Print what we're working with
        print(f"\nDEBUG: first_labeled_frame type: {type(first_labeled_frame)}")
        print(f"DEBUG: has video attr: {hasattr(first_labeled_frame, 'video')}")

        if hasattr(first_labeled_frame, "video"):
            video = first_labeled_frame.video
            print(f"DEBUG: video type: {type(video)}")
            print(f"DEBUG: video value: {video}")

            if hasattr(video, "filename"):
                print(f"DEBUG: video.filename type: {type(video.filename)}")
                print(f"DEBUG: video.filename value: {repr(video.filename)}")

            if hasattr(video, "backend"):
                print(f"DEBUG: video.backend: {video.backend}")
                if hasattr(video.backend, "filename"):
                    print(f"DEBUG: video.backend.filename: {video.backend.filename}")

        # Test extraction
        video_name = extract_video_name(first_labeled_frame)
        print(f"DEBUG: Extracted video name: {video_name}")

        # Video name should not be unknown
        assert (
            video_name != "unknown"
        ), "Video name should be extracted from real SLEAP data"

        # Get full video info
        video_info = get_video_info(first_labeled_frame)
        print(f"DEBUG: Full video info: {video_info}")

        assert video_info["name"] != "unknown"
        assert video_info["filename_type"] != "unknown"

    def test_dataframe_export_with_real_data(self, test_labels):
        """Test dataframe export with real SLEAP data."""
        df = export_labels_to_dataframe(test_labels)

        print(f"\nDEBUG: DataFrame shape: {df.shape}")
        print(f"DEBUG: DataFrame columns: {list(df.columns)}")

        if len(df) > 0:
            print(f"DEBUG: First row video name: {df.iloc[0]['Video']}")
            print(f"DEBUG: Unique video names: {df['Video'].unique()}")

            # Check that video names are not all "unknown"
            assert not all(
                df["Video"] == "unknown"
            ), "All video names should not be 'unknown'"

    def test_parse_video_filename_variations(self):
        """Test parsing various filename formats we might encounter."""
        # Test cases based on what we've seen
        test_cases = [
            # String representation of WindowsPath list
            {
                "input": "[WindowsPath('Z:/data/S_Ri_set2_day14_20250527-103422_013.tif')]",
                "expected": "S_Ri_set2_day14_20250527-103422_013",
            },
            # Direct path string
            {
                "input": "Z:/data/S_Ri_set2_day14_20250527-103422_013.tif",
                "expected": "S_Ri_set2_day14_20250527-103422_013",
            },
            # List with Path object
            {"input": [Path("Z:/data/test_video.tif")], "expected": "test_video"},
        ]

        for case in test_cases:
            result = parse_video_filename(case["input"])
            assert result == case["expected"], f"Failed for input: {case['input']}"


class TestDebugVideoExtraction:
    """Debug tests to understand the video extraction issue."""

    def test_inspect_labeled_frame_structure(self, first_labeled_frame):
        """Inspect the structure of a real labeled frame."""
        print("\n=== LABELED FRAME STRUCTURE ===")
        print(f"Type: {type(first_labeled_frame)}")
        print(f"Attributes: {dir(first_labeled_frame)}")

        if hasattr(first_labeled_frame, "video"):
            video = first_labeled_frame.video
            print(f"\n=== VIDEO OBJECT ===")
            print(f"Type: {type(video)}")
            print(f"String repr: {str(video)}")
            print(
                f"Attributes: {[attr for attr in dir(video) if not attr.startswith('_')]}"
            )

            # Check specific attributes
            for attr in ["filename", "filenames", "path", "paths", "source", "backend"]:
                if hasattr(video, attr):
                    value = getattr(video, attr)
                    print(f"\nvideo.{attr}:")
                    print(f"  Type: {type(value)}")
                    print(f"  Value: {repr(value)}")

                    # If it's a list, check first element
                    if isinstance(value, list) and len(value) > 0:
                        print(f"  First element type: {type(value[0])}")
                        print(f"  First element value: {repr(value[0])}")

    def test_manual_extraction_attempts(self, first_labeled_frame):
        """Try various manual extraction methods."""
        if not hasattr(first_labeled_frame, "video"):
            pytest.skip("No video attribute")

        video = first_labeled_frame.video

        # Try different extraction methods
        attempts = []

        # Method 1: Direct filename
        if hasattr(video, "filename"):
            attempts.append(("video.filename", video.filename))

        # Method 2: filenames list
        if hasattr(video, "filenames"):
            attempts.append(("video.filenames", video.filenames))

        # Method 3: backend
        if hasattr(video, "backend"):
            backend = video.backend
            if hasattr(backend, "filename"):
                attempts.append(("video.backend.filename", backend.filename))
            if hasattr(backend, "filenames"):
                attempts.append(("video.backend.filenames", backend.filenames))
            if hasattr(backend, "path"):
                attempts.append(("video.backend.path", backend.path))

        # Method 4: Check __dict__
        if hasattr(video, "__dict__"):
            attempts.append(("video.__dict__", video.__dict__))

        print("\n=== EXTRACTION ATTEMPTS ===")
        for method, value in attempts:
            print(f"\n{method}:")
            print(f"  Type: {type(value)}")
            print(f"  Value: {repr(value)}")

            # Try to extract name
            try:
                name = parse_video_filename(value)
                print(f"  Extracted name: {name}")
            except Exception as e:
                print(f"  Extraction failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-vvs"])

"""Centralized pytest fixtures for SLEAP visualization tests."""

import pytest
from pathlib import Path
import sleap_io


@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def test_sleap_file_path(test_data_dir):
    """Get path to the test SLEAP file."""
    return test_data_dir / "one_vid_lateral_root_MK22_Day14_test_labels.v003.slp"


@pytest.fixture
def test_labels(test_sleap_file_path):
    """Load the test SLEAP labels."""
    if not test_sleap_file_path.exists():
        pytest.skip(f"Test file not found: {test_sleap_file_path}")
    return sleap_io.load_slp(str(test_sleap_file_path))


@pytest.fixture
def first_labeled_frame(test_labels):
    """Get the first labeled frame from test data."""
    if not test_labels.labeled_frames:
        pytest.skip("No labeled frames in test data")
    return test_labels.labeled_frames[0]


@pytest.fixture
def mock_labeled_frame():
    """Create a mock labeled frame for unit tests."""
    from unittest.mock import Mock

    # Create mock instance
    instance = Mock()
    instance.numpy.return_value = [[10.0, 20.0], [30.0, 40.0]]
    instance.skeleton = Mock()
    instance.skeleton.nodes = [Mock(name="root_tip"), Mock(name="root_base")]

    # Create mock video
    video = Mock()
    video.filename = (
        "[WindowsPath('Z:/path/to/S_Ri_set2_day14_20250527-103422_013.tif')]"
    )

    # Create mock labeled frame
    labeled_frame = Mock()
    labeled_frame.instances = [instance]
    labeled_frame.video = video
    labeled_frame.frame_idx = 0

    return labeled_frame

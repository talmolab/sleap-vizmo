"""Tests for pipeline detection utilities."""
import pytest
from pathlib import Path
from sleap_vizmo.pipeline_utils import (
    detect_root_types,
    get_compatible_pipelines,
    combine_labels_from_configs,
    get_file_summary,
    validate_file_config,
)
import sleap_io as sio


class TestDetectRootTypes:
    """Test root type detection from file configurations."""
    
    def test_empty_configs(self):
        """Test with empty configuration list."""
        result = detect_root_types([])
        assert result == {"primary": False, "lateral": False, "crown": False}
    
    def test_single_primary(self):
        """Test with single primary root configuration."""
        configs = [{"root_type": "primary", "path": "test.slp"}]
        result = detect_root_types(configs)
        assert result == {"primary": True, "lateral": False, "crown": False}
    
    def test_single_lateral(self):
        """Test with single lateral root configuration."""
        configs = [{"root_type": "lateral", "path": "test.slp"}]
        result = detect_root_types(configs)
        assert result == {"primary": False, "lateral": True, "crown": False}
    
    def test_single_crown(self):
        """Test with single crown root configuration."""
        configs = [{"root_type": "crown", "path": "test.slp"}]
        result = detect_root_types(configs)
        assert result == {"primary": False, "lateral": False, "crown": True}
    
    def test_primary_and_lateral(self):
        """Test with both primary and lateral roots."""
        configs = [
            {"root_type": "primary", "path": "primary.slp"},
            {"root_type": "lateral", "path": "lateral.slp"},
        ]
        result = detect_root_types(configs)
        assert result == {"primary": True, "lateral": True, "crown": False}
    
    def test_all_root_types(self):
        """Test with all three root types."""
        configs = [
            {"root_type": "primary", "path": "primary.slp"},
            {"root_type": "lateral", "path": "lateral.slp"},
            {"root_type": "crown", "path": "crown.slp"},
        ]
        result = detect_root_types(configs)
        assert result == {"primary": True, "lateral": True, "crown": True}
    
    def test_invalid_root_type(self):
        """Test with invalid root type (should be ignored)."""
        configs = [
            {"root_type": "primary", "path": "primary.slp"},
            {"root_type": "invalid", "path": "invalid.slp"},
        ]
        result = detect_root_types(configs)
        assert result == {"primary": True, "lateral": False, "crown": False}
    
    def test_missing_root_type_key(self):
        """Test with missing root_type key."""
        configs = [
            {"path": "test.slp"},  # Missing root_type
            {"root_type": "primary", "path": "primary.slp"},
        ]
        result = detect_root_types(configs)
        assert result == {"primary": True, "lateral": False, "crown": False}


class TestGetCompatiblePipelines:
    """Test pipeline compatibility detection."""
    
    def test_no_root_types(self):
        """Test with no root types selected."""
        root_types = {"primary": False, "lateral": False, "crown": False}
        result = get_compatible_pipelines(root_types)
        assert result == []
    
    def test_primary_only(self):
        """Test with primary roots only."""
        root_types = {"primary": True, "lateral": False, "crown": False}
        result = get_compatible_pipelines(root_types)
        assert len(result) == 1
        assert result[0][0] == "PrimaryRootPipeline"
    
    def test_lateral_only(self):
        """Test with lateral roots only."""
        root_types = {"primary": False, "lateral": True, "crown": False}
        result = get_compatible_pipelines(root_types)
        assert len(result) == 1
        assert result[0][0] == "LateralRootPipeline"
    
    def test_crown_only(self):
        """Test with crown roots only."""
        root_types = {"primary": False, "lateral": False, "crown": True}
        result = get_compatible_pipelines(root_types)
        assert len(result) == 1
        assert result[0][0] == "OlderMonocotPipeline"
    
    def test_primary_and_lateral(self):
        """Test with primary and lateral roots (dicot)."""
        root_types = {"primary": True, "lateral": True, "crown": False}
        result = get_compatible_pipelines(root_types)
        assert len(result) == 2
        assert result[0][0] == "DicotPipeline"
        assert result[1][0] == "MultipleDicotPipeline"
    
    def test_primary_and_crown(self):
        """Test with primary and crown roots (young monocot)."""
        root_types = {"primary": True, "lateral": False, "crown": True}
        result = get_compatible_pipelines(root_types)
        assert len(result) == 1
        assert result[0][0] == "YoungerMonocotPipeline"
    
    def test_all_root_types(self):
        """Test with all root types (no compatible pipeline)."""
        root_types = {"primary": True, "lateral": True, "crown": True}
        result = get_compatible_pipelines(root_types)
        assert result == []
    
    def test_lateral_and_crown(self):
        """Test with lateral and crown only (no compatible pipeline)."""
        root_types = {"primary": False, "lateral": True, "crown": True}
        result = get_compatible_pipelines(root_types)
        assert result == []


class TestGetFileSummary:
    """Test file summary generation."""
    
    def test_empty_configs(self):
        """Test with empty configuration."""
        result = get_file_summary([])
        assert result == {"primary": [], "lateral": [], "crown": []}
    
    def test_single_file_each_type(self):
        """Test with one file per root type."""
        configs = [
            {"root_type": "primary", "path": "/path/to/primary.slp"},
            {"root_type": "lateral", "path": "/path/to/lateral.slp"},
            {"root_type": "crown", "path": "/path/to/crown.slp"},
        ]
        result = get_file_summary(configs)
        assert result["primary"] == ["primary.slp"]
        assert result["lateral"] == ["lateral.slp"]
        assert result["crown"] == ["crown.slp"]
    
    def test_multiple_files_same_type(self):
        """Test with multiple files of the same root type."""
        configs = [
            {"root_type": "primary", "path": "primary1.slp"},
            {"root_type": "primary", "path": "primary2.slp"},
            {"root_type": "lateral", "path": "lateral1.slp"},
        ]
        result = get_file_summary(configs)
        assert len(result["primary"]) == 2
        assert "primary1.slp" in result["primary"]
        assert "primary2.slp" in result["primary"]
        assert result["lateral"] == ["lateral1.slp"]
        assert result["crown"] == []
    
    def test_path_objects(self):
        """Test with Path objects instead of strings."""
        configs = [
            {"root_type": "primary", "path": Path("/path/to/primary.slp")},
            {"root_type": "lateral", "path": Path("/path/to/lateral.slp")},
        ]
        result = get_file_summary(configs)
        assert result["primary"] == ["primary.slp"]
        assert result["lateral"] == ["lateral.slp"]


class TestValidateFileConfig:
    """Test file configuration validation."""
    
    def test_empty_file_path(self):
        """Test with empty file path."""
        is_valid, message, labels = validate_file_config("", "primary")
        assert not is_valid
        assert "No file path provided" in message
        assert labels is None
    
    def test_invalid_root_type(self):
        """Test with invalid root type."""
        is_valid, message, labels = validate_file_config("test.slp", "invalid")
        assert not is_valid
        assert "Invalid root type" in message
        assert labels is None
    
    def test_nonexistent_file(self):
        """Test with non-existent file."""
        is_valid, message, labels = validate_file_config("/nonexistent/file.slp", "primary")
        assert not is_valid
        assert "File not found" in message
        assert labels is None
    
    def test_non_slp_file(self, tmp_path):
        """Test with non-.slp file."""
        # Create a temporary non-.slp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a slp file")
        
        is_valid, message, labels = validate_file_config(str(test_file), "primary")
        assert not is_valid
        assert "Not a .slp file" in message
        assert labels is None
    
    def test_valid_file(self, test_sleap_file_path):
        """Test with valid .slp file."""
        is_valid, message, labels = validate_file_config(test_sleap_file_path, "lateral")
        assert is_valid
        assert "Valid file" in message
        assert labels is not None
        assert len(labels.labeled_frames) > 0


class TestCombineLabelsFromConfigs:
    """Test combining labels from multiple configurations."""
    
    def test_empty_configs(self):
        """Test with empty configuration."""
        result = combine_labels_from_configs([])
        assert result is None
    
    def test_configs_without_labels(self):
        """Test with configs that don't have labels."""
        configs = [
            {"root_type": "primary", "path": "test.slp"},
            {"root_type": "lateral", "path": "test2.slp"},
        ]
        result = combine_labels_from_configs(configs)
        assert result is None
    
    def test_single_valid_config(self, test_labels):
        """Test with single valid configuration."""
        configs = [
            {"root_type": "lateral", "path": "test.slp", "labels": test_labels}
        ]
        result = combine_labels_from_configs(configs)
        assert result is not None
        assert len(result.labeled_frames) == len(test_labels.labeled_frames)
        assert len(result.videos) == len(test_labels.videos)
    
    def test_multiple_valid_configs(self, test_labels, test_data_dir):
        """Test combining multiple valid configurations."""
        # Load the primary labels
        primary_path = test_data_dir / "primary_root_MK22_Day14_labels.v003.slp"
        if primary_path.exists():
            primary_labels = sio.load_slp(str(primary_path))
            configs = [
                {"root_type": "lateral", "path": "lateral.slp", "labels": test_labels},
                {"root_type": "primary", "path": "primary.slp", "labels": primary_labels},
            ]
            result = combine_labels_from_configs(configs)
            assert result is not None
            # Combined labels should have frames from both
            expected_frames = len(test_labels.labeled_frames) + len(primary_labels.labeled_frames)
            assert len(result.labeled_frames) == expected_frames
            # Should have videos from both files
            assert len(result.videos) >= 1  # At least one video
        else:
            # If primary file doesn't exist, just test with single config
            configs = [{"root_type": "lateral", "path": "lateral.slp", "labels": test_labels}]
            result = combine_labels_from_configs(configs)
            assert result is not None
            assert len(result.labeled_frames) == len(test_labels.labeled_frames)
    
    def test_mixed_valid_invalid_configs(self, test_labels):
        """Test with mix of valid and invalid configurations."""
        configs = [
            {"root_type": "lateral", "path": "lateral.slp", "labels": test_labels},
            {"root_type": "primary", "path": "invalid.slp"},  # No labels
            {"root_type": "crown", "path": "crown.slp", "labels": None},  # None labels
        ]
        result = combine_labels_from_configs(configs)
        assert result is not None
        # Should only have frames from the valid config
        assert len(result.labeled_frames) == len(test_labels.labeled_frames)
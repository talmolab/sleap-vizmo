"""Tests for JSON utility functions."""

import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from sleap_vizmo.json_utils import (
    ensure_json_serializable,
    save_json,
    validate_json_serializable,
)


class TestEnsureJsonSerializable:
    """Test ensure_json_serializable function."""

    def test_numpy_integers(self):
        """Test conversion of numpy integer types."""
        assert ensure_json_serializable(np.int8(42)) == 42
        assert ensure_json_serializable(np.int16(42)) == 42
        assert ensure_json_serializable(np.int32(42)) == 42
        assert ensure_json_serializable(np.int64(42)) == 42
        assert ensure_json_serializable(np.uint8(42)) == 42
        assert ensure_json_serializable(np.uint16(42)) == 42
        assert ensure_json_serializable(np.uint32(42)) == 42
        assert ensure_json_serializable(np.uint64(42)) == 42

    def test_numpy_floats(self):
        """Test conversion of numpy float types."""
        assert ensure_json_serializable(np.float16(3.14)) == pytest.approx(
            3.14, rel=1e-2
        )
        assert ensure_json_serializable(np.float32(3.14)) == pytest.approx(3.14)
        assert ensure_json_serializable(np.float64(3.14)) == pytest.approx(3.14)

    def test_numpy_arrays(self):
        """Test conversion of numpy arrays."""
        arr = np.array([1, 2, 3])
        assert ensure_json_serializable(arr) == [1, 2, 3]

        arr_2d = np.array([[1, 2], [3, 4]])
        assert ensure_json_serializable(arr_2d) == [[1, 2], [3, 4]]

        arr_mixed = np.array([1.5, 2.5, 3.5])
        result = ensure_json_serializable(arr_mixed)
        assert result == [1.5, 2.5, 3.5]

    def test_pandas_series(self):
        """Test conversion of pandas Series."""
        series = pd.Series([1, 2, 3])
        assert ensure_json_serializable(series) == [1, 2, 3]

        series_with_numpy = pd.Series([np.int64(1), np.int64(2), np.int64(3)])
        assert ensure_json_serializable(series_with_numpy) == [1, 2, 3]

    def test_pandas_dataframe(self):
        """Test conversion of pandas DataFrame."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = ensure_json_serializable(df)
        assert result == [{"a": 1, "b": 3}, {"a": 2, "b": 4}]

    def test_nested_structures(self):
        """Test conversion of nested structures with numpy types."""
        nested = {
            "int": np.int64(42),
            "float": np.float32(3.14),
            "array": np.array([1, 2, 3]),
            "list": [np.int64(10), np.float64(20.5)],
            "dict": {
                "nested_int": np.int32(100),
                "nested_array": np.array([[1, 2], [3, 4]]),
            },
        }

        result = ensure_json_serializable(nested)

        assert result["int"] == 42
        assert result["float"] == pytest.approx(3.14)
        assert result["array"] == [1, 2, 3]
        assert result["list"] == [10, 20.5]
        assert result["dict"]["nested_int"] == 100
        assert result["dict"]["nested_array"] == [[1, 2], [3, 4]]

        # Ensure it's actually JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_sets(self):
        """Test conversion of sets."""
        s = {1, 2, 3}
        result = ensure_json_serializable(s)
        assert sorted(result) == [1, 2, 3]

    def test_bytes(self):
        """Test conversion of bytes."""
        b = b"hello"
        assert ensure_json_serializable(b) == "hello"

        # Test with non-UTF8 bytes
        b_invalid = b"\x80\x81"
        result = ensure_json_serializable(b_invalid)
        assert isinstance(result, str)

    def test_already_serializable(self):
        """Test that already serializable objects are unchanged."""
        assert ensure_json_serializable(42) == 42
        assert ensure_json_serializable(3.14) == 3.14
        assert ensure_json_serializable("hello") == "hello"
        assert ensure_json_serializable(True) is True
        assert ensure_json_serializable(None) is None
        assert ensure_json_serializable([1, 2, 3]) == [1, 2, 3]
        assert ensure_json_serializable({"a": 1}) == {"a": 1}


class TestSaveJson:
    """Test save_json function."""

    def test_save_with_numpy_types(self, tmp_path):
        """Test saving data with numpy types."""
        data = {
            "count": np.int64(42),
            "values": np.array([1, 2, 3]),
            "score": np.float32(0.95),
        }

        json_path = tmp_path / "test.json"
        save_json(data, json_path)

        # Verify file was created
        assert json_path.exists()

        # Load and verify content
        with open(json_path, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["count"] == 42
        assert loaded["values"] == [1, 2, 3]
        assert loaded["score"] == pytest.approx(0.95)

    def test_save_with_indent(self, tmp_path):
        """Test saving with custom indentation."""
        data = {"a": 1, "b": 2}
        json_path = tmp_path / "test.json"

        save_json(data, json_path, indent=4)

        with open(json_path, encoding="utf-8") as f:
            content = f.read()

        # Check that indentation is present
        assert '    "a"' in content  # 4 spaces


class TestValidateJsonSerializable:
    """Test validate_json_serializable function."""

    def test_valid_data(self):
        """Test validation of JSON-serializable data."""
        valid, error = validate_json_serializable({"a": 1, "b": "test"})
        assert valid is True
        assert error == ""

        valid, error = validate_json_serializable([1, 2, 3])
        assert valid is True
        assert error == ""

    def test_invalid_data(self):
        """Test validation of non-JSON-serializable data."""
        valid, error = validate_json_serializable({"a": np.int64(1)})
        assert valid is False
        assert "int64" in error

        valid, error = validate_json_serializable(np.array([1, 2, 3]))
        assert valid is False
        assert "ndarray" in error


# Integration test fixtures
@pytest.fixture
def complex_sleap_roots_data():
    """Create complex data similar to sleap-roots output."""
    return {
        "series_name": "test_series",
        "plant_count": np.int64(8),
        "measurements": {
            "primary_length": np.float64(125.5),
            "lateral_count": np.int32(15),
            "angles": np.array([45.2, 50.1, 48.7]),
            "root_system_width": np.float32(85.3),
        },
        "statistics": pd.DataFrame(
            {
                "trait": ["length", "width", "depth"],
                "mean": np.array([100.5, 80.2, 45.8]),
                "std": np.array([10.2, 8.5, 5.3]),
            }
        ),
        "metadata": {
            "processed": True,
            "version": "1.0",
            "plant_ids": [np.int64(i) for i in range(1, 9)],
        },
    }


def test_sleap_roots_integration(complex_sleap_roots_data, tmp_path):
    """Test handling of complex sleap-roots data structures."""
    # Ensure it can be made serializable
    serializable = ensure_json_serializable(complex_sleap_roots_data)

    # Verify key conversions
    assert serializable["plant_count"] == 8
    assert isinstance(serializable["plant_count"], int)
    assert serializable["measurements"]["angles"] == [45.2, 50.1, 48.7]
    assert len(serializable["statistics"]) == 3  # DataFrame converted to list of dicts
    assert all(isinstance(pid, int) for pid in serializable["metadata"]["plant_ids"])

    # Test saving to file
    json_path = tmp_path / "sleap_roots_output.json"
    save_json(complex_sleap_roots_data, json_path)

    # Verify we can load it back
    with open(json_path, encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["series_name"] == "test_series"
    assert loaded["plant_count"] == 8

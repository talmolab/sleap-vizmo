"""JSON utility functions for handling numpy and pandas types."""

import json
import numpy as np
import pandas as pd
from typing import Any, Union, Dict, List


def ensure_json_serializable(obj: Any) -> Any:
    """
    Convert an object to be JSON serializable by handling numpy/pandas types.

    Args:
        obj: Any object that needs to be JSON serializable

    Returns:
        JSON-serializable version of the object

    Examples:
        >>> import numpy as np
        >>> ensure_json_serializable(np.int64(42))
        42
        >>> ensure_json_serializable(np.array([1, 2, 3]))
        [1, 2, 3]
        >>> ensure_json_serializable({'a': np.float32(1.5), 'b': [np.int64(10)]})
        {'a': 1.5, 'b': [10]}
    """
    # Handle numpy integer types
    if isinstance(obj, np.integer):
        return int(obj)

    # Handle numpy floating types
    elif isinstance(obj, np.floating):
        return float(obj)

    # Handle numpy arrays
    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    # Handle pandas Series
    elif isinstance(obj, pd.Series):
        return obj.tolist()

    # Handle pandas DataFrame
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")

    # Handle bytes
    elif isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")

    # Handle dictionaries recursively
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}

    # Handle lists and tuples recursively
    elif isinstance(obj, (list, tuple)):
        return [ensure_json_serializable(item) for item in obj]

    # Handle sets
    elif isinstance(obj, set):
        return list(obj)

    # Return as-is for JSON-native types
    else:
        return obj


def save_json(data: Any, filepath: Union[str, "Path"], indent: int = 2) -> None:
    """
    Save data to JSON file, automatically handling numpy/pandas types.

    Args:
        data: Data to save
        filepath: Path to save the JSON file
        indent: JSON indentation level (default: 2)

    Raises:
        TypeError: If data cannot be made JSON serializable
    """
    from pathlib import Path

    filepath = Path(filepath)
    serializable_data = ensure_json_serializable(data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, indent=indent)


def validate_json_serializable(data: Any) -> tuple[bool, str]:
    """
    Check if data is JSON serializable and return validation result.

    Args:
        data: Data to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_json_serializable({'a': 1, 'b': 'test'})
        (True, '')
        >>> validate_json_serializable({'a': np.int64(1)})[0]
        False
    """
    try:
        json.dumps(data)
        return True, ""
    except (TypeError, ValueError) as e:
        return False, str(e)

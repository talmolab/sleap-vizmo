"""Utility functions for safe SLEAP data structure access."""

from typing import Any, List, Optional


def safe_len(obj: Any, attr: str) -> int:
    """
    Safely get length of an attribute that might be None.

    Args:
        obj: Object to check
        attr: Attribute name to check

    Returns:
        Length of attribute or 0 if None/missing
    """
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        if val is not None:
            return len(val)
    return 0


def safe_iter(obj: Any, attr: str) -> List:
    """
    Safely iterate over an attribute that might be None.

    Args:
        obj: Object to check
        attr: Attribute name to iterate over

    Returns:
        Iterable attribute or empty list if None/missing
    """
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        if val is not None:
            return val
    return []


def has_valid_attr(obj: Any, attr: str) -> bool:
    """
    Check if object has a non-None attribute.

    Args:
        obj: Object to check
        attr: Attribute name

    Returns:
        True if attribute exists and is not None
    """
    return hasattr(obj, attr) and getattr(obj, attr) is not None


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Safely get an attribute with a default value.

    Args:
        obj: Object to check
        attr: Attribute name
        default: Default value if attribute is None/missing

    Returns:
        Attribute value or default
    """
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        if val is not None:
            return val
    return default

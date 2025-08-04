"""Test to understand how Series.load_from_slps works."""

from sleap_roots.series import Series
import inspect


def test_load_from_slps():
    """Check how load_from_slps expects files to be organized."""

    print("\n=== Series.load_from_slps Analysis ===\n")

    # Check if the method exists
    if hasattr(Series, "load_from_slps"):
        # Check the signature
        sig = inspect.signature(Series.load_from_slps)
        print(f"Series.load_from_slps signature: {sig}")

        # Check docstring
        if Series.load_from_slps.__doc__:
            print(f"\nDocstring:\n{Series.load_from_slps.__doc__}")
    else:
        print("Series.load_from_slps not found")

    # Check for other loading methods
    print("\n=== Other Series loading methods ===")
    load_methods = [m for m in dir(Series) if "load" in m and not m.startswith("_")]
    for method in load_methods:
        print(f"  - {method}")


def test_pipeline_compatibility():
    """Determine which pipelines work with which root type combinations."""

    print("\n=== Pipeline Compatibility Matrix ===\n")

    # Based on the root types each pipeline expects
    compatibility = {
        "PrimaryRootPipeline": {
            "required": ["primary"],
            "optional": [],
            "description": "Single primary root only",
        },
        "LateralRootPipeline": {
            "required": ["lateral"],
            "optional": [],
            "description": "Lateral roots only",
        },
        "DicotPipeline": {
            "required": ["primary", "lateral"],
            "optional": [],
            "description": "Primary + lateral roots (single plant)",
        },
        "MultipleDicotPipeline": {
            "required": ["primary", "lateral"],
            "optional": [],
            "description": "Primary + lateral roots (multiple plants)",
        },
        "OlderMonocotPipeline": {
            "required": ["crown"],
            "optional": [],
            "description": "Crown roots only (older monocots)",
        },
        "YoungerMonocotPipeline": {
            "required": ["primary", "crown"],
            "optional": [],
            "description": "Primary + crown roots (younger monocots)",
        },
    }

    for pipeline, info in compatibility.items():
        print(f"{pipeline}:")
        print(f"  Required root types: {', '.join(info['required'])}")
        print(f"  Description: {info['description']}")
        print()


if __name__ == "__main__":
    test_load_from_slps()
    test_pipeline_compatibility()

"""Test to understand sleap-roots pipeline requirements."""

import pytest
from sleap_roots.trait_pipelines import (
    Pipeline,
    PrimaryRootPipeline,
    LateralRootPipeline,
    DicotPipeline,
    MultipleDicotPipeline,
    OlderMonocotPipeline,
    YoungerMonocotPipeline,
)
import inspect


def test_pipeline_requirements():
    """Analyze what each pipeline expects."""

    pipelines = {
        "PrimaryRootPipeline": PrimaryRootPipeline,
        "LateralRootPipeline": LateralRootPipeline,
        "DicotPipeline": DicotPipeline,
        "MultipleDicotPipeline": MultipleDicotPipeline,
        "OlderMonocotPipeline": OlderMonocotPipeline,
        "YoungerMonocotPipeline": YoungerMonocotPipeline,
    }

    print("\n=== Pipeline Analysis ===\n")

    for name, pipeline_class in pipelines.items():
        print(f"\n{name}:")

        # Create instance
        pipeline = pipeline_class()

        # Check what traits it expects as inputs
        if hasattr(pipeline, "traits"):
            input_traits = set()
            for trait in pipeline.traits:
                if hasattr(trait, "input_traits"):
                    input_traits.update(trait.input_traits)
            print(f"  Input traits expected: {sorted(input_traits)}")

        # Check docstring
        if pipeline_class.__doc__:
            doc_lines = pipeline_class.__doc__.strip().split("\n")
            print(f"  Description: {doc_lines[0]}")

        # Check methods
        methods = [
            m for m in dir(pipeline_class) if "compute" in m and not m.startswith("_")
        ]
        print(f"  Compute methods: {methods}")


def test_series_load_requirements():
    """Check how Series.load expects files."""
    from sleap_roots.series import Series

    print("\n=== Series.load Analysis ===\n")

    # Check the load method signature
    load_sig = inspect.signature(Series.load)
    print(f"Series.load signature: {load_sig}")

    # Check docstring
    if Series.load.__doc__:
        print(f"\nSeries.load docstring (first 500 chars):")
        print(Series.load.__doc__[:500])


def test_trait_definitions():
    """Check what root types are expected by examining trait definitions."""
    from sleap_roots.trait_pipelines import Pipeline

    print("\n=== Root Type Analysis ===\n")

    # Check common input traits across pipelines
    all_pipelines = [
        PrimaryRootPipeline(),
        LateralRootPipeline(),
        DicotPipeline(),
        MultipleDicotPipeline(),
        OlderMonocotPipeline(),
        YoungerMonocotPipeline(),
    ]

    root_types = set()
    for pipeline in all_pipelines:
        if hasattr(pipeline, "traits"):
            for trait in pipeline.traits:
                if hasattr(trait, "input_traits"):
                    for input_trait in trait.input_traits:
                        if "pts" in input_trait or "root" in input_trait:
                            root_types.add(input_trait)

    print(f"Root types found across all pipelines: {sorted(root_types)}")

    # Check which pipelines use which root types
    print("\nRoot types by pipeline:")
    for pipeline in all_pipelines:
        pipeline_name = pipeline.__class__.__name__
        pipeline_root_types = set()
        if hasattr(pipeline, "traits"):
            for trait in pipeline.traits:
                if hasattr(trait, "input_traits"):
                    for input_trait in trait.input_traits:
                        if "pts" in input_trait or "root" in input_trait:
                            pipeline_root_types.add(input_trait)
        print(f"  {pipeline_name}: {sorted(pipeline_root_types)}")


if __name__ == "__main__":
    test_pipeline_requirements()
    test_series_load_requirements()
    test_trait_definitions()

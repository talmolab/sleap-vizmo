"""Tests for sleap-roots imports and functionality."""

import pytest
import importlib
import inspect


class TestSleapRootsImports:
    """Test suite for verifying sleap-roots imports."""

    def test_sleap_roots_installed(self):
        """Test that sleap-roots can be imported."""
        try:
            import sleap_roots
            assert sleap_roots is not None
        except ImportError:
            pytest.fail("sleap-roots is not installed")

    def test_sleap_roots_version(self):
        """Check sleap-roots version."""
        import sleap_roots
        
        if hasattr(sleap_roots, "__version__"):
            print(f"sleap-roots version: {sleap_roots.__version__}")
        else:
            print("sleap-roots version not available")

    def test_trait_pipelines_module(self):
        """Test what's available in trait_pipelines module."""
        try:
            from sleap_roots import trait_pipelines
            
            # List all available functions/classes in trait_pipelines
            available = []
            for name, obj in inspect.getmembers(trait_pipelines):
                if not name.startswith("_"):  # Skip private members
                    available.append(name)
            
            print(f"Available in trait_pipelines: {sorted(available)}")
            
            # Check if MultipleDicotPipeline exists
            assert hasattr(trait_pipelines, "MultipleDicotPipeline"), (
                f"MultipleDicotPipeline not found. "
                f"Available: {sorted(available)}"
            )
            
            # Check if the pipeline has the method we need
            pipeline = trait_pipelines.MultipleDicotPipeline()
            assert hasattr(pipeline, "compute_multiple_dicots_traits"), (
                "MultipleDicotPipeline missing compute_multiple_dicots_traits method"
            )
            
        except ImportError as e:
            pytest.fail(f"Cannot import trait_pipelines: {e}")

    def test_series_class(self):
        """Test that Series class can be imported."""
        try:
            from sleap_roots import Series
            assert Series is not None
            print(f"Series class found: {Series}")
        except ImportError:
            # Try alternative import
            try:
                from sleap_roots.series import Series
                assert Series is not None
                print(f"Series class found via sleap_roots.series: {Series}")
            except ImportError as e:
                pytest.fail(f"Cannot import Series class: {e}")

    def test_find_trait_computation_functions(self):
        """Search for trait computation functions in sleap-roots."""
        import sleap_roots
        
        # Search through all modules for functions with 'trait' in name
        trait_functions = {}
        
        for module_name in dir(sleap_roots):
            if not module_name.startswith("_"):
                try:
                    module = getattr(sleap_roots, module_name)
                    if hasattr(module, "__dict__"):
                        for name, obj in inspect.getmembers(module):
                            if "trait" in name.lower() and (
                                inspect.isfunction(obj) or inspect.isclass(obj)
                            ):
                                trait_functions[f"{module_name}.{name}"] = obj
                except Exception:
                    pass
        
        print("\nFound trait-related functions/classes:")
        for path in sorted(trait_functions.keys()):
            print(f"  - {path}")
        
        # Also check for pipeline functions
        pipeline_functions = {}
        for module_name in dir(sleap_roots):
            if not module_name.startswith("_"):
                try:
                    module = getattr(sleap_roots, module_name)
                    if hasattr(module, "__dict__"):
                        for name, obj in inspect.getmembers(module):
                            if "pipeline" in name.lower() and (
                                inspect.isfunction(obj) or inspect.isclass(obj)
                            ):
                                pipeline_functions[f"{module_name}.{name}"] = obj
                except Exception:
                    pass
        
        print("\nFound pipeline-related functions/classes:")
        for path in sorted(pipeline_functions.keys()):
            print(f"  - {path}")

    def test_alternative_dicot_functions(self):
        """Look for alternative dicot trait computation functions."""
        import sleap_roots
        
        # Search for anything with 'dicot' in the name
        dicot_items = {}
        
        def search_module(module, prefix=""):
            """Recursively search module for dicot-related items."""
            for name in dir(module):
                if not name.startswith("_"):
                    try:
                        item = getattr(module, name)
                        full_name = f"{prefix}{name}" if prefix else name
                        
                        if "dicot" in name.lower():
                            dicot_items[full_name] = item
                            
                        # Recursively search submodules
                        if hasattr(item, "__dict__") and not inspect.isfunction(item):
                            search_module(item, f"{full_name}.")
                    except Exception:
                        pass
        
        search_module(sleap_roots)
        
        print("\nFound dicot-related items:")
        for path in sorted(dicot_items.keys()):
            print(f"  - {path}: {type(dicot_items[path]).__name__}")

    def test_sleap_roots_documentation(self):
        """Check available documentation and examples."""
        import sleap_roots
        
        print("\nsleap-roots main module docstring:")
        if sleap_roots.__doc__:
            print(sleap_roots.__doc__[:500] + "..." if len(sleap_roots.__doc__) > 500 else sleap_roots.__doc__)
        
        # Check if there's a trait_pipelines docstring
        try:
            from sleap_roots import trait_pipelines
            print("\ntrait_pipelines module docstring:")
            if trait_pipelines.__doc__:
                print(trait_pipelines.__doc__[:500] + "..." if len(trait_pipelines.__doc__) > 500 else trait_pipelines.__doc__)
        except ImportError:
            print("\ntrait_pipelines module not found")

    def test_complete_sleap_roots_workflow(self):
        """Test the complete workflow as used in sleap_viz.py."""
        # Test the imports
        try:
            import sleap_roots as sr
            from sleap_roots.trait_pipelines import MultipleDicotPipeline
            
            # Test Series import
            assert hasattr(sr, "Series"), "Series not found in sleap_roots"
            
            # Test pipeline instantiation
            pipeline = MultipleDicotPipeline()
            assert pipeline is not None, "Failed to create MultipleDicotPipeline instance"
            
            # Test method exists
            assert hasattr(pipeline, "compute_multiple_dicots_traits"), (
                "compute_multiple_dicots_traits method not found"
            )
            
            print("\nAll sleap-roots imports successful!")
            print(f"   - sleap_roots.Series: {sr.Series}")
            print(f"   - MultipleDicotPipeline: {MultipleDicotPipeline}")
            print(f"   - compute_multiple_dicots_traits: {pipeline.compute_multiple_dicots_traits}")
            
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
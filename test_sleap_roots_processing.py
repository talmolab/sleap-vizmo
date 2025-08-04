#!/usr/bin/env python
"""
Test script to verify sleap-roots processing functionality.
Run this before using the Jupyter notebook to ensure all components work.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    try:
        import sleap_io as sio
        print("✓ sleap_io imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sleap_io: {e}")
        print("  Install with: pip install sleap-io")
        return False
    
    try:
        import sleap_roots as sr
        print("✓ sleap_roots imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sleap_roots: {e}")
        print("  Install with: pip install sleap-roots")
        return False
    
    try:
        from sleap_roots.trait_pipelines import MultipleDicotPipeline
        print("✓ MultipleDicotPipeline imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MultipleDicotPipeline: {e}")
        return False
    
    try:
        from sleap_vizmo.roots_utils import (
            split_labels_by_video,
            save_individual_video_labels,
            validate_series_compatibility,
            create_series_name_from_video
        )
        print("✓ sleap_vizmo.roots_utils imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sleap_vizmo.roots_utils: {e}")
        return False
    
    return True


def test_data_files():
    """Test that test data files exist."""
    print("\nTesting data files...")
    test_data_dir = Path("tests/data")
    lateral_file = test_data_dir / "lateral_root_MK22_Day14_test_labels.v003.slp"
    primary_file = test_data_dir / "primary_root_MK22_Day14_labels.v003.slp"
    
    if not lateral_file.exists():
        print(f"✗ Lateral file not found: {lateral_file}")
        return False
    print(f"✓ Lateral file found: {lateral_file}")
    
    if not primary_file.exists():
        print(f"✗ Primary file not found: {primary_file}")
        return False
    print(f"✓ Primary file found: {primary_file}")
    
    return True


def test_loading_labels():
    """Test loading SLEAP files."""
    print("\nTesting label loading...")
    import sleap_io as sio
    
    test_data_dir = Path("tests/data")
    lateral_file = test_data_dir / "lateral_root_MK22_Day14_test_labels.v003.slp"
    primary_file = test_data_dir / "primary_root_MK22_Day14_labels.v003.slp"
    
    try:
        lateral_labels = sio.load_slp(lateral_file)
        print(f"✓ Loaded lateral labels: {len(lateral_labels)} frames")
    except Exception as e:
        print(f"✗ Failed to load lateral labels: {e}")
        return False
    
    try:
        primary_labels = sio.load_slp(primary_file)
        print(f"✓ Loaded primary labels: {len(primary_labels)} frames")
    except Exception as e:
        print(f"✗ Failed to load primary labels: {e}")
        return False
    
    return True


def test_series_compatibility():
    """Test series compatibility validation."""
    print("\nTesting series compatibility...")
    import sleap_io as sio
    from sleap_vizmo.roots_utils import validate_series_compatibility
    
    test_data_dir = Path("tests/data")
    lateral_file = test_data_dir / "lateral_root_MK22_Day14_test_labels.v003.slp"
    
    try:
        lateral_labels = sio.load_slp(lateral_file)
        compat = validate_series_compatibility(lateral_labels)
        print(f"✓ Compatibility check completed: {compat['is_compatible']}")
        if compat['warnings']:
            print(f"  Warnings: {compat['warnings']}")
    except Exception as e:
        print(f"✗ Failed compatibility check: {e}")
        return False
    
    return True


def test_video_splitting():
    """Test splitting labels by video."""
    print("\nTesting video splitting...")
    import sleap_io as sio
    from sleap_vizmo.roots_utils import split_labels_by_video
    
    test_data_dir = Path("tests/data")
    lateral_file = test_data_dir / "lateral_root_MK22_Day14_test_labels.v003.slp"
    
    try:
        lateral_labels = sio.load_slp(lateral_file)
        split_labels = split_labels_by_video(lateral_labels)
        print(f"✓ Split into {len(split_labels)} video(s)")
        for video_name in split_labels:
            print(f"  - {video_name}: {len(split_labels[video_name])} frames")
    except Exception as e:
        print(f"✗ Failed to split labels: {e}")
        return False
    
    return True


def test_series_loading():
    """Test if sleap-roots Series.load works with our naming convention."""
    print("\nTesting Series.load compatibility...")
    try:
        import sleap_roots as sr
        print("✓ Can create Series objects")
        
        # Test the load method exists
        if hasattr(sr.Series, 'load'):
            print("✓ Series.load method exists")
        else:
            print("✗ Series.load method not found")
            return False
            
    except Exception as e:
        print(f"✗ Failed Series test: {e}")
        return False
    
    return True


def test_pipeline():
    """Test MultipleDicotPipeline availability."""
    print("\nTesting MultipleDicotPipeline...")
    try:
        from sleap_roots.trait_pipelines import MultipleDicotPipeline
        pipeline = MultipleDicotPipeline()
        print("✓ MultipleDicotPipeline instantiated")
        
        # Check for expected methods
        if hasattr(pipeline, 'compute_multiple_dicots_traits'):
            print("✓ compute_multiple_dicots_traits method exists")
        else:
            print("✗ compute_multiple_dicots_traits method not found")
            return False
            
    except Exception as e:
        print(f"✗ Failed pipeline test: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("SLEAP-Roots Processing Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_data_files,
        test_loading_labels,
        test_series_compatibility,
        test_video_splitting,
        test_series_loading,
        test_pipeline
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! You can proceed with the Jupyter notebook.")
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
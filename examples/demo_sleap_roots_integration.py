"""
Demo script showing how to use the SLEAP-roots integration in sleap-vizmo.

This demonstrates:
1. Loading a multi-video SLEAP labels file
2. Visualizing frames (existing functionality)
3. Using the new SLEAP-roots integration to:
   - Split multi-video files
   - Save individual video files
   - Run trait computation (if sleap-roots is installed)
"""

import sleap_io as sio
from sleap_vizmo.roots_utils import (
    get_videos_in_labels,
    split_labels_by_video,
    save_individual_video_labels,
    validate_series_compatibility,
)

# Example usage
def demo_sleap_roots_workflow():
    # Load your multi-video labels file
    labels_path = "path/to/your/multi_video_labels.slp"
    # labels = sio.load_slp(labels_path)
    
    # For demo, we'll use the test file
    # Note: Run this from the project root directory
    labels = sio.load_slp("tests/data/lateral_root_MK22_Day14_test_labels.v003.slp")
    
    # Check what videos we have
    videos = get_videos_in_labels(labels)
    print(f"Found {len(videos)} video(s):")
    for video_name, video_obj in videos:
        print(f"  - {video_name}")
    
    # Validate Series compatibility
    compatibility = validate_series_compatibility(labels)
    print(f"\nSeries compatibility: {compatibility['is_compatible']}")
    if compatibility['warnings']:
        print("Warnings:")
        for warning in compatibility['warnings']:
            print(f"  - {warning}")
    
    # Split and save individual video files
    output_paths = save_individual_video_labels(
        labels,
        output_dir="./output/individual_videos",
        prefix="plant_",  # Optional prefix
        suffix=""         # Could use "_primary" or "_lateral"
    )
    
    print(f"\nSaved {len(output_paths)} individual video files:")
    for video_name, path in output_paths.items():
        print(f"  - {video_name}: {path}")
    
    # Now you can use these files with sleap-roots Series.load()
    print("\nNext steps:")
    print("1. Ensure your files are properly labeled as primary/lateral")
    print("2. Use sleap-roots Series.load() with the saved files")
    print("3. Run compute_multiple_dicots_traits() for trait analysis")

if __name__ == "__main__":
    print("SLEAP-roots Integration Demo")
    print("=" * 50)
    demo_sleap_roots_workflow()
    print("\nTo use the interactive app, run:")
    print("  marimo run sleap_viz.py")
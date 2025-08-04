#!/usr/bin/env python
"""
Standalone script to process SLEAP files with sleap-roots MultipleDicotPipeline.
This is a Python script version of the Jupyter notebook for command-line usage.
"""

import sleap_io as sio
import sleap_roots as sr
from sleap_roots.trait_pipelines import MultipleDicotPipeline
from sleap_vizmo.roots_utils import (
    split_labels_by_video,
    save_individual_video_labels,
    validate_series_compatibility,
    create_series_name_from_video
)
from sleap_vizmo.sleap_roots_processing import (
    create_expected_count_csv,
    move_output_files_to_directory,
    combine_trait_csvs,
    merge_traits_with_expected_counts,
    create_processing_summary,
    save_pre_execution_snapshot
)
from sleap_vizmo.json_utils import save_json
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import argparse


def process_sleap_files(lateral_file, primary_file, output_dir=None):
    """
    Process SLEAP files with sleap-roots MultipleDicotPipeline.
    
    Args:
        lateral_file: Path to lateral root SLEAP file
        primary_file: Path to primary root SLEAP file  
        output_dir: Output directory (creates timestamped dir if None)
    
    Returns:
        Path to final CSV file with all plant traits
    """
    # Create timestamped output directory if not specified
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_dir = Path("output") / f"sleap_roots_processing_{timestamp}"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Output directory: {output_dir}")
    
    # Load SLEAP files
    print("\n🔄 Loading SLEAP files...")
    lateral_labels = sio.load_slp(lateral_file)
    primary_labels = sio.load_slp(primary_file)
    
    print(f"  Lateral: {len(lateral_labels)} frames, {len(lateral_labels.videos)} videos")
    print(f"  Primary: {len(primary_labels)} frames, {len(primary_labels.videos)} videos")
    
    # Validate compatibility
    print("\n🔍 Validating Series compatibility...")
    lateral_compat = validate_series_compatibility(lateral_labels)
    primary_compat = validate_series_compatibility(primary_labels)
    
    if not lateral_compat['is_compatible']:
        print(f"  ⚠️ Lateral labels warnings: {lateral_compat['warnings']}")
    if not primary_compat['is_compatible']:
        print(f"  ⚠️ Primary labels warnings: {primary_compat['warnings']}")
    
    # Split by video
    print("\n✂️ Splitting labels by video...")
    lateral_split = split_labels_by_video(lateral_labels)
    primary_split = split_labels_by_video(primary_labels)
    
    print(f"  Lateral split into {len(lateral_split)} video(s)")
    print(f"  Primary split into {len(primary_split)} video(s)")
    
    # Save with proper naming
    print("\n💾 Saving individual video files...")
    series_data = {}
    
    # Process lateral roots
    for video_name, labels in lateral_split.items():
        series_name = create_series_name_from_video(video_name)
        if series_name not in series_data:
            series_data[series_name] = {}
        
        output_path = output_dir / f"{series_name}.lateral.slp"
        labels.save(str(output_path))
        series_data[series_name]['lateral_path'] = str(output_path)
        print(f"  Saved: {output_path.name}")
    
    # Process primary roots
    for video_name, labels in primary_split.items():
        series_name = create_series_name_from_video(video_name)
        if series_name not in series_data:
            series_data[series_name] = {}
        
        output_path = output_dir / f"{series_name}.primary.slp"
        labels.save(str(output_path))
        series_data[series_name]['primary_path'] = str(output_path)
        print(f"  Saved: {output_path.name}")
    
    # Load Series and process
    print(f"\n🌱 Loading {len(series_data)} Series...")
    all_series = []
    
    for series_name, paths in series_data.items():
        print(f"\n  Processing: {series_name}")
        load_kwargs = {'series_name': series_name}
        
        if 'primary_path' in paths:
            load_kwargs['primary_path'] = paths['primary_path']
        if 'lateral_path' in paths:
            load_kwargs['lateral_path'] = paths['lateral_path']
        
        try:
            series = sr.Series.load(**load_kwargs)
            all_series.append(series)
            print(f"    ✓ Loaded successfully")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Process with MultipleDicotPipeline
    print(f"\n🔬 Computing traits with MultipleDicotPipeline...")
    pipeline = MultipleDicotPipeline()
    all_traits = []
    
    for series in all_series:
        print(f"\n  Processing series: {series.series_name}")
        try:
            traits = pipeline.compute_multiple_dicots_traits(
                series,
                write_csv=True,
                csv_suffix=f"_{series.series_name}_traits.csv",
                output_dir=str(output_dir)
            )
            
            # Convert to DataFrame if needed
            if not isinstance(traits, pd.DataFrame):
                traits = pd.DataFrame(traits)
            
            traits['series_name'] = series.series_name
            all_traits.append(traits)
            print(f"    ✓ Computed traits for {len(traits)} plants")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Combine and save final CSV
    if all_traits:
        print("\n📊 Creating final CSV...")
        final_traits_df = pd.concat(all_traits, ignore_index=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        final_csv_path = output_dir / f"all_plants_traits_{timestamp}.csv"
        final_traits_df.to_csv(final_csv_path, index=False)
        
        print(f"\n✅ Success!")
        print(f"  Total plants: {len(final_traits_df)}")
        print(f"  Final CSV: {final_csv_path}")
        print(f"  Columns: {', '.join(final_traits_df.columns[:10])}...")
        
        # Save summary
        summary = {
            "timestamp": timestamp,
            "output_directory": str(output_dir),
            "series_processed": len(all_series),
            "total_plants": len(final_traits_df),
            "trait_columns": list(final_traits_df.columns)
        }
        
        summary_path = output_dir / "processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return final_csv_path
    else:
        print("\n⚠️ No traits computed successfully")
        return None


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Process SLEAP files with sleap-roots MultipleDicotPipeline"
    )
    parser.add_argument(
        "--lateral",
        default="tests/data/lateral_root_MK22_Day14_test_labels.v003.slp",
        help="Path to lateral root SLEAP file"
    )
    parser.add_argument(
        "--primary", 
        default="tests/data/primary_root_MK22_Day14_labels.v003.slp",
        help="Path to primary root SLEAP file"
    )
    parser.add_argument(
        "--output",
        help="Output directory (creates timestamped if not specified)"
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    lateral_path = Path(args.lateral)
    primary_path = Path(args.primary)
    
    if not lateral_path.exists():
        print(f"❌ Lateral file not found: {lateral_path}")
        return 1
    
    if not primary_path.exists():
        print(f"❌ Primary file not found: {primary_path}")
        return 1
    
    # Process files
    result = process_sleap_files(lateral_path, primary_path, args.output)
    
    return 0 if result else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
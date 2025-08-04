"""SLEAP-roots processing utilities for batch analysis."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np

from .json_utils import ensure_json_serializable, save_json


def create_expected_count_csv(
    all_series: List,
    series_data: Dict[str, Dict[str, str]],
    output_dir: Union[str, Path],
) -> tuple[pd.DataFrame, Path]:
    """
    Create expected plant count CSV for MultipleDicotPipeline.

    Args:
        all_series: List of loaded Series objects
        series_data: Dictionary mapping series names to file paths
        output_dir: Output directory path

    Returns:
        Tuple of (DataFrame with expected plant counts, Path to saved CSV)
    """
    expected_counts = []

    for series in all_series:
        # Get the series name which will be our plant_qr_code
        plant_qr_code = series.series_name

        # Count the number of instances (plants) in the primary root file
        if hasattr(series, "primary_labels") and series.primary_labels is not None:
            # Count unique instances across all frames
            all_instances = set()
            for lf in series.primary_labels:
                for instance in lf.instances:
                    all_instances.add(instance)

            num_plants = len(all_instances)
        else:
            # If no primary labels, default to 0
            num_plants = 0

        # Get the paths for documentation
        primary_path = ""
        lateral_path = ""

        # Find the corresponding paths from our series_data
        if plant_qr_code in series_data:
            primary_path = series_data[plant_qr_code].get("primary_path", "")
            lateral_path = series_data[plant_qr_code].get("lateral_path", "")

        # Extract genotype and replicate from the series name
        parts = plant_qr_code.split("_")
        genotype = "_".join(parts[:2]) if len(parts) > 1 else plant_qr_code

        # Try to extract replicate number from "set" part
        replicate = 1  # default
        for part in parts:
            if part.startswith("set"):
                try:
                    replicate = int(part.replace("set", ""))
                except:
                    pass

        # Create row for expected count CSV
        row = {
            "plant_qr_code": plant_qr_code,
            "genotype": genotype,
            "replicate": replicate,
            "path": primary_path,
            "qc_cylinder": 0,
            "qc_code": None,
            "number_of_plants_cylinder": num_plants,
            "primary_root_proofread": primary_path,
            "lateral_root_proofread": lateral_path if lateral_path else None,
        }

        expected_counts.append(row)
        print(f"{plant_qr_code}: {num_plants} plants detected")

    # Create DataFrame
    expected_count_df = pd.DataFrame(expected_counts)

    # Add empty columns to match the expected format
    for col in [
        "Unnamed: 9",
        "Unnamed: 10",
        "Unnamed: 11",
        "Unnamed: 12",
        "Instructions",
    ]:
        expected_count_df[col] = None

    # Save the expected count CSV
    output_dir = Path(output_dir)
    expected_count_path = output_dir / "expected_plant_counts.csv"
    expected_count_df.to_csv(expected_count_path, index=False)

    print(f"\n✅ Expected count CSV saved to: {expected_count_path}")
    print(f"Total series: {len(expected_count_df)}")
    print(
        f"Total plants across all series: {expected_count_df['number_of_plants_cylinder'].sum()}"
    )

    return expected_count_df, expected_count_path


def move_output_files_to_directory(
    output_dir: Union[str, Path], file_patterns: List[str]
) -> List[Path]:
    """
    Move files matching patterns to output directory.

    Args:
        output_dir: Destination directory
        file_patterns: List of glob patterns to match files

    Returns:
        List of moved file paths
    """
    import shutil
    import glob

    output_dir = Path(output_dir)
    moved_files = []

    print("\nMoving generated files to output directory...")

    for pattern in file_patterns:
        files = glob.glob(pattern)
        for file_path in files:
            src = Path(file_path)
            dst = output_dir / src.name
            shutil.move(str(src), str(dst))
            moved_files.append(dst)
            print(f"  Moved {src.name} to output directory")

    if moved_files:
        print(f"\n✅ All files moved to: {output_dir}")
    else:
        print(f"\n⚠️ No files found to move")

    return moved_files


def combine_trait_csvs(
    output_dir: Union[str, Path],
    csv_pattern: str = "*_all_plants_traits.csv",
    timestamp: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    Combine all individual plant trait CSVs into one dataframe.

    Args:
        output_dir: Directory containing CSV files
        csv_pattern: Glob pattern to match CSV files
        timestamp: Optional timestamp for output filename

    Returns:
        Combined dataframe or None if no files found
    """
    import glob

    output_dir = Path(output_dir)
    csv_pattern_full = str(output_dir / csv_pattern)
    csv_files = glob.glob(csv_pattern_full)

    print(f"Found {len(csv_files)} individual CSV files")

    if not csv_files:
        print("No individual CSV files found to combine")
        return None

    # Read and combine all CSVs
    all_plants_dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        # Extract series name from filename
        series_name = Path(csv_file).stem.replace("_all_plants_traits", "")
        df["series_name"] = series_name
        all_plants_dfs.append(df)
        print(f"  - {Path(csv_file).name}: {len(df)} plants")

    # Combine all dataframes
    all_plants_combined_df = pd.concat(all_plants_dfs, ignore_index=True)

    # Save the combined dataframe
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    final_combined_csv_path = output_dir / f"series_summary_statistics_{timestamp}.csv"
    all_plants_combined_df.to_csv(final_combined_csv_path, index=False)

    print(f"\n✅ Combined CSV saved: {final_combined_csv_path}")
    print(f"Total plants in combined CSV: {len(all_plants_combined_df)}")
    print(f"Columns: {list(all_plants_combined_df.columns)}")

    return all_plants_combined_df


def merge_traits_with_expected_counts(
    traits_df: pd.DataFrame,
    expected_count_df: pd.DataFrame,
    output_dir: Union[str, Path],
    timestamp: Optional[str] = None,
) -> pd.DataFrame:
    """
    Merge the combined traits dataframe with expected counts dataframe.

    Args:
        traits_df: DataFrame with all plant traits
        expected_count_df: DataFrame with expected plant counts and metadata
        output_dir: Output directory for saving merged CSV
        timestamp: Optional timestamp for filename

    Returns:
        Merged DataFrame with traits and expected count information
    """
    output_dir = Path(output_dir)

    # Merge on series_name/plant_qr_code
    # The traits_df has 'series_name' and expected_count_df has 'plant_qr_code'
    # These should match
    merged_df = traits_df.merge(
        expected_count_df,
        left_on="series_name",
        right_on="plant_qr_code",
        how="left",
        suffixes=("", "_expected"),
    )

    # Reorder columns to put metadata first
    metadata_cols = [
        "series_name",
        "plant_qr_code",
        "genotype",
        "replicate",
        "number_of_plants_cylinder",
        "primary_root_proofread",
        "lateral_root_proofread",
    ]

    # Get all other columns
    other_cols = [col for col in merged_df.columns if col not in metadata_cols]

    # Reorder
    ordered_cols = [
        col for col in metadata_cols if col in merged_df.columns
    ] + other_cols
    merged_df = merged_df[ordered_cols]

    # Save the merged CSV
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    merged_csv_path = output_dir / f"final_series_summary_with_metadata_{timestamp}.csv"
    merged_df.to_csv(merged_csv_path, index=False)

    print(f"\n✅ Merged traits with metadata saved to: {merged_csv_path}")
    print(f"Total rows: {len(merged_df)}")
    print(f"Total columns: {len(merged_df.columns)}")

    # Show summary of plants per series
    plants_per_series = merged_df.groupby("series_name").size()
    print(f"\nPlants per series:")
    for series, count in plants_per_series.items():
        expected = expected_count_df[expected_count_df["plant_qr_code"] == series][
            "number_of_plants_cylinder"
        ].values
        expected_val = expected[0] if len(expected) > 0 else "N/A"
        print(f"  {series}: {count} plants (expected: {expected_val})")

    return merged_df


def save_notebook_snapshot(
    output_dir: Union[str, Path],
    notebook_path: Optional[Union[str, Path]] = None,
    notebook_name: Optional[str] = None,
    suffix: str = "",
    save_html: bool = True,
) -> Optional[Path]:
    """
    Save a snapshot of the processing notebook to the output directory.

    Args:
        output_dir: Output directory to save the notebook
        notebook_path: Path to the notebook to copy. If None, looks for sleap_roots_processing.ipynb
        notebook_name: Name for the saved notebook snapshot. If None, uses default with suffix
        suffix: Suffix to add to the filename (e.g., "_before_execution", "_after_execution")
        save_html: Whether to also save an HTML version of the notebook

    Returns:
        Path to the saved notebook or None if not found
    """
    import shutil

    output_dir = Path(output_dir)

    # If no notebook path provided, look for the default notebook
    if notebook_path is None:
        # Try to find the notebook in common locations
        possible_paths = [
            Path("sleap_roots_processing.ipynb"),
            Path("../sleap_roots_processing.ipynb"),
            Path(__file__).parent.parent / "sleap_roots_processing.ipynb",
        ]

        for path in possible_paths:
            if path.exists():
                notebook_path = path
                break

    if notebook_path is None:
        print("⚠️ No processing notebook found to save snapshot")
        return None

    notebook_path = Path(notebook_path)

    if not notebook_path.exists():
        print(f"⚠️ Notebook not found at: {notebook_path}")
        return None

    # Determine the notebook name
    if notebook_name is None:
        base_name = "sleap_roots_processing_notebook"
        if suffix:
            notebook_name = f"{base_name}{suffix}.ipynb"
        else:
            notebook_name = f"{base_name}_snapshot.ipynb"

    # Copy the notebook to output directory
    destination = output_dir / notebook_name
    shutil.copy2(str(notebook_path), str(destination))

    print(
        f"📓 Saved notebook snapshot{' (' + suffix.replace('_', ' ').strip() + ')' if suffix else ''}: {destination.name}"
    )

    # Also save as HTML if requested
    if save_html:
        try:
            # Try to use nbconvert to create HTML version
            import subprocess

            html_name = notebook_name.replace(".ipynb", ".html")
            html_destination = output_dir / html_name

            # Use nbconvert command line tool
            # Note: --output should be just the filename, not the full path
            result = subprocess.run(
                [
                    "jupyter",
                    "nbconvert",
                    "--to",
                    "html",
                    "--output",
                    html_name,
                    "--output-dir",
                    str(output_dir),
                    str(destination),
                    "--no-input",  # Hide input cells for cleaner output
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"📄 Saved HTML version to: {html_name}")
            else:
                # If --no-input fails, try without it
                result = subprocess.run(
                    [
                        "jupyter",
                        "nbconvert",
                        "--to",
                        "html",
                        "--output",
                        html_name,
                        "--output-dir",
                        str(output_dir),
                        str(destination),
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print(f"📄 Saved HTML version to: {html_name}")
                else:
                    print(f"⚠️ Could not create HTML version: {result.stderr}")

        except (ImportError, FileNotFoundError) as e:
            print(f"⚠️ Could not create HTML version (nbconvert not available): {e}")
        except Exception as e:
            print(f"⚠️ Error creating HTML version: {e}")

    return destination


def save_pre_execution_snapshot(
    output_dir: Union[str, Path],
    notebook_path: Optional[Union[str, Path]] = None,
    save_html: bool = True,
) -> Optional[Path]:
    """
    Save a snapshot of the processing notebook before execution.

    This is a convenience function that calls save_notebook_snapshot with
    the "_before_execution" suffix.

    Args:
        output_dir: Output directory to save the notebook
        notebook_path: Path to the notebook to copy. If None, looks for sleap_roots_processing.ipynb
        save_html: Whether to also save an HTML version of the notebook

    Returns:
        Path to the saved notebook or None if not found
    """
    return save_notebook_snapshot(
        output_dir=output_dir,
        notebook_path=notebook_path,
        suffix="_before_execution",
        save_html=save_html,
    )


def create_processing_summary(
    timestamp: str,
    output_dir: Union[str, Path],
    input_files: Dict[str, Union[str, Path]],
    all_series: List,
    expected_count_df: pd.DataFrame,
    series_summary_df: Optional[pd.DataFrame] = None,
    all_traits_json_path: Optional[Union[str, Path]] = None,
    series_summary_csv_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Create and save a processing summary.

    Args:
        timestamp: Processing timestamp
        output_dir: Output directory path
        input_files: Dictionary of input file paths
        all_series: List of processed series
        expected_count_df: Expected count dataframe
        series_summary_df: Series summary statistics dataframe
        all_traits_json_path: Path to all traits JSON
        series_summary_csv_path: Path to series summary CSV

    Returns:
        Summary dictionary
    """
    output_dir = Path(output_dir)

    # Create summary dictionary
    summary = {
        "timestamp": timestamp,
        "output_directory": str(output_dir),
        "input_files": {k: str(v) for k, v in input_files.items()},
        "series_processed": len(all_series),
        "total_series_with_summary": (
            len(series_summary_df) if series_summary_df is not None else 0
        ),
        "pipeline_used": "MultipleDicotPipeline",
        "expected_count_csv": str(output_dir / "expected_plant_counts.csv"),
        "expected_total_plants": int(
            expected_count_df["number_of_plants_cylinder"].sum()
        ),
        "all_series_traits_json": (
            str(all_traits_json_path) if all_traits_json_path else None
        ),
        "series_summary_csv": (
            str(series_summary_csv_path) if series_summary_csv_path else None
        ),
        "summary_columns": (
            list(series_summary_df.columns) if series_summary_df is not None else []
        ),
    }

    # Save summary as JSON using our utility that handles numpy types
    summary_path = output_dir / "processing_summary.json"
    save_json(summary, summary_path)

    # Save notebook snapshot (after execution)
    notebook_snapshot_path = save_notebook_snapshot(
        output_dir, suffix="_after_execution"
    )
    if notebook_snapshot_path:
        summary["notebook_snapshot_after"] = str(notebook_snapshot_path)

    # Print summary
    print(f"\n📊 Processing Summary:")
    print(f"  - Series processed: {summary['series_processed']}")
    print(f"  - Expected plants: {summary['expected_total_plants']}")
    print(f"  - Series with summary statistics: {summary['total_series_with_summary']}")
    print(f"  - Output directory: {summary['output_directory']}")

    if summary.get("all_series_traits_json"):
        print(f"  - All traits JSON: {Path(summary['all_series_traits_json']).name}")

    if summary.get("series_summary_csv"):
        print(f"  - Series summary CSV: {Path(summary['series_summary_csv']).name}")

    print(f"  - Summary saved to: {summary_path.name}")

    return summary

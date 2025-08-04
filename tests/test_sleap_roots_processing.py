"""Tests for SLEAP-roots processing utilities."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
from unittest.mock import Mock, patch

from sleap_vizmo.sleap_roots_processing import (
    create_expected_count_csv,
    move_output_files_to_directory,
    combine_trait_csvs,
    merge_traits_with_expected_counts,
    create_processing_summary,
)


class TestCreateExpectedCountCsv:
    """Test create_expected_count_csv function."""
    
    def test_basic_functionality(self, tmp_path):
        """Test basic expected count CSV creation."""
        # Create mock series with primary labels
        mock_series = []
        series_data = {}
        
        for i in range(3):
            series = Mock()
            series.series_name = f"test_series_{i}"
            
            # Create mock labeled frames with instances
            mock_instances = [Mock() for _ in range(5 + i)]  # 5, 6, 7 instances
            mock_lf = Mock()
            mock_lf.instances = mock_instances
            
            series.primary_labels = [mock_lf]
            mock_series.append(series)
            
            # Add to series_data
            series_data[series.series_name] = {
                'primary_path': f"/path/to/{series.series_name}.primary.slp",
                'lateral_path': f"/path/to/{series.series_name}.lateral.slp"
            }
        
        # Create expected count CSV
        df, csv_path_returned = create_expected_count_csv(mock_series, series_data, tmp_path)
        
        # Verify DataFrame structure
        assert len(df) == 3
        assert 'plant_qr_code' in df.columns
        assert 'number_of_plants_cylinder' in df.columns
        assert 'primary_root_proofread' in df.columns
        assert 'lateral_root_proofread' in df.columns
        
        # Verify counts
        assert df['number_of_plants_cylinder'].tolist() == [5, 6, 7]
        
        # Verify CSV was saved
        csv_path = tmp_path / "expected_plant_counts.csv"
        assert csv_path.exists()
        assert csv_path_returned == csv_path
    
    def test_genotype_extraction(self, tmp_path):
        """Test genotype and replicate extraction from series names."""
        series = Mock()
        series.series_name = "F_Ac_set2_day14_20250527_102755_001"
        series.primary_labels = []
        
        series_data = {
            series.series_name: {
                'primary_path': "test.primary.slp"
            }
        }
        
        df, _ = create_expected_count_csv([series], series_data, tmp_path)
        
        assert df.iloc[0]['genotype'] == "F_Ac"
        assert df.iloc[0]['replicate'] == 2
    
    def test_no_primary_labels(self, tmp_path):
        """Test handling of series without primary labels."""
        series = Mock()
        series.series_name = "test_series"
        series.primary_labels = None
        
        series_data = {series.series_name: {}}
        
        df, _ = create_expected_count_csv([series], series_data, tmp_path)
        
        assert df.iloc[0]['number_of_plants_cylinder'] == 0


class TestMoveOutputFilesToDirectory:
    """Test move_output_files_to_directory function."""
    
    def test_move_files(self, tmp_path):
        """Test moving files to output directory."""
        # Create test files in current directory
        test_files = []
        for i in range(3):
            file_path = tmp_path.parent / f"test_{i}_all_plants_traits.csv"
            file_path.write_text(f"data_{i}")
            test_files.append(file_path)
        
        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Move files
        with patch('glob.glob') as mock_glob:
            mock_glob.return_value = [str(f) for f in test_files]
            
            moved = move_output_files_to_directory(output_dir, ["*_all_plants_traits.csv"])
        
        # Verify files were moved
        assert len(moved) == 3
        for i in range(3):
            expected_path = output_dir / f"test_{i}_all_plants_traits.csv"
            assert expected_path.exists()
            assert expected_path.read_text() == f"data_{i}"
    
    def test_no_files_to_move(self, tmp_path):
        """Test when no files match patterns."""
        moved = move_output_files_to_directory(tmp_path, ["*.nonexistent"])
        assert len(moved) == 0


class TestCombineTraitCsvs:
    """Test combine_trait_csvs function."""
    
    def test_combine_csvs(self, tmp_path):
        """Test combining multiple CSV files."""
        # Create test CSV files
        for i in range(3):
            df = pd.DataFrame({
                'trait1': [1, 2, 3],
                'trait2': [4, 5, 6]
            })
            csv_path = tmp_path / f"series_{i}_all_plants_traits.csv"
            df.to_csv(csv_path, index=False)
        
        # Combine CSVs
        combined_df = combine_trait_csvs(tmp_path)
        
        # Verify combined DataFrame
        assert combined_df is not None
        assert len(combined_df) == 9  # 3 files × 3 rows each
        assert 'series_name' in combined_df.columns
        assert combined_df['series_name'].nunique() == 3
        
        # Verify output file was created
        output_files = list(tmp_path.glob("series_summary_statistics_*.csv"))
        assert len(output_files) == 1
    
    def test_no_csvs_found(self, tmp_path):
        """Test when no CSV files are found."""
        result = combine_trait_csvs(tmp_path)
        assert result is None
    
    def test_custom_timestamp(self, tmp_path):
        """Test using custom timestamp."""
        # Create a test CSV
        df = pd.DataFrame({'trait': [1, 2, 3]})
        csv_path = tmp_path / "test_all_plants_traits.csv"
        df.to_csv(csv_path, index=False)
        
        # Combine with custom timestamp
        timestamp = "20240101_120000_000000"
        result = combine_trait_csvs(tmp_path, timestamp=timestamp)
        
        # Verify output filename
        expected_file = tmp_path / f"series_summary_statistics_{timestamp}.csv"
        assert expected_file.exists()


class TestMergeTraitsWithExpectedCounts:
    """Test merge_traits_with_expected_counts function."""
    
    def test_basic_merge(self, tmp_path):
        """Test basic merging of traits with expected counts."""
        # Create traits dataframe
        traits_df = pd.DataFrame({
            'series_name': ['series1', 'series1', 'series2', 'series2'],
            'plant_idx': [0, 1, 0, 1],
            'trait1': [10.5, 12.3, 15.0, 16.5],
            'trait2': [20.0, 22.0, 25.0, 28.0]
        })
        
        # Create expected count dataframe
        expected_count_df = pd.DataFrame({
            'plant_qr_code': ['series1', 'series2'],
            'genotype': ['F_Ac', 'OG_Cp'],
            'replicate': [1, 2],
            'number_of_plants_cylinder': [2, 2],
            'primary_root_proofread': ['path1.slp', 'path2.slp'],
            'lateral_root_proofread': ['lat1.slp', 'lat2.slp']
        })
        
        # Merge
        merged_df = merge_traits_with_expected_counts(
            traits_df, expected_count_df, tmp_path
        )
        
        # Verify merge results
        assert len(merged_df) == 4  # All traits rows should be present
        assert 'genotype' in merged_df.columns
        assert 'replicate' in merged_df.columns
        assert 'number_of_plants_cylinder' in merged_df.columns
        assert 'trait1' in merged_df.columns
        assert 'trait2' in merged_df.columns
        
        # Check metadata is correctly merged
        series1_rows = merged_df[merged_df['series_name'] == 'series1']
        assert all(series1_rows['genotype'] == 'F_Ac')
        assert all(series1_rows['replicate'] == 1)
        
        # Verify CSV was saved
        csv_files = list(tmp_path.glob("final_series_summary_with_metadata_*.csv"))
        assert len(csv_files) == 1
    
    def test_custom_timestamp(self, tmp_path):
        """Test using custom timestamp."""
        traits_df = pd.DataFrame({
            'series_name': ['series1'],
            'trait1': [10.0]
        })
        
        expected_count_df = pd.DataFrame({
            'plant_qr_code': ['series1'],
            'genotype': ['test'],
            'number_of_plants_cylinder': [1]
        })
        
        timestamp = "20240101_120000_000000"
        merged_df = merge_traits_with_expected_counts(
            traits_df, expected_count_df, tmp_path, timestamp
        )
        
        # Check output filename
        expected_file = tmp_path / f"final_series_summary_with_metadata_{timestamp}.csv"
        assert expected_file.exists()
    
    def test_missing_series_in_expected_counts(self, tmp_path):
        """Test handling of series not in expected counts."""
        traits_df = pd.DataFrame({
            'series_name': ['series1', 'series_unknown'],
            'trait1': [10.0, 20.0]
        })
        
        expected_count_df = pd.DataFrame({
            'plant_qr_code': ['series1'],
            'genotype': ['test'],
            'number_of_plants_cylinder': [1]
        })
        
        merged_df = merge_traits_with_expected_counts(
            traits_df, expected_count_df, tmp_path
        )
        
        # Should still have all rows
        assert len(merged_df) == 2
        
        # Unknown series should have NaN for metadata
        unknown_row = merged_df[merged_df['series_name'] == 'series_unknown']
        assert pd.isna(unknown_row['genotype'].iloc[0])


class TestCreateProcessingSummary:
    """Test create_processing_summary function."""
    
    def test_complete_summary(self, tmp_path):
        """Test creating a complete processing summary."""
        # Setup test data
        timestamp = "20240101_120000_000000"
        input_files = {
            "lateral": "/path/to/lateral.slp",
            "primary": "/path/to/primary.slp"
        }
        
        # Mock series
        all_series = [Mock() for _ in range(5)]
        
        # Create expected count DataFrame
        expected_count_df = pd.DataFrame({
            'number_of_plants_cylinder': [7, 8, 7, 8, 8]
        })
        
        # Create series summary DataFrame
        series_summary_df = pd.DataFrame({
            'series': ['series1', 'series2'],
            'lateral_count_mean': [10.5, 12.3],
            'lateral_count_std': [2.1, 1.8],
            'series_name': ['series1', 'series2']
        })
        
        # Create summary
        summary = create_processing_summary(
            timestamp=timestamp,
            output_dir=tmp_path,
            input_files=input_files,
            all_series=all_series,
            expected_count_df=expected_count_df,
            series_summary_df=series_summary_df,
            all_traits_json_path=tmp_path / "traits.json",
            series_summary_csv_path=tmp_path / "series_summary.csv"
        )
        
        # Verify summary contents
        assert summary['timestamp'] == timestamp
        assert summary['series_processed'] == 5
        assert summary['total_series_with_summary'] == 2
        assert summary['expected_total_plants'] == 38  # sum of [7, 8, 7, 8, 8]
        assert 'lateral_count_mean' in summary['summary_columns']
        assert 'lateral_count_std' in summary['summary_columns']
        
        # Verify JSON file was created
        summary_path = tmp_path / "processing_summary.json"
        assert summary_path.exists()
        
        # Verify it's valid JSON
        with open(summary_path) as f:
            loaded_summary = json.load(f)
        assert loaded_summary['timestamp'] == timestamp
    
    def test_minimal_summary(self, tmp_path):
        """Test creating summary with minimal data."""
        summary = create_processing_summary(
            timestamp="test",
            output_dir=tmp_path,
            input_files={},
            all_series=[],
            expected_count_df=pd.DataFrame({'number_of_plants_cylinder': []})
        )
        
        assert summary['series_processed'] == 0
        assert summary['total_series_with_summary'] == 0
        assert summary['expected_total_plants'] == 0
        assert summary['all_series_traits_json'] is None
        assert summary['series_summary_csv'] is None
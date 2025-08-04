"""SLEAP visualization utilities package."""

__version__ = "0.1.0"  # Update this version as needed

from .video_utils import extract_video_name, parse_video_filename, get_video_info
from .plotting_utils import (
    get_color_palette,
    plot_instance_plotly,
    plot_instances_plotly,
    create_frame_figure,
)
from .data_utils import (
    extract_instance_data,
    export_labels_to_dataframe,
    save_labels_to_csv,
    summarize_labels,
)
from .saving_utils import (
    create_output_directory,
    save_frame_plots,
    save_all_frames,
)
from .roots_utils import (
    get_videos_in_labels,
    split_labels_by_video,
    save_individual_video_labels,
    validate_series_compatibility,
    create_series_name_from_video,
)
from .pipeline_utils import (
    detect_root_types,
    get_compatible_pipelines,
    combine_labels_from_configs,
    get_file_summary,
    validate_file_config,
)
from .json_utils import (
    ensure_json_serializable,
    save_json,
    validate_json_serializable,
)
from .utils import (
    safe_len,
    safe_iter,
    has_valid_attr,
    safe_get_attr,
)
from .sleap_roots_processing import (
    create_expected_count_csv,
    move_output_files_to_directory,
    combine_trait_csvs,
    merge_traits_with_expected_counts,
    create_processing_summary,
    save_notebook_snapshot,
    save_pre_execution_snapshot,
)

__all__ = [
    # video_utils
    "extract_video_name",
    "parse_video_filename",
    "get_video_info",
    # plotting_utils
    "get_color_palette",
    "plot_instance_plotly",
    "plot_instances_plotly",
    "create_frame_figure",
    # data_utils
    "extract_instance_data",
    "export_labels_to_dataframe",
    "save_labels_to_csv",
    "summarize_labels",
    # saving_utils
    "create_output_directory",
    "save_frame_plots",
    "save_all_frames",
    # roots_utils
    "get_videos_in_labels",
    "split_labels_by_video",
    "save_individual_video_labels",
    "validate_series_compatibility",
    "create_series_name_from_video",
    # pipeline_utils
    "detect_root_types",
    "get_compatible_pipelines",
    "combine_labels_from_configs",
    "get_file_summary",
    "validate_file_config",
    # json_utils
    "ensure_json_serializable",
    "save_json",
    "validate_json_serializable",
    # utils
    "safe_len",
    "safe_iter",
    "has_valid_attr",
    "safe_get_attr",
    # sleap_roots_processing
    "create_expected_count_csv",
    "move_output_files_to_directory",
    "combine_trait_csvs",
    "merge_traits_with_expected_counts",
    "create_processing_summary",
    "save_notebook_snapshot",
    "save_pre_execution_snapshot",
]

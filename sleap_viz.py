import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sleap_io
    import numpy as np
    from pathlib import Path
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.io as pio
    from datetime import datetime

    # Import our custom modules
    from sleap_vizmo import (
        extract_video_name,
        get_video_info,
        create_frame_figure,
        export_labels_to_dataframe,
        save_labels_to_csv,
        summarize_labels,
        save_all_frames,
        # New imports for SLEAP-roots
        get_videos_in_labels,
        split_labels_by_video,
        create_series_name_from_video,
        # Pipeline detection utilities
        detect_root_types,
        get_compatible_pipelines,
        combine_labels_from_configs,
        get_file_summary,
        validate_file_config,
    )

    return (
        Path,
        create_frame_figure,
        get_video_info,
        mo,
        np,
        pd,
        save_all_frames,
        sleap_io,
        summarize_labels,
        detect_root_types,
        get_compatible_pipelines,
        combine_labels_from_configs,
        get_file_summary,
        validate_file_config,
    )


@app.cell
def _(mo):
    mo.md(
        """
    # SLEAP Interactive Visualizer

    This app loads SLEAP `.slp` files and displays interactive plots with labeled instances.
    """
    )
    return


@app.cell
def _(Path, mo):
    # Create file inputs section
    file_inputs_header = mo.md("### SLEAP File Inputs")
    file_inputs_header
    return


@app.cell
def _(Path, mo):
    # File input 1
    file1_path = mo.ui.text(
        placeholder="Path to .slp file (optional)",
        value="",
        label="File 1:",
        full_width=True,
    )
    file1_root_type = mo.ui.dropdown(
        options={
            "none": "Select root type...",
            "primary": "Primary roots",
            "lateral": "Lateral roots",
            "crown": "Crown roots",
        },
        value="none",
        label="Root type:",
    )

    file1_input = mo.hstack([file1_path, file1_root_type], widths=[3, 1])
    file1_input
    return file1_path, file1_root_type


@app.cell
def _(Path, mo):
    # File input 2
    file2_path = mo.ui.text(
        placeholder="Path to .slp file (optional)",
        value="",
        label="File 2:",
        full_width=True,
    )
    file2_root_type = mo.ui.dropdown(
        options={
            "none": "Select root type...",
            "primary": "Primary roots",
            "lateral": "Lateral roots",
            "crown": "Crown roots",
        },
        value="none",
        label="Root type:",
    )

    file2_input = mo.hstack([file2_path, file2_root_type], widths=[3, 1])
    file2_input
    return file2_path, file2_root_type


@app.cell
def _(Path, mo):
    # File input 3
    file3_path = mo.ui.text(
        placeholder="Path to .slp file (optional)",
        value="",
        label="File 3:",
        full_width=True,
    )
    file3_root_type = mo.ui.dropdown(
        options={
            "none": "Select root type...",
            "primary": "Primary roots",
            "lateral": "Lateral roots",
            "crown": "Crown roots",
        },
        value="none",
        label="Root type:",
    )

    file3_input = mo.hstack([file3_path, file3_root_type], widths=[3, 1])
    file3_input
    return file3_path, file3_root_type


@app.cell
def _(mo):
    # Instructions
    file_input_instructions = mo.md(
        """
    **Instructions:**
    - Each file should contain only one root type
    - Select the appropriate root type for each file
    - Leave unused file inputs blank
    - Files will be combined into a single Series for analysis
    """
    )
    file_input_instructions
    return


@app.cell
def _(Path, mo, sleap_io, file1_path, file1_root_type, file2_path, file2_root_type, file3_path, file3_root_type):
    # Collect and validate file inputs
    file_configs = []
    validation_messages = []

    # Check each file input
    for i, (file_path_ui, root_type_ui) in enumerate(
        [
            (file1_path, file1_root_type),
            (file2_path, file2_root_type),
            (file3_path, file3_root_type),
        ],
        1,
    ):
        if file_path_ui.value and root_type_ui.value != "none":
            try:
                file_path = Path(file_path_ui.value)
                if file_path.exists() and file_path.suffix == ".slp":
                    # Load to check it's valid
                    labels = sleap_io.load_slp(str(file_path))
                    file_configs.append(
                        {
                            "path": file_path,
                            "root_type": root_type_ui.value,
                            "labels": labels,
                        }
                    )
                    validation_messages.append(
                        f"✅ File {i}: {file_path.name} ({root_type_ui.value} roots)"
                    )
                else:
                    validation_messages.append(
                        f"❌ File {i}: Not found or not a .slp file"
                    )
            except Exception as e:
                validation_messages.append(f"❌ File {i}: Error - {str(e)}")
        elif file_path_ui.value and root_type_ui.value == "none":
            validation_messages.append(f"⚠️ File {i}: Please select a root type")
        elif not file_path_ui.value and root_type_ui.value != "none":
            validation_messages.append(f"⚠️ File {i}: Please provide a file path")

    # Create validation status display
    if validation_messages:
        validation_status = mo.md(
            "### File Validation:\n" + "\n".join(validation_messages)
        )
    else:
        validation_status = mo.md("*No files provided*")

    validation_status
    return file_configs


@app.cell
def _(file_configs, mo, summarize_labels):
    # Create summary for all loaded files
    if file_configs:
        summaries = []
        for summary_config in file_configs:
            summary = summarize_labels(summary_config["labels"])
            summary_text = f"**{summary_config['path'].name} ({summary_config['root_type']} roots):**\n"
            summary_text += f"- Videos: {summary['n_videos']}\n"
            summary_text += f"- Labeled frames: {summary['n_labeled_frames']}\n"
            summary_text += f"- Total instances: {summary['total_instances']}\n"
            summaries.append(summary_text)
        
        file_summary = mo.md("## File Summary\n" + "\n".join(summaries))
    else:
        file_summary = mo.md("*No files loaded yet*")
    
    file_summary
    return


@app.cell
def _(file_configs, mo, combine_labels_from_configs):
    # Initialize all variables at the top
    frame_selector = None
    show_image_toggle = None
    show_edges_toggle = None
    show_labels_toggle = None
    color_by_node_toggle = None
    controls_panel = None
    viz_labels = None

    # Combine labels from all loaded files
    if file_configs:
        viz_labels = combine_labels_from_configs(file_configs)

    if viz_labels and len(viz_labels.labeled_frames) > 0:
        frame_selector = mo.ui.slider(
            start=0,
            stop=len(viz_labels.labeled_frames) - 1,
            value=0,
            label="Select frame:",
            show_value=True,
        )

        # Visualization options
        show_image_toggle = mo.ui.checkbox(value=True, label="Show image")
        show_edges_toggle = mo.ui.checkbox(value=True, label="Show skeleton edges")
        show_labels_toggle = mo.ui.checkbox(value=True, label="Show node labels")
        color_by_node_toggle = mo.ui.checkbox(value=False, label="Color by node")

        # Get summary of combined files
        combined_summary = f"**Combined visualization from {len(file_configs)} file(s)**"
        
        controls_panel = mo.vstack(
            [
                mo.md(combined_summary),
                mo.md(
                    f"### Frame Navigation ({len(viz_labels.labeled_frames)} frames available)"
                ),
                frame_selector,
                mo.md("### Visualization Options"),
                mo.hstack(
                    [
                        show_image_toggle,
                        show_edges_toggle,
                        show_labels_toggle,
                        color_by_node_toggle,
                    ]
                ),
            ]
        )
    else:
        frame_selector = None
        show_image_toggle = mo.ui.checkbox(value=True)
        show_edges_toggle = mo.ui.checkbox(value=True)
        show_labels_toggle = mo.ui.checkbox(value=True)
        color_by_node_toggle = mo.ui.checkbox(value=False)
        controls_panel = mo.md("No labeled frames available to display.")

    controls_panel
    return (
        color_by_node_toggle,
        frame_selector,
        show_edges_toggle,
        show_image_toggle,
        show_labels_toggle,
        viz_labels,
    )


@app.cell
def _(color_by_node_toggle, create_frame_figure, frame_selector, viz_labels, mo, show_edges_toggle, show_image_toggle, show_labels_toggle):
    # Initialize variables at the top
    plot_element = None
    viz_frame_idx = None
    viz_fig = None
    viz_lf = None

    if viz_labels and frame_selector is not None:
        viz_frame_idx = frame_selector.value
        viz_lf = viz_labels.labeled_frames[viz_frame_idx]

        # Create figure using the modular function
        viz_fig = create_frame_figure(
            viz_lf,
            show_image=show_image_toggle.value,
            color_by_track=False,
            color_by_node=color_by_node_toggle.value,
            show_edges=show_edges_toggle.value,
            show_labels=show_labels_toggle.value,
            ms=10,
            lw=2,
        )

        # Update title
        viz_fig.update_layout(
            title=f"Frame {viz_frame_idx} - {len(viz_lf.instances)} instances"
        )

        plot_element = mo.ui.plotly(viz_fig)
    else:
        plot_element = mo.md("No frames to display")
        viz_frame_idx = None
        viz_fig = None
        viz_lf = None

    plot_element
    return (viz_frame_idx,)


@app.cell
def _(get_video_info, viz_labels, mo, np, pd, viz_frame_idx):
    # Initialize variables at the top
    table_element = None
    coord_video_name = None
    coord_video_info = None
    coord_df = None

    if viz_labels and viz_frame_idx is not None:
        coord_labeled_frame = viz_labels.labeled_frames[viz_frame_idx]

        # Get video info using our utility function
        coord_video_info = get_video_info(coord_labeled_frame)
        coord_video_name = coord_video_info["name"]

        # Create a summary table with video info
        coord_table_data = []
        for coord_instance_idx, coord_inst in enumerate(coord_labeled_frame.instances):
            coord_inst_points = coord_inst.numpy()
            coord_inst_skeleton = coord_inst.skeleton
            coord_inst_node_names = [node.name for node in coord_inst_skeleton.nodes]

            for coord_node_idx, (coord_node_name, coord_pt) in enumerate(
                zip(coord_inst_node_names, coord_inst_points)
            ):
                if not np.isnan(coord_pt).any():
                    coord_table_data.append(
                        {
                            "Video": coord_video_name,
                            "Frame": viz_frame_idx,
                            "Instance": coord_instance_idx,
                            "Node": coord_node_name,
                            "X": coord_pt[0],
                            "Y": coord_pt[1],
                        }
                    )

        if coord_table_data:
            coord_df = pd.DataFrame(coord_table_data)
            table_element = mo.ui.table(coord_df, label="Instance coordinates")
        else:
            table_element = mo.md("No valid points found in this frame")
            coord_df = None
    else:
        table_element = mo.md("No frame selected")
        coord_video_name = None
        coord_video_info = None
        coord_df = None

    table_element
    return


@app.cell
def _(viz_labels, mo):
    # Save All controls
    # Initialize variables at the top
    save_all_button = None
    save_controls = None

    if viz_labels and len(viz_labels.labeled_frames) > 0:
        save_all_button = mo.ui.run_button(
            label="📦 Save All Frames (PNG + HTML + CSV)"
        )

        save_controls = mo.vstack(
            [
                mo.md("### Export Options"),
                mo.md(
                    "Click to export all frames as static (PNG) and interactive (HTML) plots, plus a CSV summary."
                ),
                save_all_button,
                mo.md(
                    "💡 **Tip**: Individual plots can also be saved using Plotly's built-in camera icon in the plot toolbar."
                ),
            ]
        )
    else:
        save_all_button = None
        save_controls = mo.md("Load data to enable export options")

    save_controls
    return (save_all_button,)


@app.cell
def _(mo, file_configs, detect_root_types):
    # Use the tested function to determine root types
    root_types = detect_root_types(file_configs)

    # Display detected root types
    if file_configs:
        primary_icon = "✅" if root_types["primary"] else "❌"
        lateral_icon = "✅" if root_types["lateral"] else "❌"
        crown_icon = "✅" if root_types["crown"] else "❌"
        
        root_types_text = "### Detected Root Types:\n"
        root_types_text += f"- **Primary roots**: {primary_icon}\n"
        root_types_text += f"- **Lateral roots**: {lateral_icon}\n"
        root_types_text += f"- **Crown roots**: {crown_icon}\n"
        
        root_types_display = mo.md(root_types_text)
    else:
        root_types_display = mo.md("*No root types detected - load files above*")

    root_types_display
    return root_types


@app.cell
def _(viz_labels, mo, save_all_button, save_all_frames):
    # Handle Save All button click
    # Initialize save_all_status at the top
    save_all_status = mo.md("")  # Default to empty

    if save_all_button is not None and save_all_button.value and viz_labels:
        try:
            # Perform the export (without progress callback for now)
            results = save_all_frames(
                viz_labels,
                show_image=True,
                show_edges=True,
                show_labels=True,
            )

            # Create summary message
            summary_parts = [
                f"✅ **Export Complete!**",
                f"📁 Output directory: `{results['output_dir']}`",
                f"🖼️ Saved {len(results['png_files'])} PNG files",
                f"🌐 Saved {len(results['html_files'])} interactive HTML files",
            ]

            if results["csv_file"]:
                summary_parts.append(f"📊 Saved CSV: `{results['csv_file'].name}`")

            if results["errors"]:
                summary_parts.append(f"⚠️ {len(results['errors'])} errors occurred")
                for save_all_error in results["errors"][:3]:  # Show first 3 errors
                    summary_parts.append(f"  - {save_all_error}")

            save_all_status = mo.md("\n\n".join(summary_parts))

        except Exception as e:
            import traceback as tb_save_all

            save_all_error_details = tb_save_all.format_exc()
            save_all_status = mo.md(
                f"❌ **Error during export**: {str(e)}\n\n```\n{save_all_error_details}\n```"
            )
    else:
        save_all_status = mo.md("")  # Display nothing when button not clicked

    # Display the status
    save_all_status
    return


@app.cell  
def _(mo, root_types, file_configs, get_compatible_pipelines):
    # Use the tested function to determine compatible pipelines
    compatible_pipelines = get_compatible_pipelines(root_types)
    pipeline_selector = None
    pipeline_section = mo.md("")  # Default empty

    if compatible_pipelines:
        # Create pipeline selector
        pipeline_options = {desc: name for name, desc in compatible_pipelines}
        pipeline_selector = mo.ui.dropdown(
            options=pipeline_options,
            value=(
                compatible_pipelines[0][1] if compatible_pipelines else None
            ),  # Use description as value
            label="Select pipeline:",
        )

        pipeline_section = mo.vstack(
            [
                mo.md("### Compatible Pipelines:"),
                pipeline_selector,
                mo.callout(
                    f"Based on your root types, {len(compatible_pipelines)} pipeline(s) are compatible.",
                    kind="success",
                ),
            ]
        )
    else:
        if any(root_types.values()):
            pipeline_section = mo.callout(
                "No compatible pipeline found for the selected combination of root types. "
                "Please check the sleap-roots documentation for supported combinations.",
                kind="warn",
            )
        else:
            # No root types selected - show helpful message
            pipeline_section = mo.callout(
                "Load files above to see compatible pipelines.",
                kind="info",
            )
            # Create a dummy selector for the trait computation logic
            pipeline_selector = mo.ui.dropdown(options={"none": "none"}, value="none")

    pipeline_section
    return compatible_pipelines, pipeline_selector


@app.cell
def _(file_configs, mo, get_videos_in_labels):
    # SLEAP-roots traits section
    # Initialize variables at the top
    roots_traits_button = None
    roots_section = None

    if file_configs:
        # Get info about all loaded files
        total_videos = 0
        file_info_parts = ["### SLEAP-roots Trait Computation\n"]

        for info_config in file_configs:
            videos = get_videos_in_labels(info_config["labels"])
            total_videos += len(videos)
            file_info_parts.append(
                f"**{info_config['path'].name}** ({info_config['root_type']} roots): {len(videos)} video(s)"
            )

        file_info_parts.append(f"\n**Total videos across all files:** {total_videos}")

        # Add button
        roots_traits_button = mo.ui.run_button(
            label="🌱 Compute SLEAP-roots Traits", kind="success"
        )

        roots_section = mo.vstack(
            [
                mo.md("\n".join(file_info_parts)),
                mo.md(
                    "**Note:** Files will be combined into a Series based on root type for processing."
                ),
                roots_traits_button,
            ]
        )
    else:
        roots_traits_button = None
        roots_section = mo.md("")

    roots_section
    return roots_traits_button


@app.cell
def _(file_configs, mo, roots_traits_button, Path, datetime, sleap_io, pipeline_selector, extract_video_name, compatible_pipelines, root_types):
    # Handle SLEAP-roots traits button click - prefixed variables to avoid conflicts
    # Initialize traits_display at the top (similar to save_all_status pattern)
    new_traits_display = mo.md("")  # Default to empty

    if roots_traits_button is not None and roots_traits_button.value:
        try:
            # Create output directory for all outputs
            new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            new_roots_output_dir = Path("./output") / f"sleap_roots_{new_timestamp}"
            new_roots_output_dir.mkdir(parents=True, exist_ok=True)

            new_status_messages = [
                f"📁 Created output directory: `{new_roots_output_dir}`",
            ]

            # Import sleap-roots
            try:
                import sleap_roots as new_sr
                from sleap_roots.trait_pipelines import (
                    PrimaryRootPipeline as NewPrimaryRootPipeline,
                    LateralRootPipeline as NewLateralRootPipeline,
                    DicotPipeline as NewDicotPipeline,
                    MultipleDicotPipeline as NewMultipleDicotPipeline,
                    OlderMonocotPipeline as NewOlderMonocotPipeline,
                    YoungerMonocotPipeline as NewYoungerMonocotPipeline,
                )
            except ImportError as e:
                new_status_messages.append(f"\n❌ sleap-roots not installed: {str(e)}")
                new_status_messages.append("\nInstall with: `pip install sleap-roots`")
                new_traits_display = mo.md("\n".join(new_status_messages))
                raise

            # Check if files are loaded
            if not file_configs:
                new_status_messages.append("\n❌ **Error**: Please load files first!")
                new_traits_display = mo.md("\n".join(new_status_messages))
                raise ValueError("No files loaded")

            if not compatible_pipelines:
                new_status_messages.append(
                    "\n❌ **Error**: No compatible pipeline found!"
                )
                new_status_messages.append("Please check your root type combination.")
                new_traits_display = mo.md("\n".join(new_status_messages))
                raise ValueError("No compatible pipeline")

            # Process files based on configuration
            new_status_messages.append("\n🔄 Processing files...")
            new_status_messages.append(
                f"Root types: Primary={root_types['primary']}, Lateral={root_types['lateral']}, Crown={root_types['crown']}"
            )

            # Prepare files for Series loading based on root type
            # Each root type gets its own file, combining videos from multiple files if needed
            series_files = {"primary": None, "lateral": None, "crown": None}

            # If we have multiple files for the same root type, we need to combine them
            for series_config in file_configs:
                root_type = series_config["root_type"]

                # For now, use the first file for each root type
                # TODO: Implement combining multiple files of same root type
                if series_files[root_type] is None:
                    # Save the file to the output directory with appropriate naming
                    output_path = new_roots_output_dir / f"combined_{root_type}.slp"
                    sleap_io.save_slp(series_config["labels"], str(output_path))
                    series_files[root_type] = output_path
                    new_status_messages.append(
                        f"✓ Saved {root_type} roots: {output_path.name}"
                    )
                else:
                    new_status_messages.append(
                        f"⚠️ Multiple {root_type} files detected - using first one only"
                    )

            # Create Series with the prepared files
            new_series_name = "sleap_vizmo_series"
            new_status_messages.append(f"\n🌱 Creating Series: {new_series_name}")

            # Load Series with appropriate files
            new_series_kwargs = {"series_name": new_series_name}
            if series_files["primary"]:
                new_series_kwargs["primary_path"] = str(series_files["primary"])
            if series_files["lateral"]:
                new_series_kwargs["lateral_path"] = str(series_files["lateral"])
            if series_files["crown"]:
                new_series_kwargs["crown_path"] = str(series_files["crown"])

            new_status_messages.append(
                f"  Series.load arguments: {list(new_series_kwargs.keys())}"
            )
            new_series = new_sr.Series.load(**new_series_kwargs)

            # Run pipeline
            new_pipeline_map = {
                "PrimaryRootPipeline": NewPrimaryRootPipeline,
                "LateralRootPipeline": NewLateralRootPipeline,
                "DicotPipeline": NewDicotPipeline,
                "MultipleDicotPipeline": NewMultipleDicotPipeline,
                "OlderMonocotPipeline": NewOlderMonocotPipeline,
                "YoungerMonocotPipeline": NewYoungerMonocotPipeline,
            }

            new_selected_pipeline_name = (
                pipeline_selector.value
                if pipeline_selector is not None
                else "DicotPipeline"
            )
            NewPipelineClass = new_pipeline_map.get(
                new_selected_pipeline_name, NewDicotPipeline
            )

            new_status_messages.append(f"  Using pipeline: {NewPipelineClass.__name__}")

            # Run the pipeline
            new_pipeline = NewPipelineClass()

            # Use correct API based on pipeline type
            if new_selected_pipeline_name in [
                "MultipleDicotPipeline",
                "PrimaryRootPipeline",
            ]:
                # Check if we should use multiple plant analysis
                # For PrimaryRootPipeline, we can use compute_multiple_dicots_traits if available
                if hasattr(new_pipeline, "compute_multiple_dicots_traits"):
                    new_status_messages.append(
                        "  Computing traits for multiple plants..."
                    )
                    new_traits = new_pipeline.compute_multiple_dicots_traits(
                        new_series,
                        write_json=True,
                        json_suffix=f"_{new_series_name}_traits.json",
                        write_csv=True,
                        csv_suffix=f"_{new_series_name}_traits.csv",
                    )
                    new_status_messages.append(
                        f"  ✓ Saved JSON and CSV for per-plant traits"
                    )
                else:
                    # Fallback to single plant method
                    new_status_messages.append("  Computing single plant traits...")
                    new_traits = new_pipeline.compute_plant_traits(
                        new_series,
                        write_csv=True,
                        output_dir=str(new_roots_output_dir),
                        csv_suffix=f"_{new_series_name}_traits.csv",
                    )
                    new_status_messages.append(f"  ✓ Saved CSV for plant traits")
            elif hasattr(new_pipeline, "compute_plant_traits"):
                # For single plant pipelines
                new_status_messages.append("  Computing plant traits...")
                new_traits = new_pipeline.compute_plant_traits(
                    new_series,
                    write_csv=True,
                    output_dir=str(new_roots_output_dir),
                    csv_suffix=f"_{new_series_name}_traits.csv",
                )
                new_status_messages.append(f"  ✓ Saved CSV for plant traits")
            else:
                # Generic approach for other pipelines
                new_status_messages.append("  Computing traits with generic method...")
                try:
                    # Try the most appropriate method for the pipeline
                    if hasattr(new_pipeline, "compute_multiple_dicots_traits"):
                        new_traits = new_pipeline.compute_multiple_dicots_traits(
                            new_series,
                            write_json=True,
                            json_suffix=f"_{new_series_name}_traits.json",
                            write_csv=True,
                            csv_suffix=f"_{new_series_name}_traits.csv",
                        )
                    else:
                        # Fallback to basic trait computation
                        new_traits = {}
                        new_status_messages.append(
                            "  ⚠️ No suitable compute method found for this pipeline"
                        )
                except Exception as e:
                    new_status_messages.append(
                        f"  ❌ Error with pipeline method: {str(e)}"
                    )
                    new_traits = {}

            new_status_messages.append(f"\n🎉 **Trait computation complete!**")
            new_status_messages.append(
                f"📊 All results saved to: `{new_roots_output_dir}`"
            )

        except Exception as e:
            import traceback as new_tb_roots

            new_roots_error_details = new_tb_roots.format_exc()
            new_status_messages.append(f"\n❌ **Error**: {str(e)}")
            if "new_tb_roots" in locals():
                new_status_messages.append(f"\n```\n{new_roots_error_details}\n```")

        new_traits_display = mo.md("\n".join(new_status_messages))
    else:
        new_traits_display = mo.md("")  # Display nothing when button not clicked

    new_traits_display
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.14.13"
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
    from src import (
        extract_video_name,
        get_video_info,
        create_frame_figure,
        export_labels_to_dataframe,
        save_labels_to_csv,
        summarize_labels,
        save_all_frames,
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
    file_path_input = mo.ui.text(
        placeholder="Enter path to .slp file",
        value=str(Path("./lateral/lateral_root_MK22_Day14_labels.v002.slp").absolute()),
        label="SLEAP file path:",
        full_width=True,
    )

    n_frames_input = mo.ui.slider(
        start=1,
        stop=50,
        value=10,
        label="Number of frames to display:",
        show_value=True,
    )

    input_panel = mo.vstack([file_path_input, n_frames_input])
    return file_path_input, input_panel, n_frames_input


@app.cell
def _(input_panel):
    input_panel
    return


@app.cell
def _(Path, file_path_input, mo, sleap_io):
    # Load SLEAP file based on input path
    try:
        load_file_path = Path(file_path_input.value)
        if load_file_path.exists() and load_file_path.suffix == ".slp":
            labels = sleap_io.load_slp(str(load_file_path))
            load_status = mo.md(f"✅ Successfully loaded: {load_file_path.name}")
        else:
            labels = None
            load_status = mo.md("❌ File not found or not a .slp file")
    except Exception as e:
        labels = None
        load_status = mo.md(f"❌ Error loading file: {str(e)}")

    load_status
    return (labels,)


@app.cell
def _(labels, mo, summarize_labels):
    if labels:
        summary = summarize_labels(labels)
        file_summary = mo.md(
            f"""
            ## File Summary
            - **Videos**: {summary['n_videos']}
            - **Skeletons**: {summary['n_skeletons']}
            - **Labeled frames**: {summary['n_labeled_frames']}
            - **Tracks**: {summary['n_tracks']}
            - **Total instances**: {summary['total_instances']}
            - **Total valid points**: {summary['total_points']}
            - **Average instances per frame**: {summary.get('avg_instances_per_frame', 0):.1f}
            """
        )
    else:
        file_summary = mo.md("No file loaded yet.")
        summary = None

    file_summary
    return


@app.cell
def _(labels, mo, n_frames_input):
    if labels and len(labels.labeled_frames) > 0:
        viz_n_frames = min(n_frames_input.value, len(labels.labeled_frames))
        frame_selector = mo.ui.slider(
            start=0,
            stop=min(viz_n_frames - 1, len(labels.labeled_frames) - 1),
            value=0,
            label="Select frame:",
            show_value=True,
        )

        # Visualization options
        show_image_toggle = mo.ui.checkbox(value=True, label="Show image")
        show_edges_toggle = mo.ui.checkbox(value=True, label="Show skeleton edges")
        show_labels_toggle = mo.ui.checkbox(value=True, label="Show node labels")
        color_by_node_toggle = mo.ui.checkbox(value=False, label="Color by node")

        controls_panel = mo.vstack(
            [
                mo.md(f"### Displaying first {viz_n_frames} labeled frames"),
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
        viz_n_frames = 0
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
    )


@app.cell
def _(
    color_by_node_toggle,
    create_frame_figure,
    frame_selector,
    labels,
    mo,
    show_edges_toggle,
    show_image_toggle,
    show_labels_toggle,
):
    if labels and frame_selector is not None:
        viz_frame_idx = frame_selector.value
        viz_lf = labels.labeled_frames[viz_frame_idx]

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
def _(get_video_info, labels, mo, np, pd, viz_frame_idx):
    if labels and viz_frame_idx is not None:
        coord_labeled_frame = labels.labeled_frames[viz_frame_idx]

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
def _(labels, mo):
    # Save All controls
    if labels and len(labels.labeled_frames) > 0:
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
def _(labels, mo, save_all_button, save_all_frames):
    # Handle Save All button click
    if save_all_button is not None and save_all_button.value and labels:
        print("Export button clicked - starting export process")

        try:
            # Perform the export (without progress callback for now)
            results = save_all_frames(
                labels,
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
                for error in results["errors"][:3]:  # Show first 3 errors
                    summary_parts.append(f"  - {error}")

            save_all_status = mo.md("\n\n".join(summary_parts))
            print(f"Export complete! Files saved to: {results['output_dir']}")

        except Exception as e:
            import traceback as tb_save_all

            error_details = tb_save_all.format_exc()
            save_all_status = mo.md(
                f"❌ **Error during export**: {str(e)}\n\n```\n{error_details}\n```"
            )
        # Display the status
        save_all_status
    else:
        mo.md("")  # Display nothing when button not clicked
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## Instructions

    1. Enter the path to your SLEAP `.slp` file or use the default example
    2. Adjust the number of frames to display using the slider
    3. Navigate through frames using the frame selector
    4. Hover over points to see instance and coordinate information
    5. Points are numbered and connected based on the skeleton structure
    6. **Export Options:**
       - Use the "Save All Frames" button to export all frames as PNG and HTML plots, plus a CSV summary
       - Individual plots can be saved using Plotly's built-in camera icon in the plot toolbar
       - All exports are saved to a timestamped output folder

    Run with: `marimo run sleap_viz.py`
    """
    )
    return


if __name__ == "__main__":
    app.run()

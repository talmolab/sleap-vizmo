# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a SLEAP (Social LEAP Estimates Animal Poses) annotation project for tracking plant root growth in Medicago plates over time. The project contains labeled data for analyzing primary, lateral, and tertiary root development across a 24-day experimental period.

## Project Structure

```
SLEAP_medicago_plates/
├── sleap_viz.py              # Main Marimo notebook (run from root)
├── src/                       # Core utility modules
│   ├── __init__.py           # Package initialization
│   ├── video_utils.py        # Video metadata extraction utilities
│   ├── plotting_utils.py     # Plotly visualization functions
│   └── data_utils.py         # Data export and analysis utilities
├── tests/                     # Pytest test suite
│   ├── test_video_utils.py   # Tests for video utilities
│   ├── test_plotting_utils.py # Tests for plotting utilities
│   └── test_data_utils.py    # Tests for data utilities
├── lateral/                   # Lateral root annotations
├── primary/                   # Primary root annotations (if present)
├── tertiary/                  # Tertiary root annotations (if present)
└── exports/                   # Default export directory for visualizations
```

### Key Design Principles

1. **Modular Architecture**: All functions are in `src/` modules for reusability and testing
2. **100% Test Coverage**: Comprehensive pytest tests for all utility functions
3. **Cross-platform Compatibility**: Use `Path.as_posix()` for paths
4. **Marimo Best Practices**: The notebook imports from `src/` to avoid variable conflicts

## Marimo Guidelines

When contributing to Marimo apps:

- **To display UI elements**: Place them as the last expression in the cell (e.g., `mo.md(...)`, `mo.ui.plotly(...)`, `mo.ui.table(...)`). Do NOT use `return` statements.
- **To pass variables to other cells**: Use the `return` statement with variable names (e.g., `return var1, var2`).
- **To display UI AND pass variables**: Place the UI element as the last expression, then use `return` for variables on the next line.
- **For layout containers**: `mo.vstack([...])` or `mo.hstack([...])` should be the last expression to display.
- **Use conditional logic**: Always ensure a UI element is displayed, even if it's just an explanatory message.
- **IMPORTANT - Variable naming**: NEVER redefine variables that are already defined in other cells. This will cause "This cell redefines variables from other cells" errors. Each variable name must be unique across all cells unless you're importing it through the function signature.
- **Button kinds**: When using `mo.ui.button()`, the `kind` parameter must be one of: `'neutral'`, `'success'`, `'warn'`, `'danger'`, `'info'`, or `'alert'`. Do NOT use `'primary'` or other values.

Example patterns:
```python
# Display only
@app.cell
def __(mo):
    mo.md("Hello")  # Last expression, no return
    
# Pass variables only  
@app.cell
def __():
    x = 5
    return x,  # Note the comma for single variable
    
# Display and pass variables
@app.cell
def __(mo):
    x = 5
    mo.md("Hello")  # Display this
    return x,  # Pass this variable

# INCORRECT - Variable redefinition (will cause error)
@app.cell
def __():
    frame_idx = 0
    return frame_idx

@app.cell 
def __():
    frame_idx = 1  # ERROR: Redefines frame_idx from another cell
    return frame_idx

# CORRECT - Import variable from another cell
@app.cell
def __():
    frame_idx = 0
    return frame_idx

@app.cell
def __(frame_idx):  # Import frame_idx from the cell above
    # Use frame_idx here
    print(f"Frame index is {frame_idx}")
    return
```

These patterns ensure the app renders properly in the Marimo notebook UI and avoids variable conflicts.

## Marimo Cell Hygiene

To ensure clean execution and maintainability:

- Avoid defining the same variable names in multiple cells unless intentionally reused (e.g., `labels`, `fig`).
- Use descriptive or scoped names for loop variables and temporary values (e.g., `csv_node_name` instead of `node_name` when in the CSV export cell).
- Only return values from cells if needed by other cells.
- When returning UI elements and data, return them as tuples and avoid returning unused intermediate variables.
- Refactor shared logic into functions to prevent code duplication and variable leaks.
- When processing data in loops, prefix variable names with context (e.g., `csv_` prefix for CSV export loop variables).
- **CRITICAL**: ALWAYS prefix ALL variable names in each cell with a unique context identifier (e.g., `table_backend_filename` in the table cell, `csv_backend_filename` in the CSV export cell). This applies to ALL variables, not just loop variables!
- **Never access `.value` of a `mo.ui` element in the same cell where it is created**. Always access `.value` in a downstream cell. This prevents runtime errors like "RuntimeError: Accessing the value of a UIElement in the cell that created it is not allowed."
- **Never use UIElements in boolean contexts directly**. Always access `.value`. The truthiness of a UIElement is always True, which will trigger a warning: "The truth value of a UIElement is always True. You probably want to call `.value` instead."
- **Button click handling**: For triggering computations like exports, use `mo.ui.run_button()` instead of `mo.ui.button()`. A run button's value is `True` when clicked and automatically resets to `False` after dependent cells execute. Check with `if button is not None and button.value:` to handle cases where the button might not exist. Never use the UIElement itself in a boolean context.
- **File export dependencies**: When exporting Plotly figures to images, ensure `plotly.io` is imported as `pio` and included in the cell's function parameters. Use `pio.write_image()` instead of `fig.write_image()` for more reliable exports.
- **Import statements in cells**: When importing modules inside cells (especially in exception handlers), always use unique aliases to avoid variable redefinition errors. For example, use `import traceback as tb_png` in one cell and `import traceback as tb_csv` in another, rather than importing `traceback` in both cells.
- **Progress tracking**: Use `mo.state()` for mutable values that need to be updated during computation. `mo.md()` objects are immutable and don't have an `update()` method. For progress tracking, create a state object with `progress_state = mo.state([])` and update it with `progress_state.set_value(new_list)`.

## Prerequisites

### Required System Tools
The organization script requires the `unzip` command to extract zip files:

```bash
# Ubuntu/Debian
sudo apt-get install unzip

# CentOS/RHEL/Fedora
sudo yum install unzip
# or
sudo dnf install unzip

# macOS (if using Homebrew)
brew install unzip
```

## Common Commands

### Working with SLEAP
For SLEAP commands, refer to the official SLEAP documentation at https://sleap.ai/

### Installing Dependencies
```bash
# Install uv if not already installed
pip install uv

# Install the project and its dependencies
uv pip install -e .

# Install dev dependencies (pytest, pytest-cov, black)
uv pip install -e ".[dev]"

# Or install all dev dependencies with uv sync
uv sync --dev
```

### Running the SLEAP Visualizer
```bash
# Use the sleap_viz mamba environment
# Run the interactive SLEAP visualizer from the project root
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m marimo run sleap_viz.py

# Or edit the visualizer interactively
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m marimo edit sleap_viz.py

# For running tests with coverage (pytest options are configured in pyproject.toml)
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m pytest

# Or run specific test files
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m pytest tests/test_video_utils.py -v

# Format code with black (configured in pyproject.toml)
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m black src/ tests/ sleap_viz.py

# Check formatting without making changes
C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m black src/ tests/ sleap_viz.py --check
```

The SLEAP visualizer is a Marimo app that:
- Loads SLEAP `.slp` files interactively
- Displays labeled frames with Plotly visualizations
- Shows hover information with instance numbers and coordinates
- Displays skeleton connections between body parts
- Provides a coordinate table for all instances
- Offers visualization options (toggle image, edges, labels, coloring mode)
- Contains modular visualization functions within the same file for reusable plotting

### Organizing TIF Files from Google Drive Downloads
```bash
# Organize TIF files from downloaded Google Drive zip files
# Run this script whenever you download new chunked data from Google Drive
./organize_tifs.sh

# Or specify a custom directory (project name will be extracted from the path)
./organize_tifs.sh /path/to/your/tifs/ProjectName

# Generate metadata report and check for missing files without reorganizing
./organize_tifs.sh --metadata-only

# The script will:
# 1. Extract project name from the target directory path
# 2. Extract any zip files in the directory (unless --metadata-only)
# 3. Dynamically discover scan days from TIF filenames (e.g., day1, day3, day14, etc.)
# 4. Create [PROJECT_NAME]_Scans directory with day-based subdirectories
# 5. Move all TIF files to appropriate day directories (unless --metadata-only)
# 6. Handle permission issues by copying files when move fails
# 7. Generate CSV metadata report with file details
# 8. Check for missing files and report warnings
# 9. Report final file counts by day
```

### Metadata and File Analysis
The script generates a comprehensive metadata report saved as `tif_metadata_report.csv` containing:
- Day number
- Prefix (F, OG, S, no_peptide1, no_peptide2, no_peptide3)
- Treatment (Ac, Cp, De, DhA, DhB, DhC, DhD, Fo, Gr, Mt, Ri, Ri1, Ri2, RiA4)
- Set (set1, set2, set3)
- Timestamp
- File number
- Full file path
- Filename

The script also performs missing file analysis by:
- Dynamically discovering scan days from TIF filenames (works with any experimental timeline)
- Counting files per day
- Listing unique treatment combinations
- Warning about days with fewer than 10 files (potential missing data)
- Identifying missing day directories
- Adapts to different experimental schedules automatically

## Data Organization

### Directory Structure
The script dynamically creates directories based on the target directory name:
```
tifs/[PROJECT_NAME]/[PROJECT_NAME]_Scans/
├── Day1_scans_[PROJECT_NAME]/
├── Day3_scans_[PROJECT_NAME]/
├── Day6_scans_[PROJECT_NAME]/
├── Day8_scans_[PROJECT_NAME]/
├── Day10_scans_[PROJECT_NAME]/
├── Day14_scans_[PROJECT_NAME]/
├── Day16_scans_[PROJECT_NAME]/
├── Day21_scans_[PROJECT_NAME]/
└── Day24_scans_[PROJECT_NAME]/
```

For example, with `tifs/MK22/`:
```
tifs/MK22/MK22_Scans/
├── Day1_scans_MK22/
├── Day3_scans_MK22/
├── Day6_scans_MK22/
├── Day8_scans_MK22/
├── Day10_scans_MK22/
├── Day14_scans_MK22/
├── Day16_scans_MK22/
├── Day21_scans_MK22/
└── Day24_scans_MK22/
```

### File Naming Convention
TIF files follow the pattern: `[Prefix]_[Treatment]_[Set]_[Day]_[Timestamp]_[Number].tif`

- **Prefixes**: F_ (fertilizer), OG_ (organic), S_ (standard)
- **Days**: Dynamically detected from filenames (e.g., day1, day3, day14, etc.)
- **Sets**: set1, set2, set3 (experimental replicates)

### Root Type Directories
Separate folders contain SLEAP annotation files for:
- Primary root annotations
- Lateral root annotations  
- Tertiary root annotations

## Video Metadata Robustness

When extracting video names from SLEAP labeled frames:
- **IMPORTANT**: The `video.filename` attribute may be a list of Path objects (e.g., `[WindowsPath('path/to/file.tif')]`), not a string!
- Always check if `filename` is a list and extract the first element if so.
- Check both `video.filename` and `video.backend.filename` as fallbacks.
- **CRITICAL**: SLEAP Video objects may evaluate to `False` in boolean contexts. Never use `if not labeled_frame.video:` - instead check `if not hasattr(labeled_frame, "video"):`.
- Use `Path(...).stem` to strip extensions after extracting the actual path.
- Check type before string operations - non-string types (like integers) should return "unknown".
- Handle malformed string representations like `"[WindowsPath('incomplete"` gracefully.
- Direct filename (`video.filename`) should take precedence over backend filename.

## Testing Best Practices

### Using Real SLEAP Data
- Always create tests using real SLEAP data fixtures when available (see `tests/conftest.py`)
- The test data file `tests/data/lateral_root_MK22_Day14_test_labels.v003.slp` contains real SLEAP annotations
- Real data tests catch edge cases that mocks might miss (e.g., Video objects evaluating to False)

### Mock Objects
- When creating Mock objects for nodes, always set the `.name` attribute directly:
  ```python
  node = Mock()
  node.name = "root_tip"  # Don't use Mock(name="root_tip")
  ```
- This ensures the `.name` attribute returns a string, not another Mock object

### Code Formatting
- The project uses `black` for code formatting with configuration in `pyproject.toml`
- Run `black src/ tests/ sleap_viz.py` to format all Python files
- Black is included in the dev dependencies

## Recent Updates (August 2025)

### Fixed Video Name Extraction
- Video name extraction now correctly handles SLEAP's list-of-Path format for filenames
- Fixed issue where Video objects evaluating to False would return "unknown"
- Added comprehensive tests for all video filename formats

### Modular Architecture
- Reorganized code into four core modules in `src/`:
  - `video_utils.py`: Video metadata extraction
  - `plotting_utils.py`: Plotly visualization functions  
  - `data_utils.py`: Data export and analysis
  - `saving_utils.py`: Automated batch export functionality
- All functions are fully tested with high coverage
- Marimo notebook imports from modules to avoid variable conflicts

### Testing Infrastructure
- Created `tests/conftest.py` with centralized pytest fixtures
- Added real SLEAP data tests alongside mock tests
- All tests now pass consistently

### Automated Export System
- Replaced manual save buttons with a single "Save All" button
- Exports all labeled frames automatically to a timestamped folder
- Includes both static (PNG) and interactive (HTML) plots
- Saves comprehensive CSV summary alongside visualizations

## Output Saving Guidelines

- Avoid redundant UI for actions already available via Plotly.
- Automate saving of all labeled frames on user trigger.
- Use a unique timestamped folder for every export.
- Save both interactive (.html) and static (.png) plots for each frame.
- Base file naming on the video filename and frame index.
- Save CSV summaries alongside visualizations for consistency.

### Export Directory Structure
When using the "Save All" button, files are exported to:
```
output/
└── output_YYYYMMDD_HHMMSS_ffffff/
    ├── video_name_frame_0000.png
    ├── video_name_frame_0000.html
    ├── video_name_frame_0001.png
    ├── video_name_frame_0001.html
    ├── ...
    └── video_name_instances.csv
```

The microsecond precision in timestamps ensures unique directory names even for rapid consecutive exports.

## Save-All Export Logic

- Use `mo.ui.run_button()` for export operations - it's designed for triggering computations.
- Check `if button is not None and button.value:` to detect clicks (handles cases where button might not exist).
- Never use the UIElement itself in boolean contexts (e.g., avoid `if button and button.value:`).
- Always access `.value` in a **different cell** from the one where the button is created.
- The run button automatically resets to `False` after dependent cells execute.
- Save all outputs to a timestamped folder when the button is clicked.
- Include PNG, HTML plots, and CSV exports with clear naming conventions.
- Report progress interactively and summarize export results at the end.

## Plotly Visualization Quality

- Always show correct X, Y coordinates in hover tooltips.
- Use `hovertemplate` or `hovertext` to control node/edge info.
- When plotting nodes, show node name and index in tooltip.
- Avoid reusing edge labels or confusing identifiers for node-level scatter traces.
- Align hover data with axes scale and orientation (check for reversed y-axis or scaling).
- When using edge coloring mode, create separate traces for edges (lines only) and nodes (markers).
- Set `hoverinfo="skip"` for edge traces to avoid confusing hover information.
- Include instance information in hover templates to identify which instance a node belongs to.
- Format hover templates with HTML tags for clear structure (e.g., `<b>` for headers, `<br>` for line breaks).
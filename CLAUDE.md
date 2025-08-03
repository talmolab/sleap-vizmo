# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SLEAP-Vizmo is an interactive visualization tool for SLEAP (Social LEAP Estimates Animal Poses) annotation files. It provides a modern, web-based interface for exploring pose tracking data using Marimo notebooks and Plotly visualizations.

## Project Structure

```
sleap-vizmo/
├── sleap_viz.py              # Main Marimo notebook application
├── sleap_vizmo/              # Core package with utility modules
│   ├── __init__.py           # Package initialization and exports
│   ├── video_utils.py        # Video metadata extraction utilities
│   ├── plotting_utils.py     # Plotly visualization functions
│   ├── data_utils.py         # Data export and analysis utilities
│   └── saving_utils.py       # Batch export and file management
├── tests/                    # Comprehensive pytest test suite
│   ├── conftest.py          # Shared fixtures and test data
│   ├── test_video_utils.py  # Tests for video utilities
│   ├── test_plotting_utils.py # Tests for plotting utilities
│   ├── test_data_utils.py   # Tests for data utilities
│   ├── test_saving_utils.py # Tests for saving utilities
│   ├── test_sleap_integration.py # Integration tests with real data
│   └── test_button_logic.py # Tests for UI button behavior
├── .github/workflows/        # CI/CD configuration
│   ├── ci.yml               # Testing and linting
│   └── uvpublish.yml        # PyPI publishing
├── pyproject.toml           # Project configuration and dependencies
├── LICENSE                  # MIT license
└── output/                  # Default export directory
```

## Key Design Principles

1. **Modular Architecture**: All functions are in `sleap_vizmo/` package for reusability and testing
2. **High Test Coverage**: Comprehensive pytest tests targeting >90% coverage
3. **Cross-platform Compatibility**: Use `Path.as_posix()` for paths, handle Windows/Unix differences
4. **Marimo Best Practices**: The notebook imports from `sleap_vizmo` to avoid variable conflicts
5. **Type Safety**: Use type hints and handle edge cases (None values, empty data, etc.)

## Import Pattern

**IMPORTANT**: All imports should use the `sleap_vizmo` package name, not `src`:

```python
# Correct
from sleap_vizmo.video_utils import extract_video_name
from sleap_vizmo.plotting_utils import create_frame_figure
from sleap_vizmo.data_utils import export_labels_to_dataframe
from sleap_vizmo.saving_utils import save_all_frames

# Incorrect (old pattern - do not use)
from src.video_utils import extract_video_name  # DON'T DO THIS
```

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

## Common Commands

### Development Setup
```bash
# Create and activate environment
conda create -n sleap-vizmo-dev python=3.11
conda activate sleap-vizmo-dev

# Install in development mode
pip install -e ".[dev]"
```

### Running the Visualizer
```bash
# Run the interactive visualizer
python -m marimo run sleap_viz.py

# Or edit the visualizer interactively
python -m marimo edit sleap_viz.py
```

### Testing and Code Quality
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_video_utils.py -v

# Format code with black
black sleap_vizmo tests sleap_viz.py

# Check formatting without changes
black sleap_vizmo tests sleap_viz.py --check

# Run linting
ruff check sleap_vizmo/
```

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
- Run `black sleap_vizmo tests sleap_viz.py` to format all Python files
- Black is included in the dev dependencies

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
    └── labels_frames{N}_instances{M}.csv
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

## CI/CD Configuration

The project uses GitHub Actions for continuous integration:

### ci.yml
- Runs on pull requests affecting code files
- Tests on multiple platforms (Ubuntu, Windows, macOS)
- Python 3.11 support
- Runs black formatting check
- Runs ruff linting
- Executes full test suite with coverage reporting
- Uploads coverage to Codecov

### uvpublish.yml
- Triggers on GitHub releases
- Publishes to TestPyPI for pre-releases (versions with letters)
- Publishes to PyPI for stable releases
- Uses trusted publishing (no tokens needed)

## Recent Updates (January 2025)

### Package Restructuring
- Migrated from `src/` to `sleap_vizmo/` package structure
- Updated all imports throughout the codebase
- Fixed test imports to use new package name
- Added proper package initialization with `__all__` exports

### CI/CD Setup
- Added GitHub Actions workflows for testing and publishing
- Configured black and ruff for code quality
- Set up automated PyPI publishing
- Added multi-platform testing support

### Documentation Updates
- Created user-friendly README with clear sections
- Removed user-specific paths from documentation
- Added badges for CI status and PyPI
- Updated installation and usage instructions
# SLEAP Medicago Plates Visualization & Analysis

Interactive visualization and analysis tool for SLEAP (Social LEAP Estimates Animal Poses) annotations, specifically designed for tracking plant root growth in Medicago plates over time. Built with Marimo and Plotly for a modern, interactive experience.

## 🌱 Project Overview

This project provides tools for visualizing and analyzing SLEAP pose estimation data from time-series experiments tracking primary, lateral, and tertiary root development in Medicago truncatula across a 24-day experimental period. The interactive visualizer enables researchers to explore labeled frames, export publication-ready figures, and analyze root growth patterns.

## 📋 Table of Contents

- [For Users](#-for-users)
  - [Quick Start](#quick-start)
  - [Features](#features)
  - [Usage Guide](#usage-guide)
  - [Export Options](#export-options)
- [For Developers](#-for-developers)
  - [Architecture](#architecture)
  - [Development Setup](#development-setup)
  - [Testing](#testing)
  - [Contributing](#contributing)
- [Project Structure](#-project-structure)
- [Data Organization](#-data-organization)

---

## 👤 For Users

### Quick Start

1. **Install the environment** (Windows example shown):
   ```bash
   # Using mamba/conda
   mamba create -n sleap_viz python=3.11
   mamba activate sleap_viz
   
   # Install dependencies
   pip install marimo sleap-io plotly numpy pandas kaleido
   ```

2. **Run the visualizer**:
   ```bash
   # On Windows
   C:\Users\Elizabeth\miniforge3\envs\sleap_viz\python.exe -m marimo run sleap_viz.py
   
   # On Unix/Mac
   python -m marimo run sleap_viz.py
   ```

3. **Load your SLEAP file** and start exploring!

### Features

- **📁 Interactive File Loading**: Load SLEAP `.slp` files via text input with real-time validation
- **📊 Smart Visualization**:
  - Hover tooltips show node names, instance info, and precise coordinates
  - Skeleton connections with proper edge/node separation
  - Multiple coloring modes (by instance, by node, by track)
  - Toggle options for images, edges, labels, and coloring schemes
- **🎯 Frame Navigation**: Slider to navigate through labeled frames with instant updates
- **📈 Data Display**: Coordinate table showing all instances with video context
- **💾 Batch Export System**:
  - One-click export of all labeled frames
  - Generates PNG (static) and HTML (interactive) plots
  - Creates comprehensive CSV with descriptive filename
  - Organized in timestamped folders

### Usage Guide

1. **Loading Data**:
   - Enter the path to your `.slp` file in the text input
   - The app validates the file and displays a summary
   - Adjust the number of frames to display (default: 10)

2. **Exploring Frames**:
   - Use the frame slider to navigate
   - Hover over nodes to see detailed information
   - Toggle visualization options to focus on specific features

3. **Exporting Results**:
   - Click "📦 Save All Frames" to export everything
   - Files are saved to `output/output_YYYYMMDD_HHMMSS_ffffff/`
   - CSV filename includes: `{labels_file}_frames{N}_instances{M}.csv`

### Export Options

The export system creates:
- **PNG files**: High-resolution static images (1200x800px, 2x scale)
- **HTML files**: Interactive Plotly figures with full zoom/pan capabilities
- **CSV summary**: All instance coordinates with frame and video metadata

---

## 💻 For Developers

### Architecture

The project follows a modular architecture with clear separation of concerns:

```
src/
├── __init__.py           # Package exports
├── video_utils.py        # Video metadata extraction
├── plotting_utils.py     # Plotly visualization functions
├── data_utils.py         # Data export and analysis
└── saving_utils.py       # Automated batch export
```

### Development Setup

1. **Clone and install in development mode**:
   ```bash
   git clone <repository>
   cd SLEAP_medicago_plates
   
   # Install with development dependencies
   pip install -e ".[dev]"
   
   # Or using uv
   uv pip install -e ".[dev]"
   ```

2. **Install pre-commit hooks** (if using):
   ```bash
   pre-commit install
   ```

### Testing

The project maintains high test coverage with comprehensive test suites:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test modules
python -m pytest tests/test_plotting_utils.py -v

# Format code before committing
python -m black src/ tests/ sleap_viz.py
```

#### Test Structure
- `tests/conftest.py` - Shared fixtures and test data
- `tests/test_video_utils.py` - Video metadata extraction tests
- `tests/test_plotting_utils.py` - Visualization tests including hover templates
- `tests/test_data_utils.py` - Data export functionality tests
- `tests/test_saving_utils.py` - Batch export system tests

### Contributing

1. **Code Style**:
   - Use Black for formatting (configured in `pyproject.toml`)
   - Follow the patterns in CLAUDE.md for Marimo-specific code
   - Add tests for new functionality

2. **Marimo Best Practices**:
   - Never redefine variables across cells
   - Use unique prefixes for cell-specific variables
   - Access `mo.ui` element values only in downstream cells
   - Use `mo.ui.run_button()` for action triggers

3. **Pull Request Process**:
   - Ensure all tests pass
   - Update documentation as needed
   - Add your changes to the "Recent Updates" in CLAUDE.md

---

## 📂 Project Structure

```
SLEAP_medicago_plates/
├── sleap_viz.py          # Main Marimo application
├── src/                  # Core utility modules
│   ├── video_utils.py    # Video name extraction, metadata parsing
│   ├── plotting_utils.py # Plotly figures, hover templates, coloring
│   ├── data_utils.py     # DataFrame export, CSV generation
│   └── saving_utils.py   # Batch export, directory management
├── tests/                # Comprehensive test suite
│   ├── conftest.py       # Shared fixtures
│   ├── data/             # Test SLEAP files
│   └── test_*.py         # Module-specific tests
├── lateral/              # Lateral root SLEAP annotations
├── primary/              # Primary root SLEAP annotations
├── tertiary/             # Tertiary root SLEAP annotations
├── output/               # Default export directory
├── CLAUDE.md             # AI assistant guidelines
├── pyproject.toml        # Project configuration
└── organize_tifs.sh      # TIF file organization script
```

---

## 📊 Data Organization

### SLEAP Files
- Organized by root type: primary, lateral, tertiary
- Naming convention: `{root_type}_root_{experiment}_{day}_labels.v{version}.slp`

### TIF Images
- Organized by experimental day in `tifs/{PROJECT}/`
- File pattern: `{Prefix}_{Treatment}_{Set}_{Day}_{Timestamp}_{Number}.tif`
- Use `organize_tifs.sh` to structure downloaded files

### Export Structure
```
output_YYYYMMDD_HHMMSS_ffffff/
├── {video_name}_frame_0000.png
├── {video_name}_frame_0000.html
├── ...
└── {labels_name}_frames{N}_instances{M}.csv
```

---

## 🔧 Troubleshooting

### Common Issues

1. **"AttributeError: '_md' object has no attribute 'update'"**
   - This occurs with older Marimo versions
   - Solution: Update Marimo or use the current codebase

2. **Button not triggering**
   - Ensure you're using `mo.ui.run_button()` not `mo.ui.button()`
   - Check that you're accessing `.value` in a different cell

3. **Hover shows wrong information**
   - Update to the latest version which separates edge and node traces
   - Edges now have `hoverinfo="skip"` to avoid confusion

### Getting Help

- Check CLAUDE.md for detailed technical guidelines
- Review test files for usage examples
- Open an issue with reproducible steps for bugs

---

## 📝 License

[Add your license information here]

## 🙏 Acknowledgments

Built with:
- [SLEAP](https://sleap.ai/) - Animal pose tracking framework
- [Marimo](https://marimo.io/) - Reactive Python notebooks
- [Plotly](https://plotly.com/python/) - Interactive visualizations
# SLEAP-Vizmo: Interactive SLEAP Visualization with Marimo

[![CI](https://github.com/talmolab/sleap-vizmo/actions/workflows/ci.yml/badge.svg)](https://github.com/talmolab/sleap-vizmo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sleap-vizmo)](https://pypi.org/project/sleap-vizmo/)
[![Python Version](https://img.shields.io/pypi/pyversions/sleap-vizmo)](https://pypi.org/project/sleap-vizmo/)

Interactive visualization and analysis tool for SLEAP (Social LEAP Estimates Animal Poses) annotations. Built with Marimo and Plotly for a modern, interactive experience.

## 🌟 Features

- **📁 Interactive File Loading**: Load SLEAP `.slp` files with real-time validation
- **📊 Smart Visualization**:
  - Hover tooltips with node names, instance info, and precise coordinates
  - Skeleton connections with proper edge/node separation
  - Multiple coloring modes (by instance, by node, by track)
  - Toggle options for images, edges, labels, and coloring schemes
- **🎯 Frame Navigation**: Slider to navigate through labeled frames
- **📈 Data Display**: Coordinate table showing all instances with video context
- **💾 Batch Export**: One-click export of all frames as PNG, HTML, and CSV

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when available)
pip install sleap-vizmo

# Or install from source
git clone https://github.com/talmolab/sleap-vizmo.git
cd sleap-vizmo
pip install -e .
```

### Running the Visualizer

```bash
# Run the interactive visualizer
python -m marimo run sleap_viz.py

# Or edit the visualizer
python -m marimo edit sleap_viz.py
```

## 📋 Usage Guide

1. **Load your SLEAP file**: Enter the path to your `.slp` file
2. **Navigate frames**: Use the slider to explore labeled frames
3. **Customize display**: Toggle visualization options
4. **Export results**: Click "Save All Frames" to export everything

### Export Structure
```
output/
└── output_YYYYMMDD_HHMMSS_ffffff/
    ├── video_name_frame_0000.png
    ├── video_name_frame_0000.html
    ├── ...
    └── labels_summary.csv
```

## 💻 Development

### Setup

```bash
# Clone repository
git clone https://github.com/talmolab/sleap-vizmo.git
cd sleap-vizmo

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sleap_vizmo --cov-report=html

# Run specific test file
pytest tests/test_plotting_utils.py -v

# Format code
black sleap_vizmo tests sleap_viz.py

# Lint code
ruff check sleap_vizmo/
```

### Project Structure

```
sleap-vizmo/
├── sleap_viz.py              # Main Marimo application
├── sleap_vizmo/              # Core package
│   ├── __init__.py
│   ├── video_utils.py        # Video metadata extraction
│   ├── plotting_utils.py     # Plotly visualization functions
│   ├── data_utils.py         # Data export and analysis
│   └── saving_utils.py       # Batch export functionality
├── tests/                    # Comprehensive test suite
│   ├── conftest.py          # Shared fixtures
│   ├── data/                # Test SLEAP files
│   └── test_*.py            # Module tests
├── .github/                 # CI/CD workflows
│   └── workflows/
│       ├── ci.yml           # Tests and linting
│       └── uvpublish.yml    # PyPI publishing
├── pyproject.toml           # Project configuration
├── CLAUDE.md                # AI assistant guidelines
└── README.md                # This file
```

## 🧪 For Developers

### Architecture

The project follows a modular architecture:

- **`video_utils`**: Handles video metadata extraction from SLEAP files
- **`plotting_utils`**: Creates Plotly visualizations with proper hover info
- **`data_utils`**: Exports data to pandas DataFrames and CSV
- **`saving_utils`**: Manages batch exports and file organization

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure tests pass and code is formatted
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Use Black for formatting (configured in `pyproject.toml`)
- Follow Google-style docstrings
- Add comprehensive tests for new features
- Update CLAUDE.md if changing core behavior

## 📊 Data Formats

### Input
- SLEAP files (`.slp`) containing pose annotations
- Supports video backends and image sequences

### Output
- **PNG**: High-resolution static images (1200x800px, 2x scale)
- **HTML**: Interactive Plotly figures with zoom/pan
- **CSV**: Instance coordinates with frame and video metadata

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Ensure you've installed in development mode: `pip install -e .`
2. **Marimo errors**: Update to latest version: `pip install --upgrade marimo`
3. **Export failures**: Check write permissions in the output directory

### Getting Help

- Check [CLAUDE.md](CLAUDE.md) for technical guidelines
- Review test files for usage examples
- Open an [issue](https://github.com/talmolab/sleap-vizmo/issues) for bugs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [SLEAP](https://sleap.ai/) - Animal pose tracking framework
- [Marimo](https://marimo.io/) - Reactive Python notebooks
- [Plotly](https://plotly.com/python/) - Interactive visualizations

## 📚 Citation

If you use SLEAP-Vizmo in your research, please cite:

```bibtex
@software{sleap-vizmo,
  title = {SLEAP-Vizmo: Interactive SLEAP Visualization with Marimo},
  author = {Berrigan, Elizabeth},
  year = {2025},
  url = {https://github.com/talmolab/sleap-vizmo}
}
```
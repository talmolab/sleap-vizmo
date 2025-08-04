# SLEAP-Vizmo Examples

This directory contains example scripts and demos for using SLEAP-Vizmo.

## Files

### `demo_sleap_roots_integration.py`
A simple demo showing how to use the SLEAP-roots integration features:
- Loading multi-video SLEAP files
- Splitting by video
- Validating Series compatibility
- Saving individual video files

### `run_sleap_roots_processing.py`
A standalone command-line script version of the Jupyter notebook workflow:
- Processes lateral and primary root SLEAP files
- Runs the MultipleDicotPipeline
- Generates trait CSV files
- Can be run from the command line with arguments

Usage:
```bash
python examples/run_sleap_roots_processing.py \
    --lateral path/to/lateral.slp \
    --primary path/to/primary.slp \
    --output ./output/my_results
```

### `check_sleap_roots_setup.py`
A pre-flight check script to verify your environment is set up correctly:
- Tests all required imports
- Verifies test data files exist
- Checks that SLEAP files can be loaded
- Tests basic functionality

Run this before using the Jupyter notebook:
```bash
python examples/check_sleap_roots_setup.py
```

## Note
These are example scripts for demonstration purposes. For production use, 
refer to the main documentation and use the provided modules directly.
"""Test that example scripts are valid Python."""

import subprocess
import sys
from pathlib import Path
import pytest


class TestExamples:
    """Test example scripts for basic validity."""

    @pytest.fixture
    def examples_dir(self):
        """Get examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_examples_directory_exists(self, examples_dir):
        """Test that examples directory exists."""
        assert examples_dir.exists()
        assert examples_dir.is_dir()

    def test_demo_script_syntax(self, examples_dir):
        """Test demo script has valid syntax."""
        demo_file = examples_dir / "demo_sleap_roots_integration.py"
        assert demo_file.exists()

        # Check syntax by compiling
        with open(demo_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            compile(code, str(demo_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in demo script: {e}")

    def test_run_script_syntax(self, examples_dir):
        """Test run script has valid syntax."""
        run_file = examples_dir / "run_sleap_roots_processing.py"
        assert run_file.exists()

        # Check syntax by compiling
        with open(run_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            compile(code, str(run_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in run script: {e}")

    def test_check_script_syntax(self, examples_dir):
        """Test check script has valid syntax."""
        check_file = examples_dir / "check_sleap_roots_setup.py"
        assert check_file.exists()

        # Check syntax by compiling
        with open(check_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            compile(code, str(check_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in check script: {e}")

    def test_run_script_help(self, examples_dir):
        """Test that run script shows help."""
        run_file = examples_dir / "run_sleap_roots_processing.py"

        # Run with --help
        result = subprocess.run(
            [sys.executable, str(run_file), "--help"], capture_output=True, text=True
        )

        # Should exit with 0 and show help
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--lateral" in result.stdout
        assert "--primary" in result.stdout

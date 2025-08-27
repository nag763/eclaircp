"""
Tests for the CLI module.
"""

import pytest
from eclaircp.cli import main


def test_main_returns_zero():
    """Test that main function returns 0 for success."""
    result = main([])
    assert result == 0


def test_main_with_args():
    """Test main function with arguments."""
    result = main(["--help"])
    assert result == 0
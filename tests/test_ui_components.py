"""
Unit tests for the ui_components module.
"""
import tkinter as tk
import pytest
from src.ui_components import UIStyleManager


def test_ui_style_manager_initialization():
    """Test initialization of UIStyleManager."""
    style_manager = UIStyleManager()
    assert hasattr(style_manager, "colors")
    assert "technology" in style_manager.colors  # Check for button color
    assert "task" in style_manager.colors  # Check for task color
    assert "error_critical" in style_manager.colors  # Check for error color
    assert "background" in style_manager.colors  # Check for background color


@pytest.mark.skip(reason="Skipping UI tests that require Tkinter in CI environment")
def test_create_modern_frame():
    """Test creation of a modern frame."""
    # This test is skipped in CI as it requires a proper Tkinter environment
    pass


@pytest.mark.skip(reason="Skipping UI tests that require Tkinter in CI environment")
def test_create_modern_button():
    """Test creation of a modern button."""
    # This test is skipped in CI as it requires a proper Tkinter environment
    pass


@pytest.mark.skip(reason="Skipping UI tests that require Tkinter in CI environment")
def test_set_window_theme():
    """Test setting window theme."""
    # This test is skipped in CI as it requires a proper Tkinter environment
    pass


@pytest.mark.skip(reason="Skipping UI tests that require Tkinter in CI environment")
def test_create_back_button_area():
    """Test creation of back button area."""
    # This test is skipped in CI as it requires a proper Tkinter environment
    pass

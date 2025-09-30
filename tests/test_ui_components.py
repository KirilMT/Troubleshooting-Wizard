"""
Unit tests for the ui_components module.
"""
import tkinter as tk
import pytest
from unittest.mock import MagicMock, patch
from src.ui_components import UIStyleManager


def test_ui_style_manager_initialization():
    """Test initialization of UIStyleManager."""
    style_manager = UIStyleManager()
    assert hasattr(style_manager, "colors")
    assert "technology" in style_manager.colors  # Check for button color
    assert "task" in style_manager.colors  # Check for task color
    assert "error_critical" in style_manager.colors  # Check for error color
    assert "background" in style_manager.colors  # Check for background color


def test_create_modern_frame():
    """Test creation of a modern frame."""
    root = tk.Tk()
    try:
        style_manager = UIStyleManager()
        frame = style_manager.create_modern_frame(root)

        assert isinstance(frame, tk.Frame)
        # Check if the frame has the expected styling
        assert frame.cget("bg") == style_manager.colors["background"]
    finally:
        root.destroy()


def test_create_modern_button():
    """Test creation of a modern button."""
    root = tk.Tk()
    try:
        style_manager = UIStyleManager()
        button = style_manager.create_modern_button(root, "Test Button", lambda: None, "technology")

        assert isinstance(button, tk.Button)
        assert button.cget("text") == "Test Button"
        # Check if the button has the expected styling
        assert button.cget("bg") == style_manager.colors["technology"]
    finally:
        root.destroy()


def test_set_window_theme():
    """Test setting window theme."""
    root = MagicMock()
    style_manager = UIStyleManager()
    bg_color = style_manager.set_window_theme(root, "technology")

    # The method should return the background color for the technology theme
    assert bg_color == style_manager.colors["bg_technology"]
    root.configure.assert_called_with(bg=bg_color)


def test_create_back_button_area():
    """Test creation of back button area."""
    root = tk.Tk()
    try:
        style_manager = UIStyleManager()
        frame = tk.Frame(root)

        def test_callback():
            pass

        back_frame = style_manager.create_back_button_area(frame, "Back to Test", test_callback)

        assert isinstance(back_frame, tk.Frame)
        # Check if the back button was created with correct text
        for widget in back_frame.winfo_children():
            if isinstance(widget, tk.Button):
                assert "Back to Test" in widget.cget("text")
    finally:
        root.destroy()

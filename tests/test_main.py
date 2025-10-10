"""
Unit tests for the main application module.

These tests focus on the core functionality of the MainApplication class,
avoiding direct testing of Tkinter UI components which are better tested manually.
"""
import os
import sys
import webbrowser
import pytest
from unittest.mock import MagicMock, patch, ANY
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the imports that would be problematic in tests
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()

# Import the main module
from src import main


class MockUIStyleManager:
    """Mock UIStyleManager for testing core functionality without UI."""

    def __init__(self):
        self.colors = {
            "technology": "#e1f5fe",
            "task": "#e8f5e9",
            "error_critical": "#ffebee",
            "background": "#f5f5f5",
            "surface": "#ffffff",
        }

    def create_modern_frame(self, *args, **kwargs):
        mock_frame = MagicMock()
        mock_frame.winfo_reqwidth.return_value = 800
        mock_frame.winfo_reqheight.return_value = 600
        return mock_frame

    def create_modern_button(self, *args, **kwargs):
        return MagicMock()

    def create_modern_label(self, *args, **kwargs):
        return MagicMock()

    def create_modern_entry(self, *args, **kwargs):
        return MagicMock()

    def create_back_button_area(self, *args, **kwargs):
        return MagicMock()

    def create_dual_back_button_area(self, *args, **kwargs):
        return MagicMock()

    def set_window_theme(self, *args, **kwargs):
        return self.colors.get(kwargs.get("theme", "background"), self.colors["background"])


# Sample test data
TEST_JSON_DATA = {
    "MainApplication": {
        "title": "Test Application",
        "width": 800,
        "height": 600,
        "Technologies": {
            "Tech1": {
                "button_text": "Test Tech 1",
                "tasks": [
                    {"PDF Task": {"task_type": "open_pdf", "pdf_path": "test.pdf"}},
                    {"URL Task": {"task_type": "open_url", "url_path": "http://example.com"}},
                ],
            }
        },
    },
    "labels": {
        "back_to_technologies": "Back to Technologies",
        "back_to_tasks": "Back to Tasks",
        "sew_db_not_specified": "Not specified",
        "insert_fault_code": "Search:",
        "search": "Go",
    },
}


@pytest.fixture
def mock_root():
    """Create a mock Tkinter root window for testing."""
    mock = MagicMock()
    mock.winfo_screenwidth.return_value = 1920
    mock.winfo_screenheight.return_value = 1080
    return mock


@pytest.fixture
def app(mock_root):
    """Create an instance of MainApplication for testing with all UI components mocked."""
    with patch("src.main.SEWDatabaseManager"), patch(
        "src.main.UIStyleManager", new=MockUIStyleManager
    ), patch("src.main.os.path.join", side_effect=os.path.join), patch(
        "src.main.os.path.dirname", return_value=os.path.dirname(__file__)
    ), patch(
        "src.main.os.path.exists", return_value=True
    ), patch(
        "src.main.os.path.abspath", side_effect=lambda x: x
    ), patch(
        "src.main.tk.Frame"
    ) as mock_frame, patch(
        "src.main.tk.Toplevel"
    ), patch(
        "src.main.webbrowser.open_new"
    ) as mock_webbrowser:
        # Mock frame with proper sizing methods
        mock_frame_instance = MagicMock()
        mock_frame_instance.winfo_reqwidth.return_value = 800
        mock_frame_instance.winfo_reqheight.return_value = 600
        mock_frame.return_value = mock_frame_instance

        # Patch the show_main_program method to avoid UI creation during init
        with patch.object(main.MainApplication, "show_main_program"):
            app = main.MainApplication(mock_root, TEST_JSON_DATA, os.path.dirname(__file__))

        # Mock the view stack and current view
        app.view_stack = []
        app.current_view = mock_frame_instance
        app.webbrowser = mock_webbrowser

        yield app


def test_initialization(app):
    """Test that the MainApplication initializes correctly."""
    assert app.root is not None
    assert app.initial_width == TEST_JSON_DATA["MainApplication"]["width"]
    assert app.initial_height == TEST_JSON_DATA["MainApplication"]["height"]
    assert app.json_data == TEST_JSON_DATA


def test_show_main_program(app):
    """Test that the main program view is shown correctly."""
    # Call the method
    app.show_main_program()

    # Verify the view was created
    assert app.current_view is not None


def test_show_technology(app):
    """Test showing a technology view."""
    tech_data = {
        "button_text": "Test Tech",
        "tasks": [{"Test Task": {"task_type": "test"}}],
        "name": "Test Technology",
    }

    # Call the method
    app.show_technology(tech_data)

    # Verify the view was updated
    assert app.current_view is not None
    assert app.variables == tech_data


def test_show_task_open_pdf(app):
    """Test showing a task to open a PDF."""
    task_attrs = {"task_type": "open_pdf", "pdf_path": "test.pdf"}
    tech_data = {"name": "Test Tech"}

    with patch("src.main.PDFViewerWindow") as mock_pdf_viewer, patch(
        "src.main.os.path.exists", return_value=True
    ):
        # Call the method
        app.show_task(task_attrs, tech_data)

        # Verify the PDF viewer was created
        mock_pdf_viewer.assert_called_once()


def test_show_task_open_url(app):
    """Test showing a task to open a URL."""
    task_attrs = {"task_type": "open_url", "url_path": "http://example.com"}
    tech_data = {"name": "Test Tech"}

    # Call the method
    app.show_task(task_attrs, tech_data)

    # Verify webbrowser.open_new was called
    app.webbrowser.assert_called_once_with("http://example.com")


def test_show_error_codes_search_uses_pdf_path(app):
    """Test that traditional error search uses pdf_path."""
    task_attrs = {"task_type": "error_codes", "pdf_path": "error_manual.pdf"}
    tech_data = {"button_text": "Some Other Tech"}  # To ensure traditional search is used

    # Mock the entry field to return a search term
    mock_entry = MagicMock()
    mock_entry.get.return_value = "E-123"
    app.ui_style.create_modern_entry = MagicMock(return_value=mock_entry)

    # Use a side effect to capture the command from the search button
    captured_command = {}

    def capture_command_side_effect(*args, **kwargs):
        # args[1] is the button text, args[2] is the command lambda
        if args[1] == app.json_data["labels"]["search"]:
            captured_command["command"] = args[2]
        return MagicMock()

    app.ui_style.create_modern_button = MagicMock(side_effect=capture_command_side_effect)

    with patch.object(app, "_open_pdf_viewer") as mock_open_pdf_viewer:
        # This will build the UI and trigger the side effect
        app.show_error_codes(task_attrs, tech_data)

        # Ensure the command was captured
        assert "command" in captured_command, "Search button command was not captured."

        # Execute the captured command
        captured_command["command"]()

        # Verify that the PDF viewer was called with the correct path and search term
        mock_open_pdf_viewer.assert_called_once_with("error_manual.pdf", search_term="E-123")


def test_format_single_line_content(app):
    """Test formatting text to a single line."""
    # Test with newlines and extra spaces
    assert app._format_single_line_content("line1\nline2\n   line3   ") == "line1 line2 line3"

    # Test with empty input (returns default message)
    assert app._format_single_line_content("") == "Not specified"

    # Test with None input (returns default message)
    assert app._format_single_line_content(None) == "Not specified"


def test_show_previous_view(app):
    """Test navigation to previous view."""
    # Set up view stack with proper tuple format (function, data)
    mock_func = MagicMock()
    app.view_stack = [(mock_func, None)]

    # Call the method
    app.show_previous_view()

    # Verify the function was called
    mock_func.assert_called_once()
    assert len(app.view_stack) == 0  # Should have removed the view from stack

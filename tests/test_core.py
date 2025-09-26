"""
Unit tests for the core functionality of the Troubleshooting Wizard.

These tests focus on the business logic rather than the UI components.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch, ANY

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the imports that would be problematic in tests
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()

# Import the main module
from src import main

# Sample test data
TEST_JSON_DATA = {
    "MainApplication": {
        "title": "Test Application",
        "width": 800,
        "height": 600,
        "colors": {
            "technology": "#e1f5fe",
            "task": "#e8f5e9",
            "error_critical": "#ffebee",
            "background": "#f5f5f5",
        },
        "Technologies": {
            "Tech1": {
                "button_text": "Test Tech 1",
                "tasks": [{"Task 1": {"task_type": "open_url", "url_path": "test.pdf"}}],
            }
        },
        "labels": {
            "back_to_technologies": "Back to Technologies",
            "sew_db_not_specified": "Not specified",
        },
    }
}


class TestMainApplication:
    """Test the MainApplication class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the Tkinter root window
        self.mock_root = MagicMock()
        self.mock_root.winfo_screenwidth.return_value = 1920
        self.mock_root.winfo_screenheight.return_value = 1080

        # Create a partial mock of MainApplication
        with patch("src.main.SEWDatabaseManager"), patch("src.main.UIStyleManager"), patch(
            "src.main.PDFViewerWindow"
        ):
            # Create the app instance without calling __init__
            self.app = main.MainApplication.__new__(main.MainApplication)
            self.app.root = self.mock_root
            self.app.json_data = TEST_JSON_DATA
            self.app.initial_width = 800
            self.app.initial_height = 600

            # Mock UI components and methods
            self.app.ui_style = MagicMock()
            self.app.view_stack = []
            self.app.current_view = MagicMock()
            self.app.destroy_current_view = MagicMock()

            # Mock additional required attributes
            self.app.json_data = TEST_JSON_DATA
            self.app.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.app.variables = {}

            # Mock the _open_pdf_viewer method
            self.app._open_pdf_viewer = MagicMock()

            # Mock window methods
            self.app.root = MagicMock()
            self.app.root.winfo_reqwidth.return_value = 200
            self.app.root.winfo_reqheight.return_value = 200

            # Mock frame methods
            self.mock_frame = MagicMock()
            self.mock_frame.winfo_reqwidth.return_value = 200
            self.mock_frame.winfo_reqheight.return_value = 200

            # Mock the UI style manager methods
            self.app.ui_style.set_window_theme.return_value = "#f0f0f0"
            self.app.ui_style.create_modern_frame.return_value = self.mock_frame
            self.app.ui_style.create_back_button_area.return_value = MagicMock()
            self.app.ui_style.create_modern_button.return_value = MagicMock()

            # Mock the columnconfigure method on the frame
            self.mock_frame.columnconfigure = MagicMock()

            # Create a mock button for the technology buttons
            self.mock_button = MagicMock()
            self.mock_button.grid = MagicMock()
            self.app.ui_style.create_modern_button.return_value = self.mock_button

            # Add labels to json_data
            self.app.json_data["labels"] = {
                "back_to_technologies": "Back to Technologies",
                "sew_db_not_specified": "Not specified",
            }

    def test_initialization(self):
        """Test that the MainApplication initializes correctly."""
        assert self.app.root is not None
        assert self.app.initial_width == 800
        assert self.app.initial_height == 600
        assert self.app.json_data == TEST_JSON_DATA

    def test_show_main_program(self):
        """Test that the main program view is shown correctly."""
        # Setup - use the mocks from setup_method
        self.app.current_view = MagicMock()
        self.app.view_stack = [MagicMock()]  # Start with a non-empty stack to test it gets cleared

        # Configure the mock frame
        self.mock_frame.winfo_reqwidth.return_value = 200
        self.mock_frame.winfo_reqheight.return_value = 200

        # Configure the mock UI style
        self.app.ui_style.set_window_theme.return_value = "#f0f0f0"
        self.app.ui_style.create_modern_frame.return_value = self.mock_frame

        # Configure the mock button
        self.mock_button.grid = MagicMock()

        # Set up the test data
        self.app.json_data = {
            "MainApplication": {
                "Technologies": {
                    "tech1": {"button_text": "Tech 1"},
                    "tech2": {"button_text": "Tech 2"},
                }
            }
        }

        # Call the method
        self.app.show_main_program()

        # Verify the view was created and set as current_view
        assert self.app.current_view is not None

        # Verify set_window_theme was called with the correct arguments
        self.app.ui_style.set_window_theme.assert_called_once_with(self.app.root, "technology")

        # Verify create_modern_frame was called with the correct arguments
        self.app.ui_style.create_modern_frame.assert_called_once_with(
            self.app.root, bg="#f0f0f0"  # The mocked background color
        )

        # Verify the frame was packed with the correct arguments
        self.mock_frame.pack.assert_called_once_with(fill="both", expand=True, padx=10, pady=10)

        # Verify the buttons were created (one for each technology)
        assert self.app.ui_style.create_modern_button.call_count == 2

        # Verify the buttons were gridded
        assert self.mock_button.grid.call_count == 2

        # Verify columnconfigure was called on the frame for each column
        assert self.mock_frame.columnconfigure.call_count >= 1  # At least one column

        # Verify the view stack was cleared (since show_main_program calls view_stack.clear())
        assert self.app.view_stack == []

    def test_show_technology(self):
        """Test showing a technology view."""
        # Setup
        tech_data = {
            "button_text": "Test Tech",
            "tasks": [{"Test Task": {"task_type": "test"}}],
            "name": "Test Technology",
        }

        # Create a mock frame with required methods
        mock_frame = MagicMock()
        mock_frame.winfo_reqwidth.return_value = 100
        mock_frame.winfo_reqheight.return_value = 200

        # Mock the UI style to return our mock frame
        self.app.ui_style.create_modern_frame.return_value = mock_frame

        # Mock the pack method that will be called on the frame
        mock_frame.pack = MagicMock()

        # Mock the create_back_button_area method
        self.app.ui_style.create_back_button_area = MagicMock()

        # Mock the _modify_tasks method
        self.app._modify_tasks = MagicMock()

        # Call the method
        self.app.show_technology(tech_data)

        # Verify the view was updated
        assert self.app.variables == tech_data

        # Verify methods were called
        self.app._modify_tasks.assert_called_once_with(tech_data)
        self.app.ui_style.create_back_button_area.assert_called_once()

        # Verify the view stack was updated
        assert len(self.app.view_stack) == 1
        assert self.app.current_view == mock_frame

    def test_show_task_open_url(self):
        """Test showing a task with URL."""
        # Setup
        task_attrs = {"task_type": "open_url", "url_path": "test.pdf"}
        tech_data = {"name": "Test Tech"}

        # Mock the _open_pdf_viewer method
        self.app._open_pdf_viewer = MagicMock()

        # Call the method
        self.app.show_task(task_attrs, tech_data)

        # Verify _open_pdf_viewer was called with the correct arguments
        # Note: The method is called with page_number=None by default
        self.app._open_pdf_viewer.assert_called_once_with("test.pdf", page_number=None)

    def test_format_single_line_content(self):
        """Test formatting text to a single line."""
        # Test with newlines and extra spaces
        assert (
            self.app._format_single_line_content("line1\nline2\n   line3   ") == "line1 line2 line3"
        )

        # Test with empty input - should return the default message from json_data
        assert self.app._format_single_line_content("") == "Not specified"

        # Test with None input - should return the default message from json_data
        assert self.app._format_single_line_content(None) == "Not specified"

    def test_show_previous_view(self):
        """Test navigation to previous view."""
        # Set up view stack with proper format (function, data) tuples
        view_func1 = MagicMock()
        view_data1 = {}
        view_func2 = MagicMock()
        view_data2 = {}

        # Mock the show_main_program method that will be in the view stack
        self.app.show_main_program = MagicMock()

        # Set up the view stack with a callable that doesn't require arguments
        self.app.view_stack = [
            (lambda: None, None),  # Previous view
            (self.app.show_main_program, None),  # Current view
        ]

        # Call the method
        self.app.show_previous_view()

        # Verify the view function was called
        self.app.show_main_program.assert_called_once()

        # Verify the view stack was updated (should have removed the last view)
        assert len(self.app.view_stack) == 1

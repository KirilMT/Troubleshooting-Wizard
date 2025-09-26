"""
Unit tests for the main application module.

These tests focus on the core functionality of the MainApplication class,
avoiding direct testing of Tkinter UI components which are better tested manually.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY, PropertyMock
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the imports that would be problematic in tests
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

# Import the main module after setting up mocks
from src import main

class MockUIStyleManager:
    """Mock UIStyleManager for testing core functionality without UI."""
    def __init__(self):
        self.colors = {
            'technology': '#e1f5fe',
            'task': '#e8f5e9',
            'error_critical': '#ffebee',
            'background': '#f5f5f5'
        }
    
    def create_modern_frame(self, *args, **kwargs):
        frame = MagicMock()
        frame.winfo_reqwidth.return_value = 100  # Return a default width for testing
        return frame
    
    def create_modern_button(self, *args, **kwargs):
        return MagicMock()
    
    def create_back_button_area(self, *args, **kwargs):
        return MagicMock()
    
    def set_window_theme(self, *args, **kwargs):
        return self.colors.get(kwargs.get('theme', 'background'), self.colors['background'])

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
            "background": "#f5f5f5"
        },
        "Technologies": {
            "Tech1": {
                "button_text": "Test Tech 1",
                "tasks": [
                    {"Task 1": {"task_type": "open_url", "url_path": "test.pdf"}}
                ]
            }
        },
        "labels": {
            "back_to_technologies": "Back to Technologies",
            "sew_db_not_specified": "Not specified"
        }
    }
}

@pytest.fixture
def mock_root():
    """Create a mock Tkinter root window for testing."""
    mock = MagicMock()
    mock.winfo_screenwidth.return_value = 1920
    mock.winfo_screenheight.return_value = 1080
    mock.tk = MagicMock()
    # Add winfo_reqwidth and winfo_reqheight methods
    mock.winfo_reqwidth.return_value = 100
    mock.winfo_reqheight.return_value = 100
    return mock

@pytest.fixture
def app(mock_root, tmp_path):
    """Create an instance of MainApplication for testing with all UI components mocked."""
    with patch('src.main.SEWDatabaseManager'), \
         patch('src.main.UIStyleManager', new=MockUIStyleManager), \
         patch('src.main.os.path') as mock_path, \
         patch('src.main.tk.Frame'), \
         patch('src.main.tk.Toplevel'):

        # Mock path operations
        mock_path.join.side_effect = os.path.join
        mock_path.dirname.return_value = str(tmp_path)
        mock_path.exists.return_value = True
        mock_path.abspath.side_effect = lambda x: str(Path(x).absolute())
        
        # Create a mock for the frame that will be returned by create_modern_frame
        mock_frame = MagicMock()
        mock_frame.winfo_reqwidth.return_value = 100
        mock_frame.winfo_reqheight.return_value = 100
        
        # Patch the create_modern_frame method to return our mock frame
        with patch('src.main.UIStyleManager.create_modern_frame', return_value=mock_frame):
            # Create the app instance
            app = main.MainApplication(mock_root, TEST_JSON_DATA, str(tmp_path))
            # Mock the view stack and current view
            app.view_stack = []
            app.current_view = MagicMock()
            
            # Mock window sizing methods
            app.current_view.winfo_reqwidth.return_value = 800
            app.current_view.winfo_reqheight.return_value = 600
            
            # Mock the destroy method
            app.current_view.destroy = MagicMock()
            
            # Mock the UI component creation
            app._create_technology_buttons = MagicMock()
            app._create_task_buttons = MagicMock()
            
            # Yield the app instance for testing
            yield app
            
            # Cleanup after the test
            app.current_view.destroy()

def test_initialization(app):
    """Test that the MainApplication initializes correctly."""
    assert app.root is not None
    assert app.initial_width == TEST_JSON_DATA["MainApplication"]["width"]
    assert app.initial_height == TEST_JSON_DATA["MainApplication"]["height"]
    assert app.json_data == TEST_JSON_DATA

def test_show_main_program(app):
    """Test that the main program view is shown correctly."""
    # Clear any existing view
    app.current_view = None
    
    # Call the method
    app.show_main_program()
    
    # Verify the view was created and methods were called
    assert app.current_view is not None
    app._create_technology_buttons.assert_called_once()

def test_show_technology(app):
    """Test showing a technology view."""
    tech_data = {
        "button_text": "Test Tech",
        "tasks": [{"Test Task": {"task_type": "test"}}],
        "name": "Test Technology"
    }
    
    # Call the method
    app.show_technology(tech_data)
    
    # Verify the view was updated and methods were called
    assert app.current_view is not None
    assert app.variables == tech_data
    app._create_task_buttons.assert_called_once()

def test_show_task_open_url(app):
    """Test showing a task with URL."""
    task_attrs = {"task_type": "open_url", "url_path": "test.pdf"}
    tech_data = {"name": "Test Tech"}
    
    with patch('src.main.PDFViewerWindow') as mock_pdf_viewer:
        # Call the method
        app.show_task(task_attrs, tech_data)
        
        # Verify the PDF viewer was created with the correct arguments
        mock_pdf_viewer.assert_called_once()
        args, kwargs = mock_pdf_viewer.call_args
        assert kwargs.get('file_path') == "test.pdf"

def test_format_single_line_content(app):
    """Test formatting text to a single line."""
    # Test with newlines and extra spaces
    assert app._format_single_line_content("line1\nline2\n   line3   ") == "line1 line2 line3"
    
    # Test with empty input
    assert app._format_single_line_content("") == ""
    
    # Test with None input
    assert app._format_single_line_content(None) == ""

def test_show_previous_view(app):
    """Test navigation to previous view."""
    # Set up view stack
    view1 = MagicMock()
    view2 = MagicMock()
    app.view_stack = [view1, view2]
    
    # Call the method
    app.show_previous_view()
    
    # Verify the view was updated
    assert app.current_view == view2
    assert len(app.view_stack) == 1  # Should have removed the last view from stack
    view1.destroy.assert_called_once()  # The old view should be destroyed

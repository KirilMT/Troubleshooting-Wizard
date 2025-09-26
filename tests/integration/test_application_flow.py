"""
Integration tests for the main application flow.
"""
import tkinter as tk
import pytest
from src.main import MainApplication

class TestApplicationFlow:
    """Test the main application flow and component integration."""
    
    @pytest.fixture
    def app(self):
        """Create and return a test application instance."""
        root = tk.Tk()
        test_data = {
            "MainApplication": {
                "title": "Test App",
                "width": 800,
                "height": 600,
                "Technologies": {
                    "tech1": {
                        "button_text": "Test Tech 1",
                        "tasks": ["Task 1", "Task 2"]
                    }
                }
            },
            "labels": {
                "back_to_technologies": "Back to Technologies"
            }
        }
        app = MainApplication(root, test_data, "/test/path")
        yield app
        root.destroy()
    
    def test_initialization(self, app):
        """Test application initialization."""
        assert app.root.title() == "Test App"
        assert app.current_view is not None
        
    def test_technology_selection(self, app):
        """Test selecting a technology from the main menu."""
        # Simulate clicking on the technology button
        for widget in app.current_view.winfo_children():
            if isinstance(widget, tk.Button) and "Test Tech 1" in widget.cget("text"):
                # Store the current view before clicking
                old_view = app.current_view
                # Simulate button click
                widget.invoke()
                # Verify view changed
                assert app.current_view != old_view
                # Verify back button is present
                self._verify_back_button(app.current_view)
                return
        
        pytest.fail("Test Tech 1 button not found in the UI")
    
    def _verify_back_button(self, parent):
        """Helper to verify back button exists and is functional."""
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button) and "Back to" in child.cget("text"):
                        return True
        pytest.fail("Back button not found in the view")

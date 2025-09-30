"""
Integration tests for the main application flow.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.main import MainApplication


class TestApplicationFlow:
    """Test the main application flow and component integration."""

    @pytest.fixture
    def app(self):
        """Create and return a test application instance."""
        with patch("src.main.tk.Tk") as mock_tk, patch("src.main.SEWDatabaseManager"), patch(
            "src.main.UIStyleManager"
        ) as mock_ui:
            # Mock Tkinter root
            mock_root = MagicMock()
            mock_root.winfo_screenwidth.return_value = 1920
            mock_root.winfo_screenheight.return_value = 1080
            mock_tk.return_value = mock_root

            # Mock UI style manager
            mock_ui_instance = MagicMock()
            mock_frame = MagicMock()
            mock_frame.winfo_reqwidth.return_value = 300
            mock_frame.winfo_reqheight.return_value = 200
            mock_ui_instance.create_modern_frame.return_value = mock_frame
            mock_ui_instance.create_modern_button.return_value = MagicMock()
            mock_ui_instance.set_window_theme.return_value = "#f5f5f5"
            mock_ui.return_value = mock_ui_instance

            test_data = {
                "MainApplication": {
                    "title": "Test App",
                    "width": 800,
                    "height": 600,
                    "Technologies": {
                        "tech1": {"button_text": "Test Tech 1", "tasks": ["Task 1", "Task 2"]}
                    },
                },
                "labels": {"back_to_technologies": "Back to Technologies"},
            }

            with patch.object(MainApplication, "show_main_program"):
                app = MainApplication(mock_root, test_data, "/test/path")

            yield app

    def test_initialization(self, app):
        """Test application initialization."""
        assert app.root is not None
        assert app.json_data["MainApplication"]["title"] == "Test App"

    def test_technology_selection(self, app):
        """Test selecting a technology from the main menu."""
        tech_data = {
            "button_text": "Test Tech 1",
            "tasks": [
                {"Task 1": {"task_type": "open_url", "url_path": "test.pdf"}},
                {"Task 2": {"task_type": "error_codes"}},
            ],
        }

        # Test the show_technology method directly
        app.show_technology(tech_data)

        # Verify the technology data was stored
        assert app.variables == tech_data

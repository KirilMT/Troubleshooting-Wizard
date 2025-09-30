"""
Health Check Module - Automated testing during application startup
"""

import logging
import os
import sqlite3
import tempfile
import tkinter as tk

from .database_manager import SEWDatabaseManager
from .ui_components import UIStyleManager


def run_health_checks() -> bool:
    """Run critical health checks during app startup. Returns True if all pass."""
    checks = [_test_database_functionality, _test_ui_components, _test_logging_system]

    failed_checks = []
    for check in checks:
        try:
            if not check():
                failed_checks.append(check.__name__)
        except Exception as e:
            logging.error(f"Health check {check.__name__} failed with exception: {e}")
            failed_checks.append(check.__name__)

    if failed_checks:
        logging.warning(f"Health checks failed: {failed_checks}")
        return False

    logging.info("All health checks passed")
    return True


def _test_database_functionality() -> bool:
    """Test database operations work correctly."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    try:
        # Create test database
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE sew_error_codes_detailed (
                id INTEGER PRIMARY KEY,
                error_code TEXT,
                suberror_code TEXT,
                error_designation TEXT
            )
        """
        )
        cursor.execute(
            "INSERT INTO sew_error_codes_detailed "
            "(error_code, suberror_code, error_designation) VALUES (?, ?, ?)",
            ("TEST", "01", "Test error"),
        )
        conn.commit()
        conn.close()

        # Test database manager
        db_manager = SEWDatabaseManager(temp_db.name)
        results = db_manager.search_error_codes(error_code="TEST")
        return len(results) == 1 and results[0]["error_code"] == "TEST"

    finally:
        os.unlink(temp_db.name)


def _test_ui_components() -> bool:
    """Test UI components can be created."""
    root = tk.Tk()
    root.withdraw()

    try:
        ui_manager = UIStyleManager()

        # Test basic component creation
        button = ui_manager.create_modern_button(root, "Test", lambda: None)
        frame = ui_manager.create_modern_frame(root)

        return (
            isinstance(button, tk.Button)
            and isinstance(frame, tk.Frame)
            and "technology" in ui_manager.colors
        )
    finally:
        root.destroy()


def _test_logging_system() -> bool:
    """Test logging system is properly configured."""
    logger = logging.getLogger()
    return logger.level == logging.WARNING and len(logger.handlers) >= 1

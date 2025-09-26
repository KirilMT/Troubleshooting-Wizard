"""
Pytest configuration and fixtures for Troubleshooting Wizard tests.
"""
import os
import sys
import tempfile
import pytest
import sqlite3
from pathlib import Path
from typing import Generator, Dict, Any

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Now import using the full package path
from src.database_manager import SEWDatabaseManager
from src.ui_components import UIStyleManager

@pytest.fixture(scope="module")
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    
    # Set up test database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sew_error_codes_detailed (
            id INTEGER PRIMARY KEY,
            error_code TEXT,
            suberror_code TEXT,
            error_designation TEXT,
            description TEXT,
            possible_causes TEXT,
            recommended_actions TEXT
        )
    """)
    
    # Insert test data
    test_data = [
        ("TEST1", "01", "Test Error 1", "Description 1", "Cause 1", "Action 1"),
        ("TEST1", "02", "Test Error 2", "Description 2", "Cause 2", "Action 2"),
        ("TEST2", "01", "Test Error 3", "Description 3", "Cause 3", "Action 3"),
    ]
    
    cursor.executemany(
        """
        INSERT INTO sew_error_codes_detailed 
        (error_code, suberror_code, error_designation, description, possible_causes, recommended_actions)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        test_data
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Clean up
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

@pytest.fixture
def db_manager(temp_db: str) -> SEWDatabaseManager:
    """Create a database manager instance with a test database."""
    return SEWDatabaseManager(temp_db)

@pytest.fixture
def ui_style() -> UIStyleManager:
    """Create a UI style manager instance."""
    return UIStyleManager()

@pytest.fixture
def sample_error_data() -> Dict[str, Any]:
    """Return sample error data for testing."""
    return {
        "error_code": "E01",
        "suberror_code": "01",
        "error_designation": "Test Error",
        "description": "This is a test error description.",
        "possible_causes": "Test cause 1, Test cause 2",
        "recommended_actions": "Test action 1, Test action 2"
    }

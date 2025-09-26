"""
Unit tests for the database_manager module.
"""
import pytest
from typing import List, Dict, Any
from src.database_manager import SEWDatabaseManager

def test_search_error_codes(db_manager: SEWDatabaseManager):
    """Test searching for error codes."""
    # Test exact match
    results = db_manager.search_error_codes(error_code="TEST1", suberror_code="01")
    assert len(results) == 1
    assert results[0]["error_code"] == "TEST1"
    assert results[0]["suberror_code"] == "01"
    assert results[0]["error_designation"] == "Test Error 1"

def test_search_partial_match(db_manager: SEWDatabaseManager):
    """Test partial matching of error codes."""
    # Test partial code match
    results = db_manager.search_error_codes(error_code="TEST1")
    assert len(results) == 2
    assert all(r["error_code"] == "TEST1" for r in results)

def test_search_no_results(db_manager: SEWDatabaseManager):
    """Test search with no matching results."""
    results = db_manager.search_error_codes(error_code="NONEXISTENT")
    assert len(results) == 0

def test_get_all_errors(db_manager: SEWDatabaseManager):
    """Test retrieving all error codes."""
    # Test with specific condition to get all records
    results = db_manager.search_error_codes("TEST")
    assert len(results) >= 3  # Should find all test records

def test_error_handling(db_manager: SEWDatabaseManager):
    """Test error handling for invalid queries."""
    # Test with invalid column name
    with pytest.raises(Exception):
        db_manager.search_error_codes(nonexistent_column="value")

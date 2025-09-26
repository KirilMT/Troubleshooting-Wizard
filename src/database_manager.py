"""
Database Manager Module for Troubleshooting Wizard

This module contains database management classes for handling error code databases
and other data persistence operations.
"""

import os
import sqlite3
import logging


class SEWDatabaseManager:
    """Manages SEW error code database operations."""

    def __init__(self, db_path):
        self.db_path = db_path

    def search_error_codes(self, error_code=None, suberror_code=None, error_designation=None):
        """Search for error codes in the SEW database based on provided criteria."""
        if not os.path.exists(self.db_path):
            logging.critical(f"Database file not found at {self.db_path}")
            return []
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            conditions, params = [], []
            
            if error_code and error_code.strip():
                conditions.append("error_code LIKE ?")
                params.append(f"%{error_code.strip()}%")
            
            if suberror_code and suberror_code.strip():
                conditions.append("suberror_code LIKE ?")
                params.append(f"%{suberror_code.strip()}%")
            
            if error_designation and error_designation.strip():
                conditions.append("error_designation LIKE ?")
                params.append(f"%{error_designation.strip()}%")
            
            if not conditions:
                return []
            
            query = "SELECT * FROM sew_error_codes_detailed WHERE " + " AND ".join(conditions)
            cursor.execute(query, params)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
            
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()

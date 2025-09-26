"""Database Manager Module for Troubleshooting Wizard.

This module provides database management functionality for the Troubleshooting Wizard application,
including searching and retrieving error code information from SQLite databases. It handles all
interactions with the error code database, including query optimization and result caching.
"""

import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from .cache_manager import cached
from .search_optimizer import SearchOptimizer


class SEWDatabaseManager:
    """Manages SEW error code database operations.

    This class provides methods to search and retrieve error code information from the SEW
    error code database. It includes caching mechanisms and query optimization for better
    performance.

    Attributes:
        db_path (str): Path to the SQLite database file.
        search_optimizer (SearchOptimizer): Instance of SearchOptimizer for query optimization.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize the SEWDatabaseManager with a path to the database file.

        Args:
            db_path: Path to the SQLite database file containing error code information.
        """
        self.db_path = db_path
        self.search_optimizer = SearchOptimizer()

    @cached(ttl=1800)  # Cache for 30 minutes
    def search_error_codes(
        self,
        error_code: Optional[str] = None,
        suberror_code: Optional[str] = None,
        error_designation: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for error codes in the SEW database based on provided criteria.

        Performs a case-insensitive search across error codes, sub-error codes, and error
        designations. Results are cached for 30 minutes to improve performance.

        Args:
            error_code: Full or partial error code to search for (e.g., 'F001').
            suberror_code: Full or partial sub-error code to search for (e.g., '1').
            error_designation: Text to search within error descriptions.

        Returns:
            A list of dictionaries, where each dictionary represents a matching error code
            with its associated information. Returns an empty list if no matches are found
            or if an error occurs.

        Example:
            >>> db = SEWDatabaseManager('error_codes.db')
            >>> results = db.search_error_codes(error_code='F001')
            >>> print(results)
            [{'error_code': 'F001', 'suberror_code': '1', 'error_designation': 'Motor overload', ...}]

        Note:
            At least one search parameter must be provided. If no parameters are provided,
            an empty list will be returned.
        """
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

            # Optimize query for better performance
            optimized_where, optimized_params = self.search_optimizer.optimize_database_query(
                conditions, params
            )
            query = f"SELECT * FROM sew_error_codes_detailed WHERE {optimized_where}"
            cursor.execute(query, optimized_params)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            return [dict(zip(columns, row)) for row in results]

        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()

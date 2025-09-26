"""
Search Optimization Module for Troubleshooting Wizard

Provides optimized search algorithms for better performance with large datasets.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache


class SearchOptimizer:
    """Optimized search algorithms for database and text operations."""
    
    def __init__(self):
        self._compiled_patterns = {}
    
    @lru_cache(maxsize=128)
    def _get_compiled_pattern(self, pattern: str, flags: int = re.IGNORECASE) -> re.Pattern:
        """Cache compiled regex patterns for better performance."""
        return re.compile(pattern, flags)
    
    def fuzzy_search(self, query: str, text: str, threshold: float = 0.6) -> bool:
        """Fast fuzzy string matching using optimized algorithm."""
        if not query or not text:
            return False
        
        query = query.lower().strip()
        text = text.lower().strip()
        
        # Exact match (fastest)
        if query in text:
            return True
        
        # Quick length check
        if len(query) > len(text) * 2:
            return False
        
        # Simple similarity check
        matches = sum(1 for char in query if char in text)
        similarity = matches / len(query)
        
        return similarity >= threshold
    
    def optimize_database_query(self, conditions: List[str], params: List[str]) -> Tuple[str, List[str]]:
        """Optimize database query by reordering conditions for better performance."""
        if not conditions:
            return "", []
        
        # Reorder conditions: exact matches first, then LIKE patterns
        exact_conditions = []
        like_conditions = []
        exact_params = []
        like_params = []
        
        for i, condition in enumerate(conditions):
            if "LIKE" in condition:
                like_conditions.append(condition)
                like_params.append(params[i])
            else:
                exact_conditions.append(condition)
                exact_params.append(params[i])
        
        # Combine: exact matches first for better index usage
        optimized_conditions = exact_conditions + like_conditions
        optimized_params = exact_params + like_params
        
        return " AND ".join(optimized_conditions), optimized_params
    
    def batch_search(self, queries: List[str], dataset: List[Dict[str, Any]], 
                    search_fields: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple searches efficiently in a single pass."""
        results = {query: [] for query in queries}
        
        for item in dataset:
            for query in queries:
                for field in search_fields:
                    field_value = str(item.get(field, ""))
                    if self.fuzzy_search(query, field_value):
                        results[query].append(item)
                        break  # Found match, no need to check other fields
        
        return results
"""
Cache Manager Module for Troubleshooting Wizard

Provides caching functionality for frequently accessed data like search results
and PDF metadata to improve application performance.
"""

import os
import json
import time
import logging
from typing import Any, Optional
from functools import wraps


class CacheManager:
    """Simple file-based cache with TTL (time-to-live) support."""

    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600) -> None:
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key."""
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """Get cached data by key. Returns None if not found or expired."""
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache has expired
            if time.time() > cache_data.get("expires_at", 0):
                os.remove(cache_path)
                return None

            return cache_data.get("data")

        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Failed to read cache for key '{key}': {e}")
            return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache data with optional TTL override."""
        cache_path = self._get_cache_path(key)
        ttl = ttl or self.default_ttl

        cache_data = {"data": data, "created_at": time.time(), "expires_at": time.time() + ttl}

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
        except OSError as e:
            logging.warning(f"Failed to write cache for key '{key}': {e}")

    def clear(self) -> None:
        """Clear all cached data."""
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, filename))


# Global cache instance - will be initialized properly in run.py
_cache = None


def _get_global_cache():
    """Get or create the global cache instance with proper path."""
    global _cache
    if _cache is None:
        # Default to data/cache relative to project root
        import sys
        if hasattr(sys, '_MEIPASS'):  # Running as .exe
            cache_dir = os.path.join(os.path.dirname(sys.executable), "data", "cache")
        else:  # Running as script
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(script_dir, "data", "cache")
        _cache = CacheManager(cache_dir)
    return _cache


def cached(ttl: int = 3600):
    """Decorator to cache function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache first
            cache = _get_global_cache()
            result = cache.get(cache_key)
            if result is not None:
                logging.debug(f"Cache hit for {func.__name__}")
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logging.debug(f"Cached result for {func.__name__}")
            return result

        return wrapper

    return decorator

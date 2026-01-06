"""
Simple In-Memory Cache with 24-hour TTL for Insights

Prevents excessive API calls and improves performance.
Cache invalidates on new expenses or after 24 hours.
"""

from datetime import datetime, timedelta
from typing import Optional, Any


class InsightCache:
    """
    Simple in-memory cache with 24-hour TTL.
    
    Usage:
        cache = InsightCache()
        cache.set("user_123_spending", data)
        cached_data = cache.get("user_123_spending")
        cache.invalidate(user_id=123)  # Clear all user data
    """
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if valid, None if expired or not found
        """
        if key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        
        # Check if expired (24 hours)
        if datetime.utcnow() - timestamp > timedelta(hours=24):
            del self.cache[key]
            return None
        
        return data
    
    def set(self, key: str, data: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache[key] = (data, datetime.utcnow())
    
    def invalidate(self, user_id: int) -> None:
        """
        Clear all cache entries for a specific user.
        Called when user adds new expense/income.
        
        Args:
            user_id: User ID to invalidate
        """
        prefix = f"insights_{user_id}"
        keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del self.cache[k]
    
    def clear_all(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
    
    def get_cache_info(self) -> dict:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_count = 0
        
        for key, (_, timestamp) in self.cache.items():
            if datetime.utcnow() - timestamp > timedelta(hours=24):
                expired_count += 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "active_entries": total_entries - expired_count
        }


# Global cache instance
insight_cache = InsightCache()

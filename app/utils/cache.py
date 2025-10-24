"""Cache utilities supporting FileSystem and Redis backends."""
import os
from cachelib import FileSystemCache
# from cachelib import RedisCache
from config import Config


class CacheManager:
    """Manages caching with support for FileSystem and Redis."""
    
    def __init__(self):
        """Initialize cache based on configuration."""
        self.cache_type = Config.CACHE_TYPE
        
        if self.cache_type == 'filesystem':
            # Ensure cache directory exists
            os.makedirs(Config.CACHE_DIR, exist_ok=True)
            self.cache = FileSystemCache(
                cache_dir=Config.CACHE_DIR,
                threshold=500,
                default_timeout=Config.CACHE_DEFAULT_TIMEOUT
            )
        # elif self.cache_type == 'redis':
        #     # Redis cache (commented out for now)
        #     self.cache = RedisCache(
        #         host=Config.REDIS_HOST,
        #         port=Config.REDIS_PORT,
        #         db=Config.REDIS_DB,
        #         default_timeout=Config.CACHE_DEFAULT_TIMEOUT
        #     )
        else:
            raise ValueError(f"Unsupported cache type: {self.cache_type}")
    
    def get(self, key):
        """Get value from cache."""
        return self.cache.get(key)
    
    def set(self, key, value, timeout=None):
        """Set value in cache."""
        return self.cache.set(key, value, timeout=timeout)
    
    def delete(self, key):
        """Delete value from cache."""
        return self.cache.delete(key)
    
    def clear(self):
        """Clear all cache entries."""
        return self.cache.clear()
    
    def has(self, key):
        """Check if key exists in cache."""
        return self.cache.has(key)
    
    @staticmethod
    def make_cache_key(event_name, subgroup, data_type='raw'):
        """
        Generate a cache key for event data.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
            data_type: Type of data ('raw', 'accounts', 'aggregated')
        
        Returns:
            Cache key string (case-insensitive)
        """
        # Convert to lowercase for case-insensitive matching
        return f"{data_type}:{event_name.lower()}:{subgroup.lower()}"
    
    def invalidate_event_cache(self, event_name, subgroup):
        """
        Invalidate all cache entries for a specific event/subgroup.
        
        Args:
            event_name: Name of the event
            subgroup: Subgroup name
        """
        # Invalidate different data types
        for data_type in ['raw', 'accounts', 'aggregated']:
            key = self.make_cache_key(event_name, subgroup, data_type)
            self.delete(key)


# Global cache instance
cache_manager = CacheManager()

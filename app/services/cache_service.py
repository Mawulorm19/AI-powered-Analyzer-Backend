"""
Price Analyzer API - Caching Service
Redis-based caching for products, reviews, and analysis results.
"""
import json
import redis
from typing import Optional, Any
from ..config import get_settings


class CacheService:
    """Redis-based caching service for API responses."""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    @property
    def redis(self) -> Optional[redis.Redis]:
        """Get Redis connection with lazy initialization."""
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    password=self.settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self._redis.ping()
                self._connected = True
            except redis.ConnectionError as e:
                print(f"Redis connection failed: {e}")
                self._connected = False
                return None
        return self._redis
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except redis.ConnectionError:
            self._connected = False
            return False
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a cache key with prefix."""
        return f"price_analyzer:{prefix}:{identifier}"
    
    def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """
        Get a cached value.
        
        Args:
            prefix: Cache key prefix (e.g., 'search', 'analysis')
            identifier: Unique identifier
            
        Returns:
            Cached value or None
        """
        if not self.is_connected:
            return None
        
        try:
            key = self._make_key(prefix, identifier)
            value = self.redis.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except (redis.RedisError, json.JSONDecodeError) as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        prefix: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a cached value.
        
        Args:
            prefix: Cache key prefix
            identifier: Unique identifier
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (defaults to settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            key = self._make_key(prefix, identifier)
            ttl = ttl or self.settings.CACHE_TTL
            
            self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
            
        except (redis.RedisError, TypeError) as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, identifier: str) -> bool:
        """
        Delete a cached value.
        
        Args:
            prefix: Cache key prefix
            identifier: Unique identifier
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            key = self._make_key(prefix, identifier)
            return self.redis.delete(key) > 0
            
        except redis.RedisError as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """
        Clear all cache entries with a given prefix.
        
        Args:
            prefix: Cache key prefix to clear
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected:
            return 0
        
        try:
            pattern = self._make_key(prefix, "*")
            keys = list(self.redis.scan_iter(match=pattern))
            
            if keys:
                return self.redis.delete(*keys)
            return 0
            
        except redis.RedisError as e:
            print(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_connected:
            return {"connected": False}
        
        try:
            info = self.redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
        except redis.RedisError:
            return {"connected": False}


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

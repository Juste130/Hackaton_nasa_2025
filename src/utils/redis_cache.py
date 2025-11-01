"""
Redis caching layer for Neo4j queries
Reduces redundant database calls and improves response times

Environment variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- CACHE_TTL: Cache time-to-live in seconds (default: 3600 = 1 hour)
"""
import os
import json
import logging
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client for Neo4j query results"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = int(os.environ.get("CACHE_TTL", "36000"))  # 10 hours default
        self.enabled = os.environ.get("REDIS_ENABLED", "true").lower() == "true"
        
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.client.ping()
                logger.info(f" Redis cache connected: {self.redis_url}")
            except RedisError as e:
                logger.warning(f" Redis connection failed: {e}. Cache disabled.")
                self.client = None
                self.enabled = False
        else:
            logger.info("ℹ Redis cache disabled via REDIS_ENABLED=false")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments
        
        Args:
            prefix: Key prefix (e.g., 'neo4j:full_graph')
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a stable representation of the arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistency
        }
        
        # Hash the arguments for a compact key
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            cached = self.client.get(key)
            if cached:
                logger.debug(f" Cache HIT: {key}")
                return json.loads(cached)
            else:
                logger.debug(f" Cache MISS: {key}")
                return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f" Cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            logger.debug(f" Cache SET: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f" Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            result = self.client.delete(key)
            logger.debug(f" Cache DELETE: {key}")
            return bool(result)
        except RedisError as e:
            logger.warning(f" Cache delete error for {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'neo4j:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f" Cache cleared {deleted} keys matching '{pattern}'")
                return deleted
            return 0
        except RedisError as e:
            logger.warning(f" Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {
                "enabled": False,
                "connected": False
            }
        
        try:
            info = self.client.info('stats')
            return {
                "enabled": True,
                "connected": True,
                "total_commands": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": (
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
                ) * 100
            }
        except RedisError as e:
            logger.warning(f" Cache stats error: {e}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e)
            }


# Global cache instance
_cache = None


def get_cache() -> RedisCache:
    """Get or create global cache instance"""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


def cache_neo4j_query(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache Neo4j query results
    
    Usage:
        @cache_neo4j_query('neo4j:full_graph', ttl=1800)
        async def get_full_graph(limit: int = 100):
            # ... Neo4j query ...
            return result
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds (optional)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function arguments
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function arguments
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


test=RedisCache()
print(test.get_stats())
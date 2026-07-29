"""
Redis Cache Service
"""
import os
import json
import hashlib
from datetime import timedelta
from typing import Optional, Any
import redis
from redis.connection import ConnectionPool


class CacheService:
    """Redis-based caching service for analysis results and session management."""
    
    # Cache key prefixes
    KEY_ANALYSIS = 'analysis'
    KEY_SESSION = 'session'
    KEY_RATE_LIMIT = 'ratelimit'
    KEY_MODEL_WARMUP = 'model:warmup'
    
    # Default TTL values (in seconds)
    DEFAULT_ANALYSIS_TTL = 3600  # 1 hour
    DEFAULT_SESSION_TTL = 3600   # 1 hour
    DEFAULT_RATE_LIMIT_WINDOW = 60  # 1 minute
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection with connection pooling."""
        self.redis_url = redis_url or os.getenv(
            'REDIS_URL', 
            'redis://localhost:6379/0'
        )
        
        # Configure connection pool for better performance
        self._pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,  # Max connections in pool
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        self._client = redis.Redis(connection_pool=self._pool)
        
    @property
    def client(self) -> redis.Redis:
        """Get the Redis client."""
        return self._client
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of content for cache key."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_analysis(self, content_hash: str) -> Optional[dict]:
        """Get cached analysis result by content hash."""
        key = f"{self.KEY_ANALYSIS}:{content_hash}"
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except redis.RedisError as e:
            # Log error but don't fail - cache is optional
            print(f"Redis get error: {e}")
        return None
    
    def set_analysis(
        self, 
        content_hash: str, 
        result: dict, 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache analysis result with optional TTL."""
        key = f"{self.KEY_ANALYSIS}:{content_hash}"
        ttl = ttl or self.DEFAULT_ANALYSIS_TTL
        try:
            self._client.setex(key, ttl, json.dumps(result))
            return True
        except redis.RedisError as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete_analysis(self, content_hash: str) -> bool:
        """Delete cached analysis result."""
        key = f"{self.KEY_ANALYSIS}:{content_hash}"
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            print(f"Redis delete error: {e}")
            return False
    
    def get_session(self, user_id: str) -> Optional[dict]:
        """Get session data for user."""
        key = f"{self.KEY_SESSION}:{user_id}"
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except redis.RedisError as e:
            print(f"Redis get error: {e}")
        return None
    
    def set_session(self, user_id: str, session_data: dict, ttl: Optional[int] = None) -> bool:
        """Set session data for user."""
        key = f"{self.KEY_SESSION}:{user_id}"
        ttl = ttl or self.DEFAULT_SESSION_TTL
        try:
            self._client.setex(key, ttl, json.dumps(session_data))
            return True
        except redis.RedisError as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete_session(self, user_id: str) -> bool:
        """Delete user session."""
        key = f"{self.KEY_SESSION}:{user_id}"
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            print(f"Redis delete error: {e}")
            return False
    
    def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        
        Returns:
            tuple: (is_allowed, remaining_requests)
        """
        key = f"{self.KEY_RATE_LIMIT}:{identifier}"
        try:
            current = self._client.get(key)
            if current is None:
                self._client.setex(key, window, 1)
                return True, limit - 1
            
            count = int(current)
            if count >= limit:
                return False, 0
            
            self._client.incr(key)
            return True, limit - count - 1
        except redis.RedisError as e:
            # On Redis error, allow the request (fail open)
            print(f"Redis rate limit error: {e}")
            return True, limit
    
    def get_rate_limit_remaining(self, identifier: str, limit: int) -> int:
        """Get remaining rate limit for identifier."""
        key = f"{self.KEY_RATE_LIMIT}:{identifier}"
        try:
            current = self._client.get(key)
            if current is None:
                return limit
            return max(0, limit - int(current))
        except redis.RedisError:
            return limit
    
    def set_model_warmup_status(self, is_warm: bool) -> bool:
        """Set ML model warmup status."""
        key = self.KEY_MODEL_WARMUP
        try:
            self._client.set(key, '1' if is_warm else '0', ex=300)
            return True
        except redis.RedisError as e:
            print(f"Redis set error: {e}")
            return False
    
    def get_model_warmup_status(self) -> bool:
        """Get ML model warmup status."""
        key = self.KEY_MODEL_WARMUP
        try:
            status = self._client.get(key)
            return status == '1'
        except redis.RedisError:
            return False
    
    def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self._client.ping()
        except redis.RedisError:
            return False
    
    def flush_all(self) -> bool:
        """Flush all keys from current database (use with caution!)."""
        try:
            self._client.flushdb()
            return True
        except redis.RedisError as e:
            print(f"Redis flush error: {e}")
            return False
    
    def close(self):
        """Close Redis connection pool."""
        self._client.close()
        self._pool.disconnect()


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def init_cache_service(redis_url: str) -> CacheService:
    """Initialize cache service with custom URL."""
    global _cache_service
    _cache_service = CacheService(redis_url)
    return _cache_service
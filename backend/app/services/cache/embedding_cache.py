"""
Redis-based caching layer for query embeddings.

This service caches user query embeddings to avoid regenerating
embeddings for similar or identical queries, reducing response time.
"""

import json
import hashlib
import logging
from typing import List, Optional
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Redis-based cache for query embeddings.
    
    Features:
    - Automatic hash-based key generation for queries
    - Configurable TTL (default 24 hours)
    - Async operations for performance
    - Automatic serialization/deserialization of embeddings
    """
    
    def __init__(
        self,
        redis_url: str = None,
        default_ttl: int = 86400  # 24 hours in seconds
    ):
        """
        Initialize embedding cache.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
            default_ttl: Default time-to-live for cached embeddings (seconds)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """
        Get or create Redis client.
        
        Returns:
            Async Redis client
        """
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle binary data ourselves
            )
        return self._client
    
    def _generate_cache_key(self, query: str, repo_id: str) -> str:
        """
        Generate a cache key for a query.
        
        Uses SHA256 hash of (query + repo_id) to create a unique key.
        
        Args:
            query: User's query text
            repo_id: Repository UUID
            
        Returns:
            Cache key string
        """
        key_string = f"{query}:{repo_id}"
        hash_obj = hashlib.sha256(key_string.encode())
        hash_hex = hash_obj.hexdigest()
        return f"embedding:{hash_hex}"
    
    async def get(self, query: str, repo_id: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding for a query.
        
        Args:
            query: User's query text
            repo_id: Repository UUID
            
        Returns:
            Cached embedding vector or None if not found
        """
        try:
            cache_key = self._generate_cache_key(query, repo_id)
            client = await self._get_client()
            
            cached_data = await client.get(cache_key)
            
            if cached_data:
                embedding = json.loads(cached_data.decode('utf-8'))
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return embedding
            else:
                logger.debug(f"Cache miss for query: {query[:50]}...")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get embedding from cache: {e}")
            return None
    
    async def set(
        self,
        query: str,
        repo_id: str,
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache an embedding for a query.
        
        Args:
            query: User's query text
            repo_id: Repository UUID
            embedding: Embedding vector to cache
            ttl: Time-to-live in seconds (defaults to default_ttl)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(query, repo_id)
            client = await self._get_client()
            
            ttl = ttl or self.default_ttl
            
            # Serialize embedding to JSON
            embedding_json = json.dumps(embedding)
            
            # Store in Redis with TTL
            await client.setex(cache_key, ttl, embedding_json.encode('utf-8'))
            
            logger.debug(f"Cached embedding for query: {query[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")
            return False
    
    async def delete(self, query: str, repo_id: str) -> bool:
        """
        Delete a cached embedding.
        
        Args:
            query: User's query text
            repo_id: Repository UUID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(query, repo_id)
            client = await self._get_client()
            
            await client.delete(cache_key)
            logger.debug(f"Deleted cached embedding for query: {query[:50]}...")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to delete cached embedding: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """
        Clear all cached embeddings.
        
        Warning: This will clear ALL embeddings from the cache,
        not just for a specific query or repository.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            
            # Scan for all keys with prefix "embedding:"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await client.scan(
                    cursor,
                    match="embedding:*",
                    count=100
                )
                
                if keys:
                    await client.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} cached embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear embedding cache: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            client = await self._get_client()
            
            # Count keys with prefix "embedding:"
            cursor = 0
            count = 0
            
            while True:
                cursor, keys = await client.scan(
                    cursor,
                    match="embedding:*",
                    count=100
                )
                count += len(keys)
                
                if cursor == 0:
                    break
            
            # Get Redis memory usage
            info = await client.info('memory')
            used_memory = info.get('used_memory_human', 'unknown')
            
            return {
                "cached_embeddings": count,
                "redis_memory_usage": used_memory
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "cached_embeddings": 0,
                "redis_memory_usage": "unknown",
                "error": str(e)
            }
    
    async def close(self):
        """
        Close the Redis connection.
        
        Call this when shutting down the application.
        """
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Embedding cache connection closed")


# Singleton instance
_embedding_cache = None


def get_embedding_cache() -> EmbeddingCache:
    """
    Get the singleton embedding cache instance.
    
    The cache is initialized once and reused across all requests.
    
    Returns:
        EmbeddingCache instance
    """
    global _embedding_cache
    
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    
    return _embedding_cache
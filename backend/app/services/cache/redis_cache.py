"""
Redis caching service for embeddings and query results.

Provides two levels of caching:
1. Embedding cache - Cache query embeddings to avoid re-computing
2. Query result cache - Cache complete query responses
"""

import redis
import hashlib
import json
import logging
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Redis caching service for performance optimization.
    
    Caches:
    - Query embeddings (24h TTL)
    - Full query responses (1h TTL)
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("✓ Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    # --- Embedding Cache ---
    
    def _make_embedding_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"emb:{text_hash}"
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        if not self.is_available():
            return None
        
        try:
            key = self._make_embedding_key(text)
            cached = self.client.get(key)
            if cached:
                logger.debug(f"✓ Embedding cache hit for key: {key}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")
            return None
    
    def set_embedding(self, text: str, embedding: List[float], ttl: int = 86400):
        """
        Cache embedding for text.
        
        Args:
            text: Query text
            embedding: Embedding vector
            ttl: Time to live in seconds (default: 24h)
        """
        if not self.is_available():
            return
        
        try:
            key = self._make_embedding_key(text)
            self.client.setex(
                key,
                ttl,
                json.dumps(embedding)
            )
            logger.debug(f"✓ Cached embedding for key: {key}")
        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
    
    # --- Query Result Cache ---
    
    def _make_query_key(self, query: str, repo_id: str, commit_sha: str) -> str:
        """Generate cache key for query result."""
        combined = f"{query}|{repo_id}|{commit_sha}"
        query_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return f"query:{query_hash}"
    
    def get_query_result(
        self, 
        query: str, 
        repo_id: str, 
        commit_sha: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached query result."""
        if not self.is_available():
            return None
        
        try:
            key = self._make_query_key(query, repo_id, commit_sha)
            cached = self.client.get(key)
            if cached:
                logger.info(f"🎯 Query result cache HIT for: {query[:50]}...")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Error getting cached query result: {e}")
            return None
    
    def set_query_result(
        self,
        query: str,
        repo_id: str,
        commit_sha: str,
        result: Dict[str, Any],
        ttl: int = 3600
    ):
        """
        Cache complete query result.
        
        Args:
            query: User's query
            repo_id: Repository ID
            commit_sha: Commit SHA
            result: Complete query result to cache
            ttl: Time to live in seconds (default: 1h)
        """
        if not self.is_available():
            return
        
        try:
            key = self._make_query_key(query, repo_id, commit_sha)
            self.client.setex(
                key,
                ttl,
                json.dumps(result, default=str)  # default=str handles UUIDs, etc.
            )
            logger.info(f"✓ Cached query result for: {query[:50]}...")
        except Exception as e:
            logger.error(f"Error caching query result: {e}")
    
    # --- Utility Methods ---
    
    def clear_cache(self, pattern: str = "*"):
        """Clear cache entries matching pattern."""
        if not self.is_available():
            return
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"✓ Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.client.info("stats")
            return {
                "status": "available",
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0) + 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Singleton instance
_cache_service = None


def get_cache_service() -> RedisCacheService:
    """Get singleton cache service instance."""
    global _cache_service
    
    if _cache_service is None:
        _cache_service = RedisCacheService()
    
    return _cache_service

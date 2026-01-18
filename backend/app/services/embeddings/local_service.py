"""
Local embedding service using BAAI/bge-small-en-v1.5.

Provides fast, free, and private embeddings without API calls.
"""

from typing import List, Union
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class LocalEmbeddingService:
    """
    Local embedding service using BGE model.
    
    Uses BAAI/bge-small-en-v1.5 for generating embeddings:
    - Size: ~33MB
    - Dimensions: 384
    - Speed: 1000+ chunks/second on CPU
    - No API costs or rate limits
    """
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize the local embedding model.
        
        Args:
            model_name: HuggingFace model name
        """
        logger.info(f"Loading local embedding model: {model_name}")
        
        # Load model (will download on first run, then cache locally)
        self.model = SentenceTransformer(model_name)
        
        # Get embedding dimension from model
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
    
    def embed(self, texts: Union[str, List[str]], batch_size: int = 32) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        OPTIMIZED: Uses Redis cache for single queries to avoid re-computation.
        
        Args:
            texts: Single text string or list of texts
            batch_size: Number of texts to process at once
            
        Returns:
            Single embedding or list of embeddings
        """
        is_single = isinstance(texts, str)
        
        if is_single:
            # OPTIMIZATION: Check cache for single queries
            try:
                from app.services.cache.redis_cache import get_cache_service
                cache = get_cache_service()
                
                if cache.is_available():
                    cached_embedding = cache.get_embedding(texts)
                    if cached_embedding:
                        logger.debug("✓ Embedding cache hit!")
                        return cached_embedding
            except Exception as e:
                logger.debug(f"Cache check failed (non-critical): {e}")
            
            texts = [texts]
        
        # Generate embeddings in batches for efficiency
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convert to list format
        embeddings_list = embeddings.tolist()
        
        if is_single:
            result = embeddings_list[0]
            
            # OPTIMIZATION: Cache the result for future requests
            try:
                from app.services.cache.redis_cache import get_cache_service
                cache = get_cache_service()
                
                if cache.is_available():
                    cache.set_embedding(texts[0], result, ttl=86400)  # 24h TTL
            except Exception as e:
                logger.debug(f"Cache set failed (non-critical): {e}")
            
            return result
        
        return embeddings_list
    
    def embed_batch(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Optimized for processing many texts at once.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,  # Show progress for large batches
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.embedding_dim


# Singleton instance
_embedding_service = None


def get_embedding_service() -> LocalEmbeddingService:
    """
    Get the singleton embedding service instance.
    
    The model is loaded once and reused across all embedding requests.
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService()
    
    return _embedding_service

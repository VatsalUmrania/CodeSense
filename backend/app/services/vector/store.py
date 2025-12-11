from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import uuid
from app.core.logger import get_logger

logger = get_logger("vector_store")

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
        self.collection_name = "codesense_codebase"
        self.cache_collection = "codesense_cache"
        self._ensure_collections()

    def _ensure_collections(self):
        # Main Codebase Collection
        collections = self.client.get_collections().collections
        existing_names = [c.name for c in collections]
        
        if self.collection_name not in existing_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )
            logger.info("created_collection", name=self.collection_name)

        # Semantic Cache Collection
        if self.cache_collection not in existing_names:
            self.client.create_collection(
                collection_name=self.cache_collection,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )
            logger.info("created_collection", name=self.cache_collection)

    def upsert_chunks(self, chunks: list):
        if not chunks: return
        points = [
            models.PointStruct(
                id=chunk["id"],
                vector=chunk["vector"],
                payload=chunk["payload"]
            )
            for chunk in chunks
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info("upserted_vectors", count=len(points))

    def delete_repo(self, repo_id: str):
        """Deletes all vectors associated with a specific repository ID."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="repo_id", match=models.MatchValue(value=repo_id))]
                )
            )
        )
        logger.info("deleted_repo_vectors", repo_id=repo_id)

    # --- Cache Methods ---

    def search_cache(self, query_vector: list, threshold: float = 0.95):
        """Searches the cache for a semantically similar question."""
        results = self.client.search(
            collection_name=self.cache_collection,
            query_vector=query_vector,
            limit=1,
            score_threshold=threshold
        )
        if results:
            logger.info("semantic_cache_hit", score=results[0].score)
            return results[0].payload.get("answer")
        return None

    def save_cache(self, query_vector: list, answer: str):
        """Saves a question/answer pair to the cache."""
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=query_vector,
            payload={"answer": answer}
        )
        self.client.upsert(collection_name=self.cache_collection, points=[point])
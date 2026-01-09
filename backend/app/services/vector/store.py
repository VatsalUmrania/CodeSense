from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        # Synchronous client for bulk ingestion tasks
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "codesense_codebase"
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            existing_names = [c.name for c in collections]
            
            if self.collection_name not in existing_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=768,  # Matches Gemini text-embedding-004 size
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")

    def upsert_chunks(self, points: list[dict]):
        """
        Upserts a list of vectors (points) into Qdrant.
        Each point dict should have: id, vector, payload
        """
        if not points:
            return

        try:
            # Convert dicts to Qdrant PointStructs
            point_structs = [
                models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"]
                )
                for p in points
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=point_structs
            )
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise e
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
        self.collection_name = "codesense_codebase"
        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE
                )
            )
            print(f"Created collection: {self.collection_name}")

    def upsert_chunks(self, chunks: list):
        points = [
            models.PointStruct(
                id=chunk["id"],
                vector=chunk["vector"],
                payload=chunk["payload"]
            )
            for chunk in chunks
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Uploaded {len(points)} vectors to Qdrant.")

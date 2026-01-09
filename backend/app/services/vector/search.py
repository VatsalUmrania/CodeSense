from qdrant_client import AsyncQdrantClient, models
from app.core.config import settings
from app.services.llm.gemini import GeminiService
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    page_content: str
    metadata: Dict[str, Any]
    score: float

class VectorSearchService:
    def __init__(self, llm_service: GeminiService):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "codesense_codebase"
        self.llm = llm_service

    async def search(self, repo_id: str, query: str, commit_sha: str, limit: int = 10) -> List[SearchResult]:
        # 1. Embed the query
        query_vector = await self.llm.embed_query(query)
        if not query_vector:
            logger.error("Failed to generate embedding for query.")
            return []

        # 2. Log Debug Info (Check this in your docker logs!)
        logger.info(f"Searching Qdrant - Repo: {repo_id}, Commit: {commit_sha}, Query: '{query}'")

        # 3. Perform Search
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="repo_id", match=models.MatchValue(value=str(repo_id))),
                        models.FieldCondition(key="commit_sha", match=models.MatchValue(value=commit_sha)),
                    ]
                ),
                limit=limit,
                score_threshold=0.35 # FIX: Lowered from 0.60 to 0.35 to catch more relevant results
            )
            
            logger.info(f"Qdrant returned {len(results)} hits.")

            return [
                SearchResult(
                    page_content=hit.payload.get("content", ""),
                    metadata=hit.payload,
                    score=hit.score
                )
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Qdrant Search Error: {e}")
            return []
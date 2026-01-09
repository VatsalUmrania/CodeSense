from langchain.schema import Document
from app.services.vector.search import VectorSearchService
from app.services.llm.gemini import GeminiService
from app.agent.state import AgentState
from app.schemas.chat import ChunkCitation

class AgentNodes:
    def __init__(self, vector_service: VectorSearchService, llm_service: GeminiService):
        self.vector = vector_service
        self.llm = llm_service

    async def retrieve(self, state: AgentState) -> AgentState:
        """
        Fetches code chunks. Enforces commit_sha filter.
        """
        print(f"---RETRIEVING--- Commit: {state['commit_sha']}")
        
        # We fetch a bit more than we need (e.g. 10), then let the grade_documents 
        # step filter down to the absolute best ones (e.g. top 5).
        results = await self.vector.search(
            repo_id=state["repo_id"],
            query=state["question"],
            commit_sha=state["commit_sha"],
            limit=10 
        )
        
        # Convert to Citations
        citations = [
            ChunkCitation(
                file_path=r.metadata.get("file_path", "unknown"),
                symbol_name=r.metadata.get("symbol_name", "unknown"),
                start_line=r.metadata.get("start_line", 0),
                content_preview=r.page_content,
                score=r.score
            ) for r in results
        ]
        
        return {**state, "documents": citations}

    async def grade_documents(self, state: AgentState) -> AgentState:
        """
        OPTIMIZED: Filters documents based on Vector Similarity Score.
        Replaces expensive LLM calls with efficient local filtering.
        """
        print("---CHECKING RELEVANCE (Local Filter)---")
        
        # Sort by score descending (highest relevance first)
        # Note: Qdrant usually returns sorted, but we ensure it here.
        sorted_docs = sorted(
            state["documents"], 
            key=lambda x: x.score if x.score is not None else 0, 
            reverse=True
        )

        # Strategy: Keep Top 5 documents
        # This reduces context window usage and ensures we only send high-quality chunks.
        # You can also add a score threshold (e.g., if doc.score > 0.4)
        filtered_docs = sorted_docs[:5]
        
        print(f"---FILTERED: Kept {len(filtered_docs)}/{len(state['documents'])} docs based on vector score---")
                
        return {**state, "documents": filtered_docs}

    async def generate(self, state: AgentState) -> AgentState:
        """
        Generates the final answer using valid docs.
        """
        print("---GENERATING---")
        
        if not state["documents"]:
            return {**state, "generation": "I could not find relevant code in this commit to answer your question."}
            
        # This is now the ONLY Gemini call in the pipeline per message.
        answer = await self.llm.generate_rag_response(
            question=state["question"],
            context=state["documents"]
        )
        
        return {**state, "generation": answer}
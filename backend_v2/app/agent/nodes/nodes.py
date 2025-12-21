from langchain.schema import Document
from app.services.vector.search import VectorSearchService
from app.services.llm.gemini import GeminiService # Assumed wrapper
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
        results = await self.vector.search(
            repo_id=state["repo_id"],
            query=state["question"],
            commit_sha=state["commit_sha"], # CRITICAL: Time Travel enforcement
            limit=10
        )
        
        # Convert to Citations
        citations = [
            ChunkCitation(
                file_path=r.metadata["file_path"],
                symbol_name=r.metadata.get("symbol_name", "unknown"),
                start_line=r.metadata.get("start_line", 0),
                content_preview=r.page_content,
                score=r.score
            ) for r in results
        ]
        
        return {**state, "documents": citations}

    async def grade_documents(self, state: AgentState) -> AgentState:
        """
        Binary score: 'yes' or 'no' on whether the doc answers the question.
        Filters out irrelevant chunks to reduce context noise.
        """
        print("---CHECKING RELEVANCE---")
        question = state["question"]
        filtered_docs = []
        
        for doc in state["documents"]:
            # Fast, cheap LLM call (e.g., Gemini Flash)
            score = await self.llm.grade_relevance(question, doc.content_preview)
            if score.binary_score == "yes":
                filtered_docs.append(doc)
            else:
                print(f"---GRADED: REJECTED {doc.file_path}---")
                
        return {**state, "documents": filtered_docs}

    async def generate(self, state: AgentState) -> AgentState:
        """
        Generates the final answer using valid docs.
        """
        print("---GENERATING---")
        
        if not state["documents"]:
            # Fallback behavior if retrieval failed
            return {**state, "generation": "I could not find relevant code in this commit to answer your question."}
            
        answer = await self.llm.generate_rag_response(
            question=state["question"],
            context=state["documents"]
        )
        
        return {**state, "generation": answer}
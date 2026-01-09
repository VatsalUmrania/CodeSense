from typing import TypedDict, List
from app.schemas.chat import ChunkCitation

class AgentState(TypedDict):
    """
    The shared state of the RAG workflow.
    """
    question: str
    repo_id: str
    commit_sha: str
    
    # Internal flow control
    documents: List[ChunkCitation] # Retrieved chunks
    generation: str # Final answer
    web_search_needed: bool # If code is insufficient (optional future proofing)
    
    # Loop safety
    revision_count: int
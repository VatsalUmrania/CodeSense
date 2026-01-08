from sqlmodel import Session
from app.models.chat import ChatSession, ChatMessage, MessageChunk
from app.models.enums import MessageRole
from app.schemas.chat import MessageResponse, ChunkCitation
from app.services.llm.gemini import GeminiService
from app.services.vector.search import VectorSearchService
from app.agent.nodes.nodes import AgentNodes
from app.agent.graph import GraphBuilder
from typing import List
import uuid
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        try:
            # Initialize Services with error handling
            self.llm_service = GeminiService()
            self.vector_service = VectorSearchService(self.llm_service)
            
            # Initialize Agent Graph
            self.nodes = AgentNodes(self.vector_service, self.llm_service)
            self.graph = GraphBuilder(self.nodes).build()
        except Exception as e:
            logger.error(f"Failed to initialize ChatService dependencies: {e}")
            raise e

    async def process_message(self, session_id: uuid.UUID, content: str) -> MessageResponse:
        # 1. Fetch Session Metadata
        session_record = self.db.get(ChatSession, session_id)
        if not session_record:
            raise ValueError("Session not found")

        # 2. Persist User Message
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=content
        )
        self.db.add(user_msg)
        self.db.commit() 
        
        # 3. Invoke Agent (Wrapped in Try/Except)
        try:
            initial_state = {
                "question": content,
                "repo_id": str(session_record.repo_id),
                "commit_sha": session_record.commit_sha,
                "documents": [],
                "generation": "",
                "revision_count": 0,
                "web_search_needed": False
            }

            final_state = await self.graph.ainvoke(initial_state)
            
            generated_content = final_state.get("generation", "No response generated.")
            citations: List[ChunkCitation] = final_state.get("documents", [])

        except Exception as e:
            logger.error(f"Agent Execution Failed: {e}", exc_info=True)
            generated_content = f"I encountered an error processing your request: {str(e)}"
            citations = []

        # 4. Persist Assistant Message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=generated_content
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        # 5. Persist Citations
        if citations:
            for cite in citations:
                chunk_link = MessageChunk(
                    message_id=assistant_msg.id,
                    chunk_id=str(uuid.uuid4()), 
                    score=cite.score
                )
                self.db.add(chunk_link)
            self.db.commit()

        return MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            citations=citations
        )
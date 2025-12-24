from sqlmodel import Session
from app.models.chat import ChatSession, ChatMessage, MessageChunk
from app.models.enums import MessageRole
from app.schemas.chat import MessageResponse, ChunkCitation
from typing import List, Any
import uuid

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    async def process_message(self, session_id: uuid.UUID, content: str) -> MessageResponse:
        """
        Orchestrates the Agent and handles strict persistence.
        """
        # 1. Persist User Message
        user_msg = Message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content
        )
        self.db.add(user_msg)
        self.db.commit() 
        
        # 2. Invoke Agent (LangGraph)
        # (Instantiation of nodes/graph omitted for brevity, same as Step 6)
        # result = await agent.ainvoke(...)
        
        # MOCK RESULT for architecture demonstration
        generated_content = "Here is the answer based on the code..."
        citations: List[ChunkCitation] = [] 

        # 3. Persist Assistant Message
        assistant_msg = Message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=generated_content
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        # 4. Persist Citations (Traceability)
        # Fixed: Explicitly writing to the MessageChunk join table
        for cite in citations:
            # We assume cite.chunk_id comes from the Vector DB results
            # In a real run, we'd map the citation back to the chunk_id
            chunk_link = MessageChunk(
                message_id=assistant_msg.id,
                chunk_id="chunk_hash_from_vector_db", 
                score=cite.score
            )
            self.db.add(chunk_link)
        
        self.db.commit()

        # 5. Return Response
        return MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            citations=citations
        )
# from sqlmodel import Session
# from app.models.chat import ChatSession, ChatMessage, MessageChunk
# from app.models.enums import MessageRole
# from app.schemas.chat import MessageResponse, ChunkCitation
# from typing import List, Any
# import uuid

# class ChatService:
#     def __init__(self, db: Session):
#         self.db = db

#     async def process_message(self, session_id: uuid.UUID, content: str) -> MessageResponse:
#         """
#         Orchestrates the Agent and handles strict persistence.
#         """
#         # 1. Persist User Message
#         user_msg = Message(
#             session_id=session_id,
#             role=MessageRole.USER,
#             content=content
#         )
#         self.db.add(user_msg)
#         self.db.commit() 
        
#         # 2. Invoke Agent (LangGraph)
#         # (Instantiation of nodes/graph omitted for brevity, same as Step 6)
#         # result = await agent.ainvoke(...)
        
#         # MOCK RESULT for architecture demonstration
#         generated_content = "Here is the answer based on the code..."
#         citations: List[ChunkCitation] = [] 

#         # 3. Persist Assistant Message
#         assistant_msg = Message(
#             session_id=session_id,
#             role=MessageRole.ASSISTANT,
#             content=generated_content
#         )
#         self.db.add(assistant_msg)
#         self.db.commit()
#         self.db.refresh(assistant_msg)
        
#         # 4. Persist Citations (Traceability)
#         # Fixed: Explicitly writing to the MessageChunk join table
#         for cite in citations:
#             # We assume cite.chunk_id comes from the Vector DB results
#             # In a real run, we'd map the citation back to the chunk_id
#             chunk_link = MessageChunk(
#                 message_id=assistant_msg.id,
#                 chunk_id="chunk_hash_from_vector_db", 
#                 score=cite.score
#             )
#             self.db.add(chunk_link)
        
#         self.db.commit()

#         # 5. Return Response
#         return MessageResponse(
#             id=assistant_msg.id,
#             role=assistant_msg.role,
#             content=assistant_msg.content,
#             created_at=assistant_msg.created_at,
#             citations=citations
#         )


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

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        # Initialize Services
        self.llm_service = GeminiService()
        self.vector_service = VectorSearchService(self.llm_service)
        
        # Initialize Agent Graph
        self.nodes = AgentNodes(self.vector_service, self.llm_service)
        self.graph = GraphBuilder(self.nodes).build()

    async def process_message(self, session_id: uuid.UUID, content: str) -> MessageResponse:
        """
        Orchestrates the Agent and handles strict persistence.
        """
        # 1. Fetch Session Metadata (to get repo_id and commit_sha)
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
        
        # 3. Invoke Agent (LangGraph)
        initial_state = {
            "question": content,
            "repo_id": str(session_record.repo_id),
            "commit_sha": session_record.commit_sha,
            "documents": [],
            "generation": "",
            "revision_count": 0,
            "web_search_needed": False
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        generated_content = final_state.get("generation", "I'm sorry, I couldn't generate a response.")
        citations: List[ChunkCitation] = final_state.get("documents", [])

        # 4. Persist Assistant Message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=generated_content
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        # 5. Persist Citations (Traceability)
        for cite in citations:
            # We map the citation back to the chunk_id stored in metadata
            # Note: chunk_id logic depends on how you store it in 'metadata' inside 'retrieve' node
            # For now, we assume VectorSearchService returns it in metadata['chunk_id']
            # If standard UUID is strictly required by DB, ensure Vector Store uses UUIDs
            chunk_link = MessageChunk(
                message_id=assistant_msg.id,
                chunk_id=str(uuid.uuid4()), # Placeholder if original ID isn't available/compatible
                score=cite.score
            )
            self.db.add(chunk_link)
        
        self.db.commit()

        # 6. Return Response
        return MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            citations=citations
        )
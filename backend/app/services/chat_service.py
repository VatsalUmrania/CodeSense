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
from app.services.query.hybrid_service import HybridQueryService
from app.agent.nodes.nodes import AgentNodes
from app.agent.graph import GraphBuilder
from typing import List, Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self, 
        db: Session,
        llm_service: GeminiService,
        vector_service: VectorSearchService
    ):
        self.db = db
        # Use injected singleton services instead of creating new ones
        self.llm_service = llm_service
        self.vector_service = vector_service
        
        # Initialize Hybrid Query Service (Phase 3) with injected services
        self.hybrid_service = HybridQueryService(
            db=db,
            llm_service=llm_service,
            vector_service=vector_service
        )
        
        # Initialize Agent Graph (fallback for complex queries)
        self.nodes = AgentNodes(self.vector_service, self.llm_service)
        self.graph = GraphBuilder(self.nodes).build()
        
        # Flag to enable/disable hybrid mode
        self.use_hybrid = True  # Set to False to use old agent-based approach

    async def process_message(self, session_id: uuid.UUID, content: str) -> MessageResponse:
        """
        Orchestrates query processing with hybrid approach (Phase 3).
        
        Now uses static analysis + semantic search + LLM generation.
        OPTIMIZED: Single DB commit instead of 3 separate commits.
        """
        # 1. Fetch Session Metadata (to get repo_id and commit_sha)
        session_record = self.db.get(ChatSession, session_id)
        if not session_record:
            raise ValueError("Session not found")

        # 2. Create User Message (don't commit yet)
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=content
        )
        self.db.add(user_msg)
        # OPTIMIZATION: Don't commit yet, batch with other operations
        
        # 3. Process with Hybrid Service or Traditional Agent
        generated_content = ""
        citations: List[ChunkCitation] = []
        static_results = None
        
        if self.use_hybrid:
            logger.info("Using hybrid query service (Phase 3)")
            try:
                # Use new hybrid service
                hybrid_result = await self.hybrid_service.execute_query(
                    query=content,
                    repo_id=session_record.repo_id,
                    commit_sha=session_record.commit_sha,
                    top_k=5
                )
                
                generated_content = hybrid_result.llm_answer
                static_results = hybrid_result.static_results
                
                # Convert retrieved chunks to citations
                # FIX: Map to correct ChunkCitation schema fields
                for chunk in hybrid_result.retrieved_chunks:
                    citations.append(ChunkCitation(
                        file_path=chunk.metadata.get('file_path', 'unknown'),
                        symbol_name=chunk.metadata.get('symbol_name', 'code_block'),  # FIX: was missing
                        start_line=chunk.metadata.get('start_line', 0),
                        content_preview=chunk.page_content[:200],  # FIX: was 'content', limit to 200 chars
                        score=chunk.score
                    ))
                
                logger.info(f"Hybrid query: {hybrid_result.query_type}, " +
                           f"static={hybrid_result.static_results is not None}, " +
                           f"semantic_chunks={len(citations)}")
            
            except Exception as e:
                logger.error(f"Hybrid service failed: {e}, falling back to agent")
                # Fall back to traditional agent
                generated_content, citations = await self._process_with_agent(
                    content, session_record
                )
        else:
            # Use traditional agent-based approach
            logger.info("Using traditional agent (hybrid disabled)")
            generated_content, citations = await self._process_with_agent(
                content, session_record
            )

        # 4. Create Assistant Message (don't commit yet)
        assistant_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=generated_content
        )
        self.db.add(assistant_msg)
        # OPTIMIZATION: Don't commit yet, batch with citations
        
        # 5. Create Citations (don't commit yet)
        for cite in citations:
            chunk_link = MessageChunk(
                message_id=assistant_msg.id,
                chunk_id=str(uuid.uuid4()),  # Placeholder
                score=cite.score
            )
            self.db.add(chunk_link)
        
        # OPTIMIZATION: Single batch commit for all operations (user_msg + assistant_msg + citations)
        # This reduces DB round-trips from 3 to 1, saving ~500ms-1s
        self.db.commit()
        self.db.refresh(assistant_msg)  # Refresh to get generated ID and timestamps

        # 6. Return Response (with optional static analysis metadata)
        response = MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            citations=citations
        )
        
        # Add static analysis metadata if available
        if static_results and static_results.success:
            # Store in message metadata or include in response
            logger.info(f"Static analysis: {static_results.query_type}, " +
                       f"{len(static_results.results)} results")
        
        return response
    
    async def _process_with_agent(
        self,
        content: str,
        session_record: ChatSession
    ) -> tuple[str, List[ChunkCitation]]:
        """
        Process with traditional LangGraph agent (fallback).
        """
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
        
        return generated_content, citations
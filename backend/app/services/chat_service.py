import json
from typing import AsyncGenerator, List, Dict, Optional
from app.services.llm.gemini import GeminiService
from app.services.vector.store import VectorStore
from app.services.storage import StorageService
from flashrank import Ranker, RerankRequest
from app.core.logger import get_logger

logger = get_logger("chat_service")

class ChatService:
    def __init__(self):
        self.gemini = GeminiService()
        self.vector_store = VectorStore()
        self.storage = StorageService()
        self.ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="/tmp/flashrank")

    async def generate_response(
        self, 
        message: str, 
        repo_id: Optional[str], 
        history: List[Dict[str, str]], 
        pinned_files: List[str]
    ) -> AsyncGenerator[str, None]:
        
        # 1. Embed Query
        query_vector = self.gemini.embed_content(message)
        if not query_vector:
            yield json.dumps({"type": "error", "content": "Failed to generate embedding."}) + "\n"
            return

        # 2. Semantic Cache Check (Read Path Optimization)
        # Only check cache if no files are pinned (context specific)
        if not pinned_files:
            cached_answer = self.vector_store.search_cache(query_vector)
            if cached_answer:
                # Stream the cached answer
                yield json.dumps({"type": "chunk", "content": cached_answer}) + "\n"
                return

        # 3. Standard RAG Flow
        seen_files = set()
        candidates_for_reranking = []
        pinned_context = ""
        final_sources = []

        if repo_id and pinned_files:
            for file_path in pinned_files:
                content = self.storage.get_file_content(repo_id, file_path)
                if content:
                    pinned_context += f"// --- PINNED FILE: {file_path} ---\n{content}\n\n"
                    final_sources.append({
                        "file": file_path,
                        "code": content,
                        "start_line": 1,
                        "repo_id": repo_id,
                        "pinned": True
                    })
                    seen_files.add(file_path)

        # Wide Retrieval
        search_results = self.vector_store.client.search(
            collection_name="codesense_codebase",
            query_vector=query_vector,
            limit=25
        )

        for hit in search_results:
            metadata = hit.payload.get('metadata', {})
            file_path = metadata.get('file_path', 'unknown')
            if file_path in seen_files: continue
                
            content = hit.payload.get('content', '')
            candidates_for_reranking.append({
                "id": hit.id,
                "text": content,
                "meta": {
                    "file_path": file_path,
                    "repo_id": hit.payload.get('repo_id', ''),
                    "start_line": metadata.get('start_line', 1)
                }
            })
            seen_files.add(file_path)

        # Re-ranking
        reranked_chunks = []
        if candidates_for_reranking:
            rerank_request = RerankRequest(query=message, passages=candidates_for_reranking)
            reranked_results = self.ranker.rerank(rerank_request)
            
            for result in reranked_results[:5]:
                meta = result['meta']
                raw_content = result['text']
                lines = raw_content.split('\n')
                clean_code = "\n".join(lines[1:]) if lines and lines[0].startswith("// File:") else raw_content
                reranked_chunks.append(raw_content)
                final_sources.append({
                    "file": meta['file_path'],
                    "code": clean_code,
                    "start_line": meta['start_line'],
                    "repo_id": meta['repo_id']
                })

        retrieved_context = "\n\n".join(reranked_chunks)
        full_context = pinned_context + "\n" + retrieved_context
        
        history_text = ""
        for msg in history[-10:]: 
            role = "User" if msg['role'] == "user" else "AI"
            history_text += f"{role}: {msg['content']}\n"

        system_prompt = f"""
        You are CodeSense, an expert AI software architect.
        ### CONTEXT:
        {full_context}
        ### HISTORY:
        {history_text}
        ### QUESTION: 
        {message}
        ### INSTRUCTIONS:
        1. Answer comprehensively using context.
        2. Cite files using [filename](path/to/file).
        """

        # Stream & Capture for Cache
        yield json.dumps({"type": "sources", "data": final_sources}) + "\n"
        
        full_response_accumulator = ""
        for chunk in self.gemini.stream_chat(system_prompt):
            full_response_accumulator += chunk
            yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
            
        # Write to Cache (Write Path Optimization)
        # Only cache if no pinned files were used (generic queries)
        if not pinned_files and full_response_accumulator:
            self.vector_store.save_cache(query_vector, full_response_accumulator)
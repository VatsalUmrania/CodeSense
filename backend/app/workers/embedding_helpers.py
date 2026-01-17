"""
Simplified local embedding functions for pipelines.py

Replace the old Gemini API calls with this.
"""

import hashlib
from typing import List, Dict
from app.services.embeddings.local_service import get_embedding_service


def process_embeddings_local(repo, run, chunks):
    """
    Process embeddings using local BGE model.
    
    Much faster than Gemini API - no rate limits, no network calls.
    """
    if not chunks:
        return
    
    print(f"Processing {len(chunks)} chunks with local BGE embeddings...")
    
    # Get embedding service
    embedder = get_embedding_service()
    
    # Extract text from chunks
    texts = [chunk["content"] for chunk in chunks]
    
    # Generate all embeddings in batches (FAST!)
    print("Generating embeddings...")
    embeddings = embedder.embed_batch(texts, batch_size=16)
    
    # Prepare for Qdrant
    from app.services.vector.store import VectorStore
    vector_store = VectorStore()
    
    print("Preparing vectors for storage...")
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        # Deterministic ID - convert SHA256 to UUID format for Qdrant
        unique_str = f"{repo.id}:{run.commit_sha}:{chunk['file_path']}:{chunk['start_line']}"
        hash_hex = hashlib.sha256(unique_str.encode()).hexdigest()
        # Take first 32 chars and format as UUID
        vector_id = f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
        
        vectors.append({
            "id": vector_id,
            "vector": embedding,
            "payload": {
                "repo_id": str(repo.id),
                "commit_sha": run.commit_sha,
                "file_path": chunk["file_path"],
                "content": chunk["content"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"]
            }
        })
        
        # Upsert in batches
        if len(vectors) >= 100 or i == len(chunks) - 1:
            vector_store.upsert_chunks(vectors)
            print(f"Indexed {i + 1}/{len(chunks)} chunks...")
            vectors = []
    
    print(f"✅ Successfully embedded and indexed all {len(chunks)} chunks!")

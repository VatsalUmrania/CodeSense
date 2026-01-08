import os

class ChunkingService:
    def chunk_repository(self, repo_path: str) -> list[dict]:
        """
        Iterates over the repo and chunks supported files.
        """
        chunks = []
        # Add more extensions as needed
        supported_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".md", ".txt"}

        for root, _, files in os.walk(repo_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext not in supported_extensions:
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                    # Simple Line-based Chunking (every 60 lines with 10 lines overlap)
                    lines = content.splitlines()
                    chunk_size = 60
                    overlap = 10
                    
                    if not lines:
                        continue

                    # Handle small files
                    if len(lines) <= chunk_size:
                         chunks.append({
                            "file_path": rel_path,
                            "content": content,
                            "start_line": 1,
                            "end_line": len(lines)
                        })
                         continue

                    # Handle larger files
                    for i in range(0, len(lines), chunk_size - overlap):
                        chunk_lines = lines[i : i + chunk_size]
                        chunk_text = "\n".join(chunk_lines)
                        
                        if not chunk_text.strip():
                            continue

                        chunks.append({
                            "file_path": rel_path,
                            "content": chunk_text,
                            "start_line": i + 1,
                            "end_line": i + len(chunk_lines)
                        })

                except Exception as e:
                    print(f"Error chunking {rel_path}: {e}")

        return chunks
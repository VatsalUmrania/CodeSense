import os
from typing import List, Dict

class ParserService:
    def __init__(self):
        self.languages = {
            ".py": "python", ".js": "javascript", ".ts": "typescript", 
            ".tsx": "typescript", ".jsx": "javascript", ".go": "go", 
            ".rs": "rust", ".java": "java", ".md": "markdown", 
            ".json": "json", ".css": "css", ".html": "html", 
            ".yml": "yaml", ".yaml": "yaml"
        }

    def parse_directory(self, repo_path: str) -> List[Dict]:
        chunks = []
        for root, _, files in os.walk(repo_path):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if ext in self.languages:
                    rel_path = os.path.relpath(file_path, repo_path)
                    file_chunks = self._parse_file(file_path, rel_path, self.languages[ext])
                    chunks.extend(file_chunks)
                    
        return chunks

    def _parse_file(self, full_path: str, rel_path: str, lang_name: str) -> List[Dict]:
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            
            chunks = []
            lines = code.split('\n')
            
            # --- FIX: INCREASED CHUNK SIZE ---
            # 60 was too small. 300 captures full classes/functions better.
            chunk_size = 300 
            overlap = 50 
            
            for i in range(0, len(lines), chunk_size - overlap):
                chunk_lines = lines[i:i+chunk_size]
                chunk_content = '\n'.join(chunk_lines)
                
                if not chunk_content.strip(): 
                    continue
                
                # We keep the header for the AI, but we will strip it in the UI if needed
                final_content = f"// File: {rel_path} (Lines {i+1}-{i+len(chunk_lines)})\n" + chunk_content
                    
                chunks.append({
                    "content": final_content,
                    "metadata": {
                        "file_path": rel_path,
                        "language": lang_name,
                        "start_line": i + 1,  # Tracking real line numbers
                        "end_line": i + len(chunk_lines)
                    }
                })
            return chunks
            
        except Exception as e:
            print(f"Error parsing {rel_path}: {e}")
            return []

import os
from typing import List, Dict
from tree_sitter_languages import get_language, get_parser

class ParserService:
    def __init__(self):
        # Supported languages mapping
        self.languages = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java"
        }

    def parse_directory(self, repo_path: str) -> List[Dict]:
        """
        Walks the directory and parses all supported files.
        Returns a list of chunks: [{'content': '...', 'metadata': {...}}]
        """
        chunks = []
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                # Skip hidden files/dirs
                if file.startswith(".") or "node_modules" in root or "venv" in root:
                    continue
                
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if ext in self.languages:
                    file_chunks = self._parse_file(file_path, self.languages[ext])
                    chunks.extend(file_chunks)
                    
        return chunks

    def _parse_file(self, file_path: str, lang_name: str) -> List[Dict]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Simple chunking strategy: Split by function/class definitions would be ideal
            # For MVP/Simplicity: We will split by logical lines or token count.
            # Ideally, we use tree-sitter queries here to extract specific nodes.
            
            # Let's stick to a naive splitter first to ensure flow works, 
            # then upgrade to Tree-Sitter smart splitting later.
            
            chunks = []
            lines = code.split('\n')
            chunk_size = 50 # lines
            
            for i in range(0, len(lines), chunk_size):
                chunk_content = '\n'.join(lines[i:i+chunk_size])
                if not chunk_content.strip(): 
                    continue
                    
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "file_path": file_path,
                        "language": lang_name,
                        "start_line": i,
                        "end_line": i + chunk_size
                    }
                })
            return chunks
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
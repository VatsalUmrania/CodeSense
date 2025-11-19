import os
from typing import List, Dict

class ParserService:
    def __init__(self):
        # Added .md, .json, .css, .html, .yml
        self.languages = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".md": "markdown",
            ".json": "json",
            ".css": "css",
            ".html": "html",
            ".yml": "yaml",
            ".yaml": "yaml"
        }

    def parse_directory(self, repo_path: str) -> List[Dict]:
        chunks = []
        for root, _, files in os.walk(repo_path):
            # Skip strict exclusions
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if ext in self.languages:
                    # Pass the relative path so the AI knows "src/components/Button.tsx"
                    # instead of "/tmp/codesense_repos/uuid/src/..."
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
            
            # --- IMPROVEMENT: Overlap ---
            # We add overlap so context isn't cut in the middle of a function
            chunk_size = 60 
            overlap = 10 
            
            for i in range(0, len(lines), chunk_size - overlap):
                chunk_lines = lines[i:i+chunk_size]
                chunk_content = '\n'.join(chunk_lines)
                
                if not chunk_content.strip(): 
                    continue
                
                # Add filename header to every chunk so the AI knows where it comes from
                # This helps the vector search significantly.
                final_content = f"// File: {rel_path}\n" + chunk_content
                    
                chunks.append({
                    "content": final_content,
                    "metadata": {
                        "file_path": rel_path,
                        "language": lang_name,
                        "start_line": i + 1,
                        "end_line": i + len(chunk_lines)
                    }
                })
            return chunks
            
        except Exception as e:
            print(f"Error parsing {rel_path}: {e}")
            return []

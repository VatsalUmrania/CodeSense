import os
import re
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
            chunk_size = 300 
            overlap = 50 
            
            for i in range(0, len(lines), chunk_size - overlap):
                chunk_lines = lines[i:i+chunk_size]
                chunk_content = '\n'.join(chunk_lines)
                
                if not chunk_content.strip(): 
                    continue
                
                final_content = f"// File: {rel_path} (Lines {i+1}-{i+len(chunk_lines)})\n" + chunk_content
                    
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

    # --- NEW: Graph Logic ---
    def analyze_imports(self, repo_path: str) -> Dict:
        nodes = []
        edges = []
        file_map = {}

        # 1. Identify Nodes
        for root, _, files in os.walk(repo_path):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue
            for file in files:
                if os.path.splitext(file)[1] in self.languages:
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    nodes.append({"id": rel_path, "label": file, "path": rel_path})
                    file_map[file] = rel_path # Simple map: filename -> path

        # 2. Identify Edges
        # Patterns for JS/TS/Py/Go
        import_patterns = [
            r'^import\s+[\{]?\s*([a-zA-Z0-9_,\s]+)\s*[\}]?\s+from\s+[\'"]([^\'"]+)[\'"]', # JS/TS from
            r'^import\s+[\'"]([^\'"]+)[\'"]', # JS side-effect
            r'^import\s+([a-zA-Z0-9_\.]+)', # Python
            r'from\s+([a-zA-Z0-9_\.]+)\s+import' # Python from
        ]

        for node in nodes:
            full_path = os.path.join(repo_path, node["path"])
            try:
                # Use 'ignore' errors to prevent crashing on binary/weird files
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith(('#', '//', '/*')): continue

                    for pattern in import_patterns:
                        match = re.search(pattern, line)
                        if match:
                            target = match.group(1)
                            # Cleanup target string (remove quotes/paths)
                            clean_target = target.split('/')[-1].split('.')[0]
                            
                            # Try to match against known files
                            for fname, fpath in file_map.items():
                                fname_no_ext = fname.split('.')[0]
                                if clean_target == fname_no_ext and fpath != node["path"]:
                                    edges.append({
                                        "source": node["path"],
                                        "target": fpath
                                    })
                                    break
            except Exception as e:
                # Log but don't crash
                print(f"Skipping file {node['path']}: {e}")
                continue

        # Remove duplicates
        unique_edges = [dict(t) for t in {tuple(d.items()) for d in edges}]
        
        return {"nodes": nodes, "edges": unique_edges}  
        nodes = [] 
        edges = []
        file_map = {}

        # 1. Identify Nodes
        for root, _, files in os.walk(repo_path):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue
            for file in files:
                if os.path.splitext(file)[1] in self.languages:
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    nodes.append({"id": rel_path, "label": file, "path": rel_path})
                    file_map[file] = rel_path

        # 2. Identify Edges (Regex-based import detection)
        import_patterns = [
            r'^import\s+[\{]?\s*([a-zA-Z0-9_,\s]+)\s*[\}]?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'^import\s+[\'"]([^\'"]+)[\'"]', 
            r'^import\s+([a-zA-Z0-9_\.]+)' 
        ]

        for node in nodes:
            full_path = os.path.join(repo_path, node["path"])
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                for line in content.split('\n'):
                    line = line.strip()
                    for pattern in import_patterns:
                        match = re.search(pattern, line)
                        if match:
                            target = match.group(1)
                            # Simple heuristic to find target file
                            for fname, fpath in file_map.items():
                                clean_target = target.split('/')[-1]
                                clean_fname = fname.split('.')[0]
                                
                                if clean_target == clean_fname and fpath != node["path"]:
                                    edges.append({
                                        "source": node["path"],
                                        "target": fpath
                                    })
                                    break
            except Exception:
                pass

        return {"nodes": nodes, "edges": edges}
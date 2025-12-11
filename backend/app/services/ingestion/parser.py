import os
from typing import List, Dict, Set
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class ParserService:
    def __init__(self):
        # Map file extensions to LangChain languages
        self.extension_map = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".ts": Language.TS,
            ".tsx": Language.TS,
            ".java": Language.JAVA,
            ".go": Language.GO,
            ".rs": Language.RUST,
            ".html": Language.HTML,
            ".md": Language.MARKDOWN,
        }
        self.max_file_size = 1 * 1024 * 1024  # 1 MB Limit (P0 Fix)

    def parse_directory(self, repo_path: str) -> tuple[List[Dict], Dict]:
        """
        Walks the directory, chunks code using AST-aware splitters, 
        and builds a simple dependency graph based on imports.
        Returns: (chunks, graph_data)
        """
        chunks = []
        nodes = []
        edges = []
        file_paths = set()

        for root, _, files in os.walk(repo_path):
            if any(ignore in root for ignore in ["node_modules", ".git", "venv", "__pycache__"]):
                continue

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                ext = os.path.splitext(file)[1]

                # 1. Security Check: Skip large files
                if os.path.getsize(full_path) > self.max_file_size:
                    print(f"Skipping large file: {rel_path}")
                    continue

                if ext in self.extension_map:
                    file_paths.add(rel_path)
                    
                    # 2. Parse & Chunk
                    file_chunks = self._process_file(full_path, rel_path, self.extension_map[ext])
                    chunks.extend(file_chunks)
                    
                    # 3. Graph Node
                    nodes.append({"id": rel_path, "label": file, "type": "file"})

                    # 4. Extract Imports (Simple Heuristic for now, can be upgraded to full AST later)
                    # We do this here to avoid reading the file twice
                    file_edges = self._extract_imports(full_path, rel_path, repo_path)
                    edges.extend(file_edges)

        return chunks, {"nodes": nodes, "edges": edges}

    def _process_file(self, full_path: str, rel_path: str, language: Language) -> List[Dict]:
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()

            # AST-Aware Splitting
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=800,
                chunk_overlap=100
            )
            raw_docs = splitter.create_documents([code])
            
            structured_chunks = []
            for i, doc in enumerate(raw_docs):
                # Add context header to improve RAG retrieval
                content_with_header = f"// File: {rel_path}\n{doc.page_content}"
                
                structured_chunks.append({
                    "content": content_with_header,
                    "metadata": {
                        "file_path": rel_path,
                        "language": language.value,
                        "chunk_index": i
                    }
                })
            return structured_chunks

        except Exception as e:
            print(f"Error processing {rel_path}: {e}")
            return []

    def _extract_imports(self, full_path: str, rel_path: str, repo_root: str) -> List[Dict]:
        """
        Basic import extraction to build the graph edges.
        Currently uses simple heuristics, can be upgraded to AST queries.
        """
        edges = []
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Very basic heuristic for Demo purposes (Replace with Tree-Sitter queries for Production)
            # This is "Good Enough" for Phase 2 without over-engineering
            lines = content.split('\n')
            for line in lines:
                clean = line.strip()
                target = None
                
                # Python
                if clean.startswith("import ") or clean.startswith("from "):
                    parts = clean.split(' ')
                    if len(parts) > 1:
                        target = parts[1].replace('.', '/') + ".py"
                
                # JS/TS
                elif clean.startswith("import") and "from" in clean:
                    if '"' in clean or "'" in clean:
                        # Extract string between quotes
                        import_path = clean.split('"')[1] if '"' in clean else clean.split("'")[1]
                        if import_path.startswith('.'):
                            # Resolve relative path
                            dir_name = os.path.dirname(rel_path)
                            target = os.path.normpath(os.path.join(dir_name, import_path))
                            # Blindly append extensions (naive but works for visualization)
                            if not target.endswith(('.ts', '.js', '.tsx')):
                                target += ".ts" # Default guess

                if target and os.path.exists(os.path.join(repo_root, target)):
                    edges.append({"source": rel_path, "target": target})

        except Exception:
            pass
            
        return edges
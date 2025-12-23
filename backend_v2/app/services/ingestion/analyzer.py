import os
import ast
from typing import List, Dict, Any

class GraphAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.nodes = []
        self.edges = []

    def analyze_structure(self) -> Dict[str, Any]:
        """
        Walks the file system to build the initial file/folder graph.
        """
        for root, dirs, files in os.walk(self.repo_path):
            # Ignore hidden directories (like .git)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            rel_dir = os.path.relpath(root, self.repo_path)
            if rel_dir == ".":
                rel_dir = ""

            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.join(rel_dir, file)
                
                # Create a file node
                node_id = rel_path
                self.nodes.append({
                    "id": node_id,
                    "type": "file",
                    "name": file,
                    "path": rel_path,
                    "size": os.path.getsize(file_path)
                })

                # Simple Directory Edge (Parent -> Child)
                parent_dir = os.path.dirname(rel_path)
                if parent_dir:
                    self.edges.append({
                        "source": parent_dir,
                        "target": node_id,
                        "relation": "contains"
                    })

        return {
            "nodes": self.nodes,
            "edges": self.edges
        }

    def generate_ast(self) -> List[Dict[str, Any]]:
        """
        Parses Python files to extract functions and classes (AST).
        Returns a list of symbols found.
        """
        symbols = []
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.repo_path)
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=file)
                        
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            symbols.append({
                                "file": rel_path,
                                "type": "function",
                                "name": node.name,
                                "line_start": node.lineno,
                                "line_end": node.end_lineno,
                                "args": [a.arg for a in node.args.args]
                            })
                        elif isinstance(node, ast.ClassDef):
                            symbols.append({
                                "file": rel_path,
                                "type": "class",
                                "name": node.name,
                                "line_start": node.lineno,
                                "line_end": node.end_lineno
                            })
                except Exception as e:
                    # Skip files that fail to parse (syntax errors, etc.)
                    print(f"Skipping AST for {rel_path}: {e}")
                    continue

        return symbols
import hashlib
from typing import List
from .models import ParsedElement, Chunk, SymbolType

class SemanticChunker:
    def chunk_file(self, file_path: str, code: str, elements: List[ParsedElement]) -> List[Chunk]:
        chunks = []
        
        # Fallback: If no symbols found (e.g., config file, script), chunk the whole file
        if not elements:
            return [self._create_chunk(
                content=f"// File: {file_path}\n// Type: MODULE\n{code}",
                file_path=file_path,
                symbol_name=file_path.split('/')[-1],
                symbol_type=SymbolType.MODULE
            )]

        for elem in elements:
            # Enriched Header with Hierarchy
            header = f"// File: {file_path}\n// Type: {elem.type.value}\n"
            if elem.parent_name:
                header += f"// Context: {elem.parent_name} (Depth: {elem.depth})\n"
            header += f"// Name: {elem.name}\n"
            
            full_content = header + elem.content
            
            chunks.append(self._create_chunk(
                content=full_content,
                file_path=file_path,
                symbol_name=elem.name,
                symbol_type=elem.type,
                parent=elem.parent_name
            ))
            
        return chunks

    def _create_chunk(self, content: str, file_path: str, symbol_name: str, symbol_type: SymbolType, parent: str = None) -> Chunk:
        # Stable Hash
        chunk_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        return Chunk(
            content=content,
            chunk_id=chunk_hash,
            metadata={
                "file_path": file_path,
                "symbol_name": symbol_name,
                "symbol_type": symbol_type.value,
                "parent_symbol": parent,
                "code_hash": chunk_hash
            }
        )
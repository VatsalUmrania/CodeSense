from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

class SymbolType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    IMPORT = "import"
    MODULE = "module"  # Fallback for file-level content

@dataclass
class ParsedElement:
    type: SymbolType
    name: str
    start_byte: int
    end_byte: int
    content: str
    # Hierarchy Context
    parent_name: Optional[str] = None 
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    chunk_id: str  # Stable Hash
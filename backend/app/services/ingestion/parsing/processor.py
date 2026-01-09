from typing import List, Optional
from tree_sitter import Node
from tree_sitter_languages import get_language
from .languages import TreeSitterConfig, LanguageType, get_query
from .models import ParsedElement, SymbolType

class CodeProcessor:
    def parse(self, code: bytes, lang: LanguageType) -> List[ParsedElement]:
        parser = TreeSitterConfig.get_parser(lang)
        tree = parser.parse(code)
        
        ts_lang = get_language(lang.value)
        query = ts_lang.query(get_query(lang))
        
        captures = query.captures(tree.root_node)
        elements = []
        
        for node, capture_name in captures:
            if capture_name.endswith(".def"):
                # Determine Type
                raw_type = capture_name.split('.')[0] # 'class' or 'function'
                symbol_type = SymbolType.CLASS if raw_type == 'class' else SymbolType.FUNCTION
                
                # Extract Name
                name_node = node.child_by_field_name("name")
                name = code[name_node.start_byte : name_node.end_byte].decode("utf8") if name_node else "anonymous"
                
                # Resolve Hierarchy
                parent_name, depth = self._resolve_context(node, code)
                
                elements.append(ParsedElement(
                    type=symbol_type,
                    name=name,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    content=code[node.start_byte : node.end_byte].decode("utf8"),
                    parent_name=parent_name,
                    depth=depth
                ))
                
        return elements

    def _resolve_context(self, node: Node, code: bytes) -> tuple[Optional[str], int]:
        """
        Walks up the tree to find semantic parents.
        Returns: (parent_name, nesting_depth)
        """
        current = node.parent
        depth = 0
        parent_name = None
        
        while current:
            # Check if parent is a class or function definition
            if current.type in ['class_definition', 'function_definition', 'class_declaration', 'function_declaration']:
                depth += 1
                if parent_name is None:
                    # Capture immediate parent name
                    name_child = current.child_by_field_name("name")
                    if name_child:
                        parent_name = code[name_child.start_byte : name_child.end_byte].decode("utf8")
            current = current.parent
            
        return parent_name, depth
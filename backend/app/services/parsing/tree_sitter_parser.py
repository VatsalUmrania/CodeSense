"""
Multi-language AST parser using Tree-sitter.

This module provides a unified interface for parsing source code into ASTs
and extracting code symbols (functions, classes, variables, imports) across
multiple programming languages.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import tree_sitter_languages
from tree_sitter import Node, Language
import logging

from app.services.parsing.language_detector import detect_language

logger = logging.getLogger(__name__)


@dataclass
class FunctionDefinition:
    """Represents a function or method definition."""
    name: str
    line_start: int
    line_end: int
    signature: Optional[str] = None
    parameters: Optional[List[str]] = None
    parent_class: Optional[str] = None
    decorators: Optional[List[str]] = None
    is_async: bool = False
    is_method: bool = False


@dataclass
class ClassDefinition:
    """Represents a class definition."""
    name: str
    line_start: int
    line_end: int
    base_classes: Optional[List[str]] = None
    decorators: Optional[List[str]] = None
    methods: Optional[List[str]] = None


@dataclass
class ImportStatement:
    """Represents an import/include statement."""
    module: str
    line_number: int
    imported_names: Optional[List[str]] = None
    alias: Optional[str] = None
    is_from_import: bool = False


@dataclass
class VariableDeclaration:
    """Represents a variable declaration."""
    name: str
    line_number: int
    scope: str  # 'global', 'class', 'function'
    type_annotation: Optional[str] = None
    is_constant: bool = False


class TreeSitterParser:
    """
    Multi-language source code parser using Tree-sitter.
    
    Supports all languages available in tree-sitter-languages package.
    """
    
    def __init__(self):
        """Initialize parsers for all supported languages."""
        self.parsers = {}
        self.languages = {}
        
    def _get_parser(self, language: str):
        """Get or create parser for a language."""
        if language not in self.parsers:
            try:
                self.parsers[language] = tree_sitter_languages.get_parser(language)
                self.languages[language] = tree_sitter_languages.get_language(language)
                logger.info(f"Initialized parser for {language}")
            except Exception as e:
                logger.error(f"Failed to initialize parser for {language}: {e}")
                return None
        return self.parsers[language]
    
    def parse_file(self, file_path: str, content: str) -> Optional[Node]:
        """
        Parse a source file into an AST.
        
        Args:
            file_path: Path to the file (used for language detection)
            content: File content as string
            
        Returns:
            Root AST node or None if parsing failed
        """
        language = detect_language(file_path)
        if not language:
            logger.warning(f"Unsupported language for file: {file_path}")
            return None
        
        parser = self._get_parser(language)
        if not parser:
            return None
        
        try:
            tree = parser.parse(bytes(content, "utf8"))
            return tree.root_node
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def extract_functions(self, root_node: Node, language: str, source_code: bytes) -> List[FunctionDefinition]:
        """
        Extract function definitions from AST.
        
        Args:
            root_node: Root AST node
            language: Programming language
            source_code: Original source code as bytes
            
        Returns:
            List of function definitions
        """
        functions = []
        
        # Language-specific query patterns
        if language == "python":
            functions = self._extract_python_functions(root_node, source_code)
        elif language in ["javascript", "typescript", "tsx"]:
            functions = self._extract_js_functions(root_node, source_code)
        elif language == "java":
            functions = self._extract_java_methods(root_node, source_code)
        elif language == "go":
            functions = self._extract_go_functions(root_node, source_code)
        elif language in ["c", "cpp"]:
            functions = self._extract_c_functions(root_node, source_code)
        elif language == "rust":
            functions = self._extract_rust_functions(root_node, source_code)
        # Add more languages as needed
        
        return functions
    
    def extract_classes(self, root_node: Node, language: str, source_code: bytes) -> List[ClassDefinition]:
        """Extract class definitions from AST."""
        classes = []
        
        if language == "python":
            classes = self._extract_python_classes(root_node, source_code)
        elif language in ["javascript", "typescript", "tsx"]:
            classes = self._extract_js_classes(root_node, source_code)
        elif language == "java":
            classes = self._extract_java_classes(root_node, source_code)
        elif language == "cpp":
            classes = self._extract_cpp_classes(root_node, source_code)
        elif language == "rust":
            classes = self._extract_rust_structs(root_node, source_code)
        
        return classes
    
    def extract_imports(self, root_node: Node, language: str, source_code: bytes) -> List[ImportStatement]:
        """Extract import statements from AST."""
        imports = []
        
        if language == "python":
            imports = self._extract_python_imports(root_node, source_code)
        elif language in ["javascript", "typescript", "tsx"]:
            imports = self._extract_js_imports(root_node, source_code)
        elif language == "java":
            imports = self._extract_java_imports(root_node, source_code)
        elif language == "go":
            imports = self._extract_go_imports(root_node, source_code)
        
        return imports
    
    def extract_variables(self, root_node: Node, language: str, source_code: bytes) -> List[VariableDeclaration]:
        """Extract variable declarations from AST."""
        variables = []
        
        if language == "python":
            variables = self._extract_python_variables(root_node, source_code)
        elif language in ["javascript", "typescript", "tsx"]:
            variables = self._extract_js_variables(root_node, source_code)
        
        return variables
    
    # Python-specific extractors
    def _extract_python_functions(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        """Extract Python function definitions."""
        functions = []
        
        def visit_node(node: Node, parent_class: Optional[str] = None):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                params_node = node.child_by_field_name("parameters")
                
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf8')
                    
                    # Extract parameters
                    parameters = []
                    if params_node:
                        for param in params_node.children:
                            if param.type == "identifier":
                                parameters.append(source_code[param.start_byte:param.end_byte].decode('utf8'))
                    
                    # Check for async
                    is_async = False
                    for child in node.children:
                        if child.type == "async":
                            is_async = True
                            break
                    
                    functions.append(FunctionDefinition(
                        name=name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        parameters=parameters,
                        parent_class=parent_class,
                        is_async=is_async,
                        is_method=parent_class is not None
                    ))
            
            # Check for class definitions to track methods
            if node.type == "class_definition":
                class_name_node = node.child_by_field_name("name")
                if class_name_node:
                    class_name = source_code[class_name_node.start_byte:class_name_node.end_byte].decode('utf8')
                    for child in node.children:
                        visit_node(child, parent_class=class_name)
            else:
                for child in node.children:
                    visit_node(child, parent_class)
        
        visit_node(root_node)
        return functions
    
    def _extract_python_classes(self, root_node: Node, source_code: bytes) -> List[ClassDefinition]:
        """Extract Python class definitions."""
        classes = []
        
        def visit_node(node: Node):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                superclasses_node = node.child_by_field_name("superclasses")
                
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf8')
                    
                    base_classes = []
                    if superclasses_node:
                        for arg in superclasses_node.children:
                            if arg.type == "identifier":
                                base_classes.append(source_code[arg.start_byte:arg.end_byte].decode('utf8'))
                    
                    classes.append(ClassDefinition(
                        name=name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        base_classes=base_classes if base_classes else None
                    ))
            
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        return classes
    
    def _extract_python_imports(self, root_node: Node, source_code: bytes) -> List[ImportStatement]:
        """Extract Python import statements."""
        imports = []
        
        def visit_node(node: Node):
            if node.type == "import_statement":
                # import module
                for child in node.children:
                    if child.type == "dotted_name":
                        module = source_code[child.start_byte:child.end_byte].decode('utf8')
                        imports.append(ImportStatement(
                            module=module,
                            line_number=node.start_point[0] + 1,
                            is_from_import=False
                        ))
            
            elif node.type == "import_from_statement":
                # from module import name
                module_node = node.child_by_field_name("module_name")
                if module_node:
                    module = source_code[module_node.start_byte:module_node.end_byte].decode('utf8')
                    
                    imported_names = []
                    for child in node.children:
                        if child.type == "dotted_name" or child.type == "identifier":
                            if child != module_node:
                                imported_names.append(source_code[child.start_byte:child.end_byte].decode('utf8'))
                    
                    imports.append(ImportStatement(
                        module=module,
                        line_number=node.start_point[0] + 1,
                        imported_names=imported_names if imported_names else None,
                        is_from_import=True
                    ))
            
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        return imports
    
    def _extract_python_variables(self, root_node: Node, source_code: bytes) -> List[VariableDeclaration]:
        """Extract Python variable declarations."""
        # Basic implementation - can be enhanced
        return []
    
    # JavaScript/TypeScript extractors (simplified - can be expanded)
    def _extract_js_functions(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        """Extract JavaScript/TypeScript function definitions."""
        functions = []
        
        def visit_node(node: Node):
            if node.type in ["function_declaration", "function", "method_definition", "arrow_function"]:
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf8')
                    functions.append(FunctionDefinition(
                        name=name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1
                    ))
            
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        return functions
    
    def _extract_js_classes(self, root_node: Node, source_code: bytes) -> List[ClassDefinition]:
        """Extract JavaScript/TypeScript class definitions."""
        classes = []
        
        def visit_node(node: Node):
            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf8')
                    classes.append(ClassDefinition(
                        name=name,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1
                    ))
            
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        return classes
    
    def _extract_js_imports(self, root_node: Node, source_code: bytes) -> List[ImportStatement]:
        """Extract JavaScript/TypeScript import statements."""
        imports = []
        
        def visit_node(node: Node):
            if node.type == "import_statement":
                source_node = node.child_by_field_name("source")
                if source_node:
                    module = source_code[source_node.start_byte:source_node.end_byte].decode('utf8').strip('\'"')
                    imports.append(ImportStatement(
                        module=module,
                        line_number=node.start_point[0] + 1
                    ))
            
            for child in node.children:
                visit_node(child)
        
        visit_node(root_node)
        return imports
    
    def _extract_js_variables(self, root_node: Node, source_code: bytes) -> List[VariableDeclaration]:
        """Extract JavaScript/TypeScript variable declarations."""
        return []
    
    # Placeholder methods for other languages (implement as needed)
    def _extract_java_methods(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        return []
    
    def _extract_java_classes(self, root_node: Node, source_code: bytes) -> List[ClassDefinition]:
        return []
    
    def _extract_java_imports(self, root_node: Node, source_code: bytes) -> List[ImportStatement]:
        return []
    
    def _extract_go_functions(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        return []
    
    def _extract_go_imports(self, root_node: Node, source_code: bytes) -> List[ImportStatement]:
        return []
    
    def _extract_c_functions(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        return []
    
    def _extract_cpp_classes(self, root_node: Node, source_code: bytes) -> List[ClassDefinition]:
        return []
    
    def _extract_rust_functions(self, root_node: Node, source_code: bytes) -> List[FunctionDefinition]:
        return []
    
    def _extract_rust_structs(self, root_node: Node, source_code: bytes) -> List[ClassDefinition]:
        return []

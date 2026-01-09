from enum import Enum
from tree_sitter_languages import get_language, get_parser

class LanguageType(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"

class TreeSitterConfig:
    _parsers = {}

    @classmethod
    def get_parser(cls, lang: LanguageType):
        if lang not in cls._parsers:
            cls._parsers[lang] = get_parser(lang.value)
        return cls._parsers[lang]

# Defined strict capture groups: @import, @class.def, @function.def
QUERIES = {
    LanguageType.PYTHON: """
        (import_statement) @import
        (import_from_statement) @import
        
        (class_definition
            name: (identifier) @class.name
            body: (block) @class.body) @class.def
            
        (function_definition
            name: (identifier) @function.name
            body: (block) @function.body) @function.def
    """,
    LanguageType.TYPESCRIPT: """
        (import_statement) @import
        (export_statement source: (string)) @import
        
        (class_declaration
            name: (type_identifier) @class.name
            body: (class_body) @class.body) @class.def

        (function_declaration
            name: (identifier) @function.name
            body: (statement_block) @function.body) @function.def
            
        (method_definition
            name: (property_identifier) @function.name
            body: (statement_block) @function.body) @function.def
    """
}

def get_query(lang: LanguageType) -> str:
    return QUERIES.get(lang, "")
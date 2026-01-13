"""
Language detection utility for determining programming language from file extension.
"""

from typing import Optional


# Comprehensive language mapping for all languages supported by tree-sitter-languages
EXTENSION_TO_LANGUAGE = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".mts": "typescript",
    ".cts": "typescript",
    
    # Java/Kotlin
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    
    # Go
    ".go": "go",
    
    # Rust
    ".rs": "rust",
    
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".hh": "cpp",
    
    # C#
    ".cs": "c_sharp",
    
    # Ruby
    ".rb": "ruby",
    ".rake": "ruby",
    
    # PHP
    ".php": "php",
    ".phtml": "php",
    
    # Swift
    ".swift": "swift",
    
    # Scala
    ".scala": "scala",
    
    # Bash/Shell
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    
    # Lua
    ".lua": "lua",
    
    # Perl
    ".pl": "perl",
    ".pm": "perl",
    
    # Haskell
    ".hs": "haskell",
    ".lhs": "haskell",
    
    # Elixir
    ".ex": "elixir",
    ".exs": "elixir",
    
    # Elm
    ".elm": "elm",
    
    # OCaml
    ".ml": "ocaml",
    ".mli": "ocaml",
    
    # Julia
    ".jl": "julia",
    
    # R
    ".r": "r",
    ".R": "r",
    
    # YAML
    ".yaml": "yaml",
    ".yml": "yaml",
    
    # TOML
    ".toml": "toml",
    
    # JSON
    ".json": "json",
    
    # HTML/CSS
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
    
    # SQL
    ".sql": "sql",
    
    # XML
    ".xml": "xml",
    
    # Dockerfile
    "Dockerfile": "dockerfile",
    ".dockerfile": "dockerfile",
    
    # Makefile
    "Makefile": "make",
    ".mk": "make",
}


def detect_language(file_path: str) -> Optional[str]:
    """
    Detect programming language from file path/extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language identifier (e.g., 'python', 'javascript') or None if not supported
    """
    import os
    
    # Check exact filename match (e.g., Dockerfile, Makefile)
    filename = os.path.basename(file_path)
    if filename in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[filename]
    
    # Check extension
    _, ext = os.path.splitext(file_path)
    return EXTENSION_TO_LANGUAGE.get(ext.lower())


def is_supported_language(file_path: str) -> bool:
    """Check if a file's language is supported for parsing."""
    return detect_language(file_path) is not None


def get_supported_extensions() -> list[str]:
    """Get list of all supported file extensions."""
    return list(EXTENSION_TO_LANGUAGE.keys())

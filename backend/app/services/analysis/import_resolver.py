"""
Import resolution service for cross-file symbol lookup.

This module builds an import graph that maps symbol names in each file to their
definitions, handling absolute imports, relative imports, and aliased imports.

This is critical for resolving function calls like login() in api.py to the
actual definition of login() in auth.py.
"""

from typing import Dict, List, Optional, Set
import uuid
from sqlmodel import Session, select
from app.models.code_graph import CodeSymbol
import os.path
import logging

logger = logging.getLogger(__name__)


class ImportResolver:
    """
    Resolves imports to create a mapping from (file, symbol_name) -> target CodeSymbol.
    
    Handles:
    - Absolute imports: `import os.path`
    - Relative imports: `from ..utils import helper`
    - Aliased imports: `import numpy as np`
    - From imports: `from auth import login, logout`
    - JavaScript/TypeScript ES6 imports: `import { Component } from './utils'`
    """
    
    def __init__(self):
        # Import resolution map: {file_path: {symbol_name: CodeSymbol}}
        self.import_map: Dict[str, Dict[str, CodeSymbol]] = {}
        
        # Symbol cache for fast lookups: {file_path::qualified_name: CodeSymbol}
        self.symbol_cache: Dict[str, CodeSymbol] = {}
        
        # File existence cache for module resolution
        self.file_exists: Set[str] = set()
    
    def build_import_graph(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        db: Session
    ) -> Dict[str, Dict[str, CodeSymbol]]:
        """
        Build complete import resolution map for a repository.
        
        Args:
            repo_id: Repository UUID
            commit_sha: Commit SHA
            db: Database session
            
        Returns:
            Nested dict: {file_path: {symbol_name: target_CodeSymbol}}
            
        Example output:
            {
                "api.py": {
                    "login": <CodeSymbol id=... name="login" file_path="auth.py">,
                    "User": <CodeSymbol id=... name="User" file_path="models.py">
                },
                "services/handler.py": {
                    "authenticate": <CodeSymbol name="authenticate" file_path="auth.py">
                }
            }
        """
        logger.info(f"Building import graph for repo {repo_id}")
        
        # Load all symbols for this repository
        symbols = db.exec(
            select(CodeSymbol)
            .where(CodeSymbol.repo_id == repo_id)
            .where(CodeSymbol.commit_sha == commit_sha)
        ).all()
        
        logger.info(f"Loaded {len(symbols)} symbols")
        
        # Build symbol lookup cache and collect files
        symbols_by_file: Dict[str, List[CodeSymbol]] = {}
        
        for symbol in symbols:
            # Cache by qualified name for fast lookup
            cache_key = f"{symbol.file_path}::{symbol.qualified_name}"
            self.symbol_cache[cache_key] = symbol
            
            # Also cache by simple name within file
            simple_key = f"{symbol.file_path}::{symbol.name}"
            if simple_key not in self.symbol_cache:
                self.symbol_cache[simple_key] = symbol
            
            # Group by file
            if symbol.file_path not in symbols_by_file:
                symbols_by_file[symbol.file_path] = []
            symbols_by_file[symbol.file_path].append(symbol)
            
            # Track file existence
            self.file_exists.add(symbol.file_path)
        
        logger.info(f"Indexed symbols from {len(symbols_by_file)} files")
        
        # Build import map for each file
        self.import_map.clear()
        total_imports = 0
        total_resolved = 0
        
        for file_path, file_symbols in symbols_by_file.items():
            self.import_map[file_path] = {}
            
            # Find all import symbols in this file
            import_symbols = [s for s in file_symbols if s.symbol_type == "import"]
            
            for import_sym in import_symbols:
                resolved = self._resolve_import(
                    import_sym, file_path, symbols_by_file
                )
                self.import_map[file_path].update(resolved)
                total_imports += 1
                total_resolved += len(resolved)
        
        logger.info(
            f"Import graph built: {total_imports} import statements, "
            f"{total_resolved} symbols resolved across {len(self.import_map)} files"
        )
        
        return self.import_map
    
    def _resolve_import(
        self,
        import_symbol: CodeSymbol,
        current_file: str,
        symbols_by_file: Dict[str, List[CodeSymbol]]
    ) -> Dict[str, CodeSymbol]:
        """
        Resolve a single import statement to symbol mappings.
        
        Args:
            import_symbol: CodeSymbol with type="import"
            current_file: File containing the import
            symbols_by_file: All symbols grouped by file
            
        Returns:
            Dict mapping local names to target CodeSymbols
        """
        metadata = import_symbol.extra_metadata or {}
        module = import_symbol.name  # e.g., "auth" or "utils.helpers"
        is_from_import = metadata.get("is_from_import", False)
        imported_names = metadata.get("imported_names", [])
        alias = metadata.get("alias")
        language = metadata.get("language", "python")
        
        result = {}
        
        # Resolve module path to actual file
        target_file = self._module_to_file_path(module, current_file, language)
        
        if not target_file or target_file not in symbols_by_file:
            logger.debug(
                f"Cannot resolve module '{module}' from {current_file} "
                f"(tried {target_file})"
            )
            return result
        
        target_symbols = symbols_by_file[target_file]
        
        if is_from_import and imported_names:
            # from auth import login, logout
            for name in imported_names:
                # Find symbol in target file
                symbol = self._find_symbol_in_file(name, target_symbols)
                if symbol:
                    result[name] = symbol
                    logger.debug(f"Resolved '{name}' from {module} -> {symbol.qualified_name}")
                else:
                    logger.debug(f"Could not find '{name}' in {target_file}")
        
        elif alias:
            # import auth as a
            # For now, we don't create synthetic module symbols
            # This could be enhanced to handle module-level references
            logger.debug(f"Alias import '{module} as {alias}' in {current_file} (not fully resolved)")
        
        else:
            # import auth
            # Similar limitation - would need module symbol support
            logger.debug(f"Module import '{module}' in {current_file} (not fully resolved)")
        
        return result
    
    def _module_to_file_path(
        self,
        module: str,
        current_file: str,
        language: str = "python"
    ) -> Optional[str]:
        """
        Convert module name to file path.
        
        Args:
            module: Module name (e.g., "auth", "utils.helpers", "./config")
            current_file: File containing the import
            language: Programming language
            
        Returns:
            Resolved file path, or None if not found
            
        Examples (Python):
            "auth" from "api.py" -> "auth.py"
            "utils.helpers" from "api.py" -> "utils/helpers.py"
            "..config" from "app/services/api.py" -> "app/config.py"
            
        Examples (JavaScript):
            "./auth" from "api.js" -> "auth.js"
            "../utils/helper" from "src/api.js" -> "src/utils/helper.js"
        """
        if language == "python":
            return self._resolve_python_module(module, current_file)
        elif language in ["javascript", "typescript", "tsx"]:
            return self._resolve_js_module(module, current_file)
        else:
            logger.warning(f"Unsupported language for import resolution: {language}")
            return None
    
    def _resolve_python_module(
        self,
        module: str,
        current_file: str
    ) -> Optional[str]:
        """Resolve Python module to file path."""
        # Handle relative imports
        if module.startswith('.'):
            return self._resolve_relative_import(module, current_file, '.py')
        
        # Handle absolute imports
        # Try direct file path
        candidates = [
            module.replace('.', '/') + '.py',
            module.replace('.', '/') + '/__init__.py',
        ]
        
        for candidate in candidates:
            if candidate in self.file_exists:
                return candidate
        
        logger.debug(f"Python module '{module}' not found (tried {candidates})")
        return None
    
    def _resolve_js_module(
        self,
        module: str,
        current_file: str
    ) -> Optional[str]:
        """Resolve JavaScript/TypeScript module to file path."""
        # Relative imports: ./file or ../file
        if module.startswith('.'):
            # Remove leading ./
            base_path = module
            
            # Try with various extensions
            current_dir = os.path.dirname(current_file)
            potential_path = os.path.normpath(os.path.join(current_dir, base_path))
            
            extensions = ['.js', '.ts', '.tsx', '.jsx', '/index.js', '/index.ts']
            for ext in extensions:
                candidate = potential_path + ext
                # Normalize path separators
                candidate = candidate.replace('\\', '/')
                if candidate in self.file_exists:
                    return candidate
        
        # Absolute imports (e.g., from node_modules) - skip for now
        logger.debug(f"JS module '{module}' not found or is external")
        return None
    
    def _resolve_relative_import(
        self,
        module: str,
        current_file: str,
        extension: str = '.py'
    ) -> Optional[str]:
        """
        Resolve relative import like "..utils" from "app/services/api.py".
        
        Each leading '.' goes up one directory.
        
        Args:
            module: Relative module string (e.g., "..utils", ".config")
            current_file: File containing the import
            extension: File extension to append
            
        Returns:
            Resolved file path or None
        """
        current_dir = os.path.dirname(current_file)
        
        # Count leading dots
        level = 0
        for char in module:
            if char == '.':
                level += 1
            else:
                break
        
        # Go up 'level - 1' directories (one dot means current directory)
        target_dir = current_dir
        for _ in range(level - 1):
            target_dir = os.path.dirname(target_dir)
        
        # Remaining part after dots
        remaining = module[level:]
        
        if remaining:
            # Module with name
            module_path = remaining.replace('.', '/')
            candidate_file = os.path.join(target_dir, module_path + extension)
            candidate_init = os.path.join(target_dir, module_path, '__init__' + extension)
            
            # Normalize separators
            candidate_file = candidate_file.replace('\\', '/')
            candidate_init = candidate_init.replace('\\', '/')
            
            if candidate_file in self.file_exists:
                return candidate_file
            elif candidate_init in self.file_exists:
                return candidate_init
        else:
            # Just dots, points to __init__.py in parent
            candidate = os.path.join(target_dir, '__init__' + extension)
            candidate = candidate.replace('\\', '/')
            if candidate in self.file_exists:
                return candidate
        
        return None
    
    def _find_symbol_in_file(
        self,
        name: str,
        symbols: List[CodeSymbol]
    ) -> Optional[CodeSymbol]:
        """
        Find a symbol by name in a list of symbols.
        
        Tries:
        1. Exact name match
        2. Qualified name ending with .name (for class methods)
        """
        for symbol in symbols:
            if symbol.name == name:
                return symbol
        
        # Try qualified name match for methods/nested symbols
        for symbol in symbols:
            if symbol.qualified_name.endswith(f".{name}"):
                return symbol
        
        return None
    
    def clear_cache(self):
        """Clear all caches. Call between repository analyses."""
        self.import_map.clear()
        self.symbol_cache.clear()
        self.file_exists.clear()
        logger.debug("ImportResolver cache cleared")

"""
Migration script to enable PostgreSQL extensions for code symbol indexing.

This script should be run once during initial setup or when upgrading.
It enables:
- pg_trgm: For fuzzy text search on symbol names
- btree_gist: For advanced indexing capabilities
"""

from sqlalchemy import text
from app.db.session import engine


def apply_extensions():
    """Enable PostgreSQL extensions required for code graph functionality."""
    with engine.begin() as conn:
        # Enable pg_trgm for fuzzy symbol search
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        print("✓ Enabled pg_trgm extension")
        
        # Enable btree_gist for advanced indexing
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))
        print("✓ Enabled btree_gist extension")
        
        # Create GIN index on code_symbol.name for efficient fuzzy search
        # This will be created after tables exist
        print("✓ Extensions enabled successfully")


def create_gin_indexes():
    """Create GIN indexes for fuzzy search after tables are created."""
    with engine.begin() as conn:
        try:
            # GIN index for fuzzy name search using pg_trgm
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_code_symbol_name_gin 
                ON code_symbol USING gin (name gin_trgm_ops);
            """))
            print("✓ Created GIN index on code_symbol.name")
            
            # GIN index for qualified_name search
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_code_symbol_qualified_name_gin 
                ON code_symbol USING gin (qualified_name gin_trgm_ops);
            """))
            print("✓ Created GIN index on code_symbol.qualified_name")
            
        except Exception as e:
            print(f"Note: GIN indexes might already exist or tables not created yet: {e}")


if __name__ == "__main__":
    print("Applying PostgreSQL extensions for CodeSense static analysis...")
    apply_extensions()
    print("\nExtensions applied successfully!")
    print("Note: Run create_gin_indexes() after creating database tables.")

"""
Database factory to get the appropriate database manager based on configuration.
"""

from config import get_settings

# Cache the database manager instance to reuse connections
_db_manager_cache = None


def get_database_manager():
    """
    Get the appropriate database manager based on configuration.
    Returns a cached instance to reuse database connections.
    
    Returns:
        DatabaseManager or PostgresManager instance
    """
    global _db_manager_cache
    
    # Return cached instance if available
    if _db_manager_cache is not None:
        return _db_manager_cache
    
    settings = get_settings()
    
    if settings.use_postgres and settings.database_url:
        print("Postgres database selected")
        from src.database.postgres_manager import PostgresManager
        _db_manager_cache = PostgresManager()
    else:
        print("SQLite database selected")
        from src.database.db_manager import DatabaseManager
        _db_manager_cache = DatabaseManager()
    
    return _db_manager_cache

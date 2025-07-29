"""
Database abstraction layer package.
"""

from .interfaces import (
    BaseEntity,
    DatabaseConnection,
    DatabaseTransaction,
    BaseRepository,
    QueryBuilder,
    DatabaseFactory
)

# Legacy imports for backward compatibility
from .base import Base, get_database, engine, AsyncSessionLocal

__all__ = [
    'BaseEntity',
    'DatabaseConnection', 
    'DatabaseTransaction',
    'BaseRepository',
    'QueryBuilder',
    'DatabaseFactory',
    # Legacy
    "Base", 
    "get_database", 
    "engine", 
    "AsyncSessionLocal"
]

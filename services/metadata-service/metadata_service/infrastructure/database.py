"""
Database Configuration and Connection Management

BUSINESS REQUIREMENT:
Manage PostgreSQL database connections with connection pooling
and proper lifecycle management.

DESIGN PATTERN:
Singleton connection pool with async context management
"""

import asyncpg
import os
from typing import Optional


# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_database_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool

    SINGLETON PATTERN:
    Ensures single connection pool instance per application

    Returns:
        asyncpg connection pool

    Raises:
        RuntimeError: If database configuration is missing
    """
    global _pool

    if _pool is None:
        # Get database configuration from environment
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', '5432'))  # Changed from 5433 to 5432 for container
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'postgres_password')
        db_name = os.getenv('DB_NAME', 'course_creator')

        # Create connection pool with connection timeout
        _pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            min_size=1,  # Reduced from 2 for faster startup
            max_size=10,
            command_timeout=60,
            timeout=10  # Connection timeout in seconds
        )

    return _pool


async def close_database_pool():
    """
    Close database connection pool

    CLEANUP:
    Should be called on application shutdown
    """
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None

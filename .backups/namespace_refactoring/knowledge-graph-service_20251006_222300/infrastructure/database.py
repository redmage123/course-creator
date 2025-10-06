"""
Database Connection Management

BUSINESS REQUIREMENT:
Provide robust database connection pooling for knowledge graph queries

TECHNICAL IMPLEMENTATION:
- asyncpg connection pool
- Configuration management
- Health checking
- Graceful shutdown

WHY:
Connection pooling is critical for performance and scalability
"""

import asyncpg
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_database_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool

    BUSINESS VALUE:
    Reuses connections for better performance

    Returns:
        asyncpg.Pool: Database connection pool
    """
    global _pool

    if _pool is None:
        _pool = await create_pool()

    return _pool


async def create_pool() -> asyncpg.Pool:
    """
    Create new database connection pool

    CONFIGURATION:
    - Host: DB_HOST environment variable
    - Port: DB_PORT environment variable
    - User: DB_USER environment variable
    - Password: DB_PASSWORD environment variable
    - Database: DB_NAME environment variable

    Returns:
        asyncpg.Pool: Database connection pool
    """
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '5433'))
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres_password')
    db_name = os.getenv('DB_NAME', 'course_creator')

    try:
        pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            min_size=2,
            max_size=10,
            command_timeout=60
        )

        logger.info(f"Database pool created: {db_host}:{db_port}/{db_name}")
        return pool

    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise


async def close_database_pool():
    """
    Close database connection pool gracefully

    WHY: Ensures clean shutdown and resource cleanup
    """
    global _pool

    if _pool is not None:
        await _pool.close()
        logger.info("Database pool closed")
        _pool = None


async def check_database_health() -> bool:
    """
    Check database connection health

    Returns:
        bool: True if database is accessible
    """
    try:
        pool = await get_database_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval('SELECT 1')
            return result == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

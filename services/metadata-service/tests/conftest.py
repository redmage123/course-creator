"""
Pytest configuration and fixtures for metadata service tests

BUSINESS REQUIREMENT:
Provide test fixtures for database connections, sample data, and test utilities
"""

import pytest
import pytest_asyncio
import asyncpg
import os


@pytest_asyncio.fixture(scope="function")
async def postgresql_pool():
    """
    Create PostgreSQL connection pool for tests

    SCOPE: function - Create fresh pool for each test

    Returns:
        asyncpg.Pool: Database connection pool
    """
    db_url = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://postgres:postgres_password@localhost:5433/course_creator'
    )

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)

    yield pool

    await pool.close()

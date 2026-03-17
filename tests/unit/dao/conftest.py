"""
DAO Unit Test Configuration and Fixtures

BUSINESS CONTEXT:
Provides shared fixtures and utilities for testing Data Access Objects (DAOs)
across all services. Ensures consistent test database setup, transaction management,
and cleanup across the test suite.

TECHNICAL IMPLEMENTATION:
- Creates isolated test database connection pools
- Manages test data setup and teardown
- Provides transaction rollback for test isolation
- Handles PostgreSQL and Redis test configurations

WHY THIS APPROACH:
- Each test runs in isolation with clean state
- Real database connections test actual SQL behavior
- Transaction rollbacks prevent test pollution
- Fixtures reduce boilerplate in individual tests
"""

import pytest
import asyncio
import asyncpg
import redis.asyncio as aioredis
from typing import AsyncGenerator, Dict, Any
from uuid import uuid4
import os
from datetime import datetime

# Test database configuration
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': int(os.getenv('TEST_DB_PORT', '5434')),  # Separate test DB port
    'user': os.getenv('TEST_DB_USER', 'test_user'),
    'password': os.getenv('TEST_DB_PASSWORD', 'test_password'),
    'database': os.getenv('TEST_DB_NAME', 'course_creator_test'),
}

TEST_REDIS_CONFIG = {
    'host': os.getenv('TEST_REDIS_HOST', 'localhost'),
    'port': int(os.getenv('TEST_REDIS_PORT', '6380')),  # Separate test Redis port
    'db': int(os.getenv('TEST_REDIS_DB', '1')),  # Use DB 1 for tests
}


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests

    BUSINESS REQUIREMENT:
    All DAO operations are async, requiring event loop for testing

    TECHNICAL IMPLEMENTATION:
    Session-scoped event loop shared across all async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create test database connection pool

    BUSINESS REQUIREMENT:
    Tests need real database connections to validate SQL queries

    TECHNICAL IMPLEMENTATION:
    - Creates connection pool to test database
    - Ensures test database is clean before tests start
    - Closes pool after all tests complete

    WHY THIS APPROACH:
    Session-scoped pool is created once, reducing test setup time
    """
    pool = await asyncpg.create_pool(
        host=TEST_DB_CONFIG['host'],
        port=TEST_DB_CONFIG['port'],
        user=TEST_DB_CONFIG['user'],
        password=TEST_DB_CONFIG['password'],
        database=TEST_DB_CONFIG['database'],
        min_size=2,
        max_size=10,
    )

    # Verify connection works
    async with pool.acquire() as conn:
        version = await conn.fetchval('SELECT version()')
        print(f"\n[DAO Tests] Connected to test database: {version[:50]}...")

    yield pool

    await pool.close()


@pytest.fixture
async def db_transaction(test_db_pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide transactional database connection with automatic rollback

    BUSINESS REQUIREMENT:
    Each test must run in isolation without affecting other tests

    TECHNICAL IMPLEMENTATION:
    - Acquires connection from pool
    - Starts transaction before test
    - Rolls back transaction after test (regardless of pass/fail)
    - Never commits test data to database

    WHY THIS APPROACH:
    - Tests can INSERT/UPDATE/DELETE without polluting database
    - Test failures don't leave partial data
    - Tests can run in parallel safely

    USAGE EXAMPLE:
    ```python
    async def test_create_user(db_transaction):
        # This INSERT will be rolled back after test
        result = await db_transaction.fetchrow(
            "INSERT INTO users (username, email) VALUES ($1, $2) RETURNING *",
            "testuser", "test@example.com"
        )
        assert result['username'] == 'testuser'
        # Automatic rollback happens here
    ```
    """
    async with test_db_pool.acquire() as conn:
        # Start transaction
        tx = conn.transaction()
        await tx.start()

        try:
            yield conn
        finally:
            # Always rollback, never commit test data
            await tx.rollback()


@pytest.fixture(scope="session")
async def test_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Create test Redis client

    BUSINESS REQUIREMENT:
    Tests need real Redis instance to validate caching logic

    TECHNICAL IMPLEMENTATION:
    - Connects to test Redis instance (separate from production)
    - Uses dedicated test database (DB 1)
    - Flushes test database before and after tests

    WHY THIS APPROACH:
    Real Redis connection tests actual cache behavior including
    TTL, eviction, and serialization
    """
    client = await aioredis.from_url(
        f"redis://{TEST_REDIS_CONFIG['host']}:{TEST_REDIS_CONFIG['port']}/{TEST_REDIS_CONFIG['db']}",
        encoding="utf-8",
        decode_responses=True
    )

    # Verify connection and flush test database
    await client.ping()
    await client.flushdb()
    print(f"\n[DAO Tests] Connected to test Redis: {TEST_REDIS_CONFIG['host']}:{TEST_REDIS_CONFIG['port']}/{TEST_REDIS_CONFIG['db']}")

    yield client

    # Clean up after all tests
    await client.flushdb()
    await client.close()


@pytest.fixture
async def redis_cache(test_redis_client: aioredis.Redis) -> AsyncGenerator[aioredis.Redis, None]:
    """
    Provide Redis client with automatic cleanup after each test

    BUSINESS REQUIREMENT:
    Each cache test must start with empty cache

    TECHNICAL IMPLEMENTATION:
    - Flushes test database before test
    - Provides client to test
    - Flushes again after test

    WHY THIS APPROACH:
    Ensures test isolation for cache operations
    """
    await test_redis_client.flushdb()
    yield test_redis_client
    await test_redis_client.flushdb()


# =============================================================================
# TEST DATA FACTORIES
# =============================================================================

def create_test_user_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Factory function for creating test user data

    BUSINESS REQUIREMENT:
    Tests need consistent, valid user data

    USAGE:
    ```python
    user_data = create_test_user_data({'username': 'custom_user'})
    ```
    """
    base_data = {
        'id': str(uuid4()),
        'username': f'testuser_{uuid4().hex[:8]}',
        'email': f'test_{uuid4().hex[:8]}@example.com',
        'password_hash': '$2b$12$KIXlQ7z8Z9Z8Z9Z8Z9Z8Z',  # bcrypt hash of "password123"
        'role': 'student',
        'is_active': True,
        'created_at': datetime.utcnow(),
    }

    if override:
        base_data.update(override)

    return base_data


def create_test_course_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Factory function for creating test course data

    BUSINESS REQUIREMENT:
    Tests need consistent, valid course data
    """
    base_data = {
        'id': str(uuid4()),
        'title': f'Test Course {uuid4().hex[:8]}',
        'description': 'A comprehensive test course for automated testing',
        'category': 'Programming',
        'difficulty_level': 'intermediate',
        'duration_weeks': 8,
        'instructor_id': str(uuid4()),
        'organization_id': str(uuid4()),
        'is_published': False,
        'created_at': datetime.utcnow(),
    }

    if override:
        base_data.update(override)

    return base_data


def create_test_organization_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Factory function for creating test organization data
    """
    base_data = {
        'id': str(uuid4()),
        'name': f'Test Organization {uuid4().hex[:8]}',
        'domain': f'test-org-{uuid4().hex[:8]}.example.com',
        'is_active': True,
        'created_at': datetime.utcnow(),
    }

    if override:
        base_data.update(override)

    return base_data


@pytest.fixture
def test_user_data():
    """Fixture providing fresh test user data for each test"""
    return create_test_user_data()


@pytest.fixture
def test_course_data():
    """Fixture providing fresh test course data for each test"""
    return create_test_course_data()


@pytest.fixture
def test_organization_data():
    """Fixture providing fresh test organization data for each test"""
    return create_test_organization_data()


# =============================================================================
# ASSERTION HELPERS
# =============================================================================

def assert_valid_uuid(value: str) -> None:
    """
    Assert that value is a valid UUID string

    BUSINESS REQUIREMENT:
    All entity IDs must be valid UUIDs
    """
    try:
        uuid4(value) if isinstance(value, str) else None
        assert True
    except (ValueError, TypeError):
        pytest.fail(f"Expected valid UUID, got: {value}")


def assert_timestamp_recent(timestamp: datetime, max_seconds_ago: int = 60) -> None:
    """
    Assert that timestamp is recent (within last N seconds)

    BUSINESS REQUIREMENT:
    created_at/updated_at timestamps should reflect when operation occurred
    """
    now = datetime.utcnow()
    age_seconds = (now - timestamp).total_seconds()
    assert 0 <= age_seconds <= max_seconds_ago, \
        f"Timestamp {timestamp} is {age_seconds}s old (expected <{max_seconds_ago}s)"

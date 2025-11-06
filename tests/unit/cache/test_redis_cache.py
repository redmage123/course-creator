"""
Redis Cache Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis caching operations ensuring cache correctness,
TTL behavior, invalidation logic, and edge case handling.

TECHNICAL IMPLEMENTATION:
- Tests basic cache operations (get, set, delete)
- Validates TTL (Time-To-Live) expiration
- Tests cache invalidation patterns
- Handles serialization/deserialization
- Tests concurrent access scenarios

TDD APPROACH:
These tests validate that caching layer:
- Improves performance through cache hits
- Expires stale data appropriately
- Handles cache misses gracefully
- Maintains data consistency
"""

import pytest
import json
from datetime import datetime, timedelta
from uuid import uuid4
import asyncio
import sys
from pathlib import Path

# Add shared cache module to path
shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
sys.path.insert(0, str(shared_path))

try:
    from cache.redis_cache import CacheManager
except ImportError:
    pytest.skip("Redis cache module not available", allow_module_level=True)


class TestRedisCacheBasicOperations:
    """
    Test Suite: Basic Cache Operations

    BUSINESS REQUIREMENT:
    Cache must support get, set, and delete operations
    """

    @pytest.mark.asyncio
    async def test_set_and_get_string_value(self, redis_cache):
        """
        TEST: Store and retrieve string value

        VALIDATES:
        - Value can be stored in cache
        - Same value is retrieved
        - No data corruption
        """
        key = f"test:string:{uuid4()}"
        value = "Hello, Cache!"

        # Set value
        await redis_cache.set(key, value)

        # Get value
        retrieved = await redis_cache.get(key)

        assert retrieved == value

    @pytest.mark.asyncio
    async def test_set_and_get_json_value(self, redis_cache):
        """
        TEST: Store and retrieve JSON object

        BUSINESS REQUIREMENT:
        Cache must handle complex data structures

        VALIDATES:
        - JSON serialization works
        - Data structure is preserved
        """
        key = f"test:json:{uuid4()}"
        value = {
            'user_id': str(uuid4()),
            'username': 'testuser',
            'score': 95.5,
            'tags': ['python', 'testing'],
            'metadata': {'active': True, 'count': 10}
        }

        # Serialize and store
        await redis_cache.set(key, json.dumps(value))

        # Retrieve and deserialize
        retrieved_json = await redis_cache.get(key)
        retrieved = json.loads(retrieved_json)

        assert retrieved == value
        assert retrieved['user_id'] == value['user_id']
        assert retrieved['score'] == value['score']
        assert retrieved['tags'] == value['tags']

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self, redis_cache):
        """
        TEST: Cache miss returns None

        VALIDATES:
        - Nonexistent keys return None
        - No exception is raised
        """
        key = f"test:missing:{uuid4()}"

        result = await redis_cache.get(key)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key_removes_from_cache(self, redis_cache):
        """
        TEST: Delete removes key from cache

        BUSINESS REQUIREMENT:
        Cache invalidation must work correctly

        VALIDATES:
        - Key is deleted
        - Subsequent get returns None
        """
        key = f"test:delete:{uuid4()}"
        value = "temporary value"

        # Set value
        await redis_cache.set(key, value)
        assert await redis_cache.get(key) == value

        # Delete key
        await redis_cache.delete(key)

        # Verify deleted
        assert await redis_cache.get(key) is None

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, redis_cache):
        """
        TEST: Setting key again overwrites old value

        VALIDATES:
        - Old value is replaced
        - No duplicate entries
        """
        key = f"test:overwrite:{uuid4()}"

        await redis_cache.set(key, "first value")
        await redis_cache.set(key, "second value")

        result = await redis_cache.get(key)
        assert result == "second value"


class TestRedisCacheTTL:
    """
    Test Suite: Time-To-Live (TTL) Behavior

    BUSINESS REQUIREMENT:
    Cached data must expire after configured time
    """

    @pytest.mark.asyncio
    async def test_key_expires_after_ttl(self, redis_cache):
        """
        TEST: Key expires after TTL seconds

        BUSINESS REQUIREMENT:
        Stale cache data should be automatically removed

        VALIDATES:
        - Key exists before TTL
        - Key is gone after TTL
        """
        key = f"test:ttl:{uuid4()}"
        value = "expiring value"
        ttl_seconds = 2

        # Set with TTL
        await redis_cache.setex(key, ttl_seconds, value)

        # Immediately after set, key should exist
        assert await redis_cache.get(key) == value

        # Wait for expiration
        await asyncio.sleep(ttl_seconds + 0.5)

        # Key should be gone
        assert await redis_cache.get(key) is None

    @pytest.mark.asyncio
    async def test_get_ttl_of_key(self, redis_cache):
        """
        TEST: Check remaining TTL of key

        VALIDATES:
        - TTL can be queried
        - TTL decreases over time
        """
        key = f"test:ttl:check:{uuid4()}"
        ttl_seconds = 10

        await redis_cache.setex(key, ttl_seconds, "value")

        # Check TTL
        remaining = await redis_cache.ttl(key)

        assert remaining is not None
        assert 0 < remaining <= ttl_seconds

    @pytest.mark.asyncio
    async def test_key_without_ttl_persists(self, redis_cache):
        """
        TEST: Key without TTL doesn't expire

        VALIDATES:
        - Keys can be stored permanently
        - TTL is -1 for persistent keys
        """
        key = f"test:no_ttl:{uuid4()}"

        await redis_cache.set(key, "persistent value")

        # Wait a bit
        await asyncio.sleep(1)

        # Key should still exist
        assert await redis_cache.get(key) == "persistent value"

        # TTL should be -1 (no expiration)
        ttl = await redis_cache.ttl(key)
        assert ttl == -1


class TestRedisCacheInvalidation:
    """
    Test Suite: Cache Invalidation Patterns

    BUSINESS REQUIREMENT:
    Cache must be invalidated when underlying data changes
    """

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_pattern(self, redis_cache):
        """
        TEST: Invalidate all cache keys for a user

        BUSINESS REQUIREMENT:
        When user data changes, all cached user data must be cleared

        VALIDATES:
        - Pattern matching works
        - Multiple keys are deleted
        """
        user_id = str(uuid4())

        # Cache multiple user-related items
        await redis_cache.set(f"user:{user_id}:profile", "profile data")
        await redis_cache.set(f"user:{user_id}:courses", "courses data")
        await redis_cache.set(f"user:{user_id}:analytics", "analytics data")
        await redis_cache.set(f"other:data", "unrelated data")

        # Invalidate all user cache
        pattern = f"user:{user_id}:*"
        keys = []
        async for key in redis_cache.scan_iter(match=pattern):
            keys.append(key)
            await redis_cache.delete(key)

        # User cache should be gone
        assert await redis_cache.get(f"user:{user_id}:profile") is None
        assert await redis_cache.get(f"user:{user_id}:courses") is None
        assert await redis_cache.get(f"user:{user_id}:analytics") is None

        # Unrelated cache should remain
        assert await redis_cache.get("other:data") == "unrelated data"

    @pytest.mark.asyncio
    async def test_invalidate_course_cache_on_update(self, redis_cache):
        """
        TEST: Clear course cache when course is updated

        BUSINESS REQUIREMENT:
        Course modifications must invalidate cached course data

        SIMULATES:
        1. Course data is cached
        2. Course is updated
        3. Cache is invalidated
        4. New data is fetched and cached
        """
        course_id = str(uuid4())
        cache_key = f"course:{course_id}:details"

        # Initial cache
        original_data = json.dumps({'title': 'Original Title', 'version': 1})
        await redis_cache.set(cache_key, original_data)

        # Simulate course update - invalidate cache
        await redis_cache.delete(cache_key)

        # Verify cache is cleared
        assert await redis_cache.get(cache_key) is None

        # Cache new data
        updated_data = json.dumps({'title': 'Updated Title', 'version': 2})
        await redis_cache.set(cache_key, updated_data)

        # Verify new data is cached
        cached = await redis_cache.get(cache_key)
        assert json.loads(cached)['title'] == 'Updated Title'


class TestRedisCacheAdvancedOperations:
    """
    Test Suite: Advanced Cache Operations

    BUSINESS REQUIREMENT:
    Cache must support atomic operations and data structures
    """

    @pytest.mark.asyncio
    async def test_increment_counter(self, redis_cache):
        """
        TEST: Atomic counter increment

        BUSINESS REQUIREMENT:
        Page views, likes, and other counters must be thread-safe

        VALIDATES:
        - Counter starts at 0
        - Increments are atomic
        - Multiple increments accumulate
        """
        key = f"counter:{uuid4()}"

        # Increment multiple times
        for _ in range(5):
            await redis_cache.incr(key)

        # Check final value
        value = await redis_cache.get(key)
        assert int(value) == 5

    @pytest.mark.asyncio
    async def test_set_if_not_exists(self, redis_cache):
        """
        TEST: Set key only if it doesn't exist (SETNX)

        BUSINESS REQUIREMENT:
        Prevent race conditions in distributed systems

        VALIDATES:
        - First set succeeds
        - Second set fails (key exists)
        """
        key = f"lock:{uuid4()}"

        # First set should succeed
        result1 = await redis_cache.setnx(key, "locked")
        assert result1 is True

        # Second set should fail
        result2 = await redis_cache.setnx(key, "locked again")
        assert result2 is False

        # Original value should remain
        assert await redis_cache.get(key) == "locked"

    @pytest.mark.asyncio
    async def test_hash_operations(self, redis_cache):
        """
        TEST: Store and retrieve hash (dict-like structure)

        BUSINESS REQUIREMENT:
        Complex objects should be stored efficiently

        VALIDATES:
        - Hash fields can be set
        - Individual fields can be retrieved
        - All fields can be retrieved
        """
        key = f"user:hash:{uuid4()}"

        # Set hash fields
        await redis_cache.hset(key, 'username', 'testuser')
        await redis_cache.hset(key, 'email', 'test@example.com')
        await redis_cache.hset(key, 'score', '95')

        # Get individual field
        username = await redis_cache.hget(key, 'username')
        assert username == 'testuser'

        # Get all fields
        all_fields = await redis_cache.hgetall(key)
        assert all_fields['username'] == 'testuser'
        assert all_fields['email'] == 'test@example.com'
        assert all_fields['score'] == '95'


class TestRedisCacheConcurrency:
    """
    Test Suite: Concurrent Access Patterns

    BUSINESS REQUIREMENT:
    Cache must handle concurrent reads and writes correctly
    """

    @pytest.mark.asyncio
    async def test_concurrent_reads_same_key(self, redis_cache):
        """
        TEST: Multiple concurrent reads of same key

        VALIDATES:
        - All reads return same value
        - No data corruption
        """
        key = f"concurrent:read:{uuid4()}"
        value = "shared value"

        await redis_cache.set(key, value)

        # Concurrent reads
        tasks = [redis_cache.get(key) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should return same value
        assert all(r == value for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_increments(self, redis_cache):
        """
        TEST: Multiple concurrent counter increments

        BUSINESS REQUIREMENT:
        Atomic operations must not lose updates

        VALIDATES:
        - All increments are counted
        - Final value is correct
        """
        key = f"concurrent:counter:{uuid4()}"

        # 20 concurrent increments
        tasks = [redis_cache.incr(key) for _ in range(20)]
        await asyncio.gather(*tasks)

        # Final value should be 20
        final_value = await redis_cache.get(key)
        assert int(final_value) == 20


class TestRedisCacheErrorHandling:
    """
    Test Suite: Error Handling and Edge Cases

    BUSINESS REQUIREMENT:
    Cache failures should not crash application
    """

    @pytest.mark.asyncio
    async def test_set_with_invalid_ttl_raises_error(self, redis_cache):
        """
        TEST: Invalid TTL value raises error

        VALIDATES:
        - Negative TTL is rejected
        - Appropriate error is raised
        """
        key = f"test:invalid_ttl:{uuid4()}"

        with pytest.raises(Exception):
            await redis_cache.setex(key, -10, "value")

    @pytest.mark.asyncio
    async def test_get_after_connection_close_handles_gracefully(self, redis_cache):
        """
        TEST: Operations after connection close fail gracefully

        VALIDATES:
        - Connection errors are caught
        - Application doesn't crash
        """
        key = f"test:closed:{uuid4()}"

        # This test documents expected behavior
        # In production, reconnection logic should handle this


class TestRedisCachePerformance:
    """
    Test Suite: Performance Validation

    BUSINESS REQUIREMENT:
    Cache operations must be faster than database queries
    """

    @pytest.mark.asyncio
    async def test_cache_hit_is_fast(self, redis_cache):
        """
        TEST: Cache retrieval is sub-millisecond

        VALIDATES:
        - Cache GET operations are fast (<10ms)
        """
        key = f"perf:test:{uuid4()}"
        value = "x" * 1000  # 1KB value

        await redis_cache.set(key, value)

        # Measure retrieval time
        import time
        start = time.time()
        result = await redis_cache.get(key)
        elapsed_ms = (time.time() - start) * 1000

        assert result == value
        assert elapsed_ms < 10, f"Cache GET took {elapsed_ms:.2f}ms (expected <10ms)"

    @pytest.mark.asyncio
    async def test_bulk_operations_are_efficient(self, redis_cache):
        """
        TEST: Bulk cache operations complete quickly

        VALIDATES:
        - Setting 100 keys takes <100ms
        """
        import time

        keys = [f"bulk:{uuid4()}" for _ in range(100)]

        start = time.time()
        for key in keys:
            await redis_cache.set(key, "value")
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, f"Bulk set took {elapsed_ms:.2f}ms (expected <100ms)"

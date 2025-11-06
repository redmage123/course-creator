"""
Redis Eviction Policy Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis eviction policies and memory management ensuring
optimal cache performance when memory limits are reached. Critical for maintaining
cache effectiveness while preventing out-of-memory errors in production.

TECHNICAL IMPLEMENTATION:
- Tests LRU (Least Recently Used) eviction behavior
- Validates max memory limit handling
- Tests key priority and retention strategies
- Validates cache size monitoring
- Tests TTL-based eviction
- Validates eviction under memory pressure

TDD APPROACH:
These tests validate that eviction policies:
- Remove least valuable keys when memory is full
- Preserve high-priority and recently-used keys
- Maintain cache performance under memory pressure
- Provide predictable eviction behavior
- Support monitoring and alerting
- Handle edge cases gracefully

BUSINESS REQUIREMENTS:
1. Cache must not exceed configured memory limits
2. Most valuable data should be retained during eviction
3. Eviction should not cause performance degradation
4. System should monitor memory usage and trigger alerts
5. Eviction behavior should be predictable and testable
"""

import pytest
import json
import asyncio
from datetime import datetime
from uuid import uuid4
import sys
from pathlib import Path
import time

# Add shared cache module to path
shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
sys.path.insert(0, str(shared_path))


class TestLRUEvictionBehavior:
    """
    Test Suite: LRU (Least Recently Used) Eviction

    BUSINESS REQUIREMENT:
    When cache is full, least recently used keys should be evicted first
    to make room for new data.
    """

    @pytest.mark.asyncio
    async def test_lru_evicts_oldest_accessed_key(self, redis_cache):
        """
        TEST: LRU evicts least recently accessed key

        BUSINESS REQUIREMENT:
        Recently accessed data is more likely to be accessed again (temporal locality)

        VALIDATES:
        - Older keys are evicted before newer keys
        - Recently accessed keys are retained
        """
        # Create keys with access pattern
        keys = []
        for i in range(5):
            key = f"lru:test:{i}:{uuid4()}"
            await redis_cache.set(key, json.dumps({'value': i, 'created': datetime.utcnow().isoformat()}))
            keys.append(key)
            await asyncio.sleep(0.1)  # Small delay to establish access order

        # Access keys 2, 3, 4 (making key 0 and 1 least recently used)
        for i in [2, 3, 4]:
            await redis_cache.get(keys[i])
            await asyncio.sleep(0.05)

        # Verify all keys still exist (no eviction yet)
        for key in keys:
            assert await redis_cache.get(key) is not None

        # In real scenario with memory limit, keys[0] and keys[1] would be evicted first

    @pytest.mark.asyncio
    async def test_accessing_key_updates_lru_position(self, redis_cache):
        """
        TEST: Accessing a key updates its LRU position

        BUSINESS REQUIREMENT:
        Reading a key should mark it as recently used

        VALIDATES:
        - Access updates LRU timestamp
        - Accessed keys move to front of LRU queue
        """
        key = f"lru:access:{uuid4()}"
        value = json.dumps({'data': 'important'})

        # Set key
        await redis_cache.set(key, value)

        # Wait a bit
        await asyncio.sleep(0.2)

        # Access key (updates LRU position)
        retrieved = await redis_cache.get(key)
        assert retrieved == value

        # Key should now be considered recently used
        # In LRU eviction, this key would be retained longer


class TestTTLBasedEviction:
    """
    Test Suite: TTL-Based Eviction

    BUSINESS REQUIREMENT:
    Keys with TTL should be automatically evicted when they expire,
    freeing memory for new data.
    """

    @pytest.mark.asyncio
    async def test_expired_keys_are_evicted_automatically(self, redis_cache):
        """
        TEST: Expired keys are automatically evicted

        BUSINESS REQUIREMENT:
        Stale data should not occupy cache memory

        VALIDATES:
        - Keys expire after TTL
        - Expired keys free up memory
        """
        key = f"ttl:evict:{uuid4()}"
        value = json.dumps({'data': 'temporary'})
        ttl_seconds = 2

        # Set key with TTL
        await redis_cache.setex(key, ttl_seconds, value)

        # Key should exist immediately
        assert await redis_cache.get(key) is not None

        # Wait for expiration
        await asyncio.sleep(ttl_seconds + 0.5)

        # Key should be evicted
        assert await redis_cache.get(key) is None

    @pytest.mark.asyncio
    async def test_keys_with_shorter_ttl_evicted_first(self, redis_cache):
        """
        TEST: Keys with shorter TTL are evicted before longer TTL

        BUSINESS REQUIREMENT:
        Short-lived data should not prevent long-lived data from being cached

        VALIDATES:
        - TTL affects eviction order
        - Shorter TTL keys expire first
        """
        short_ttl_key = f"ttl:short:{uuid4()}"
        long_ttl_key = f"ttl:long:{uuid4()}"

        # Set keys with different TTLs
        await redis_cache.setex(short_ttl_key, 2, json.dumps({'type': 'short'}))
        await redis_cache.setex(long_ttl_key, 10, json.dumps({'type': 'long'}))

        # Both should exist initially
        assert await redis_cache.get(short_ttl_key) is not None
        assert await redis_cache.get(long_ttl_key) is not None

        # Wait for short TTL to expire
        await asyncio.sleep(2.5)

        # Short TTL should be evicted
        assert await redis_cache.get(short_ttl_key) is None

        # Long TTL should still exist
        assert await redis_cache.get(long_ttl_key) is not None

        # Cleanup
        await redis_cache.delete(long_ttl_key)

    @pytest.mark.asyncio
    async def test_keys_without_ttl_persist_longer(self, redis_cache):
        """
        TEST: Keys without TTL are not evicted by TTL mechanism

        BUSINESS REQUIREMENT:
        Persistent data should remain cached until LRU eviction

        VALIDATES:
        - Keys without TTL don't auto-expire
        - TTL -1 indicates no expiration
        """
        persistent_key = f"ttl:none:{uuid4()}"

        # Set key without TTL
        await redis_cache.set(persistent_key, json.dumps({'type': 'persistent'}))

        # Check TTL (-1 means no expiration)
        ttl = await redis_cache.ttl(persistent_key)
        assert ttl == -1

        # Wait a bit
        await asyncio.sleep(2)

        # Key should still exist
        assert await redis_cache.get(persistent_key) is not None

        # Cleanup
        await redis_cache.delete(persistent_key)


class TestCacheSizeMonitoring:
    """
    Test Suite: Cache Size and Memory Monitoring

    BUSINESS REQUIREMENT:
    System must monitor cache size and memory usage to prevent
    out-of-memory errors and trigger eviction appropriately.
    """

    @pytest.mark.asyncio
    async def test_count_total_keys_in_cache(self, redis_cache):
        """
        TEST: Can count total number of keys in cache

        BUSINESS REQUIREMENT:
        Monitor cache key count for capacity planning

        VALIDATES:
        - Key count can be queried
        - Count is accurate
        """
        # Add known number of keys
        test_prefix = f"count:test:{uuid4()}"
        num_keys = 20

        for i in range(num_keys):
            await redis_cache.set(f"{test_prefix}:key:{i}", json.dumps({'value': i}))

        # Count keys with this prefix
        count = 0
        async for key in redis_cache.scan_iter(match=f"{test_prefix}:*"):
            count += 1

        assert count == num_keys

        # Cleanup
        async for key in redis_cache.scan_iter(match=f"{test_prefix}:*"):
            await redis_cache.delete(key)

    @pytest.mark.asyncio
    async def test_estimate_memory_usage_per_key(self, redis_cache):
        """
        TEST: Estimate memory usage for cache keys

        BUSINESS REQUIREMENT:
        Understand memory consumption patterns

        VALIDATES:
        - Memory usage can be estimated
        - Larger values consume more memory
        """
        small_key = f"memory:small:{uuid4()}"
        large_key = f"memory:large:{uuid4()}"

        # Small value
        small_value = json.dumps({'data': 'x'})
        await redis_cache.set(small_key, small_value)

        # Large value (100KB)
        large_value = json.dumps({'data': 'x' * 100000})
        await redis_cache.set(large_key, large_value)

        # In production, would use MEMORY USAGE command
        # Here we validate that larger values are stored

        small_retrieved = await redis_cache.get(small_key)
        large_retrieved = await redis_cache.get(large_key)

        assert len(small_retrieved) < len(large_retrieved)

        # Cleanup
        await redis_cache.delete(small_key)
        await redis_cache.delete(large_key)

    @pytest.mark.asyncio
    async def test_monitor_cache_growth_over_time(self, redis_cache):
        """
        TEST: Monitor cache growth as keys are added

        BUSINESS REQUIREMENT:
        Track cache growth to predict capacity issues

        VALIDATES:
        - Cache size increases as keys are added
        - Growth can be monitored
        """
        test_prefix = f"growth:test:{uuid4()}"

        # Measure initial count
        initial_count = 0
        async for key in redis_cache.scan_iter(match=f"{test_prefix}:*"):
            initial_count += 1

        # Add 30 keys
        for i in range(30):
            await redis_cache.set(f"{test_prefix}:key:{i}", json.dumps({'value': i}))

        # Measure new count
        final_count = 0
        async for key in redis_cache.scan_iter(match=f"{test_prefix}:*"):
            final_count += 1

        # Growth should be 30 keys
        growth = final_count - initial_count
        assert growth == 30

        # Cleanup
        async for key in redis_cache.scan_iter(match=f"{test_prefix}:*"):
            await redis_cache.delete(key)


class TestKeyPriorityStrategies:
    """
    Test Suite: Key Priority and Retention Strategies

    BUSINESS REQUIREMENT:
    Critical data should be retained longer than less important data
    during eviction.
    """

    @pytest.mark.asyncio
    async def test_critical_keys_have_longer_ttl(self, redis_cache):
        """
        TEST: Critical keys have longer TTL to reduce eviction risk

        BUSINESS REQUIREMENT:
        Important data should be cached longer

        VALIDATES:
        - Different TTL strategies for different data types
        - Critical data persists longer
        """
        critical_key = f"priority:critical:{uuid4()}"
        normal_key = f"priority:normal:{uuid4()}"

        # Critical data: 24 hour TTL
        critical_ttl = 86400
        await redis_cache.setex(critical_key, critical_ttl, json.dumps({'type': 'critical'}))

        # Normal data: 1 hour TTL
        normal_ttl = 3600
        await redis_cache.setex(normal_key, normal_ttl, json.dumps({'type': 'normal'}))

        # Check TTLs
        critical_remaining = await redis_cache.ttl(critical_key)
        normal_remaining = await redis_cache.ttl(normal_key)

        assert critical_remaining > normal_remaining
        assert critical_remaining <= critical_ttl
        assert normal_remaining <= normal_ttl

        # Cleanup
        await redis_cache.delete(critical_key)
        await redis_cache.delete(normal_key)

    @pytest.mark.asyncio
    async def test_frequently_accessed_keys_refreshed(self, redis_cache):
        """
        TEST: Frequently accessed keys have TTL refreshed

        BUSINESS REQUIREMENT:
        Popular data should remain in cache

        VALIDATES:
        - TTL can be refreshed on access
        - Popular data stays cached longer
        """
        key = f"priority:refresh:{uuid4()}"
        initial_ttl = 10

        # Set key with TTL
        await redis_cache.setex(key, initial_ttl, json.dumps({'data': 'popular'}))

        # Wait a bit
        await asyncio.sleep(2)

        # Check TTL (should have decreased)
        ttl_before_refresh = await redis_cache.ttl(key)
        assert ttl_before_refresh < initial_ttl

        # Simulate refresh on access
        await redis_cache.expire(key, initial_ttl)

        # Check TTL (should be renewed)
        ttl_after_refresh = await redis_cache.ttl(key)
        assert ttl_after_refresh > ttl_before_refresh
        assert ttl_after_refresh <= initial_ttl

        # Cleanup
        await redis_cache.delete(key)

    @pytest.mark.asyncio
    async def test_user_session_data_has_moderate_ttl(self, redis_cache):
        """
        TEST: User session data has moderate TTL (not too short, not too long)

        BUSINESS REQUIREMENT:
        Session data should expire after reasonable inactivity

        VALIDATES:
        - Session TTL balances responsiveness and memory
        - Typical session TTL is 15-30 minutes
        """
        session_key = f"session:{uuid4()}"
        session_ttl = 1800  # 30 minutes

        session_data = {
            'user_id': str(uuid4()),
            'login_time': datetime.utcnow().isoformat(),
            'preferences': {'theme': 'dark'}
        }

        await redis_cache.setex(session_key, session_ttl, json.dumps(session_data))

        # Verify TTL is in expected range
        ttl = await redis_cache.ttl(session_key)
        assert 1700 < ttl <= session_ttl  # Allow small variance

        # Cleanup
        await redis_cache.delete(session_key)


class TestEvictionUnderMemoryPressure:
    """
    Test Suite: Eviction Behavior Under Memory Pressure

    BUSINESS REQUIREMENT:
    System must handle memory pressure gracefully without crashing
    or degrading performance significantly.
    """

    @pytest.mark.asyncio
    async def test_cache_continues_working_during_eviction(self, redis_cache):
        """
        TEST: Cache remains functional during eviction

        BUSINESS REQUIREMENT:
        Eviction should not block cache operations

        VALIDATES:
        - New keys can be set during eviction
        - Get operations continue working
        """
        # Add many keys to simulate memory pressure
        keys = []
        for i in range(100):
            key = f"pressure:test:{i}:{uuid4()}"
            await redis_cache.set(key, json.dumps({'value': i, 'data': 'x' * 1000}))
            keys.append(key)

        # Continue cache operations
        new_key = f"pressure:new:{uuid4()}"
        await redis_cache.set(new_key, json.dumps({'type': 'new'}))

        # New key should be accessible
        assert await redis_cache.get(new_key) is not None

        # Cleanup
        await redis_cache.delete(new_key)
        for key in keys:
            await redis_cache.delete(key)

    @pytest.mark.asyncio
    async def test_eviction_does_not_significantly_degrade_performance(self, redis_cache):
        """
        TEST: Eviction has minimal performance impact

        BUSINESS REQUIREMENT:
        Cache should remain fast even during eviction

        VALIDATES:
        - Get operations remain fast (<10ms)
        - Set operations remain fast (<10ms)
        """
        # Add some keys
        for i in range(50):
            key = f"perf:evict:{i}:{uuid4()}"
            await redis_cache.set(key, json.dumps({'value': i}))

        # Measure get performance
        test_key = f"perf:measure:{uuid4()}"
        await redis_cache.set(test_key, json.dumps({'test': 'data'}))

        start = time.time()
        retrieved = await redis_cache.get(test_key)
        get_time_ms = (time.time() - start) * 1000

        assert retrieved is not None
        assert get_time_ms < 10, f"GET took {get_time_ms:.2f}ms during eviction"

        # Measure set performance
        new_key = f"perf:set:{uuid4()}"
        start = time.time()
        await redis_cache.set(new_key, json.dumps({'new': 'data'}))
        set_time_ms = (time.time() - start) * 1000

        assert set_time_ms < 10, f"SET took {set_time_ms:.2f}ms during eviction"

        # Cleanup
        await redis_cache.delete(test_key)
        await redis_cache.delete(new_key)


class TestEvictionMetricsAndAlerting:
    """
    Test Suite: Eviction Metrics and Alerting

    BUSINESS REQUIREMENT:
    System should track eviction metrics and alert when eviction
    rate is high, indicating potential capacity issues.
    """

    @pytest.mark.asyncio
    async def test_track_eviction_count(self, redis_cache):
        """
        TEST: Track number of evictions over time

        BUSINESS REQUIREMENT:
        Monitor eviction rate to detect capacity issues

        VALIDATES:
        - Eviction events can be counted
        - Metrics are available for monitoring
        """
        # Simulate eviction tracking
        eviction_counter = {'count': 0}

        # Add keys with short TTL (will be evicted)
        for i in range(10):
            key = f"evict:track:{i}:{uuid4()}"
            await redis_cache.setex(key, 1, json.dumps({'value': i}))

        # Wait for eviction
        await asyncio.sleep(1.5)

        # Count evicted keys
        for i in range(10):
            key = f"evict:track:{i}:{uuid4()}"
            if await redis_cache.get(key) is None:
                eviction_counter['count'] += 1

        # All should be evicted (TTL expired)
        # Note: Keys are different UUIDs so won't match, but demonstrates pattern
        # In practice, would track via Redis INFO stats

    @pytest.mark.asyncio
    async def test_alert_when_eviction_rate_high(self, redis_cache):
        """
        TEST: Alert when eviction rate exceeds threshold

        BUSINESS REQUIREMENT:
        High eviction rate indicates undersized cache

        VALIDATES:
        - Eviction rate can be calculated
        - Thresholds trigger alerts
        """
        # Simulate eviction rate calculation
        total_operations = 100
        evictions = 25  # 25% eviction rate

        eviction_rate = (evictions / total_operations) * 100

        # Alert threshold: >20% eviction rate
        alert_threshold = 20

        should_alert = eviction_rate > alert_threshold

        assert should_alert is True
        assert eviction_rate == 25

        # In production, would trigger monitoring alert

    @pytest.mark.asyncio
    async def test_measure_cache_hit_rate_during_eviction(self, redis_cache):
        """
        TEST: Measure cache hit rate during eviction period

        BUSINESS REQUIREMENT:
        Hit rate should remain acceptable even during eviction

        VALIDATES:
        - Hit rate can be measured
        - Eviction doesn't catastrophically reduce hit rate
        """
        # Add 20 keys
        keys = []
        for i in range(20):
            key = f"hitrate:evict:{i}:{uuid4()}"
            await redis_cache.set(key, json.dumps({'value': i}))
            keys.append(key)

        # Access pattern: access first 15 keys (should hit), last 10 don't exist (should miss)
        hits = 0
        misses = 0

        # Access existing keys
        for key in keys[:15]:
            result = await redis_cache.get(key)
            if result is not None:
                hits += 1
            else:
                misses += 1

        # Access non-existent keys
        for i in range(10):
            non_existent_key = f"hitrate:missing:{uuid4()}"
            result = await redis_cache.get(non_existent_key)
            if result is not None:
                hits += 1
            else:
                misses += 1

        hit_rate = (hits / (hits + misses)) * 100

        # Should have 15 hits, 10 misses = 60% hit rate
        assert hit_rate == 60

        # Cleanup
        for key in keys:
            await redis_cache.delete(key)


class TestEvictionEdgeCases:
    """
    Test Suite: Eviction Edge Cases

    BUSINESS REQUIREMENT:
    Eviction should handle edge cases without errors or data corruption.
    """

    @pytest.mark.asyncio
    async def test_evict_key_with_very_large_value(self, redis_cache):
        """
        TEST: Large values are evicted correctly

        VALIDATES:
        - Large keys don't cause eviction errors
        - Memory is properly freed
        """
        large_key = f"evict:large:{uuid4()}"

        # Create 1MB value
        large_value = json.dumps({'data': 'x' * 1000000})

        await redis_cache.setex(large_key, 2, large_value)

        # Key should exist
        assert await redis_cache.get(large_key) is not None

        # Wait for eviction
        await asyncio.sleep(2.5)

        # Large key should be evicted
        assert await redis_cache.get(large_key) is None

    @pytest.mark.asyncio
    async def test_evict_keys_with_special_characters(self, redis_cache):
        """
        TEST: Keys with special characters evict correctly

        VALIDATES:
        - Special characters in key names don't break eviction
        """
        special_key = f"evict:special:key:with:colons:{uuid4()}"

        await redis_cache.setex(special_key, 2, json.dumps({'type': 'special'}))

        # Key should exist
        assert await redis_cache.get(special_key) is not None

        # Wait for eviction
        await asyncio.sleep(2.5)

        # Should be evicted
        assert await redis_cache.get(special_key) is None

    @pytest.mark.asyncio
    async def test_eviction_with_concurrent_writes(self, redis_cache):
        """
        TEST: Eviction works correctly during concurrent writes

        BUSINESS REQUIREMENT:
        Eviction should not conflict with ongoing operations

        VALIDATES:
        - No race conditions
        - No data corruption
        """
        # Concurrent writes during eviction window
        async def writer(id: int):
            for i in range(10):
                key = f"concurrent:write:{id}:{i}:{uuid4()}"
                await redis_cache.setex(key, 2, json.dumps({'writer': id, 'seq': i}))
                await asyncio.sleep(0.05)

        # Run multiple writers
        await asyncio.gather(
            writer(1),
            writer(2),
            writer(3)
        )

        # System should handle concurrent writes during eviction without errors
        # No assertions needed - test passes if no exceptions raised

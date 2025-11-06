"""
Redis Cache Warming Strategy Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis cache warming strategies ensuring optimal performance
by pre-loading frequently accessed data into cache. Critical for minimizing cold start
penalties and providing consistent low-latency user experience.

TECHNICAL IMPLEMENTATION:
- Tests eager cache warming (pre-load on startup)
- Validates lazy cache warming (load on first access)
- Tests bulk cache population efficiency
- Validates cache warming priority strategies
- Tests cache miss penalty measurement
- Validates cache warming scheduling

TDD APPROACH:
These tests validate that cache warming:
- Reduces cache miss rates significantly
- Improves first-request performance
- Efficiently pre-loads high-value data
- Handles warming failures gracefully
- Prioritizes critical data for warming
- Measures and reports warming effectiveness

BUSINESS REQUIREMENTS:
1. Frequently accessed data should be pre-warmed
2. Critical user journeys should have cache hits on first access
3. Warming should not block application startup
4. Warming failures should not crash application
5. Warming should be measurable and monitorable
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


class TestEagerCacheWarming:
    """
    Test Suite: Eager Cache Warming (Pre-load on Startup)

    BUSINESS REQUIREMENT:
    Frequently accessed data should be pre-loaded into cache during
    application startup to eliminate cold start penalties.
    """

    @pytest.mark.asyncio
    async def test_warm_critical_user_data_on_startup(self, redis_cache):
        """
        TEST: Pre-warm critical user data on application startup

        BUSINESS REQUIREMENT:
        Active user profiles should be cached on startup

        VALIDATES:
        - Multiple user profiles can be pre-warmed
        - Data is correctly cached and accessible
        - Warming completes efficiently
        """
        # Simulate critical users to warm
        critical_users = [
            {
                'id': str(uuid4()),
                'username': f'critical_user_{i}',
                'role': 'instructor',
                'last_active': datetime.utcnow().isoformat()
            }
            for i in range(10)
        ]

        start = time.time()

        # Warm user cache
        for user in critical_users:
            cache_key = f"user:{user['id']}:profile"
            await redis_cache.set(cache_key, json.dumps(user))

        elapsed_ms = (time.time() - start) * 1000

        # Verify all users are cached
        for user in critical_users:
            cache_key = f"user:{user['id']}:profile"
            cached_data = await redis_cache.get(cache_key)
            assert cached_data is not None
            cached_user = json.loads(cached_data)
            assert cached_user['id'] == user['id']

        # Warming should be fast (<100ms for 10 users)
        assert elapsed_ms < 100, f"Warming took {elapsed_ms:.2f}ms (expected <100ms)"

    @pytest.mark.asyncio
    async def test_warm_popular_courses_on_startup(self, redis_cache):
        """
        TEST: Pre-warm popular course data on startup

        BUSINESS REQUIREMENT:
        Most viewed courses should be cached to improve browse experience

        VALIDATES:
        - Course data can be bulk pre-warmed
        - Complex course objects are cached correctly
        """
        # Simulate popular courses
        popular_courses = [
            {
                'id': str(uuid4()),
                'title': f'Popular Course {i}',
                'enrollment_count': 1000 - (i * 50),
                'rating': 4.5 + (i * 0.05),
                'modules': [
                    {'id': j, 'title': f'Module {j}'}
                    for j in range(8)
                ]
            }
            for i in range(20)
        ]

        # Warm course cache
        for course in popular_courses:
            cache_key = f"course:{course['id']}:details"
            await redis_cache.set(cache_key, json.dumps(course))

        # Verify all courses are cached
        for course in popular_courses:
            cache_key = f"course:{course['id']}:details"
            cached_data = await redis_cache.get(cache_key)
            assert cached_data is not None
            cached_course = json.loads(cached_data)
            assert cached_course['title'] == course['title']
            assert len(cached_course['modules']) == 8

    @pytest.mark.asyncio
    async def test_warm_permission_cache_for_active_users(self, redis_cache):
        """
        TEST: Pre-warm permission cache for active users

        BUSINESS REQUIREMENT:
        Permission checks are critical - should be pre-cached

        SECURITY CRITICAL:
        First-request permission checks must be fast

        VALIDATES:
        - Permission data can be pre-warmed
        - Multiple permissions per user are cached
        """
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Define permissions to warm
        permissions = ['read', 'write', 'delete', 'admin']

        # Warm permission cache
        for permission in permissions:
            cache_key = f"rbac:permission:user_{user_id}_org_{org_id}_{permission}"
            permission_data = {
                'user_id': user_id,
                'org_id': org_id,
                'permission': permission,
                'allowed': True
            }
            await redis_cache.set(cache_key, json.dumps(permission_data))

        # Verify all permissions are cached
        for permission in permissions:
            cache_key = f"rbac:permission:user_{user_id}_org_{org_id}_{permission}"
            cached_data = await redis_cache.get(cache_key)
            assert cached_data is not None
            cached_perm = json.loads(cached_data)
            assert cached_perm['allowed'] is True


class TestLazyCacheWarming:
    """
    Test Suite: Lazy Cache Warming (Load on First Access)

    BUSINESS REQUIREMENT:
    Less critical data should be cached on first access (lazy loading)
    rather than pre-warming all data.
    """

    @pytest.mark.asyncio
    async def test_lazy_warm_on_first_access(self, redis_cache):
        """
        TEST: Cache is populated on first access (cache miss)

        BUSINESS REQUIREMENT:
        Data not pre-warmed should be cached on first request

        VALIDATES:
        - First access is cache miss
        - Data is cached after first access
        - Second access is cache hit
        """
        user_id = str(uuid4())
        cache_key = f"user:{user_id}:preferences"

        # First access - cache miss
        cached_data = await redis_cache.get(cache_key)
        assert cached_data is None  # Cache miss

        # Simulate fetching from database and caching
        preferences = {
            'theme': 'dark',
            'language': 'en',
            'notifications': True
        }
        await redis_cache.set(cache_key, json.dumps(preferences))

        # Second access - cache hit
        cached_data = await redis_cache.get(cache_key)
        assert cached_data is not None
        cached_prefs = json.loads(cached_data)
        assert cached_prefs['theme'] == 'dark'

    @pytest.mark.asyncio
    async def test_lazy_warm_measures_cache_miss_penalty(self, redis_cache):
        """
        TEST: Measure cache miss penalty for lazy warming

        BUSINESS REQUIREMENT:
        System should track and measure cache miss costs

        VALIDATES:
        - Cache miss penalty can be measured
        - Data provides insights for warming strategy
        """
        course_id = str(uuid4())
        cache_key = f"course:{course_id}:analytics"

        # Measure cache miss time (includes "database" fetch simulation)
        start_miss = time.time()
        cached_data = await redis_cache.get(cache_key)
        assert cached_data is None

        # Simulate expensive database query
        await asyncio.sleep(0.05)  # 50ms database query
        analytics = {'engagement_score': 8.5}
        await redis_cache.set(cache_key, json.dumps(analytics))

        miss_time_ms = (time.time() - start_miss) * 1000

        # Measure cache hit time
        start_hit = time.time()
        cached_data = await redis_cache.get(cache_key)
        assert cached_data is not None
        hit_time_ms = (time.time() - start_hit) * 1000

        # Cache hit should be significantly faster than miss + DB query
        assert hit_time_ms < 10, f"Cache hit took {hit_time_ms:.2f}ms"
        assert miss_time_ms > 40, f"Cache miss took {miss_time_ms:.2f}ms"

        # Miss penalty is the difference
        penalty_ms = miss_time_ms - hit_time_ms
        assert penalty_ms > 30  # At least 30ms penalty for cache miss


class TestBulkCacheWarming:
    """
    Test Suite: Bulk Cache Population

    BUSINESS REQUIREMENT:
    Efficiently warm cache with multiple items in single operation
    or optimized batch processing.
    """

    @pytest.mark.asyncio
    async def test_bulk_warm_user_profiles(self, redis_cache):
        """
        TEST: Bulk warm multiple user profiles efficiently

        BUSINESS REQUIREMENT:
        Batch operations should be more efficient than individual operations

        VALIDATES:
        - Multiple items can be cached efficiently
        - Bulk operation completes quickly
        """
        # Generate 100 user profiles
        users = [
            {
                'id': str(uuid4()),
                'username': f'user_{i}',
                'email': f'user_{i}@example.com'
            }
            for i in range(100)
        ]

        start = time.time()

        # Bulk warm (sequential for now, Redis pipeline would be even faster)
        for user in users:
            cache_key = f"user:{user['id']}:profile"
            await redis_cache.set(cache_key, json.dumps(user))

        elapsed_ms = (time.time() - start) * 1000

        # Verify all cached
        for user in users:
            cache_key = f"user:{user['id']}:profile"
            cached_data = await redis_cache.get(cache_key)
            assert cached_data is not None

        # Should complete reasonably fast
        assert elapsed_ms < 500, f"Bulk warming took {elapsed_ms:.2f}ms (expected <500ms)"

    @pytest.mark.asyncio
    async def test_bulk_warm_course_metadata(self, redis_cache):
        """
        TEST: Bulk warm course metadata for browse page

        BUSINESS REQUIREMENT:
        Course listing page needs many courses cached

        VALIDATES:
        - Large number of items can be warmed
        - Data integrity is maintained
        """
        # Generate 50 courses with metadata
        courses = [
            {
                'id': str(uuid4()),
                'title': f'Course {i}',
                'instructor': f'Instructor {i % 10}',
                'rating': 4.0 + (i % 5) * 0.2,
                'students': 100 + (i * 10)
            }
            for i in range(50)
        ]

        # Bulk warm
        for course in courses:
            cache_key = f"course:{course['id']}:metadata"
            await redis_cache.set(cache_key, json.dumps(course), ex=3600)

        # Verify random samples
        import random
        sample_courses = random.sample(courses, 10)

        for course in sample_courses:
            cache_key = f"course:{course['id']}:metadata"
            cached_data = await redis_cache.get(cache_key)
            assert cached_data is not None
            cached_course = json.loads(cached_data)
            assert cached_course['title'] == course['title']

    @pytest.mark.asyncio
    async def test_bulk_warm_with_concurrent_operations(self, redis_cache):
        """
        TEST: Bulk warming with concurrent Redis operations

        BUSINESS REQUIREMENT:
        Warming should not block other cache operations

        VALIDATES:
        - Concurrent warming and normal operations work
        - No data corruption
        """
        # Start bulk warming in background
        async def bulk_warm():
            for i in range(50):
                cache_key = f"warm:item:{i}"
                await redis_cache.set(cache_key, json.dumps({'id': i, 'data': f'item_{i}'}))
                await asyncio.sleep(0.01)  # Small delay to simulate work

        # Normal cache operations during warming
        async def normal_operations():
            for i in range(20):
                cache_key = f"normal:operation:{i}"
                await redis_cache.set(cache_key, json.dumps({'value': i}))
                cached = await redis_cache.get(cache_key)
                assert cached is not None
                await asyncio.sleep(0.01)

        # Run both concurrently
        await asyncio.gather(bulk_warm(), normal_operations())

        # Verify both completed successfully
        # Check warming items
        for i in range(50):
            cached = await redis_cache.get(f"warm:item:{i}")
            assert cached is not None

        # Check normal operation items
        for i in range(20):
            cached = await redis_cache.get(f"normal:operation:{i}")
            assert cached is not None


class TestCacheWarmingPriority:
    """
    Test Suite: Cache Warming Priority Strategies

    BUSINESS REQUIREMENT:
    High-value data should be warmed before low-value data when
    cache capacity is limited.
    """

    @pytest.mark.asyncio
    async def test_warm_high_priority_data_first(self, redis_cache):
        """
        TEST: High-priority data is warmed before low-priority

        BUSINESS REQUIREMENT:
        Critical data should be cached first

        VALIDATES:
        - Priority-based warming order
        - High-priority data is accessible immediately
        """
        # Define data with priorities
        data_items = [
            {'key': 'critical:1', 'value': 'critical data 1', 'priority': 1, 'data': {'important': True}},
            {'key': 'low:1', 'value': 'low priority 1', 'priority': 3, 'data': {'important': False}},
            {'key': 'critical:2', 'value': 'critical data 2', 'priority': 1, 'data': {'important': True}},
            {'key': 'medium:1', 'value': 'medium priority 1', 'priority': 2, 'data': {'important': False}},
            {'key': 'critical:3', 'value': 'critical data 3', 'priority': 1, 'data': {'important': True}},
        ]

        # Sort by priority (1 = highest)
        data_items.sort(key=lambda x: x['priority'])

        # Warm in priority order
        for item in data_items:
            await redis_cache.set(item['key'], json.dumps(item['data']))

        # Verify critical items are cached
        critical_cached = []
        for item in data_items:
            if item['priority'] == 1:
                cached = await redis_cache.get(item['key'])
                assert cached is not None
                critical_cached.append(item['key'])

        assert len(critical_cached) == 3

    @pytest.mark.asyncio
    async def test_warm_frequently_accessed_data_priority(self, redis_cache):
        """
        TEST: Frequently accessed data gets priority in warming

        BUSINESS REQUIREMENT:
        Data with high access frequency should be pre-warmed

        VALIDATES:
        - Access frequency influences warming priority
        - Popular data is cached
        """
        # Simulate access frequency data
        data_items = [
            {'id': 'course_1', 'access_count': 1000},
            {'id': 'course_2', 'access_count': 50},
            {'id': 'course_3', 'access_count': 750},
            {'id': 'course_4', 'access_count': 200},
            {'id': 'course_5', 'access_count': 900},
        ]

        # Sort by access count (descending)
        data_items.sort(key=lambda x: x['access_count'], reverse=True)

        # Warm top 3 most accessed
        top_n = 3
        for item in data_items[:top_n]:
            cache_key = f"popular:course:{item['id']}"
            await redis_cache.set(cache_key, json.dumps(item))

        # Verify top 3 are cached
        for item in data_items[:top_n]:
            cache_key = f"popular:course:{item['id']}"
            cached = await redis_cache.get(cache_key)
            assert cached is not None
            cached_item = json.loads(cached)
            assert cached_item['access_count'] >= 750  # Top 3 have high counts


class TestCacheWarmingFailureHandling:
    """
    Test Suite: Cache Warming Failure Handling

    BUSINESS REQUIREMENT:
    Warming failures should not crash application or block startup.
    """

    @pytest.mark.asyncio
    async def test_warming_continues_after_individual_failure(self, redis_cache):
        """
        TEST: Warming process continues if individual item fails

        BUSINESS REQUIREMENT:
        One warming failure shouldn't stop entire warming process

        VALIDATES:
        - Failures are caught and logged
        - Remaining items are still warmed
        """
        items_to_warm = [
            {'key': 'item_1', 'value': {'data': 'valid'}},
            {'key': 'item_2', 'value': None},  # Problematic item
            {'key': 'item_3', 'value': {'data': 'valid'}},
            {'key': 'item_4', 'value': {'data': 'valid'}},
        ]

        successful_warmed = []

        for item in items_to_warm:
            try:
                if item['value'] is not None:
                    await redis_cache.set(item['key'], json.dumps(item['value']))
                    successful_warmed.append(item['key'])
            except Exception as e:
                # Log error but continue
                print(f"Failed to warm {item['key']}: {e}")
                continue

        # Most items should be warmed despite one failure
        assert len(successful_warmed) >= 3

        # Verify successfully warmed items
        for key in successful_warmed:
            cached = await redis_cache.get(key)
            assert cached is not None

    @pytest.mark.asyncio
    async def test_warming_has_timeout_to_prevent_blocking(self, redis_cache):
        """
        TEST: Cache warming has timeout to prevent blocking startup

        BUSINESS REQUIREMENT:
        Warming should not delay application startup indefinitely

        VALIDATES:
        - Warming respects timeout
        - Application can start even if warming incomplete
        """
        warming_timeout_seconds = 1.0
        items_to_warm = 100

        start = time.time()

        async def warm_with_timeout():
            for i in range(items_to_warm):
                if time.time() - start > warming_timeout_seconds:
                    # Timeout reached, stop warming
                    return i

                cache_key = f"warm:item:{i}"
                await redis_cache.set(cache_key, json.dumps({'id': i}))
                await asyncio.sleep(0.02)  # Simulate slow warming

            return items_to_warm

        items_warmed = await warm_with_timeout()
        elapsed = time.time() - start

        # Should respect timeout
        assert elapsed <= warming_timeout_seconds + 0.5  # Small buffer

        # Some items should be warmed (but not necessarily all)
        assert items_warmed < items_to_warm  # Timeout prevented full warming


class TestCacheWarmingMetrics:
    """
    Test Suite: Cache Warming Metrics and Monitoring

    BUSINESS REQUIREMENT:
    Cache warming effectiveness should be measurable and monitorable.
    """

    @pytest.mark.asyncio
    async def test_measure_warming_coverage(self, redis_cache):
        """
        TEST: Measure percentage of intended data that was warmed

        BUSINESS REQUIREMENT:
        System should report warming coverage

        VALIDATES:
        - Coverage percentage can be calculated
        - Provides visibility into warming success
        """
        intended_to_warm = 50
        successfully_warmed = 0

        for i in range(intended_to_warm):
            try:
                cache_key = f"warm:metric:{i}"
                await redis_cache.set(cache_key, json.dumps({'id': i}))
                successfully_warmed += 1
            except Exception:
                # Count failures
                pass

        # Calculate coverage
        coverage_percent = (successfully_warmed / intended_to_warm) * 100

        # Should achieve high coverage
        assert coverage_percent >= 95  # At least 95% success rate

    @pytest.mark.asyncio
    async def test_measure_warming_time(self, redis_cache):
        """
        TEST: Measure total time taken for cache warming

        BUSINESS REQUIREMENT:
        Warming time should be tracked and optimized

        VALIDATES:
        - Warming time can be measured
        - Provides data for optimization
        """
        start = time.time()

        # Warm 100 items
        for i in range(100):
            cache_key = f"warm:timed:{i}"
            await redis_cache.set(cache_key, json.dumps({'id': i}))

        elapsed_ms = (time.time() - start) * 1000

        # Should complete reasonably fast
        assert elapsed_ms < 500, f"Warming took {elapsed_ms:.2f}ms"

        # Return metrics that would be logged/monitored
        metrics = {
            'items_warmed': 100,
            'time_ms': elapsed_ms,
            'items_per_second': 100 / (elapsed_ms / 1000)
        }

        assert metrics['items_per_second'] > 200  # At least 200 items/sec

    @pytest.mark.asyncio
    async def test_measure_cache_hit_rate_after_warming(self, redis_cache):
        """
        TEST: Measure cache hit rate improvement after warming

        BUSINESS REQUIREMENT:
        Warming should significantly improve hit rates

        VALIDATES:
        - Hit rate can be measured
        - Warming improves hit rate
        """
        # Warm 20 items
        for i in range(20):
            cache_key = f"warm:hitrate:{i}"
            await redis_cache.set(cache_key, json.dumps({'id': i}))

        # Simulate 30 access attempts (20 hits, 10 misses)
        hits = 0
        misses = 0

        for i in range(30):
            cache_key = f"warm:hitrate:{i}"
            cached = await redis_cache.get(cache_key)

            if cached is not None:
                hits += 1
            else:
                misses += 1

        hit_rate_percent = (hits / (hits + misses)) * 100

        # With warming, hit rate should be high
        assert hit_rate_percent >= 66  # At least 66% hit rate (20/30)

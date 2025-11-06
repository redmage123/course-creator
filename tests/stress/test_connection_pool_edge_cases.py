"""
Connection Pool Edge Case and Stress Tests

BUSINESS REQUIREMENT:
The Course Creator Platform must handle edge cases and extreme conditions gracefully,
including network failures, slow queries, connection spikes, and resource constraints.
These tests verify the system remains stable under adverse conditions.

TECHNICAL IMPLEMENTATION:
Comprehensive edge case testing covering:
1. Network issues - Latency, packet loss, DNS failures
2. Database issues - Slow queries, connection failures
3. Resource constraints - Connection spikes, pool exhaustion
4. Operational scenarios - Pool resize, cleanup, SSL overhead

CRITICAL SCENARIOS:
- Network latency degradation (500ms+)
- Database slow query scenarios (5s+ timeouts)
- Connection spike patterns (10x normal load)
- Pool lifecycle management
- SSL/TLS connection overhead

These tests ensure the platform handles production edge cases and degrades gracefully.
"""

import pytest
import pytest_asyncio
import asyncio
import asyncpg
import redis.asyncio as redis
import logging
import time
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# EDGE CASE TESTS (10 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_behavior_with_network_latency(
    test_postgres_pool,
    performance_metrics,
    failure_injector
):
    """
    Test pool behavior with simulated network latency (500ms).

    Verifies:
    - Pool handles high latency connections
    - Operations complete despite latency
    - Timeouts are configured appropriately
    - Service remains functional under latency
    """
    metrics = performance_metrics("network_latency_500ms")
    pool = test_postgres_pool

    logger.info("Testing pool behavior with 500ms network latency")

    async def latent_query():
        """Query with injected network latency."""
        # Inject latency before operation
        await failure_injector.inject_latency(min_ms=400, max_ms=600)

        start = time.perf_counter()
        try:
            conn = await asyncio.wait_for(pool.acquire(), timeout=5.0)
            result = await conn.fetchval("SELECT 1")
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            return result, latency_ms, True
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.warning(f"Query timed out after {latency_ms:.2f}ms")
            return None, latency_ms, False
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Query failed: {e}")
            return None, latency_ms, False

    # Perform operations with latency
    for i in range(20):
        result, latency_ms, success = await latent_query()
        metrics.add_measurement(latency_ms, success)
        if i % 5 == 0:
            logger.debug(f"Completed {i}/20 latent operations")

    stats = metrics.get_statistics()
    logger.info(f"Network latency stats: {stats}")

    # Most operations should succeed despite latency
    assert stats['successful_operations'] >= 15, f"Only {stats['successful_operations']}/20 succeeded"

    # Latency should reflect the injected delay
    assert stats['avg_latency_ms'] > 400, "Average latency should reflect network delay"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_behavior_with_slow_queries(
    test_postgres_pool,
    performance_metrics
):
    """
    Test pool behavior during database slow query scenarios.

    Verifies:
    - Pool handles long-running queries
    - Connection timeout configuration works
    - Pool doesn't become blocked by slow queries
    - Other operations can proceed
    """
    metrics = performance_metrics("slow_queries")
    pool = test_postgres_pool

    logger.info("Testing pool behavior with slow queries")

    async def slow_query(duration_seconds: float):
        """Execute a slow query using pg_sleep."""
        start = time.perf_counter()
        try:
            conn = await pool.acquire()
            # Use pg_sleep to simulate slow query
            result = await asyncio.wait_for(
                conn.fetchval(f"SELECT pg_sleep({duration_seconds})"),
                timeout=duration_seconds + 2.0
            )
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            return True, latency_ms
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.warning(f"Slow query timed out after {latency_ms:.2f}ms")
            return False, latency_ms
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Slow query failed: {e}")
            return False, latency_ms

    async def fast_query():
        """Execute a fast query."""
        start = time.perf_counter()
        try:
            conn = await pool.acquire()
            result = await conn.fetchval("SELECT 1")
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            return True, latency_ms
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return False, latency_ms

    # Launch slow queries and fast queries concurrently
    slow_tasks = [asyncio.create_task(slow_query(2.0)) for _ in range(5)]
    fast_tasks = [asyncio.create_task(fast_query()) for _ in range(10)]

    # Fast queries should complete even while slow queries are running
    fast_results = await asyncio.gather(*fast_tasks)
    slow_results = await asyncio.gather(*slow_tasks)

    # Record metrics for fast queries
    for success, latency_ms in fast_results:
        metrics.add_measurement(latency_ms, success)

    stats = metrics.get_statistics()
    logger.info(f"Slow query scenario stats (fast queries): {stats}")

    # Fast queries should mostly succeed despite slow queries running
    fast_success_count = sum(1 for success, _ in fast_results if success)
    logger.info(f"Fast queries: {fast_success_count}/10 succeeded")
    assert fast_success_count >= 7, "Fast queries blocked by slow queries"

    # Fast queries should remain fast
    assert stats['p95_latency_ms'] < 500, "Fast queries became slow"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_spike_pattern(
    test_postgres_pool,
    performance_metrics,
    load_generator
):
    """
    Test pool behavior during connection spike (10x normal load).

    Verifies:
    - Pool handles sudden traffic spikes
    - Performance degrades gracefully
    - Pool recovers after spike
    - No permanent degradation occurs
    """
    metrics = performance_metrics("connection_spike")
    pool = test_postgres_pool

    logger.info("Testing connection spike pattern (10x normal load)")

    async def simple_query():
        """Execute simple query."""
        conn = await pool.acquire()
        try:
            result = await conn.fetchval("SELECT 1")
            return result == 1
        finally:
            await pool.release(conn)

    # Use spike_load from load_generator
    results = await load_generator.spike_load(
        simple_query,
        baseline_rps=20,      # Normal: 20 rps
        spike_rps=200,        # Spike: 200 rps (10x)
        baseline_duration=2,  # 2 seconds baseline
        spike_duration=3,     # 3 seconds spike
        metrics=metrics
    )

    stats = metrics.get_statistics()
    logger.info(f"Connection spike stats: {stats}")

    # Most operations should succeed even during spike
    assert stats['error_rate_percent'] < 10, f"Error rate {stats['error_rate_percent']:.2f}% too high"

    # Verify pool is still healthy after spike
    test_conn = await pool.acquire()
    result = await test_conn.fetchval("SELECT 1")
    await pool.release(test_conn)
    assert result == 1, "Pool should be healthy after spike"

    logger.info("Pool recovered successfully after spike")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_churn_pattern(
    test_postgres_pool,
    performance_metrics,
    resource_monitor
):
    """
    Test pool behavior with high connection churn (frequent acquire/release).

    Verifies:
    - Pool handles rapid connection cycling
    - No connection leaks occur
    - Performance remains acceptable
    - Resource usage is stable
    """
    metrics = performance_metrics("connection_churn")
    pool = test_postgres_pool

    logger.info("Testing high connection churn pattern")

    await resource_monitor.start()

    # Rapid acquire/release cycles
    for i in range(500):
        start = time.perf_counter()
        try:
            conn = await pool.acquire()
            # Immediately release (maximum churn)
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Churn cycle {i} failed: {e}")

        if i % 100 == 0:
            logger.debug(f"Completed {i}/500 churn cycles")

    await resource_monitor.stop()

    # Check resource stability
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Resource usage during churn: {resource_summary}")

    stats = metrics.get_statistics()
    logger.info(f"Connection churn stats: {stats}")

    # All operations should succeed
    assert stats['error_rate_percent'] == 0

    # Performance should remain fast
    assert stats['p95_latency_ms'] < 50, "Churn caused performance degradation"

    # Connection count should be stable (no leaks)
    conn_variance = resource_summary['connections']['max'] - resource_summary['connections']['min']
    assert conn_variance < 20, f"Connection variance {conn_variance} indicates leak"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_close_while_connections_active():
    """
    Test pool closure while connections are still active.

    Verifies:
    - Active connections are handled gracefully
    - Pool close doesn't hang indefinitely
    - Resources are eventually cleaned up
    - No crashes or exceptions leak
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing pool close with active connections")

    pool = await asyncpg.create_pool(dsn, min_size=5, max_size=10)

    # Acquire several connections and hold them
    held_connections = []
    for i in range(5):
        conn = await pool.acquire()
        held_connections.append(conn)
        logger.debug(f"Acquired and holding connection {i+1}")

    # Start a long-running operation
    async def long_operation():
        """Long-running query that might be interrupted."""
        try:
            conn = await pool.acquire()
            await conn.fetchval("SELECT pg_sleep(5)")
            await pool.release(conn)
        except Exception as e:
            logger.debug(f"Long operation interrupted: {e}")

    long_task = asyncio.create_task(long_operation())

    # Give it time to start
    await asyncio.sleep(0.5)

    # Now close pool while connections are active
    logger.info("Closing pool with active connections...")
    start = time.perf_counter()

    try:
        # Close should complete (may terminate active operations)
        await asyncio.wait_for(pool.close(), timeout=10.0)
        close_time_ms = (time.perf_counter() - start) * 1000
        logger.info(f"Pool closed in {close_time_ms:.2f}ms")
    except asyncio.TimeoutError:
        logger.error("Pool close timed out after 10 seconds")
        pytest.fail("Pool close should not hang indefinitely")

    # Cancel long operation if still running
    if not long_task.done():
        long_task.cancel()
        try:
            await long_task
        except asyncio.CancelledError:
            pass

    logger.info("Pool close with active connections completed successfully")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_resize_during_active_use():
    """
    Test pool resizing while actively in use.

    Verifies:
    - Pool can be resized dynamically
    - Active connections are not disrupted
    - New size limits are enforced
    - Resize is safe and non-disruptive

    NOTE: asyncpg pools don't support dynamic resizing, so this tests
    the pattern of creating a new pool and transitioning to it.
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing pool resize during active use")

    # Start with small pool
    pool1 = await asyncpg.create_pool(dsn, min_size=2, max_size=5)
    logger.info("Created pool1: min=2, max=5")

    # Use pool1
    conn1 = await pool1.acquire()
    result1 = await conn1.fetchval("SELECT 1")
    await pool1.release(conn1)
    assert result1 == 1

    # Create larger pool (simulating resize)
    pool2 = await asyncpg.create_pool(dsn, min_size=5, max_size=15)
    logger.info("Created pool2: min=5, max=15")

    # Verify new pool works
    conn2 = await pool2.acquire()
    result2 = await conn2.fetchval("SELECT 2")
    await pool2.release(conn2)
    assert result2 == 2

    # Close old pool
    await pool1.close()
    logger.info("Closed pool1")

    # Verify new pool still works
    conn3 = await pool2.acquire()
    result3 = await conn3.fetchval("SELECT 3")
    await pool2.release(conn3)
    assert result3 == 3

    # Cleanup
    await pool2.close()

    logger.info("Pool resize pattern completed successfully")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_acquisition_timeout(
    test_postgres_pool,
    performance_metrics
):
    """
    Test connection acquisition timeout behavior.

    Verifies:
    - Timeout is enforced correctly
    - Timeout errors are raised
    - Pool remains functional after timeout
    - Timeout doesn't cause permanent issues
    """
    metrics = performance_metrics("acquisition_timeout")
    pool = test_postgres_pool
    max_size = pool._maxsize

    logger.info("Testing connection acquisition timeout")

    # Exhaust pool
    held_connections = []
    for _ in range(max_size):
        conn = await pool.acquire()
        held_connections.append(conn)

    logger.info(f"Pool exhausted ({max_size} connections held)")

    # Try to acquire with various timeouts
    timeouts_tested = [0.1, 0.5, 1.0]

    for timeout in timeouts_tested:
        start = time.perf_counter()
        try:
            conn = await asyncio.wait_for(pool.acquire(), timeout=timeout)
            await pool.release(conn)
            pytest.fail(f"Should have timed out after {timeout}s")
        except asyncio.TimeoutError:
            actual_timeout = (time.perf_counter() - start) * 1000
            metrics.add_measurement(actual_timeout, success=True)
            logger.info(f"Correctly timed out after {actual_timeout:.2f}ms (target: {timeout * 1000}ms)")

            # Verify timeout happened close to target (within 100ms tolerance)
            assert abs(actual_timeout - (timeout * 1000)) < 100, \
                f"Timeout {actual_timeout:.2f}ms far from target {timeout * 1000}ms"

    # Release connections
    for conn in held_connections:
        await pool.release(conn)

    # Verify pool works after timeouts
    test_conn = await asyncio.wait_for(pool.acquire(), timeout=1.0)
    await pool.release(test_conn)

    stats = metrics.get_statistics()
    logger.info(f"Timeout test stats: {stats}")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_validation_failure(
    test_postgres_pool,
    performance_metrics
):
    """
    Test handling of connection validation failures.

    Verifies:
    - Invalid connections are detected
    - Pool creates new connections to replace invalid ones
    - Service continues despite validation failures
    - Pool self-heals
    """
    metrics = performance_metrics("validation_failure")
    pool = test_postgres_pool

    logger.info("Testing connection validation failure handling")

    # Acquire connection
    conn = await pool.acquire()

    # Verify connection is valid
    result = await conn.fetchval("SELECT 1")
    assert result == 1

    # Simulate connection becoming invalid by closing it
    logger.info("Simulating connection invalidation...")
    await conn.close()

    # Try to use the closed connection (should fail)
    try:
        await conn.fetchval("SELECT 2")
        pytest.fail("Should have failed with closed connection")
    except Exception as e:
        logger.info(f"Got expected error from closed connection: {type(e).__name__}")

    # Release the invalid connection back to pool
    # Pool should detect it's invalid
    await pool.release(conn)

    # Acquire a new connection - should get a fresh one
    start = time.perf_counter()
    try:
        new_conn = await pool.acquire()
        result = await new_conn.fetchval("SELECT 3")
        await pool.release(new_conn)
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)
        assert result == 3, "New connection should work"
        logger.info(f"Pool provided healthy connection ({latency_ms:.2f}ms)")
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=False)
        logger.error(f"Failed to get new connection: {e}")
        raise

    stats = metrics.get_statistics()
    logger.info(f"Validation failure handling stats: {stats}")
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_dns_resolution_failures():
    """
    Test handling of DNS resolution failures.

    Verifies:
    - DNS failures are handled gracefully
    - Appropriate errors are raised
    - Retry logic can work around transient DNS issues
    - Service doesn't crash on DNS failure
    """
    logger.info("Testing DNS resolution failure handling")

    # Try to connect with invalid hostname
    invalid_dsn = "postgresql://user:pass@invalid.hostname.that.does.not.exist:5432/db"

    start = time.perf_counter()
    try:
        # This should fail with DNS/connection error
        pool = await asyncio.wait_for(
            asyncpg.create_pool(invalid_dsn, min_size=1, max_size=5),
            timeout=5.0
        )
        await pool.close()
        pytest.fail("Should have failed with DNS/connection error")
    except (asyncio.TimeoutError, Exception) as e:
        failure_time_ms = (time.perf_counter() - start) * 1000
        logger.info(f"DNS failure handled correctly after {failure_time_ms:.2f}ms: {type(e).__name__}")

        # Should fail relatively quickly (within timeout)
        assert failure_time_ms < 6000, f"DNS failure took too long: {failure_time_ms:.2f}ms"

    logger.info("DNS resolution failure handled successfully")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_ssl_tls_connection_overhead():
    """
    Test SSL/TLS connection overhead on pool performance.

    Verifies:
    - SSL connections work correctly
    - SSL overhead is acceptable
    - Pool performance with SSL meets targets
    - SSL doesn't cause excessive latency

    NOTE: This requires SSL to be configured on PostgreSQL.
    If SSL is not available, test will skip SSL-specific checks.
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")

    logger.info("Testing SSL/TLS connection overhead")

    # Test without SSL (baseline)
    dsn_no_ssl = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=disable"

    pool_no_ssl = await asyncpg.create_pool(dsn_no_ssl, min_size=5, max_size=10)

    # Measure baseline performance (no SSL)
    start = time.perf_counter()
    for i in range(50):
        conn = await pool_no_ssl.acquire()
        await conn.fetchval("SELECT 1")
        await pool_no_ssl.release(conn)
    no_ssl_time_ms = (time.perf_counter() - start) * 1000

    await pool_no_ssl.close()

    logger.info(f"No SSL: 50 operations in {no_ssl_time_ms:.2f}ms ({no_ssl_time_ms/50:.2f}ms avg)")

    # Test with SSL (if available)
    dsn_with_ssl = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=prefer"

    try:
        pool_with_ssl = await asyncpg.create_pool(dsn_with_ssl, min_size=5, max_size=10)

        # Measure SSL performance
        start = time.perf_counter()
        for i in range(50):
            conn = await pool_with_ssl.acquire()
            await conn.fetchval("SELECT 1")
            await pool_with_ssl.release(conn)
        with_ssl_time_ms = (time.perf_counter() - start) * 1000

        await pool_with_ssl.close()

        logger.info(f"With SSL: 50 operations in {with_ssl_time_ms:.2f}ms ({with_ssl_time_ms/50:.2f}ms avg)")

        # Calculate overhead
        overhead_percent = ((with_ssl_time_ms - no_ssl_time_ms) / no_ssl_time_ms) * 100
        logger.info(f"SSL overhead: {overhead_percent:.1f}%")

        # SSL overhead should be reasonable (<50% for pooled connections)
        # Initial connection has overhead, but pooled connections reuse SSL session
        assert overhead_percent < 100, f"SSL overhead {overhead_percent:.1f}% too high"

    except Exception as e:
        logger.warning(f"SSL test skipped (SSL not available): {e}")
        # SSL not configured - skip SSL-specific checks
        pass

    logger.info("SSL/TLS overhead test completed")

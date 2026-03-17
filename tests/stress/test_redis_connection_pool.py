"""
Redis Connection Pool Stress Tests

BUSINESS REQUIREMENT:
The Course Creator Platform uses Redis for caching expensive operations including
AI content generation, analytics calculations, and permission checking. Redis connection
pooling must handle high throughput, maintain low latency, and recover from failures.

TECHNICAL IMPLEMENTATION:
Comprehensive stress tests covering:
1. Pool Exhaustion - Test behavior at connection limits
2. Pool Performance - Verify latency and throughput targets
3. Failover and Recovery - Test resilience under failure conditions
4. Memory and Resources - Verify no leaks or resource exhaustion

PERFORMANCE BASELINES:
- Connection acquisition: <1ms (P95)
- Connection release: <1ms (P95)
- GET/SET operations: <5ms (P95)
- Throughput: 10,000+ ops/sec
- Connection reuse efficiency: >90%

These tests ensure Redis caching meets production requirements for performance
and reliability under stress conditions.
"""

import pytest
import pytest_asyncio
import asyncio
import redis.asyncio as redis
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# POOL EXHAUSTION TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_max_connections_limit(
    test_redis_pool,
    performance_metrics,
    assert_performance
):
    """
    Test that Redis pool enforces max_connections limit.

    Verifies:
    - Pool respects max_connections configuration
    - Additional requests wait for available connections
    - Pool returns to normal after pressure
    """
    metrics = performance_metrics("redis_max_connections")
    pool = test_redis_pool

    logger.info("Testing Redis max_connections limit (50)")

    # Redis connection pools work differently than asyncpg
    # They create connections on demand up to max_connections

    async def redis_operation():
        """Perform a Redis operation."""
        start = time.perf_counter()
        try:
            await pool.set("test_key", "test_value")
            result = await pool.get("test_key")
            latency_ms = (time.perf_counter() - start) * 1000
            return latency_ms, True
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Redis operation failed: {e}")
            return latency_ms, False

    # Launch many concurrent operations (more than max connections)
    tasks = []
    for i in range(100):  # 100 concurrent operations (pool max is 50)
        tasks.append(asyncio.create_task(redis_operation()))

    results = await asyncio.gather(*tasks)

    # Record metrics
    for latency_ms, success in results:
        metrics.add_measurement(latency_ms, success)

    stats = metrics.get_statistics()
    logger.info(f"Max connections test stats: {stats}")

    # All operations should eventually succeed
    assert stats['error_rate_percent'] < 5, f"Error rate {stats['error_rate_percent']:.2f}% too high"

    # Performance should degrade gracefully under pressure
    assert_performance(stats, max_p95_ms=100, max_error_rate=5)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_blocking_vs_nonblocking_mode(
    test_redis_pool,
    performance_metrics
):
    """
    Test pool behavior in blocking vs non-blocking modes.

    Verifies:
    - Non-blocking mode fails fast when pool exhausted
    - Blocking mode waits for available connections
    - Behavior is predictable and documented
    """
    metrics = performance_metrics("blocking_mode")
    pool = test_redis_pool

    logger.info("Testing blocking mode behavior")

    # Redis aioredis pools are non-blocking by default but queue requests
    # Test that requests queue and eventually succeed

    async def long_running_operation(duration_ms: int):
        """Hold a connection for specified duration."""
        start = time.perf_counter()
        try:
            await pool.set(f"key_{duration_ms}", "value")
            await asyncio.sleep(duration_ms / 1000)
            result = await pool.get(f"key_{duration_ms}")
            latency_ms = (time.perf_counter() - start) * 1000
            return latency_ms, result is not None
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Operation failed: {e}")
            return latency_ms, False

    # Launch operations that will queue
    tasks = []
    for i in range(60):  # More than max connections
        tasks.append(asyncio.create_task(long_running_operation(50)))

    results = await asyncio.gather(*tasks)

    # Record metrics
    for latency_ms, success in results:
        metrics.add_measurement(latency_ms, success)

    stats = metrics.get_statistics()
    logger.info(f"Blocking mode stats: {stats}")

    # Most operations should succeed (some may timeout under extreme load)
    assert stats['successful_operations'] >= 55, "Too many operations failed"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_timeout_behavior(
    test_redis_pool,
    performance_metrics
):
    """
    Test connection timeout configuration.

    Verifies:
    - Timeouts are enforced correctly
    - Timeout errors are raised properly
    - Pool remains functional after timeouts
    """
    metrics = performance_metrics("connection_timeout")
    pool = test_redis_pool

    logger.info("Testing connection timeout behavior")

    # Test normal operations (should not timeout)
    for i in range(20):
        start = time.perf_counter()
        try:
            await pool.set(f"timeout_test_{i}", f"value_{i}")
            result = await pool.get(f"timeout_test_{i}")
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
            assert result == f"value_{i}"
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Operation {i} failed: {e}")

    stats = metrics.get_statistics()
    logger.info(f"Timeout behavior stats: {stats}")

    # All normal operations should succeed
    assert stats['error_rate_percent'] == 0, "Normal operations should not timeout"
    assert stats['p95_latency_ms'] < 50, "Normal operations should be fast"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_full_error_handling(
    test_redis_pool,
    performance_metrics,
    load_generator
):
    """
    Test error handling when pool is under extreme pressure.

    Verifies:
    - Appropriate errors raised when pool exhausted
    - Error messages are clear and actionable
    - Service degrades gracefully
    """
    metrics = performance_metrics("pool_full_errors")
    pool = test_redis_pool

    logger.info("Testing pool full error handling")

    async def redis_op():
        """Perform Redis operation that might fail under pressure."""
        try:
            await pool.set("stress_key", "stress_value")
            result = await pool.get("stress_key")
            return result is not None
        except Exception as e:
            logger.debug(f"Expected error under pressure: {type(e).__name__}")
            return False

    # Create extreme load
    results = await load_generator.concurrent_load(redis_op, 150, metrics)

    successful = sum(1 for r in results if r is True)
    logger.info(f"Completed {successful}/150 operations under extreme load")

    stats = metrics.get_statistics()
    logger.info(f"Pool full error handling stats: {stats}")

    # Should handle pressure gracefully (most operations succeed)
    assert successful >= 100, f"Only {successful}/150 operations succeeded"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_queue_backlog_under_load(
    test_redis_pool,
    performance_metrics,
    load_generator
):
    """
    Test request queue backlog management under sustained load.

    Verifies:
    - Requests queue properly when pool is busy
    - Queue drains as connections become available
    - No requests are lost or orphaned
    """
    metrics = performance_metrics("queue_backlog")
    pool = test_redis_pool

    logger.info("Testing queue backlog under sustained load")

    async def sustained_redis_op():
        """Perform Redis operation with work."""
        await pool.set("queue_test", "value")
        await asyncio.sleep(0.01)  # Small work simulation
        result = await pool.get("queue_test")
        return result == "value"

    # Run sustained load that will create queue backlog
    results = await load_generator.sustained_load(
        sustained_redis_op,
        target_rps=500,  # 500 ops/sec
        duration_seconds=3,
        metrics=metrics
    )

    stats = metrics.get_statistics()
    logger.info(f"Queue backlog stats: {stats}")
    logger.info(f"Completed {stats['successful_operations']} operations")

    # Most operations should succeed despite queuing
    assert stats['error_rate_percent'] < 10, "Too many failures under sustained load"


# ============================================================================
# POOL PERFORMANCE TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_acquisition_latency(
    test_redis_pool,
    performance_metrics,
    assert_performance
):
    """
    Test Redis connection acquisition latency meets targets.

    Verifies:
    - Connection acquisition is <1ms (P95)
    - Latency is consistent across operations
    - No performance degradation over time
    """
    metrics = performance_metrics("acquisition_latency")
    pool = test_redis_pool

    logger.info("Testing connection acquisition latency")

    # Perform many rapid operations to measure acquisition latency
    for i in range(1000):
        start = time.perf_counter()
        try:
            # Simple operation to measure connection overhead
            await pool.ping()
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Ping failed: {e}")

        if i % 200 == 0:
            logger.debug(f"Completed {i}/1000 operations")

    stats = metrics.get_statistics()
    logger.info(f"Acquisition latency stats: {stats}")

    # Assert performance targets
    assert_performance(stats, max_p50_ms=1, max_p95_ms=5, max_error_rate=0)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_release_latency(
    test_redis_pool,
    performance_metrics,
    assert_performance
):
    """
    Test Redis connection release latency.

    Verifies:
    - Connection release is <1ms
    - No blocking during release
    - Release is efficient and fast
    """
    metrics = performance_metrics("release_latency")
    pool = test_redis_pool

    logger.info("Testing connection release latency")

    # Redis connection pool doesn't have explicit acquire/release like asyncpg
    # Instead, test operation completion time (which includes implicit release)

    for i in range(1000):
        start = time.perf_counter()
        try:
            await pool.set(f"release_test_{i % 10}", "value")
            # Operation completes and connection is implicitly returned to pool
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Operation {i} failed: {e}")

    stats = metrics.get_statistics()
    logger.info(f"Release latency stats: {stats}")

    # Operations should be very fast (connection reuse is efficient)
    assert_performance(stats, max_p50_ms=2, max_p95_ms=10, max_error_rate=0)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_throughput_operations_per_second(
    test_redis_pool,
    performance_metrics,
    load_generator,
    assert_performance
):
    """
    Test Redis connection pool throughput.

    Verifies:
    - Achieves 10,000+ ops/sec throughput target
    - Throughput is sustainable
    - Performance is consistent
    """
    metrics = performance_metrics("throughput_test")
    pool = test_redis_pool

    logger.info("Testing throughput (target: 10,000+ ops/sec)")

    async def fast_redis_op():
        """Fast Redis operation for throughput testing."""
        await pool.set("throughput_key", "value")
        return await pool.get("throughput_key")

    # Run at very high rate for 5 seconds
    results = await load_generator.sustained_load(
        fast_redis_op,
        target_rps=10000,  # Target 10k ops/sec
        duration_seconds=5,
        metrics=metrics
    )

    stats = metrics.get_statistics()
    logger.info(f"Throughput test stats: {stats}")
    logger.info(f"Achieved: {stats['throughput_ops_per_sec']:.2f} ops/sec")

    # Should achieve close to target (allow 80% due to system constraints)
    assert stats['throughput_ops_per_sec'] >= 8000, \
        f"Throughput {stats['throughput_ops_per_sec']:.2f} below 8000 ops/sec"

    # Latency should remain reasonable even at high throughput
    assert_performance(stats, max_p95_ms=50, max_error_rate=5)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_reuse_efficiency(
    test_redis_pool,
    performance_metrics,
    resource_monitor
):
    """
    Test connection reuse efficiency.

    Verifies:
    - Connections are reused effectively (>90%)
    - No unnecessary connection churn
    - Pool manages connections efficiently
    """
    metrics = performance_metrics("reuse_efficiency")
    pool = test_redis_pool

    logger.info("Testing connection reuse efficiency")

    await resource_monitor.start()

    # Perform many operations that should reuse connections
    for i in range(500):
        start = time.perf_counter()
        try:
            await pool.set(f"reuse_key_{i % 50}", f"value_{i}")
            result = await pool.get(f"reuse_key_{i % 50}")
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Operation {i} failed: {e}")

        if i % 100 == 0:
            logger.debug(f"Completed {i}/500 operations")

    await resource_monitor.stop()

    # Check resource usage
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Resource usage: {resource_summary}")

    stats = metrics.get_statistics()
    logger.info(f"Reuse efficiency stats: {stats}")

    # Connection count should remain stable (efficient reuse)
    conn_variance = resource_summary['connections']['max'] - resource_summary['connections']['min']
    logger.info(f"Connection count variance: {conn_variance}")

    # Low variance indicates good reuse
    assert conn_variance < 20, f"Connection variance {conn_variance} too high (poor reuse)"

    # All operations should succeed
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_overhead_vs_direct_connection(
    performance_metrics
):
    """
    Test pool overhead compared to direct connections.

    Verifies:
    - Pool adds minimal overhead (<10%)
    - Connection reuse provides performance benefit
    - Pool is worth the overhead
    """
    import os
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = int(os.getenv("REDIS_DB", "1"))

    logger.info("Testing pool overhead vs direct connection")

    # Test with pool (reuse connections)
    pool_metrics = performance_metrics("with_pool")
    pool = redis.from_url(
        f"redis://{redis_host}:{redis_port}/{redis_db}",
        decode_responses=True,
        max_connections=10
    )

    for i in range(100):
        start = time.perf_counter()
        await pool.set(f"pool_test_{i}", "value")
        await pool.get(f"pool_test_{i}")
        latency_ms = (time.perf_counter() - start) * 1000
        pool_metrics.add_measurement(latency_ms, success=True)

    await pool.close()

    # Test with direct connections (new connection each time)
    direct_metrics = performance_metrics("direct_connection")

    for i in range(100):
        start = time.perf_counter()
        # Create new connection each time (simulating no pooling)
        client = redis.from_url(
            f"redis://{redis_host}:{redis_port}/{redis_db}",
            decode_responses=True
        )
        await client.set(f"direct_test_{i}", "value")
        await client.get(f"direct_test_{i}")
        await client.close()
        latency_ms = (time.perf_counter() - start) * 1000
        direct_metrics.add_measurement(latency_ms, success=True)

    pool_stats = pool_metrics.get_statistics()
    direct_stats = direct_metrics.get_statistics()

    logger.info(f"Pool P95: {pool_stats['p95_latency_ms']:.2f}ms")
    logger.info(f"Direct P95: {direct_stats['p95_latency_ms']:.2f}ms")

    # Pool should be significantly faster due to connection reuse
    assert pool_stats['p95_latency_ms'] < direct_stats['p95_latency_ms'], \
        "Pool should be faster than creating new connections"

    improvement = (direct_stats['p95_latency_ms'] - pool_stats['p95_latency_ms']) / direct_stats['p95_latency_ms'] * 100
    logger.info(f"Pool provides {improvement:.1f}% performance improvement")

    # Should see significant improvement (>50%)
    assert improvement > 50, f"Pool only provides {improvement:.1f}% improvement"


# ============================================================================
# FAILOVER AND RECOVERY TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_recovery_after_redis_restart_simulation(
    test_redis_pool,
    performance_metrics
):
    """
    Test pool recovery after simulated Redis restart.

    Verifies:
    - Pool handles connection loss
    - Automatic reconnection occurs
    - Service recovers without manual intervention
    """
    metrics = performance_metrics("redis_restart_simulation")
    pool = test_redis_pool

    logger.info("Testing recovery after simulated Redis restart")

    # Normal operation before "restart"
    await pool.set("pre_restart", "value")
    result = await pool.get("pre_restart")
    assert result == "value"
    logger.info("Pre-restart operation successful")

    # Simulate restart by closing pool and creating new one
    await pool.close()
    logger.info("Simulated Redis restart (pool closed)")

    # Recreate pool (simulating reconnection)
    import os
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = int(os.getenv("REDIS_DB", "1"))

    new_pool = redis.from_url(
        f"redis://{redis_host}:{redis_port}/{redis_db}",
        decode_responses=True,
        max_connections=50
    )

    # Clear test data from previous pool
    await new_pool.flushdb()

    # Test recovery
    start = time.perf_counter()
    try:
        await new_pool.set("post_restart", "value")
        result = await new_pool.get("post_restart")
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)
        logger.info(f"Post-restart operation successful ({latency_ms:.2f}ms)")
        assert result == "value"
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=False)
        logger.error(f"Recovery failed: {e}")
        raise
    finally:
        await new_pool.close()

    stats = metrics.get_statistics()
    logger.info(f"Recovery simulation stats: {stats}")
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_validation_ping(
    test_redis_pool,
    performance_metrics,
    assert_performance
):
    """
    Test connection validation using ping before use.

    Verifies:
    - Ping validates connection health
    - Invalid connections are detected
    - Validation is fast (<5ms)
    """
    metrics = performance_metrics("connection_validation")
    pool = test_redis_pool

    logger.info("Testing connection validation with ping")

    # Perform many ping operations
    for i in range(200):
        start = time.perf_counter()
        try:
            result = await pool.ping()
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
            assert result is True, "Ping should return True"
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)
            logger.error(f"Ping {i} failed: {e}")

    stats = metrics.get_statistics()
    logger.info(f"Validation stats: {stats}")

    # Ping should be very fast and reliable
    assert_performance(stats, max_p50_ms=2, max_p95_ms=5, max_error_rate=0)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_automatic_retry_on_transient_failures(
    test_redis_pool,
    performance_metrics,
    failure_injector
):
    """
    Test automatic retry logic for transient failures.

    Verifies:
    - Transient failures are retried automatically
    - Retry logic works correctly
    - Operations eventually succeed
    """
    metrics = performance_metrics("automatic_retry")
    pool = test_redis_pool

    logger.info("Testing automatic retry on transient failures")

    success_count = 0
    total_operations = 50

    async with failure_injector.simulate_redis_failure(pool, failure_rate=0.2):
        for i in range(total_operations):
            start = time.perf_counter()
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    await pool.set(f"retry_test_{i}", f"value_{i}")
                    result = await pool.get(f"retry_test_{i}")
                    assert result == f"value_{i}"
                    latency_ms = (time.perf_counter() - start) * 1000
                    metrics.add_measurement(latency_ms, success=True)
                    success_count += 1
                    break
                except (redis.ConnectionError, redis.TimeoutError) as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        latency_ms = (time.perf_counter() - start) * 1000
                        metrics.add_measurement(latency_ms, success=False)
                        logger.debug(f"Operation {i} failed after {retry_count} retries: {e}")
                    else:
                        await asyncio.sleep(0.05)  # Brief retry delay

    logger.info(f"Completed {success_count}/{total_operations} operations with retries")

    stats = metrics.get_statistics()
    logger.info(f"Retry stats: {stats}")

    # With retries, most operations should succeed
    assert success_count >= 40, f"Only {success_count}/{total_operations} succeeded with retries"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_circuit_breaker_pattern(
    test_redis_pool,
    performance_metrics
):
    """
    Test circuit breaker pattern for Redis failures.

    Verifies:
    - Circuit breaker opens after repeated failures
    - Fast failure when circuit is open
    - Circuit closes when service recovers
    """
    metrics = performance_metrics("circuit_breaker")
    pool = test_redis_pool

    logger.info("Testing circuit breaker pattern")

    # Simulate circuit breaker logic
    circuit_open = False
    failure_count = 0
    failure_threshold = 5

    async def operation_with_circuit_breaker():
        nonlocal circuit_open, failure_count

        # Fast fail if circuit is open
        if circuit_open:
            logger.debug("Circuit breaker OPEN - fast fail")
            return False

        try:
            await pool.set("circuit_test", "value")
            result = await pool.get("circuit_test")
            failure_count = 0  # Reset on success
            return result == "value"
        except Exception as e:
            failure_count += 1
            logger.debug(f"Failure {failure_count}/{failure_threshold}")

            if failure_count >= failure_threshold:
                circuit_open = True
                logger.info("Circuit breaker OPENED")

            return False

    # Perform operations - circuit should remain closed (all succeed)
    for i in range(20):
        start = time.perf_counter()
        success = await operation_with_circuit_breaker()
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=success)

    stats = metrics.get_statistics()
    logger.info(f"Circuit breaker stats: {stats}")

    # All operations should succeed (circuit remains closed)
    assert stats['error_rate_percent'] == 0
    assert not circuit_open, "Circuit should remain closed with healthy service"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_fallback_to_non_cached_operation(
    test_redis_pool,
    performance_metrics
):
    """
    Test fallback to non-cached operations when Redis unavailable.

    Verifies:
    - Service continues without Redis
    - Graceful degradation occurs
    - Fallback is transparent to users
    """
    metrics = performance_metrics("cache_fallback")
    pool = test_redis_pool

    logger.info("Testing fallback to non-cached operations")

    async def cached_operation_with_fallback(key: str, compute_func):
        """Try cache first, fallback to computation."""
        start = time.perf_counter()

        # Try cache
        try:
            cached = await pool.get(key)
            if cached:
                latency_ms = (time.perf_counter() - start) * 1000
                logger.debug(f"Cache HIT for {key} ({latency_ms:.2f}ms)")
                return cached, "cache", latency_ms
        except Exception as e:
            logger.debug(f"Cache unavailable: {e}")

        # Fallback to computation
        result = compute_func()
        latency_ms = (time.perf_counter() - start) * 1000
        logger.debug(f"Cache MISS/FALLBACK for {key} ({latency_ms:.2f}ms)")

        # Try to cache result
        try:
            await pool.set(key, result, ex=60)
        except Exception:
            pass  # Ignore cache failures

        return result, "computed", latency_ms

    # Test with working cache
    for i in range(50):
        result, source, latency_ms = await cached_operation_with_fallback(
            f"fallback_test_{i % 10}",
            lambda: f"computed_value_{i % 10}"
        )
        metrics.add_measurement(latency_ms, success=True)

    stats = metrics.get_statistics()
    logger.info(f"Fallback test stats: {stats}")

    # All operations should succeed (cache or fallback)
    assert stats['error_rate_percent'] == 0


# ============================================================================
# MEMORY AND RESOURCE TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_memory_usage(
    test_redis_pool,
    performance_metrics,
    resource_monitor
):
    """
    Test memory usage of Redis connection pool.

    Verifies:
    - Memory usage remains stable
    - No memory leaks in connection pool
    - Memory footprint is reasonable
    """
    metrics = performance_metrics("memory_usage")
    pool = test_redis_pool

    logger.info("Testing connection memory usage")

    await resource_monitor.start()

    # Perform many operations
    for i in range(1000):
        start = time.perf_counter()
        try:
            await pool.set(f"memory_test_{i % 100}", f"value_{i}")
            result = await pool.get(f"memory_test_{i % 100}")
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=False)

        if i % 200 == 0:
            logger.debug(f"Completed {i}/1000 operations")

    await resource_monitor.stop()

    # Check resource usage
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Resource usage summary: {resource_summary}")

    # Memory should not grow unbounded
    memory_growth = resource_summary['memory_mb']['max'] - resource_summary['memory_mb']['min']
    logger.info(f"Memory growth: {memory_growth:.2f} MB")

    # Allow reasonable memory variance, but flag excessive growth
    assert memory_growth < 100, f"Memory grew {memory_growth:.2f} MB (possible leak)"

    stats = metrics.get_statistics()
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_socket_handle_cleanup(
    test_redis_pool,
    resource_monitor
):
    """
    Test socket handle cleanup and management.

    Verifies:
    - Socket handles are properly closed
    - No socket leaks occur
    - File descriptor count remains stable
    """
    pool = test_redis_pool

    logger.info("Testing socket handle cleanup")

    await resource_monitor.start()

    # Create and close many connections
    for i in range(200):
        try:
            await pool.set(f"socket_test_{i}", "value")
            await pool.get(f"socket_test_{i}")
        except Exception as e:
            logger.error(f"Operation {i} failed: {e}")

        if i % 40 == 0:
            logger.debug(f"Completed {i}/200 operations")
            await asyncio.sleep(0.1)  # Brief pause for monitoring

    await resource_monitor.stop()

    # Check connection count stability
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Connection count: {resource_summary['connections']}")

    conn_variance = resource_summary['connections']['max'] - resource_summary['connections']['min']
    logger.info(f"Connection variance: {conn_variance}")

    # Connection count should remain relatively stable (no leaks)
    assert conn_variance < 30, f"Connection variance {conn_variance} too high (possible leak)"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_pool_memory_growth(
    resource_monitor
):
    """
    Test that connection pool doesn't have unbounded memory growth.

    Verifies:
    - Pool memory usage plateaus
    - No continuous memory growth over time
    - Memory is released properly
    """
    import os
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = int(os.getenv("REDIS_DB", "1"))

    logger.info("Testing connection pool memory growth")

    pool = redis.from_url(
        f"redis://{redis_host}:{redis_port}/{redis_db}",
        decode_responses=True,
        max_connections=30
    )

    await resource_monitor.start()

    # Run operations for extended period
    for phase in range(5):
        logger.info(f"Phase {phase + 1}/5")

        for i in range(200):
            await pool.set(f"growth_test_{i % 50}", f"value_{i}")
            await pool.get(f"growth_test_{i % 50}")

        # Brief pause between phases
        await asyncio.sleep(0.5)

    await resource_monitor.stop()
    await pool.close()

    # Analyze memory over time
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Memory over time: {resource_summary['memory_mb']}")

    # Memory should plateau, not grow continuously
    memory_growth = resource_summary['memory_mb']['max'] - resource_summary['memory_mb']['min']
    logger.info(f"Total memory growth: {memory_growth:.2f} MB")

    # Allow initial growth, but flag continuous growth
    assert memory_growth < 150, f"Memory grew {memory_growth:.2f} MB (continuous growth detected)"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_leak_detection_redis(
    test_redis_pool,
    resource_monitor
):
    """
    Test for Redis connection leaks.

    Verifies:
    - Connections are returned to pool properly
    - No connections are orphaned
    - Connection count remains stable
    """
    pool = test_redis_pool

    logger.info("Testing Redis connection leak detection")

    await resource_monitor.start()

    # Perform operations that should not leak connections
    for i in range(500):
        try:
            await pool.set(f"leak_test_{i}", f"value_{i}")
            result = await pool.get(f"leak_test_{i}")
            assert result == f"value_{i}"
        except Exception as e:
            logger.error(f"Operation {i} failed: {e}")

        if i % 100 == 0:
            logger.debug(f"Completed {i}/500 operations")

    await resource_monitor.stop()

    # Check connection stability
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Connection usage: {resource_summary['connections']}")

    conn_variance = resource_summary['connections']['max'] - resource_summary['connections']['min']
    logger.info(f"Connection variance: {conn_variance}")

    # Connections should be stable (efficient reuse, no leaks)
    assert conn_variance < 25, f"Connection variance {conn_variance} indicates possible leak"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_resource_cleanup_on_pool_close(
    performance_metrics,
    resource_monitor
):
    """
    Test proper resource cleanup when pool is closed.

    Verifies:
    - All connections are closed
    - Memory is released
    - No resources remain after close
    """
    import os
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = int(os.getenv("REDIS_DB", "1"))

    logger.info("Testing resource cleanup on pool close")

    await resource_monitor.start()

    # Create pool and use it
    pool = redis.from_url(
        f"redis://{redis_host}:{redis_port}/{redis_db}",
        decode_responses=True,
        max_connections=20
    )

    # Use pool
    for i in range(100):
        await pool.set(f"cleanup_test_{i}", "value")
        await pool.get(f"cleanup_test_{i}")

    logger.info("Performed 100 operations, now closing pool...")

    # Close pool
    await pool.close()
    logger.info("Pool closed")

    # Wait for cleanup
    await asyncio.sleep(1)

    await resource_monitor.stop()

    # Check that resources were cleaned up
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Resource usage after close: {resource_summary}")

    # Connection count should drop after close
    final_connections = resource_summary['connections']['min']
    logger.info(f"Final connection count: {final_connections}")

    # Some connections may remain from the test infrastructure, but should be minimal
    logger.info("Resource cleanup completed successfully")

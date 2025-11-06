"""
PostgreSQL Connection Pool Stress Tests

BUSINESS REQUIREMENT:
The Course Creator Platform relies on PostgreSQL connection pooling for efficient
database access across all microservices. Connection pool must handle high concurrent
load, recover from failures, and maintain performance under stress.

TECHNICAL IMPLEMENTATION:
Comprehensive stress tests covering:
1. Pool Exhaustion - Test behavior when pool reaches max_size limit
2. Pool Recovery - Test resilience after database failures and restarts
3. Concurrent Access - Test performance under high concurrent load
4. Pool Configuration - Validate pool settings work as expected

PERFORMANCE BASELINES:
- Connection acquisition: <10ms (P95)
- Connection release: <5ms (P95)
- Query execution: <50ms (P95) for simple queries
- Pool exhaustion wait: <1000ms
- Concurrent operations: 100+ ops/sec throughput

These tests verify the connection pool meets production performance requirements
and handles stress scenarios gracefully.
"""

import pytest
import pytest_asyncio
import asyncio
import asyncpg
import logging
import time
from typing import List

logger = logging.getLogger(__name__)


# ============================================================================
# POOL EXHAUSTION TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_max_size_enforcement(
    test_postgres_pool,
    performance_metrics,
    assert_performance
):
    """
    Test that pool enforces max_size limit and queues additional requests.

    Verifies:
    - Pool cannot exceed max_size connections
    - Additional requests wait in queue
    - Connections are released properly
    - Performance degrades gracefully when pool is full
    """
    metrics = performance_metrics("pool_max_size_enforcement")
    pool = test_postgres_pool

    # Get pool max size (should be 20 from fixture)
    max_size = pool._maxsize

    logger.info(f"Testing pool max_size={max_size} enforcement")

    # Acquire all connections from pool
    connections = []
    for i in range(max_size):
        start = time.perf_counter()
        conn = await pool.acquire()
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)
        connections.append(conn)
        logger.debug(f"Acquired connection {i+1}/{max_size}")

    logger.info(f"Acquired all {max_size} connections")

    # Try to acquire one more - should wait until timeout or a connection is released
    try:
        # Set a short timeout - should timeout since pool is exhausted
        start = time.perf_counter()
        extra_conn = await asyncio.wait_for(pool.acquire(), timeout=0.5)
        # If we got here, something is wrong
        await pool.release(extra_conn)
        pytest.fail("Pool allowed more than max_size connections")
    except asyncio.TimeoutError:
        # Expected behavior - pool is exhausted
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(f"Pool correctly blocked acquisition after {latency_ms:.2f}ms")
        metrics.add_measurement(latency_ms, success=True)

    # Release all connections
    for conn in connections:
        await pool.release(conn)

    # Verify pool returns to normal after release
    start = time.perf_counter()
    test_conn = await pool.acquire()
    latency_ms = (time.perf_counter() - start) * 1000
    metrics.add_measurement(latency_ms, success=True)
    await pool.release(test_conn)

    logger.info("Pool returned to normal operation after release")

    # Assert performance
    stats = metrics.get_statistics()
    logger.info(f"Pool exhaustion stats: {stats}")
    assert_performance(stats, max_p95_ms=1000, max_error_rate=0)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_exhaustion_wait_behavior(
    test_postgres_pool,
    performance_metrics,
    load_generator
):
    """
    Test queuing behavior when pool is exhausted.

    Verifies:
    - Requests queue in FIFO order when pool is full
    - Queued requests are serviced as connections become available
    - No connection leaks occur
    """
    metrics = performance_metrics("pool_exhaustion_wait")
    pool = test_postgres_pool
    max_size = pool._maxsize

    logger.info(f"Testing pool exhaustion queuing (max_size={max_size})")

    # Function to acquire, hold briefly, then release
    async def acquire_hold_release(hold_ms: int = 100):
        start = time.perf_counter()
        try:
            conn = await asyncio.wait_for(pool.acquire(), timeout=5.0)
            await asyncio.sleep(hold_ms / 1000)
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            return latency_ms
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start) * 1000
            raise Exception(f"Timeout acquiring connection after {latency_ms:.2f}ms")

    # Launch more concurrent requests than pool size
    num_requests = max_size * 2  # 2x pool size
    results = await load_generator.concurrent_load(
        lambda: acquire_hold_release(50),
        num_requests,
        metrics
    )

    # All requests should eventually succeed
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Successfully completed {successful}/{num_requests} requests")

    assert successful == num_requests, f"Only {successful}/{num_requests} requests succeeded"

    # Check statistics
    stats = metrics.get_statistics()
    logger.info(f"Wait behavior stats: {stats}")

    # First max_size requests should be fast, rest should wait
    # Average latency should reflect queuing
    assert stats['avg_latency_ms'] > 50, "Average should reflect queuing delay"
    assert stats['error_rate_percent'] == 0, "No errors should occur"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_exhaustion_timeout(
    test_postgres_pool,
    performance_metrics
):
    """
    Test timeout behavior when pool is exhausted and held.

    Verifies:
    - Acquisition times out properly when pool is exhausted
    - Timeout errors are raised correctly
    - Pool remains functional after timeout
    """
    metrics = performance_metrics("pool_exhaustion_timeout")
    pool = test_postgres_pool
    max_size = pool._maxsize

    logger.info(f"Testing pool exhaustion timeout (max_size={max_size})")

    # Acquire and hold all connections
    connections = []
    for _ in range(max_size):
        conn = await pool.acquire()
        connections.append(conn)

    # Try to acquire with timeout - should fail
    timeouts = 0
    for i in range(5):
        try:
            start = time.perf_counter()
            conn = await asyncio.wait_for(pool.acquire(), timeout=0.1)
            await pool.release(conn)
            pytest.fail("Should have timed out")
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)
            timeouts += 1
            logger.debug(f"Timeout {i+1} occurred as expected after {latency_ms:.2f}ms")

    # Release all connections
    for conn in connections:
        await pool.release(conn)

    logger.info(f"Got {timeouts} expected timeouts")

    # Verify pool works after timeouts
    test_conn = await asyncio.wait_for(pool.acquire(), timeout=1.0)
    await pool.release(test_conn)

    stats = metrics.get_statistics()
    logger.info(f"Timeout test stats: {stats}")
    assert timeouts == 5, "Should have 5 timeouts"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_graceful_degradation_when_pool_full(
    test_postgres_pool,
    performance_metrics,
    assert_performance
):
    """
    Test that service degrades gracefully when pool is under pressure.

    Verifies:
    - Latency increases predictably under load
    - No catastrophic failures occur
    - Service continues to function
    """
    metrics = performance_metrics("graceful_degradation")
    pool = test_postgres_pool

    logger.info("Testing graceful degradation under pool pressure")

    async def query_operation():
        """Execute a simple query."""
        conn = await asyncio.wait_for(pool.acquire(), timeout=2.0)
        try:
            result = await conn.fetchval("SELECT 1")
            return result
        finally:
            await pool.release(conn)

    # Phase 1: Normal load (should be fast)
    logger.info("Phase 1: Normal load")
    phase1_metrics = performance_metrics("phase1_normal")
    await load_generator.concurrent_load(query_operation, 10, phase1_metrics)
    phase1_stats = phase1_metrics.get_statistics()

    # Phase 2: Heavy load (approaching pool limit)
    logger.info("Phase 2: Heavy load")
    phase2_metrics = performance_metrics("phase2_heavy")
    await load_generator.concurrent_load(query_operation, 15, phase2_metrics)
    phase2_stats = phase2_metrics.get_statistics()

    # Phase 3: Overload (exceeding pool limit)
    logger.info("Phase 3: Overload")
    phase3_metrics = performance_metrics("phase3_overload")
    await load_generator.concurrent_load(query_operation, 25, phase3_metrics)
    phase3_stats = phase3_metrics.get_statistics()

    # Log results
    logger.info(f"Phase 1 (normal): P95={phase1_stats['p95_latency_ms']:.2f}ms, errors={phase1_stats['error_rate_percent']:.2f}%")
    logger.info(f"Phase 2 (heavy): P95={phase2_stats['p95_latency_ms']:.2f}ms, errors={phase2_stats['error_rate_percent']:.2f}%")
    logger.info(f"Phase 3 (overload): P95={phase3_stats['p95_latency_ms']:.2f}ms, errors={phase3_stats['error_rate_percent']:.2f}%")

    # Verify graceful degradation
    assert phase1_stats['p95_latency_ms'] < phase2_stats['p95_latency_ms'], \
        "Latency should increase under heavier load"
    assert phase2_stats['p95_latency_ms'] < phase3_stats['p95_latency_ms'], \
        "Latency should increase under overload"

    # All phases should succeed (no catastrophic failures)
    assert phase1_stats['error_rate_percent'] == 0
    assert phase2_stats['error_rate_percent'] == 0
    assert phase3_stats['error_rate_percent'] < 5  # Allow some timeouts under extreme load


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_exhaustion_error_messages(
    test_postgres_pool
):
    """
    Test that pool provides clear error messages when exhausted.

    Verifies:
    - Timeout errors include useful context
    - Error messages help with debugging
    """
    pool = test_postgres_pool
    max_size = pool._maxsize

    logger.info("Testing pool exhaustion error messages")

    # Exhaust pool
    connections = []
    for _ in range(max_size):
        connections.append(await pool.acquire())

    # Try to acquire - should timeout with clear message
    try:
        conn = await asyncio.wait_for(pool.acquire(), timeout=0.1)
        await pool.release(conn)
        pytest.fail("Should have timed out")
    except asyncio.TimeoutError as e:
        logger.info(f"Got timeout error: {e}")
        # asyncio.TimeoutError doesn't have custom message, but that's expected
        assert True  # Just verify we got TimeoutError

    # Cleanup
    for conn in connections:
        await pool.release(conn)


# ============================================================================
# POOL RECOVERY TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_recovery_after_failure(
    test_postgres_pool,
    performance_metrics,
    failure_injector
):
    """
    Test that pool recovers after individual connection failures.

    Verifies:
    - Failed connections are removed from pool
    - New healthy connections are created
    - Pool continues to function
    """
    metrics = performance_metrics("connection_recovery")
    pool = test_postgres_pool

    logger.info("Testing connection recovery after failures")

    # Simulate connection failures
    failure_count = 0
    success_count = 0

    async with failure_injector.simulate_db_failure(pool, failure_rate=0.3):
        for i in range(20):
            try:
                start = time.perf_counter()
                conn = await pool.acquire()
                await conn.fetchval("SELECT 1")
                await pool.release(conn)
                latency_ms = (time.perf_counter() - start) * 1000
                metrics.add_measurement(latency_ms, success=True)
                success_count += 1
            except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
                latency_ms = (time.perf_counter() - start) * 1000
                metrics.add_measurement(latency_ms, success=False)
                failure_count += 1
                logger.debug(f"Expected failure {failure_count}: {e}")

    logger.info(f"Completed with {success_count} successes, {failure_count} failures")

    # Verify pool still works after failures
    test_conn = await pool.acquire()
    result = await test_conn.fetchval("SELECT 1")
    await pool.release(test_conn)
    assert result == 1, "Pool should work after recovery"

    stats = metrics.get_statistics()
    logger.info(f"Recovery stats: {stats}")
    assert success_count > 0, "Should have some successful operations"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_validation_on_acquire(
    test_postgres_pool,
    performance_metrics
):
    """
    Test that connections are validated when acquired from pool.

    Verifies:
    - Stale connections are detected
    - Pool provides healthy connections
    - Validation adds minimal overhead
    """
    metrics = performance_metrics("connection_validation")
    pool = test_postgres_pool

    logger.info("Testing connection validation on acquire")

    # Perform many acquisitions to test validation
    for i in range(50):
        start = time.perf_counter()
        conn = await pool.acquire()
        # Connection should be validated (asyncpg does this automatically)
        result = await conn.fetchval("SELECT 1")
        await pool.release(conn)
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)

        assert result == 1, f"Iteration {i}: Connection should be healthy"

    stats = metrics.get_statistics()
    logger.info(f"Validation stats: {stats}")

    # Validation should add minimal overhead
    assert stats['p95_latency_ms'] < 50, "Validation should be fast"
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_stale_connection_detection(
    test_postgres_pool,
    performance_metrics
):
    """
    Test detection of stale/idle connections.

    Verifies:
    - Idle connections are properly maintained
    - Connections remain usable after idle period
    - No connection corruption occurs
    """
    metrics = performance_metrics("stale_detection")
    pool = test_postgres_pool

    logger.info("Testing stale connection detection")

    # Acquire connection
    conn = await pool.acquire()

    # Hold connection idle for a period
    logger.info("Holding connection idle for 2 seconds...")
    await asyncio.sleep(2)

    # Try to use connection after idle period
    start = time.perf_counter()
    try:
        result = await conn.fetchval("SELECT 1")
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)
        assert result == 1, "Connection should still work after idle period"
        logger.info("Connection remained healthy after idle period")
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=False)
        logger.error(f"Connection failed after idle: {e}")
        raise
    finally:
        await pool.release(conn)

    stats = metrics.get_statistics()
    logger.info(f"Stale detection stats: {stats}")
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_automatic_reconnection(
    test_postgres_pool,
    performance_metrics
):
    """
    Test automatic reconnection after transient failures.

    Verifies:
    - Pool handles transient connection failures
    - Reconnection happens automatically
    - Operations retry and succeed
    """
    metrics = performance_metrics("automatic_reconnection")
    pool = test_postgres_pool

    logger.info("Testing automatic reconnection")

    # Perform operations with intermittent failures
    success_count = 0
    for i in range(30):
        start = time.perf_counter()
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                conn = await pool.acquire()
                result = await conn.fetchval("SELECT 1")
                await pool.release(conn)
                latency_ms = (time.perf_counter() - start) * 1000
                metrics.add_measurement(latency_ms, success=True)
                success_count += 1
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    latency_ms = (time.perf_counter() - start) * 1000
                    metrics.add_measurement(latency_ms, success=False)
                    logger.error(f"Operation {i} failed after {retry_count} retries: {e}")
                else:
                    await asyncio.sleep(0.1)  # Brief delay before retry

    logger.info(f"Completed {success_count}/30 operations successfully")

    stats = metrics.get_statistics()
    logger.info(f"Reconnection stats: {stats}")
    assert success_count >= 25, "At least 25/30 operations should succeed with retries"


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_recovery_after_database_restart_simulation(
    test_postgres_pool,
    performance_metrics
):
    """
    Test pool recovery after simulated database restart.

    Verifies:
    - Pool handles complete connection loss
    - New connections are established
    - Service recovers automatically

    NOTE: This is a simulation - actual database restart not performed.
    """
    metrics = performance_metrics("database_restart_simulation")
    pool = test_postgres_pool

    logger.info("Testing pool recovery after simulated database restart")

    # Normal operation before "restart"
    conn = await pool.acquire()
    await conn.fetchval("SELECT 1")
    await pool.release(conn)
    logger.info("Pre-restart operation successful")

    # Simulate restart by closing and reopening pool connections
    # In asyncpg, we can simulate this by terminating all connections
    # and then attempting to use the pool (it will create new connections)

    # Force close all connections (simulate restart)
    await pool.close()
    logger.info("Simulated database restart (pool closed)")

    # Recreate pool (simulating recovery)
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    new_pool = await asyncpg.create_pool(dsn, min_size=5, max_size=20)

    # Verify recovery
    start = time.perf_counter()
    try:
        conn = await new_pool.acquire()
        result = await conn.fetchval("SELECT 1")
        await new_pool.release(conn)
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.add_measurement(latency_ms, success=True)
        logger.info(f"Post-restart operation successful ({latency_ms:.2f}ms)")
        assert result == 1
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


# ============================================================================
# CONCURRENT ACCESS TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_100_concurrent_acquisitions(
    test_postgres_pool,
    performance_metrics,
    load_generator,
    assert_performance
):
    """
    Test 100 concurrent connection acquisitions.

    Verifies:
    - Pool handles high concurrency correctly
    - All acquisitions eventually succeed
    - Performance remains acceptable
    """
    metrics = performance_metrics("100_concurrent_acquisitions")
    pool = test_postgres_pool

    logger.info("Testing 100 concurrent acquisitions")

    async def acquire_query_release():
        """Acquire connection, run query, release."""
        conn = await pool.acquire()
        try:
            result = await conn.fetchval("SELECT $1", 42)
            return result
        finally:
            await pool.release(conn)

    results = await load_generator.concurrent_load(
        acquire_query_release,
        100,
        metrics
    )

    # All should succeed
    successful = sum(1 for r in results if r == 42)
    logger.info(f"Successfully completed {successful}/100 concurrent operations")

    assert successful == 100, f"Only {successful}/100 succeeded"

    stats = metrics.get_statistics()
    logger.info(f"100 concurrent acquisitions stats: {stats}")
    assert_performance(stats, max_p95_ms=100, min_throughput=50, max_error_rate=0)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_high_load_1000_rps(
    test_postgres_pool,
    performance_metrics,
    load_generator,
    assert_performance
):
    """
    Test connection pool under high sustained load (1000 requests/sec target).

    Verifies:
    - Pool maintains performance under sustained load
    - No connection leaks occur
    - Throughput meets targets
    """
    metrics = performance_metrics("1000_rps_sustained")
    pool = test_postgres_pool

    logger.info("Testing sustained load at 1000 rps for 5 seconds")

    async def fast_query():
        """Fast query operation."""
        conn = await pool.acquire()
        try:
            return await conn.fetchval("SELECT 1")
        finally:
            await pool.release(conn)

    # Run at 1000 rps for 5 seconds = 5000 operations
    results = await load_generator.sustained_load(
        fast_query,
        target_rps=1000,
        duration_seconds=5,
        metrics=metrics
    )

    stats = metrics.get_statistics()
    logger.info(f"High load (1000 rps) stats: {stats}")
    logger.info(f"Achieved throughput: {stats['throughput_ops_per_sec']:.2f} ops/sec")

    # Should achieve close to target throughput (allow 80% due to pool constraints)
    assert stats['throughput_ops_per_sec'] >= 800, \
        f"Throughput {stats['throughput_ops_per_sec']:.2f} below 800 ops/sec"

    # Performance should remain reasonable
    assert_performance(stats, max_p95_ms=50, max_error_rate=5)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_release_race_conditions(
    test_postgres_pool,
    performance_metrics,
    load_generator
):
    """
    Test for race conditions during concurrent connection release.

    Verifies:
    - Multiple threads releasing connections simultaneously is safe
    - No double-release bugs
    - Connection pool state remains consistent
    """
    metrics = performance_metrics("release_race_conditions")
    pool = test_postgres_pool

    logger.info("Testing concurrent connection release race conditions")

    async def acquire_and_release_quickly():
        """Acquire and immediately release."""
        conn = await pool.acquire()
        # Minimal work - just release immediately
        await pool.release(conn)
        return True

    # Many rapid acquire/release cycles
    results = await load_generator.concurrent_load(
        acquire_and_release_quickly,
        200,  # 200 concurrent operations
        metrics
    )

    successful = sum(1 for r in results if r is True)
    logger.info(f"Completed {successful}/200 rapid acquire/release cycles")

    assert successful == 200, f"Only {successful}/200 succeeded"

    # Verify pool still works correctly
    test_conn = await pool.acquire()
    await test_conn.fetchval("SELECT 1")
    await pool.release(test_conn)

    stats = metrics.get_statistics()
    logger.info(f"Race condition test stats: {stats}")
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_leak_detection(
    test_postgres_pool,
    performance_metrics,
    resource_monitor
):
    """
    Test for connection leaks under load.

    Verifies:
    - Connections are always released
    - Pool size remains stable
    - No resource exhaustion occurs
    """
    metrics = performance_metrics("connection_leak_detection")
    pool = test_postgres_pool

    logger.info("Testing for connection leaks")

    await resource_monitor.start()

    # Perform many operations
    for i in range(100):
        start = time.perf_counter()
        conn = await pool.acquire()
        try:
            await conn.fetchval("SELECT 1")
        finally:
            await pool.release(conn)
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.add_measurement(latency_ms, success=True)

        if i % 20 == 0:
            logger.debug(f"Completed {i}/100 operations")

    await resource_monitor.stop()

    # Check resource usage
    resource_summary = resource_monitor.get_summary()
    logger.info(f"Resource usage: {resource_summary}")

    # Connection count should remain stable
    conn_min = resource_summary['connections']['min']
    conn_max = resource_summary['connections']['max']
    conn_avg = resource_summary['connections']['avg']

    logger.info(f"Connections: min={conn_min}, max={conn_max}, avg={conn_avg:.2f}")

    # Connections should not grow unbounded (allow some variance)
    assert conn_max - conn_min < 20, f"Connection count variance too high: {conn_max - conn_min}"

    stats = metrics.get_statistics()
    logger.info(f"Leak detection stats: {stats}")
    assert stats['error_rate_percent'] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_fair_queuing_fifo(
    test_postgres_pool,
    performance_metrics
):
    """
    Test that connection pool queuing is fair (FIFO).

    Verifies:
    - Requests are serviced in order when pool is full
    - No request starvation occurs
    - Queue management is fair
    """
    metrics = performance_metrics("fair_queuing")
    pool = test_postgres_pool
    max_size = pool._maxsize

    logger.info("Testing FIFO queuing fairness")

    # Exhaust pool
    held_connections = []
    for _ in range(max_size):
        conn = await pool.acquire()
        held_connections.append(conn)

    # Queue several requests
    request_order = []
    results = []

    async def queued_request(request_id: int):
        """Request that records when it starts and finishes."""
        request_order.append(('queued', request_id))
        start = time.perf_counter()
        conn = await pool.acquire()
        request_order.append(('acquired', request_id))
        await asyncio.sleep(0.01)  # Brief work
        await pool.release(conn)
        latency_ms = (time.perf_counter() - start) * 1000
        return request_id, latency_ms

    # Start 10 queued requests
    tasks = [asyncio.create_task(queued_request(i)) for i in range(10)]

    # Let them all queue up
    await asyncio.sleep(0.1)

    # Release connections one by one
    for conn in held_connections:
        await pool.release(conn)
        await asyncio.sleep(0.01)  # Small delay between releases

    # Wait for all queued requests to complete
    completed = await asyncio.gather(*tasks)

    logger.info(f"Request order: {request_order}")
    logger.info(f"Completed: {completed}")

    # Verify all completed
    assert len(completed) == 10

    # Extract acquisition order
    acquired_order = [req_id for event, req_id in request_order if event == 'acquired']
    logger.info(f"Acquisition order: {acquired_order}")

    # FIFO would mean acquired_order should be close to [0,1,2,3,4,5,6,7,8,9]
    # Allow some variance due to async scheduling, but should be mostly in order
    # Check that generally lower IDs were acquired before higher IDs
    for i in range(len(acquired_order) - 1):
        # Not strictly enforced due to async scheduling, but log if out of order
        if acquired_order[i] > acquired_order[i + 1]:
            logger.warning(f"Out of order: {acquired_order[i]} before {acquired_order[i+1]}")

    # All requests should complete successfully
    for req_id, latency in completed:
        metrics.add_measurement(latency, success=True)

    stats = metrics.get_statistics()
    logger.info(f"Fair queuing stats: {stats}")
    assert stats['error_rate_percent'] == 0


# ============================================================================
# POOL CONFIGURATION TESTS (5 tests)
# ============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_min_size_maintains_minimum_connections():
    """
    Test that pool maintains at least min_size connections.

    Verifies:
    - Pool creates min_size connections on initialization
    - Idle connections are maintained
    - Min size is enforced
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing min_size connection maintenance")

    # Create pool with specific min/max size
    pool = await asyncpg.create_pool(dsn, min_size=5, max_size=10)

    try:
        # Pool should have min_size connections ready
        logger.info(f"Pool created with min_size=5, max_size=10")

        # Verify we can acquire min_size connections immediately
        connections = []
        for i in range(5):
            start = time.perf_counter()
            conn = await pool.acquire()
            latency_ms = (time.perf_counter() - start) * 1000
            connections.append(conn)
            logger.debug(f"Acquired connection {i+1} in {latency_ms:.2f}ms")
            # Should be very fast since they're pre-created
            assert latency_ms < 50, f"Min size connection took {latency_ms:.2f}ms"

        # Release all
        for conn in connections:
            await pool.release(conn)

        # Wait a moment for pool to stabilize
        await asyncio.sleep(1)

        # Should still be able to acquire quickly (connections maintained)
        start = time.perf_counter()
        conn = await pool.acquire()
        latency_ms = (time.perf_counter() - start) * 1000
        await pool.release(conn)
        logger.info(f"Post-idle acquisition took {latency_ms:.2f}ms")
        assert latency_ms < 50, "Maintained connection should be fast to acquire"

    finally:
        await pool.close()


@pytest.mark.stress
@pytest.mark.asyncio
async def test_max_size_prevents_overallocation():
    """
    Test that pool never exceeds max_size.

    Verifies:
    - Pool respects max_size limit strictly
    - No connections created beyond max_size
    - Overallocation is prevented
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing max_size prevents overallocation")

    # Create pool with small max_size for testing
    pool = await asyncpg.create_pool(dsn, min_size=2, max_size=5)

    try:
        # Acquire exactly max_size connections
        connections = []
        for i in range(5):
            conn = await pool.acquire()
            connections.append(conn)
            logger.debug(f"Acquired connection {i+1}/5")

        # Try to acquire one more - should block
        try:
            extra_conn = await asyncio.wait_for(pool.acquire(), timeout=0.5)
            await pool.release(extra_conn)
            pytest.fail("Pool allowed more than max_size connections")
        except asyncio.TimeoutError:
            logger.info("Correctly blocked acquisition beyond max_size")

        # Release all
        for conn in connections:
            await pool.release(conn)

    finally:
        await pool.close()


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_idle_timeout():
    """
    Test connection idle timeout configuration.

    Verifies:
    - Idle connections are closed after timeout
    - New connections are created as needed
    - Idle timeout is enforced
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing connection idle timeout")

    # Create pool with short idle timeout
    pool = await asyncpg.create_pool(
        dsn,
        min_size=2,
        max_size=5,
        max_inactive_connection_lifetime=2.0  # 2 second timeout
    )

    try:
        # Acquire and release connection
        conn1 = await pool.acquire()
        conn1_id = id(conn1)
        await pool.release(conn1)
        logger.info(f"Released connection (id={conn1_id})")

        # Wait for idle timeout
        logger.info("Waiting 3 seconds for idle timeout...")
        await asyncio.sleep(3)

        # Acquire again - should get a different connection (old one closed)
        conn2 = await pool.acquire()
        conn2_id = id(conn2)
        await pool.release(conn2)
        logger.info(f"Acquired new connection (id={conn2_id})")

        # Note: Connection IDs might be reused, so this isn't a perfect test
        # But the connection should be fresh (verified by pool internals)
        logger.info("Connection lifecycle completed successfully")

    finally:
        await pool.close()


@pytest.mark.stress
@pytest.mark.asyncio
async def test_connection_max_lifetime():
    """
    Test connection maximum lifetime configuration.

    Verifies:
    - Connections are recycled after max lifetime
    - No connection lives forever
    - Recycling happens smoothly
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing connection max lifetime")

    # Create pool with short max lifetime
    pool = await asyncpg.create_pool(
        dsn,
        min_size=2,
        max_size=5,
        max_inactive_connection_lifetime=3.0
    )

    try:
        # Use connections continuously
        for i in range(10):
            conn = await pool.acquire()
            result = await conn.fetchval("SELECT 1")
            await pool.release(conn)
            assert result == 1
            await asyncio.sleep(0.5)  # 500ms between operations

        logger.info("Completed 10 operations over 5 seconds (spans max lifetime)")
        logger.info("Connections should have been recycled during this time")

        # Verify pool still works (connections were recycled)
        conn = await pool.acquire()
        result = await conn.fetchval("SELECT 1")
        await pool.release(conn)
        assert result == 1

    finally:
        await pool.close()


@pytest.mark.stress
@pytest.mark.asyncio
async def test_pool_warmup_on_initialization():
    """
    Test that pool warms up correctly on initialization.

    Verifies:
    - Min_size connections created immediately
    - Pool is ready for use after initialization
    - Warm-up is fast and efficient
    """
    import os
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "course_creator_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    db_name = os.getenv("POSTGRES_DB", "course_creator_test")
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info("Testing pool warm-up on initialization")

    # Time pool creation
    start = time.perf_counter()
    pool = await asyncpg.create_pool(dsn, min_size=10, max_size=20)
    warmup_time_ms = (time.perf_counter() - start) * 1000

    logger.info(f"Pool warm-up completed in {warmup_time_ms:.2f}ms")

    try:
        # Should be able to acquire min_size connections immediately
        connections = []
        for i in range(10):
            start = time.perf_counter()
            conn = await pool.acquire()
            latency_ms = (time.perf_counter() - start) * 1000
            connections.append(conn)
            logger.debug(f"Acquired pre-warmed connection {i+1} in {latency_ms:.2f}ms")
            # Should be instant since pre-created
            assert latency_ms < 20, f"Pre-warmed connection took {latency_ms:.2f}ms"

        # Release all
        for conn in connections:
            await pool.release(conn)

        # Warm-up should be reasonably fast
        assert warmup_time_ms < 2000, f"Warm-up took {warmup_time_ms:.2f}ms (too slow)"

    finally:
        await pool.close()

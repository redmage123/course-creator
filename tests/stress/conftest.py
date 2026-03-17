"""
Stress Test Fixtures for Connection Pool Testing

BUSINESS REQUIREMENT:
The Course Creator Platform requires robust connection pool management for PostgreSQL
and Redis to handle high concurrent load while maintaining performance and reliability.
These fixtures provide comprehensive testing infrastructure for connection pool stress testing.

TECHNICAL IMPLEMENTATION:
This module provides specialized pytest fixtures for stress testing:
1. Load generation - Simulate concurrent user load patterns
2. Performance timing - Measure and assert on latency and throughput metrics
3. Resource monitoring - Track CPU, memory, connection counts
4. Failure injection - Simulate network and database failures for resilience testing

USAGE:
These fixtures are automatically available to all tests in the stress/ directory.
Import them by simply using them as function parameters in test functions.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
import psutil
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis

# Configure logging for stress tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    Performance metrics container for stress test measurements.

    Tracks key performance indicators including latency percentiles,
    throughput, error rates, and resource utilization.
    """
    operation_name: str
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    latencies: List[float] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_measurement(self, latency_ms: float, success: bool = True):
        """Add a single operation measurement."""
        self.total_operations += 1
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        self.latencies.append(latency_ms)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive performance statistics.

        Returns:
            Dict containing percentiles, averages, throughput, and error rates
        """
        if not self.latencies:
            return {}

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        # Calculate percentiles
        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        # Calculate duration and throughput
        duration_seconds = 0
        if self.start_time and self.end_time:
            duration_seconds = (self.end_time - self.start_time).total_seconds()

        throughput = self.total_operations / duration_seconds if duration_seconds > 0 else 0

        return {
            'operation': self.operation_name,
            'total_operations': self.total_operations,
            'successful': self.successful_operations,
            'failed': self.failed_operations,
            'error_rate_percent': (self.failed_operations / self.total_operations * 100) if self.total_operations > 0 else 0,
            'min_latency_ms': min(sorted_latencies),
            'max_latency_ms': max(sorted_latencies),
            'avg_latency_ms': sum(sorted_latencies) / n,
            'p50_latency_ms': sorted_latencies[p50_idx],
            'p95_latency_ms': sorted_latencies[p95_idx],
            'p99_latency_ms': sorted_latencies[p99_idx],
            'duration_seconds': duration_seconds,
            'throughput_ops_per_sec': throughput
        }


@dataclass
class ResourceSnapshot:
    """
    System resource snapshot for monitoring resource usage during stress tests.
    """
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    open_connections: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'open_connections': self.open_connections
        }


class LoadGenerator:
    """
    Load generation utility for simulating concurrent user patterns.

    Provides methods to generate realistic concurrent load patterns including:
    - Steady state load (constant concurrency)
    - Spike load (sudden increase in traffic)
    - Ramp-up load (gradual increase)
    - Wave load (cyclical patterns)
    """

    @staticmethod
    async def concurrent_load(
        operation: Callable[[], Awaitable[Any]],
        num_concurrent: int,
        metrics: PerformanceMetrics
    ) -> List[Any]:
        """
        Execute operation with N concurrent tasks.

        Args:
            operation: Async function to execute concurrently
            num_concurrent: Number of concurrent executions
            metrics: Metrics container to record results

        Returns:
            List of operation results
        """
        async def timed_operation():
            start = time.perf_counter()
            success = True
            result = None
            try:
                result = await operation()
            except Exception as e:
                success = False
                logger.error(f"Operation failed: {e}")
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                metrics.add_measurement(latency_ms, success)
            return result

        metrics.start_time = datetime.utcnow()
        results = await asyncio.gather(*[timed_operation() for _ in range(num_concurrent)], return_exceptions=True)
        metrics.end_time = datetime.utcnow()

        return results

    @staticmethod
    async def sustained_load(
        operation: Callable[[], Awaitable[Any]],
        target_rps: int,
        duration_seconds: int,
        metrics: PerformanceMetrics
    ) -> List[Any]:
        """
        Execute operation at target requests per second for duration.

        Maintains consistent load over time to simulate steady-state traffic.

        Args:
            operation: Async function to execute
            target_rps: Target requests per second
            duration_seconds: How long to sustain load
            metrics: Metrics container

        Returns:
            List of operation results
        """
        interval = 1.0 / target_rps
        results = []

        metrics.start_time = datetime.utcnow()
        end_time = time.perf_counter() + duration_seconds

        while time.perf_counter() < end_time:
            start = time.perf_counter()
            success = True
            try:
                result = await operation()
                results.append(result)
            except Exception as e:
                success = False
                logger.error(f"Operation failed: {e}")
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                metrics.add_measurement(latency_ms, success)

            # Wait for next interval
            elapsed = time.perf_counter() - start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)

        metrics.end_time = datetime.utcnow()
        return results

    @staticmethod
    async def spike_load(
        operation: Callable[[], Awaitable[Any]],
        baseline_rps: int,
        spike_rps: int,
        baseline_duration: int,
        spike_duration: int,
        metrics: PerformanceMetrics
    ) -> List[Any]:
        """
        Execute with baseline load, then spike, then return to baseline.

        Simulates traffic spike scenarios to test pool behavior under sudden load changes.

        Args:
            operation: Async function to execute
            baseline_rps: Normal load level
            spike_rps: Spike load level
            baseline_duration: How long baseline phase lasts (seconds)
            spike_duration: How long spike lasts (seconds)
            metrics: Metrics container

        Returns:
            List of operation results
        """
        results = []

        # Phase 1: Baseline
        logger.info(f"Spike test: Baseline phase ({baseline_rps} rps for {baseline_duration}s)")
        baseline_results = await LoadGenerator.sustained_load(
            operation, baseline_rps, baseline_duration, metrics
        )
        results.extend(baseline_results)

        # Phase 2: Spike
        logger.info(f"Spike test: SPIKE phase ({spike_rps} rps for {spike_duration}s)")
        spike_results = await LoadGenerator.sustained_load(
            operation, spike_rps, spike_duration, metrics
        )
        results.extend(spike_results)

        # Phase 3: Return to baseline
        logger.info(f"Spike test: Recovery phase ({baseline_rps} rps for {baseline_duration}s)")
        recovery_results = await LoadGenerator.sustained_load(
            operation, baseline_rps, baseline_duration, metrics
        )
        results.extend(recovery_results)

        return results


class ResourceMonitor:
    """
    System resource monitoring for tracking resource usage during stress tests.

    Monitors CPU, memory, and connection counts to identify resource leaks
    and ensure connection pools don't exhaust system resources.
    """

    def __init__(self, sample_interval_seconds: float = 1.0):
        """
        Initialize resource monitor.

        Args:
            sample_interval_seconds: How often to sample resource usage
        """
        self.sample_interval = sample_interval_seconds
        self.snapshots: List[ResourceSnapshot] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.process = psutil.Process()

    async def start(self):
        """Start resource monitoring in background."""
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")

    async def stop(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_task:
            await self._monitor_task
        logger.info(f"Resource monitoring stopped. Captured {len(self.snapshots)} snapshots")

    async def _monitor_loop(self):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                snapshot = ResourceSnapshot(
                    timestamp=datetime.utcnow(),
                    cpu_percent=self.process.cpu_percent(interval=0.1),
                    memory_mb=self.process.memory_info().rss / 1024 / 1024,
                    open_connections=len(self.process.connections())
                )
                self.snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

            await asyncio.sleep(self.sample_interval)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get resource usage summary statistics.

        Returns:
            Dict containing min/max/avg resource usage
        """
        if not self.snapshots:
            return {}

        cpu_values = [s.cpu_percent for s in self.snapshots]
        memory_values = [s.memory_mb for s in self.snapshots]
        connection_values = [s.open_connections for s in self.snapshots]

        return {
            'sample_count': len(self.snapshots),
            'cpu_percent': {
                'min': min(cpu_values),
                'max': max(cpu_values),
                'avg': sum(cpu_values) / len(cpu_values)
            },
            'memory_mb': {
                'min': min(memory_values),
                'max': max(memory_values),
                'avg': sum(memory_values) / len(memory_values)
            },
            'connections': {
                'min': min(connection_values),
                'max': max(connection_values),
                'avg': sum(connection_values) / len(connection_values)
            }
        }


class FailureInjector:
    """
    Failure injection utility for testing resilience and error handling.

    Simulates various failure scenarios including:
    - Network latency and timeouts
    - Database connection failures
    - Query failures and deadlocks
    - Redis connection issues
    """

    @staticmethod
    async def inject_latency(min_ms: int = 100, max_ms: int = 500):
        """Inject random network latency."""
        import random
        latency = random.uniform(min_ms, max_ms) / 1000
        await asyncio.sleep(latency)

    @staticmethod
    def should_fail(failure_rate: float = 0.1) -> bool:
        """
        Determine if operation should fail based on failure rate.

        Args:
            failure_rate: Probability of failure (0.0 to 1.0)

        Returns:
            True if operation should fail
        """
        import random
        return random.random() < failure_rate

    @staticmethod
    @asynccontextmanager
    async def simulate_db_failure(pool: asyncpg.Pool, failure_rate: float = 0.1):
        """
        Context manager that simulates database connection failures.

        Usage:
            async with FailureInjector.simulate_db_failure(pool, 0.2):
                # 20% of operations will fail
                result = await pool.fetch("SELECT 1")
        """
        original_acquire = pool.acquire

        async def failing_acquire():
            if FailureInjector.should_fail(failure_rate):
                raise asyncpg.PostgresConnectionError("Simulated connection failure")
            return await original_acquire()

        pool.acquire = failing_acquire
        try:
            yield
        finally:
            pool.acquire = original_acquire

    @staticmethod
    @asynccontextmanager
    async def simulate_redis_failure(redis_client: redis.Redis, failure_rate: float = 0.1):
        """
        Context manager that simulates Redis connection failures.

        Usage:
            async with FailureInjector.simulate_redis_failure(client, 0.2):
                # 20% of operations will fail
                result = await client.get("key")
        """
        original_get = redis_client.get
        original_set = redis_client.set

        async def failing_get(*args, **kwargs):
            if FailureInjector.should_fail(failure_rate):
                raise redis.ConnectionError("Simulated Redis connection failure")
            return await original_get(*args, **kwargs)

        async def failing_set(*args, **kwargs):
            if FailureInjector.should_fail(failure_rate):
                raise redis.ConnectionError("Simulated Redis connection failure")
            return await original_set(*args, **kwargs)

        redis_client.get = failing_get
        redis_client.set = failing_set
        try:
            yield
        finally:
            redis_client.get = original_get
            redis_client.set = original_set


# ===========================
# PYTEST FIXTURES
# ===========================

@pytest.fixture
def performance_metrics():
    """
    Create performance metrics tracker for a test.

    Usage:
        def test_example(performance_metrics):
            metrics = performance_metrics("test_operation")
            # ... perform operations ...
            stats = metrics.get_statistics()
            assert stats['p95_latency_ms'] < 50
    """
    def create_metrics(operation_name: str) -> PerformanceMetrics:
        return PerformanceMetrics(operation_name=operation_name)
    return create_metrics


@pytest_asyncio.fixture
async def resource_monitor():
    """
    Create and manage resource monitor for a test.

    Automatically starts monitoring at test start and stops at test end,
    providing resource usage summary.

    Usage:
        async def test_example(resource_monitor):
            await resource_monitor.start()
            # ... perform operations ...
            await resource_monitor.stop()
            summary = resource_monitor.get_summary()
            assert summary['memory_mb']['max'] < 500
    """
    monitor = ResourceMonitor(sample_interval_seconds=0.5)
    yield monitor
    # Cleanup: stop monitoring if still running
    if monitor._monitoring:
        await monitor.stop()


@pytest.fixture
def load_generator():
    """
    Provide load generator utility for tests.

    Usage:
        async def test_concurrent_load(load_generator, performance_metrics):
            metrics = performance_metrics("concurrent_test")
            async def operation():
                return await some_async_function()

            results = await load_generator.concurrent_load(operation, 100, metrics)
            assert len(results) == 100
    """
    return LoadGenerator()


@pytest.fixture
def failure_injector():
    """
    Provide failure injector utility for tests.

    Usage:
        async def test_with_failures(failure_injector, db_pool):
            async with failure_injector.simulate_db_failure(db_pool, 0.2):
                # 20% of operations will fail
                results = await perform_operations(db_pool)
    """
    return FailureInjector()


@pytest_asyncio.fixture
async def test_postgres_pool():
    """
    Create a real PostgreSQL connection pool for stress testing.

    Connects to the test database and provides a connection pool
    configured for stress testing with appropriate limits.

    IMPORTANT: Requires PostgreSQL test database to be running.
    """
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5433")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres_password")
    db_name = os.getenv("POSTGRES_DB", "course_creator")

    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    pool = await asyncpg.create_pool(
        dsn,
        min_size=5,
        max_size=20,
        command_timeout=10.0,
        max_queries=50000,
        max_inactive_connection_lifetime=300
    )

    logger.info(f"Created PostgreSQL test pool: min=5, max=20")
    yield pool

    # Cleanup
    await pool.close()
    logger.info("Closed PostgreSQL test pool")


@pytest_asyncio.fixture
async def test_redis_pool():
    """
    Create a real Redis connection pool for stress testing.

    Connects to the test Redis instance and provides a connection pool
    configured for stress testing.

    IMPORTANT: Requires Redis test instance to be running.
    """
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = int(os.getenv("REDIS_DB", "1"))  # Use DB 1 for tests

    redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

    pool = redis.from_url(
        redis_url,
        decode_responses=True,
        max_connections=50,
        retry_on_timeout=True,
        socket_connect_timeout=5,
        socket_keepalive=True
    )

    logger.info(f"Created Redis test pool: max_connections=50")

    # Clear test database
    await pool.flushdb()

    yield pool

    # Cleanup
    await pool.flushdb()
    await pool.close()
    logger.info("Closed Redis test pool")


@pytest.fixture
def assert_performance():
    """
    Provide performance assertion helper.

    Usage:
        def test_example(assert_performance, performance_metrics):
            metrics = performance_metrics("test_op")
            # ... operations ...
            stats = metrics.get_statistics()
            assert_performance(stats, max_p95_ms=50, min_throughput=100)
    """
    def _assert(
        stats: Dict[str, Any],
        max_p50_ms: Optional[float] = None,
        max_p95_ms: Optional[float] = None,
        max_p99_ms: Optional[float] = None,
        min_throughput: Optional[float] = None,
        max_error_rate: float = 5.0
    ):
        """
        Assert performance metrics meet requirements.

        Args:
            stats: Statistics dictionary from PerformanceMetrics.get_statistics()
            max_p50_ms: Maximum allowed P50 latency
            max_p95_ms: Maximum allowed P95 latency
            max_p99_ms: Maximum allowed P99 latency
            min_throughput: Minimum required throughput (ops/sec)
            max_error_rate: Maximum allowed error rate percentage
        """
        if max_p50_ms is not None:
            assert stats['p50_latency_ms'] <= max_p50_ms, \
                f"P50 latency {stats['p50_latency_ms']:.2f}ms exceeds {max_p50_ms}ms"

        if max_p95_ms is not None:
            assert stats['p95_latency_ms'] <= max_p95_ms, \
                f"P95 latency {stats['p95_latency_ms']:.2f}ms exceeds {max_p95_ms}ms"

        if max_p99_ms is not None:
            assert stats['p99_latency_ms'] <= max_p99_ms, \
                f"P99 latency {stats['p99_latency_ms']:.2f}ms exceeds {max_p99_ms}ms"

        if min_throughput is not None:
            assert stats['throughput_ops_per_sec'] >= min_throughput, \
                f"Throughput {stats['throughput_ops_per_sec']:.2f} ops/sec below {min_throughput}"

        assert stats['error_rate_percent'] <= max_error_rate, \
            f"Error rate {stats['error_rate_percent']:.2f}% exceeds {max_error_rate}%"

    return _assert


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "stress: mark test as stress test (requires --run-integration)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip stress tests unless --run-integration flag is provided."""
    if config.getoption("--run-integration"):
        return

    skip_stress = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip_stress)

# Connection Pool Stress Tests

## Overview

This directory contains comprehensive stress tests for PostgreSQL and Redis connection pools used throughout the Course Creator Platform. These tests verify that connection pools handle high load, recover from failures, and maintain performance under stress.

## Test Files

### `conftest.py`
Pytest fixtures and utilities for stress testing:
- **LoadGenerator**: Simulate concurrent load patterns (steady, spike, sustained)
- **PerformanceMetrics**: Track latency percentiles, throughput, error rates
- **ResourceMonitor**: Monitor CPU, memory, connection counts
- **FailureInjector**: Simulate network and database failures
- **Fixtures**: Pre-configured PostgreSQL and Redis pools for testing

### `test_postgres_connection_pool.py` (20 tests)
PostgreSQL connection pool stress tests:

**Pool Exhaustion (5 tests)**
- `test_pool_max_size_enforcement` - Verify max_size limit enforcement
- `test_pool_exhaustion_wait_behavior` - Test queuing when pool is full
- `test_pool_exhaustion_timeout` - Timeout behavior when exhausted
- `test_graceful_degradation_when_pool_full` - Service degradation under pressure
- `test_pool_exhaustion_error_messages` - Error message clarity

**Pool Recovery (5 tests)**
- `test_connection_recovery_after_failure` - Recovery from connection failures
- `test_connection_validation_on_acquire` - Connection validation
- `test_stale_connection_detection` - Detect idle/stale connections
- `test_automatic_reconnection` - Automatic reconnection logic
- `test_pool_recovery_after_database_restart_simulation` - Restart recovery

**Concurrent Access (5 tests)**
- `test_100_concurrent_acquisitions` - Handle 100 concurrent requests
- `test_high_load_1000_rps` - Sustained load at 1000 rps
- `test_connection_release_race_conditions` - Race condition safety
- `test_connection_leak_detection` - Detect connection leaks
- `test_fair_queuing_fifo` - FIFO queue fairness

**Pool Configuration (5 tests)**
- `test_min_size_maintains_minimum_connections` - Maintain min_size
- `test_max_size_prevents_overallocation` - Enforce max_size
- `test_connection_idle_timeout` - Idle connection timeout
- `test_connection_max_lifetime` - Connection lifecycle management
- `test_pool_warmup_on_initialization` - Pool warm-up behavior

### `test_redis_connection_pool.py` (20 tests)
Redis connection pool stress tests:

**Pool Exhaustion (5 tests)**
- `test_max_connections_limit` - Max connections enforcement
- `test_blocking_vs_nonblocking_mode` - Blocking vs non-blocking behavior
- `test_connection_timeout_behavior` - Timeout configuration
- `test_pool_full_error_handling` - Error handling under pressure
- `test_queue_backlog_under_load` - Request queue management

**Pool Performance (5 tests)**
- `test_connection_acquisition_latency` - Acquisition latency <1ms
- `test_connection_release_latency` - Release latency <1ms
- `test_throughput_operations_per_second` - 10,000+ ops/sec
- `test_connection_reuse_efficiency` - >90% reuse efficiency
- `test_pool_overhead_vs_direct_connection` - Pool overhead analysis

**Failover and Recovery (5 tests)**
- `test_connection_recovery_after_redis_restart_simulation` - Restart recovery
- `test_connection_validation_ping` - Ping-based validation
- `test_automatic_retry_on_transient_failures` - Retry logic
- `test_circuit_breaker_pattern` - Circuit breaker implementation
- `test_fallback_to_non_cached_operation` - Cache fallback

**Memory and Resources (5 tests)**
- `test_connection_memory_usage` - Memory usage stability
- `test_socket_handle_cleanup` - Socket cleanup
- `test_connection_pool_memory_growth` - Memory growth monitoring
- `test_connection_leak_detection_redis` - Connection leak detection
- `test_resource_cleanup_on_pool_close` - Cleanup on close

### `test_connection_pool_edge_cases.py` (10 tests)
Edge case and extreme condition tests:

- `test_pool_behavior_with_network_latency` - 500ms network latency
- `test_pool_behavior_with_slow_queries` - Slow query handling
- `test_connection_spike_pattern` - 10x traffic spike
- `test_connection_churn_pattern` - Rapid acquire/release cycling
- `test_pool_close_while_connections_active` - Active connection cleanup
- `test_pool_resize_during_active_use` - Dynamic pool resizing
- `test_connection_acquisition_timeout` - Timeout precision
- `test_connection_validation_failure` - Invalid connection handling
- `test_dns_resolution_failures` - DNS failure handling
- `test_ssl_tls_connection_overhead` - SSL/TLS overhead

## Running Tests

### Prerequisites
Ensure PostgreSQL and Redis are running and accessible:
```bash
# Check PostgreSQL
docker ps | grep postgres

# Check Redis
docker ps | grep redis

# Or use platform scripts
./scripts/app-control.sh status
```

### Run All Stress Tests
```bash
pytest tests/stress/ --run-integration -v
```

### Run Specific Test File
```bash
# PostgreSQL tests only
pytest tests/stress/test_postgres_connection_pool.py --run-integration -v

# Redis tests only
pytest tests/stress/test_redis_connection_pool.py --run-integration -v

# Edge cases only
pytest tests/stress/test_connection_pool_edge_cases.py --run-integration -v
```

### Run Specific Test
```bash
pytest tests/stress/test_postgres_connection_pool.py::test_pool_max_size_enforcement --run-integration -v
```

### Run with Performance Reporting
```bash
pytest tests/stress/ --run-integration -v --tb=short --durations=20
```

## Performance Baselines

### PostgreSQL Connection Pool
- **Connection Acquisition**: <10ms (P95)
- **Connection Release**: <5ms (P95)
- **Query Execution**: <50ms (P95) for simple queries
- **Throughput**: 100+ ops/sec
- **Pool Exhaustion Wait**: <1000ms
- **Error Rate**: <5% under extreme load

### Redis Connection Pool
- **Connection Acquisition**: <1ms (P95)
- **Connection Release**: <1ms (P95)
- **GET/SET Operations**: <5ms (P95)
- **Throughput**: 10,000+ ops/sec
- **Connection Reuse**: >90% efficiency
- **Error Rate**: <5% under extreme load

### Edge Cases
- **Network Latency (500ms)**: Operations complete, 75%+ success rate
- **Slow Queries (5s)**: Other queries unaffected
- **Connection Spike (10x)**: <10% error rate, graceful degradation
- **Connection Churn**: No leaks, stable resource usage

## Environment Variables

Tests use these environment variables (with defaults):

### PostgreSQL
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=course_creator_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=course_creator_test
```

### Redis
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1  # Use DB 1 for tests to avoid collision
```

## Interpreting Results

### Performance Metrics
Each test reports:
- **Total Operations**: Number of operations performed
- **Success/Failed**: Success and failure counts
- **Error Rate**: Percentage of failed operations
- **Latency Percentiles**: P50, P95, P99 latency in milliseconds
- **Throughput**: Operations per second

### Resource Metrics
Resource monitor reports:
- **CPU Usage**: Min/Max/Avg CPU percentage
- **Memory Usage**: Min/Max/Avg memory in MB
- **Connection Count**: Min/Max/Avg open connections

### Success Criteria
Tests pass when:
1. Error rate is below threshold (typically <5%)
2. Performance meets baseline targets (P95 latency)
3. Resource usage is stable (no leaks)
4. Throughput meets minimum requirements

## Troubleshooting

### Tests Skip with "need --run-integration option"
Add the `--run-integration` flag:
```bash
pytest tests/stress/ --run-integration -v
```

### Connection Refused Errors
Ensure services are running:
```bash
./scripts/app-control.sh start
./scripts/app-control.sh status
```

### Timeout Errors
Some tests intentionally test timeout behavior. Check:
- Test is marked as expecting timeouts
- Actual timeout matches expected timeout
- Pool recovers after timeout

### High Error Rates
Acceptable under extreme load tests:
- <5% error rate is typically acceptable
- Check if test is specifically testing failure scenarios
- Verify pool recovers after stress period

### Memory Growth
Small memory growth is normal:
- Connection pools allocate memory for connections
- Python GC may delay cleanup
- Check for unbounded growth over time

## Contributing

When adding new stress tests:

1. **Use Fixtures**: Leverage existing fixtures from `conftest.py`
2. **Record Metrics**: Always use `PerformanceMetrics` to track results
3. **Assert Performance**: Use `assert_performance` for baseline checks
4. **Document Baselines**: Include expected performance in docstring
5. **Clean Up**: Ensure resources are cleaned up in finally blocks
6. **Mark as Stress**: Add `@pytest.mark.stress` decorator

Example:
```python
@pytest.mark.stress
@pytest.mark.asyncio
async def test_my_stress_scenario(
    test_postgres_pool,
    performance_metrics,
    assert_performance
):
    """
    Test description and expected behavior.

    Performance Baseline: <20ms (P95)
    """
    metrics = performance_metrics("my_scenario")

    # ... test implementation ...

    stats = metrics.get_statistics()
    assert_performance(stats, max_p95_ms=20, max_error_rate=5)
```

## Maintenance

### Regular Baseline Updates
Performance baselines should be reviewed and updated:
- After infrastructure upgrades
- After code optimizations
- When deployment environment changes

### Continuous Monitoring
Stress test results should be tracked over time:
- Run as part of CI/CD pipeline
- Monitor trends in performance metrics
- Alert on regression from baselines

## Related Documentation

- [Testing Strategy](../../claude.md/08-testing-strategy.md)
- [Architecture Overview](../../claude.md/05-architecture.md)
- [Database Abstraction Layer](/shared/database/)
- [Redis Cache Manager](/shared/cache/)

"""
Connection Pool Stress Tests Package

This package contains comprehensive stress tests for PostgreSQL and Redis
connection pools used throughout the Course Creator Platform.

Test Coverage:
- PostgreSQL Pool: 20 tests covering exhaustion, recovery, concurrency, configuration
- Redis Pool: 20 tests covering performance, failover, memory management
- Edge Cases: 10 tests covering network issues, slow queries, spike patterns

To run stress tests:
    pytest tests/stress/ --run-integration -v

Performance Baselines:
- PostgreSQL connection acquisition: <10ms (P95)
- Redis connection acquisition: <1ms (P95)
- Query execution: <50ms (P95)
- Throughput: 100+ ops/sec (PostgreSQL), 10,000+ ops/sec (Redis)
"""

__version__ = "1.0.0"

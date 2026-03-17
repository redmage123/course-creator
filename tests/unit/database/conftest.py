"""
Transaction Tests Configuration and Fixtures

BUSINESS CONTEXT:
Provides specialized fixtures for comprehensive transaction testing including:
- Multiple concurrent database connections for isolation testing
- Transaction isolation level configuration
- Deadlock scenario setup helpers
- Performance measurement utilities

TECHNICAL IMPLEMENTATION:
Builds on top of base DAO fixtures but adds transaction-specific capabilities
for testing ACID properties, concurrency, and edge cases.

WHY THIS APPROACH:
Transaction tests require special fixtures that go beyond simple DAO testing:
- Multiple concurrent connections to test isolation
- Controlled timing for deadlock scenarios
- Performance measurement for throughput testing
- Schema management for cross-schema transactions
"""

import pytest
import pytest_asyncio
import asyncio
import asyncpg
import time
from typing import AsyncGenerator, Dict, Any, List
from uuid import uuid4
import os
from datetime import datetime


# =============================================================================
# DATABASE CONNECTION FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def multiple_connections(test_db_pool) -> AsyncGenerator[List[asyncpg.Connection], None]:
    """
    Provide multiple concurrent database connections for isolation testing

    BUSINESS REQUIREMENT:
    Testing transaction isolation requires multiple concurrent connections
    to simulate different users/sessions accessing database simultaneously.

    TECHNICAL IMPLEMENTATION:
    - Creates 3 connections from pool
    - Each connection can run independent transaction
    - All connections returned to pool after test

    USAGE EXAMPLE:
    ```python
    async def test_isolation(multiple_connections):
        conn1, conn2, conn3 = multiple_connections
        # Test concurrent operations
    ```
    """
    connections = []

    try:
        # Acquire 3 connections for concurrent testing
        for _ in range(3):
            conn = await test_db_pool.acquire()
            connections.append(conn)

        yield connections

    finally:
        # Return all connections to pool
        for conn in connections:
            await test_db_pool.release(conn)


@pytest_asyncio.fixture
async def connection_pair(test_db_pool) -> AsyncGenerator[tuple, None]:
    """
    Provide pair of database connections for two-party scenarios

    BUSINESS REQUIREMENT:
    Most isolation and deadlock tests involve two concurrent transactions.

    TECHNICAL IMPLEMENTATION:
    Convenience fixture providing exactly 2 connections.

    USAGE EXAMPLE:
    ```python
    async def test_deadlock(connection_pair):
        conn1, conn2 = connection_pair
        # Create deadlock scenario
    ```
    """
    conn1 = await test_db_pool.acquire()
    conn2 = await test_db_pool.acquire()

    try:
        yield (conn1, conn2)
    finally:
        await test_db_pool.release(conn1)
        await test_db_pool.release(conn2)


# =============================================================================
# ISOLATION LEVEL FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def read_committed_connection(test_db_pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide connection with READ COMMITTED isolation level

    BUSINESS REQUIREMENT:
    PostgreSQL default isolation level. Most transactions use this.

    TECHNICAL IMPLEMENTATION:
    - Acquires connection
    - Sets isolation level explicitly
    - Returns to default after test
    """
    conn = await test_db_pool.acquire()

    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")
        yield conn
    finally:
        await test_db_pool.release(conn)


@pytest_asyncio.fixture
async def repeatable_read_connection(test_db_pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide connection with REPEATABLE READ isolation level

    BUSINESS REQUIREMENT:
    Financial reports and analytics need consistent view throughout transaction.

    TECHNICAL IMPLEMENTATION:
    Sets isolation level to REPEATABLE READ for connection.
    """
    conn = await test_db_pool.acquire()

    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        yield conn
    finally:
        await test_db_pool.release(conn)


@pytest_asyncio.fixture
async def serializable_connection(test_db_pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide connection with SERIALIZABLE isolation level

    BUSINESS REQUIREMENT:
    Critical operations requiring full isolation (financial settlements,
    inventory management) use SERIALIZABLE to prevent all anomalies.

    TECHNICAL IMPLEMENTATION:
    Sets highest isolation level. May cause serialization failures.
    """
    conn = await test_db_pool.acquire()

    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        yield conn
    finally:
        await test_db_pool.release(conn)


# =============================================================================
# DEADLOCK TESTING HELPERS
# =============================================================================

class DeadlockScenario:
    """
    Helper class for creating controlled deadlock scenarios

    BUSINESS CONTEXT:
    Deadlock testing requires precise timing and coordination of multiple
    transactions. This helper provides utilities for creating reproducible
    deadlock scenarios.

    USAGE:
    ```python
    async def test_deadlock(test_db_pool):
        scenario = DeadlockScenario(test_db_pool)
        await scenario.setup_resources(2)
        deadlock_occurred = await scenario.create_circular_deadlock()
        assert deadlock_occurred
    ```
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.table_name = f"deadlock_test_{uuid4().hex[:8]}"
        self.resource_ids = []

    async def setup_resources(self, count: int = 2) -> List[str]:
        """
        Create test table and resources for deadlock testing

        TECHNICAL IMPLEMENTATION:
        - Creates temporary table
        - Inserts specified number of resources
        - Returns resource IDs for locking
        """
        async with self.db_pool.acquire() as conn:
            # Create table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id UUID PRIMARY KEY,
                    value INT NOT NULL,
                    locked_by VARCHAR(50)
                )
            """)

            # Insert resources
            self.resource_ids = []
            for i in range(count):
                resource_id = str(uuid4())
                await conn.execute(
                    f"INSERT INTO {self.table_name} (id, value, locked_by) VALUES ($1, $2, $3)",
                    resource_id, i, None
                )
                self.resource_ids.append(resource_id)

            return self.resource_ids

    async def cleanup(self):
        """Clean up test table"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {self.table_name}")

    async def create_circular_deadlock(self) -> bool:
        """
        Create circular deadlock between two resources

        BUSINESS SCENARIO:
        Transaction 1: Lock A, then try to lock B
        Transaction 2: Lock B, then try to lock A
        Result: Deadlock

        RETURNS:
        True if deadlock detected, False otherwise
        """
        if len(self.resource_ids) < 2:
            raise ValueError("Need at least 2 resources for circular deadlock")

        deadlock_detected = False
        conn1 = await self.db_pool.acquire()
        conn2 = await self.db_pool.acquire()

        try:
            # Transaction 1: Lock resource A
            await conn1.execute("BEGIN")
            await conn1.execute(
                f"UPDATE {self.table_name} SET locked_by = 'tx1' WHERE id = $1",
                self.resource_ids[0]
            )

            # Transaction 2: Lock resource B
            await conn2.execute("BEGIN")
            await conn2.execute(
                f"UPDATE {self.table_name} SET locked_by = 'tx2' WHERE id = $1",
                self.resource_ids[1]
            )

            # Create deadlock
            async def tx1_lock_b():
                nonlocal deadlock_detected
                try:
                    await conn1.execute(
                        f"UPDATE {self.table_name} SET locked_by = 'tx1' WHERE id = $1",
                        self.resource_ids[1]
                    )
                    await conn1.execute("COMMIT")
                except asyncpg.exceptions.DeadlockDetectedError:
                    deadlock_detected = True
                    await conn1.execute("ROLLBACK")

            async def tx2_lock_a():
                nonlocal deadlock_detected
                try:
                    await conn2.execute(
                        f"UPDATE {self.table_name} SET locked_by = 'tx2' WHERE id = $1",
                        self.resource_ids[0]
                    )
                    await conn2.execute("COMMIT")
                except asyncpg.exceptions.DeadlockDetectedError:
                    deadlock_detected = True
                    await conn2.execute("ROLLBACK")

            # Execute both
            await asyncio.gather(tx1_lock_b(), tx2_lock_a(), return_exceptions=True)

        finally:
            await self.db_pool.release(conn1)
            await self.db_pool.release(conn2)

        return deadlock_detected


@pytest_asyncio.fixture
async def deadlock_scenario(test_db_pool) -> AsyncGenerator[DeadlockScenario, None]:
    """
    Provide DeadlockScenario helper for testing

    BUSINESS REQUIREMENT:
    Simplifies deadlock testing by providing pre-configured scenario.

    USAGE:
    ```python
    async def test_deadlock(deadlock_scenario):
        await deadlock_scenario.setup_resources(2)
        result = await deadlock_scenario.create_circular_deadlock()
        assert result is True
        await deadlock_scenario.cleanup()
    ```
    """
    scenario = DeadlockScenario(test_db_pool)

    yield scenario

    # Cleanup
    await scenario.cleanup()


# =============================================================================
# PERFORMANCE MEASUREMENT FIXTURES
# =============================================================================

class TransactionTimer:
    """
    Utility for measuring transaction performance

    BUSINESS CONTEXT:
    Performance testing requires accurate timing of transaction operations.
    This helper provides consistent timing measurement.

    USAGE:
    ```python
    async def test_performance(transaction_timer):
        async with transaction_timer.measure("insert_operation"):
            # Perform operation
            await conn.execute("INSERT ...")

        assert transaction_timer.get_duration("insert_operation") < 0.1
    ```
    """

    def __init__(self):
        self.timings: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    class _TimingContext:
        """Context manager for timing measurement"""

        def __init__(self, timer, operation_name: str):
            self.timer = timer
            self.operation_name = operation_name

        async def __aenter__(self):
            self.timer._start_times[self.operation_name] = time.time()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.timer._start_times[self.operation_name]
            self.timer.timings[self.operation_name] = duration
            del self.timer._start_times[self.operation_name]

    def measure(self, operation_name: str):
        """Create timing context for operation"""
        return self._TimingContext(self, operation_name)

    def get_duration(self, operation_name: str) -> float:
        """Get duration of measured operation in seconds"""
        return self.timings.get(operation_name, 0.0)

    def get_duration_ms(self, operation_name: str) -> float:
        """Get duration of measured operation in milliseconds"""
        return self.get_duration(operation_name) * 1000

    def reset(self):
        """Reset all timings"""
        self.timings.clear()
        self._start_times.clear()


@pytest.fixture
def transaction_timer() -> TransactionTimer:
    """
    Provide transaction timing utility

    BUSINESS REQUIREMENT:
    Performance tests need to measure transaction execution time.

    USAGE:
    ```python
    async def test_rollback_performance(test_db_pool, transaction_timer):
        async with transaction_timer.measure("rollback"):
            # Perform transaction and rollback
            pass

        assert transaction_timer.get_duration_ms("rollback") < 10
    ```
    """
    return TransactionTimer()


# =============================================================================
# TEST DATA FACTORIES
# =============================================================================

def create_test_table_sql(table_name: str, schema: str = "public") -> str:
    """
    Generate SQL for creating standard test table

    BUSINESS REQUIREMENT:
    Transaction tests need consistent table structure.

    RETURNS:
    SQL CREATE TABLE statement

    USAGE:
    ```python
    sql = create_test_table_sql("my_test_table")
    await conn.execute(sql)
    ```
    """
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            value INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """


def create_test_row_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Factory for creating test row data

    BUSINESS REQUIREMENT:
    Tests need consistent, valid test data.

    USAGE:
    ```python
    data = create_test_row_data({'name': 'Custom Name'})
    await conn.execute(
        "INSERT INTO test_table (id, name, value) VALUES ($1, $2, $3)",
        data['id'], data['name'], data['value']
    )
    ```
    """
    base_data = {
        'id': str(uuid4()),
        'name': f'test_row_{uuid4().hex[:8]}',
        'value': 0,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }

    if override:
        base_data.update(override)

    return base_data


# =============================================================================
# ASSERTION HELPERS
# =============================================================================

async def assert_transaction_rolled_back(
    conn: asyncpg.Connection,
    table_name: str,
    row_id: str
) -> None:
    """
    Assert that row was rolled back (doesn't exist)

    BUSINESS REQUIREMENT:
    Common assertion in rollback tests - verify data doesn't persist.

    USAGE:
    ```python
    await assert_transaction_rolled_back(conn, "test_table", test_id)
    ```
    """
    result = await conn.fetchrow(
        f"SELECT * FROM {table_name} WHERE id = $1",
        row_id
    )
    assert result is None, f"Row {row_id} should have been rolled back"


async def assert_transaction_committed(
    conn: asyncpg.Connection,
    table_name: str,
    row_id: str
) -> None:
    """
    Assert that row was committed (exists)

    BUSINESS REQUIREMENT:
    Common assertion in commit tests - verify data persisted.

    USAGE:
    ```python
    await assert_transaction_committed(conn, "test_table", test_id)
    ```
    """
    result = await conn.fetchrow(
        f"SELECT * FROM {table_name} WHERE id = $1",
        row_id
    )
    assert result is not None, f"Row {row_id} should have been committed"


async def assert_row_count(
    conn: asyncpg.Connection,
    table_name: str,
    expected_count: int,
    where_clause: str = ""
) -> None:
    """
    Assert table has expected number of rows

    BUSINESS REQUIREMENT:
    Common assertion for batch operations - verify correct number of rows.

    USAGE:
    ```python
    await assert_row_count(conn, "test_table", 10)
    await assert_row_count(conn, "test_table", 5, "WHERE status = 'active'")
    ```
    """
    query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        query += f" {where_clause}"

    count = await conn.fetchval(query)
    assert count == expected_count, f"Expected {expected_count} rows, got {count}"

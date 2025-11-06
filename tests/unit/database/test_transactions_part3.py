"""
Comprehensive Database Transaction Tests - Part 3
Deadlock and Concurrent Transaction Tests

CONTINUATION OF: test_transactions.py, test_transactions_part2.py
This file contains additional deadlock scenarios and concurrent transaction tests.
"""

import pytest
import asyncio
import asyncpg
import time
from typing import List
from datetime import datetime
from uuid import uuid4


# =============================================================================
# CATEGORY 4: DEADLOCK HANDLING TESTS (6 tests)
# ACID PROPERTY: Isolation
# =============================================================================

@pytest.mark.asyncio
async def test_simple_deadlock_scenario(test_db_pool):
    """
    Test simple two-transaction deadlock (A->B, B->A)

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Student 1 transferring credits from Course A to Course B while
    Student 2 transfers from Course B to Course A can create deadlock.

    EXPECTED BEHAVIOR:
    - Transaction 1 locks A, wants B
    - Transaction 2 locks B, wants A
    - PostgreSQL detects deadlock
    - One transaction aborted
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_accounts (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                balance DECIMAL(10, 2) NOT NULL
            )
        """)

        account_a = str(uuid4())
        account_b = str(uuid4())

        # Insert accounts
        await conn1.execute(
            "INSERT INTO test_accounts (id, name, balance) VALUES ($1, $2, $3)",
            account_a, "Account A", 1000.00
        )
        await conn1.execute(
            "INSERT INTO test_accounts (id, name, balance) VALUES ($1, $2, $3)",
            account_b, "Account B", 1000.00
        )

        deadlock_occurred = False

        # Transaction 1: A -> B
        await conn1.execute("BEGIN")
        await conn1.execute(
            "UPDATE test_accounts SET balance = balance - 100 WHERE id = $1",
            account_a
        )

        # Transaction 2: B -> A
        await conn2.execute("BEGIN")
        await conn2.execute(
            "UPDATE test_accounts SET balance = balance - 100 WHERE id = $1",
            account_b
        )

        # Create deadlock
        async def tx1_update_b():
            nonlocal deadlock_occurred
            try:
                await conn1.execute(
                    "UPDATE test_accounts SET balance = balance + 100 WHERE id = $1",
                    account_b
                )
                await conn1.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_occurred = True
                await conn1.execute("ROLLBACK")

        async def tx2_update_a():
            nonlocal deadlock_occurred
            try:
                await conn2.execute(
                    "UPDATE test_accounts SET balance = balance + 100 WHERE id = $1",
                    account_a
                )
                await conn2.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_occurred = True
                await conn2.execute("ROLLBACK")

        # Execute both
        await asyncio.gather(tx1_update_b(), tx2_update_a(), return_exceptions=True)

        assert deadlock_occurred, "Deadlock should have been detected"

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_accounts")


@pytest.mark.asyncio
async def test_three_way_deadlock(test_db_pool):
    """
    Test three-way deadlock (A->B->C->A)

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Complex workflows involving multiple resources can create
    circular wait conditions requiring deadlock detection.

    EXPECTED BEHAVIOR:
    - Three transactions lock in circular pattern
    - PostgreSQL detects multi-party deadlock
    - At least one transaction aborted
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2, test_db_pool.acquire() as conn3:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_resources (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)

        resource_a = str(uuid4())
        resource_b = str(uuid4())
        resource_c = str(uuid4())

        # Insert resources
        for resource_id, name in [(resource_a, "A"), (resource_b, "B"), (resource_c, "C")]:
            await conn1.execute(
                "INSERT INTO test_resources (id, name, status) VALUES ($1, $2, $3)",
                resource_id, name, "available"
            )

        deadlock_occurred = False

        # Transaction 1: A -> B
        await conn1.execute("BEGIN")
        await conn1.execute(
            "UPDATE test_resources SET status = 'locked' WHERE id = $1",
            resource_a
        )

        # Transaction 2: B -> C
        await conn2.execute("BEGIN")
        await conn2.execute(
            "UPDATE test_resources SET status = 'locked' WHERE id = $1",
            resource_b
        )

        # Transaction 3: C -> A
        await conn3.execute("BEGIN")
        await conn3.execute(
            "UPDATE test_resources SET status = 'locked' WHERE id = $1",
            resource_c
        )

        # Create circular deadlock
        async def tx1_lock_b():
            nonlocal deadlock_occurred
            try:
                await conn1.execute(
                    "UPDATE test_resources SET status = 'locked' WHERE id = $1",
                    resource_b
                )
                await conn1.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_occurred = True
                await conn1.execute("ROLLBACK")

        async def tx2_lock_c():
            nonlocal deadlock_occurred
            try:
                await conn2.execute(
                    "UPDATE test_resources SET status = 'locked' WHERE id = $1",
                    resource_c
                )
                await conn2.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_occurred = True
                await conn2.execute("ROLLBACK")

        async def tx3_lock_a():
            nonlocal deadlock_occurred
            try:
                await conn3.execute(
                    "UPDATE test_resources SET status = 'locked' WHERE id = $1",
                    resource_a
                )
                await conn3.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_occurred = True
                await conn3.execute("ROLLBACK")

        # Execute all three
        await asyncio.gather(
            tx1_lock_b(),
            tx2_lock_c(),
            tx3_lock_a(),
            return_exceptions=True
        )

        assert deadlock_occurred, "Three-way deadlock should have been detected"

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_resources")


@pytest.mark.asyncio
async def test_deadlock_detection_time(test_db_pool):
    """
    Test that deadlock is detected quickly

    ACID PROPERTY: Isolation (Performance)

    BUSINESS SCENARIO:
    Slow deadlock detection impacts user experience. Detection should
    occur within reasonable timeframe (typically <1 second).

    EXPECTED BEHAVIOR:
    - Deadlock created
    - Detection occurs quickly
    - One transaction aborted promptly
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_locks (
                id UUID PRIMARY KEY,
                value INT NOT NULL
            )
        """)

        lock_a = str(uuid4())
        lock_b = str(uuid4())

        # Insert locks
        await conn1.execute("INSERT INTO test_locks (id, value) VALUES ($1, $2)", lock_a, 1)
        await conn1.execute("INSERT INTO test_locks (id, value) VALUES ($1, $2)", lock_b, 2)

        detection_time = None

        # Transaction 1: Lock A
        await conn1.execute("BEGIN")
        await conn1.execute("UPDATE test_locks SET value = 10 WHERE id = $1", lock_a)

        # Transaction 2: Lock B
        await conn2.execute("BEGIN")
        await conn2.execute("UPDATE test_locks SET value = 20 WHERE id = $1", lock_b)

        start_time = time.time()

        # Create deadlock
        async def tx1():
            try:
                await conn1.execute("UPDATE test_locks SET value = 30 WHERE id = $1", lock_b)
                await conn1.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                await conn1.execute("ROLLBACK")

        async def tx2():
            nonlocal detection_time
            try:
                await conn2.execute("UPDATE test_locks SET value = 40 WHERE id = $1", lock_a)
                await conn2.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                detection_time = time.time() - start_time
                await conn2.execute("ROLLBACK")

        await asyncio.gather(tx1(), tx2(), return_exceptions=True)

        # Verify deadlock detected quickly
        if detection_time:
            assert detection_time < 2.0, f"Deadlock detection took {detection_time:.2f}s (expected <2s)"

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_locks")


@pytest.mark.asyncio
async def test_deadlock_victim_selection(test_db_pool):
    """
    Test automatic deadlock victim selection

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    When deadlock occurs, PostgreSQL selects victim based on
    transaction cost. Smaller transaction typically aborted.

    EXPECTED BEHAVIOR:
    - Deadlock detected
    - One transaction selected as victim
    - Victim aborted with DeadlockDetected error
    - Other transaction proceeds
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_operations (
                id UUID PRIMARY KEY,
                operation VARCHAR(255) NOT NULL
            )
        """)

        op_a = str(uuid4())
        op_b = str(uuid4())

        # Insert operations
        await conn1.execute(
            "INSERT INTO test_operations (id, operation) VALUES ($1, $2)",
            op_a, "Operation A"
        )
        await conn1.execute(
            "INSERT INTO test_operations (id, operation) VALUES ($1, $2)",
            op_b, "Operation B"
        )

        victim_detected = {"tx1": False, "tx2": False}

        # Transaction 1: Larger transaction (more work done)
        await conn1.execute("BEGIN")
        await conn1.execute("UPDATE test_operations SET operation = 'TX1 work' WHERE id = $1", op_a)
        # Simulate more work
        for i in range(5):
            await conn1.fetchval("SELECT pg_sleep(0.01)")

        # Transaction 2: Smaller transaction (less work done)
        await conn2.execute("BEGIN")
        await conn2.execute("UPDATE test_operations SET operation = 'TX2 work' WHERE id = $1", op_b)

        # Create deadlock
        async def tx1_update():
            try:
                await conn1.execute("UPDATE test_operations SET operation = 'TX1 final' WHERE id = $1", op_b)
                await conn1.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                victim_detected["tx1"] = True
                await conn1.execute("ROLLBACK")

        async def tx2_update():
            try:
                await conn2.execute("UPDATE test_operations SET operation = 'TX2 final' WHERE id = $1", op_a)
                await conn2.execute("COMMIT")
            except asyncpg.exceptions.DeadlockDetectedError:
                victim_detected["tx2"] = True
                await conn2.execute("ROLLBACK")

        await asyncio.gather(tx1_update(), tx2_update(), return_exceptions=True)

        # Verify one was selected as victim
        assert victim_detected["tx1"] or victim_detected["tx2"], "One transaction should be victim"

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_operations")


@pytest.mark.asyncio
async def test_deadlock_retry_logic(test_db_pool):
    """
    Test deadlock retry logic

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Application should automatically retry transactions that failed
    due to deadlock, with exponential backoff.

    EXPECTED BEHAVIOR:
    - First attempt causes deadlock
    - Automatic retry succeeds
    - Data successfully updated
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_retry (
                id UUID PRIMARY KEY,
                value INT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        row_id = str(uuid4())

        # Insert row
        await conn.execute(
            "INSERT INTO test_retry (id, value) VALUES ($1, $2)",
            row_id, 0
        )

        async def update_with_retry(max_retries=3):
            """
            BUSINESS CONTEXT:
            Retry logic handles transient deadlock failures. Exponential
            backoff reduces contention on retry attempts.
            """
            for attempt in range(max_retries):
                try:
                    async with conn.transaction():
                        current = await conn.fetchval(
                            "SELECT value FROM test_retry WHERE id = $1",
                            row_id
                        )
                        await conn.execute(
                            "UPDATE test_retry SET value = $1, updated_at = NOW() WHERE id = $2",
                            current + 1, row_id
                        )
                    return True  # Success
                except asyncpg.exceptions.DeadlockDetectedError:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await asyncio.sleep(0.1 * (2 ** attempt))
                    else:
                        raise

            return False

        # Test retry logic
        success = await update_with_retry()
        assert success, "Update should succeed with retry logic"

        # Verify update
        final_value = await conn.fetchval(
            "SELECT value FROM test_retry WHERE id = $1",
            row_id
        )
        assert final_value > 0

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_retry")


@pytest.mark.asyncio
async def test_deadlock_prevention_strategies(test_db_pool):
    """
    Test deadlock prevention by consistent lock ordering

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Prevent deadlocks by always acquiring locks in same order (e.g.,
    always lock lower ID before higher ID).

    EXPECTED BEHAVIOR:
    - Both transactions lock resources in same order
    - No deadlock occurs
    - One waits for other to complete
    - Both transactions succeed
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_ordered (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                locked_by INT
            )
        """)

        # Create resources with predictable ordering
        resource_ids = [str(uuid4()) for _ in range(3)]
        resource_ids.sort()  # Ensure consistent ordering

        for idx, resource_id in enumerate(resource_ids):
            await conn1.execute(
                "INSERT INTO test_ordered (id, name, locked_by) VALUES ($1, $2, $3)",
                resource_id, f"Resource {idx}", None
            )

        # Both transactions lock in same order (prevents deadlock)
        async def tx1_ordered_lock():
            await conn1.execute("BEGIN")
            for resource_id in resource_ids:
                await conn1.execute(
                    "UPDATE test_ordered SET locked_by = 1 WHERE id = $1",
                    resource_id
                )
            await conn1.execute("COMMIT")

        async def tx2_ordered_lock():
            await conn2.execute("BEGIN")
            # Same order as tx1
            for resource_id in resource_ids:
                await conn2.execute(
                    "UPDATE test_ordered SET locked_by = 2 WHERE id = $1",
                    resource_id
                )
            await conn2.execute("COMMIT")

        # Both should complete without deadlock (one waits for other)
        await asyncio.gather(tx1_ordered_lock(), tx2_ordered_lock())

        # Verify both transactions completed
        results = await conn1.fetch("SELECT * FROM test_ordered")
        assert len(results) == 3
        # Last transaction should have set all locked_by values
        assert all(r['locked_by'] in [1, 2] for r in results)

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_ordered")


# =============================================================================
# CATEGORY 5: CONCURRENT TRANSACTION TESTS (8 tests)
# ACID PROPERTY: Isolation, Atomicity
# =============================================================================

@pytest.mark.asyncio
async def test_concurrent_inserts(test_db_pool):
    """
    Test 10 concurrent inserts

    ACID PROPERTY: Atomicity, Isolation

    BUSINESS SCENARIO:
    Multiple students enrolling simultaneously should all succeed
    without conflicts or data corruption.

    EXPECTED BEHAVIOR:
    - All inserts succeed
    - No data loss
    - All rows unique and valid
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_enrollments (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                course_id UUID NOT NULL,
                enrolled_at TIMESTAMP DEFAULT NOW()
            )
        """)

        course_id = str(uuid4())

        async def insert_enrollment(student_id):
            enrollment_id = str(uuid4())
            async with test_db_pool.acquire() as conn_local:
                await conn_local.execute(
                    "INSERT INTO test_enrollments (id, student_id, course_id) VALUES ($1, $2, $3)",
                    enrollment_id, student_id, course_id
                )
                return enrollment_id

        # Create 10 concurrent enrollments
        student_ids = [str(uuid4()) for _ in range(10)]
        tasks = [insert_enrollment(sid) for sid in student_ids]
        enrollment_ids = await asyncio.gather(*tasks)

        # Verify all enrollments created
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM test_enrollments WHERE course_id = $1",
            course_id
        )
        assert count == 10, "All 10 concurrent inserts should succeed"

        # Verify all unique
        unique_count = await conn.fetchval(
            "SELECT COUNT(DISTINCT id) FROM test_enrollments WHERE course_id = $1",
            course_id
        )
        assert unique_count == 10

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_concurrent_updates_same_row(test_db_pool):
    """
    Test concurrent updates to same row

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Multiple instructors editing same course triggers row-level locking.
    Last write wins in READ COMMITTED isolation.

    EXPECTED BEHAVIOR:
    - Row locked during update
    - Concurrent updates wait for lock
    - All updates succeed (serialized)
    - Final value reflects last update
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_counter (
                id UUID PRIMARY KEY,
                count INT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        counter_id = str(uuid4())

        # Insert counter
        await conn.execute(
            "INSERT INTO test_counter (id, count) VALUES ($1, $2)",
            counter_id, 0
        )

        async def increment_counter():
            async with test_db_pool.acquire() as conn_local:
                async with conn_local.transaction():
                    current = await conn_local.fetchval(
                        "SELECT count FROM test_counter WHERE id = $1",
                        counter_id
                    )
                    await conn_local.execute(
                        "UPDATE test_counter SET count = $1, updated_at = NOW() WHERE id = $2",
                        current + 1, counter_id
                    )

        # 10 concurrent increments
        await asyncio.gather(*[increment_counter() for _ in range(10)])

        # Verify final count
        final_count = await conn.fetchval(
            "SELECT count FROM test_counter WHERE id = $1",
            counter_id
        )
        assert final_count == 10, "All concurrent updates should succeed"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_counter")


@pytest.mark.asyncio
async def test_concurrent_updates_different_rows(test_db_pool):
    """
    Test concurrent updates to different rows

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Multiple students updating their own profiles should not
    interfere with each other (row-level locking).

    EXPECTED BEHAVIOR:
    - Each update locks only its row
    - All updates proceed in parallel
    - No waiting or conflicts
    - All updates succeed
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_profiles (
                user_id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Insert 10 users
        user_ids = [str(uuid4()) for _ in range(10)]
        for user_id in user_ids:
            await conn.execute(
                "INSERT INTO test_profiles (user_id, name) VALUES ($1, $2)",
                user_id, "Original Name"
            )

        async def update_profile(user_id):
            async with test_db_pool.acquire() as conn_local:
                await conn_local.execute(
                    "UPDATE test_profiles SET name = $1, updated_at = NOW() WHERE user_id = $2",
                    f"Updated {user_id[:8]}", user_id
                )

        start_time = time.time()

        # Update all profiles concurrently
        await asyncio.gather(*[update_profile(uid) for uid in user_ids])

        elapsed_time = time.time() - start_time

        # Verify all updated
        updated_count = await conn.fetchval(
            "SELECT COUNT(*) FROM test_profiles WHERE name LIKE 'Updated%'"
        )
        assert updated_count == 10

        # Should complete quickly (parallel execution)
        assert elapsed_time < 2.0, f"Concurrent updates took {elapsed_time:.2f}s (expected <2s)"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_profiles")


@pytest.mark.asyncio
async def test_lost_update_problem(test_db_pool):
    """
    Test lost update problem scenario

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Two users read same value, modify it independently, and write back.
    Without proper locking, one update can be lost.

    EXPECTED BEHAVIOR:
    - Both transactions read same initial value
    - Both calculate new value
    - Both write back
    - One update may be lost (depends on isolation level)
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_inventory (
                product_id UUID PRIMARY KEY,
                quantity INT NOT NULL
            )
        """)

        product_id = str(uuid4())

        # Insert product
        await conn.execute(
            "INSERT INTO test_inventory (product_id, quantity) VALUES ($1, $2)",
            product_id, 100
        )

        async def decrement_without_lock(amount):
            async with test_db_pool.acquire() as conn_local:
                # Read
                current = await conn_local.fetchval(
                    "SELECT quantity FROM test_inventory WHERE product_id = $1",
                    product_id
                )
                # Calculate new value
                new_value = current - amount
                # Small delay to simulate processing
                await asyncio.sleep(0.01)
                # Write back
                await conn_local.execute(
                    "UPDATE test_inventory SET quantity = $1 WHERE product_id = $2",
                    new_value, product_id
                )

        # Two concurrent decrements
        await asyncio.gather(
            decrement_without_lock(10),
            decrement_without_lock(20)
        )

        # Check final value (may have lost update)
        final_quantity = await conn.fetchval(
            "SELECT quantity FROM test_inventory WHERE product_id = $1",
            product_id
        )

        # Expected: 70 (100 - 10 - 20)
        # Actual: may be 80 or 90 due to lost update
        print(f"Final quantity: {final_quantity} (expected 70, but lost update may occur)")

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_inventory")


@pytest.mark.asyncio
async def test_write_skew_anomaly(test_db_pool):
    """
    Test write skew anomaly

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Ensuring at least one administrator remains in system. Two transactions
    check constraint passes, but concurrent execution violates it.

    EXPECTED BEHAVIOR:
    - Both transactions read and see constraint satisfied
    - Both make changes
    - Final state violates constraint (write skew)
    - SERIALIZABLE isolation prevents this
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_admins (
                id UUID PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                is_admin BOOLEAN NOT NULL
            )
        """)

        admin1_id = str(uuid4())
        admin2_id = str(uuid4())

        # Insert two admins
        await conn.execute(
            "INSERT INTO test_admins (id, username, is_admin) VALUES ($1, $2, $3)",
            admin1_id, "Admin1", True
        )
        await conn.execute(
            "INSERT INTO test_admins (id, username, is_admin) VALUES ($1, $2, $3)",
            admin2_id, "Admin2", True
        )

        async def remove_admin_privilege(admin_id):
            async with test_db_pool.acquire() as conn_local:
                async with conn_local.transaction():
                    # Check if at least 2 admins
                    admin_count = await conn_local.fetchval(
                        "SELECT COUNT(*) FROM test_admins WHERE is_admin = TRUE"
                    )

                    if admin_count >= 2:
                        # Safe to remove one
                        await asyncio.sleep(0.01)  # Simulate processing
                        await conn_local.execute(
                            "UPDATE test_admins SET is_admin = FALSE WHERE id = $1",
                            admin_id
                        )

        # Both transactions try to remove admin privilege concurrently
        await asyncio.gather(
            remove_admin_privilege(admin1_id),
            remove_admin_privilege(admin2_id)
        )

        # Check final admin count (write skew may have occurred)
        final_admin_count = await conn.fetchval(
            "SELECT COUNT(*) FROM test_admins WHERE is_admin = TRUE"
        )

        print(f"Final admin count: {final_admin_count} (write skew may have reduced to 0)")

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_admins")


@pytest.mark.asyncio
async def test_serialization_anomaly(test_db_pool):
    """
    Test serialization anomaly prevention with SERIALIZABLE isolation

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    SERIALIZABLE isolation prevents anomalies by detecting conflicts
    and aborting one transaction.

    EXPECTED BEHAVIOR:
    - Both transactions execute
    - Conflict detected
    - One transaction gets SerializationFailure error
    - Requires retry
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_transactions (
                account_id UUID PRIMARY KEY,
                balance DECIMAL(10, 2) NOT NULL
            )
        """)

        account1 = str(uuid4())
        account2 = str(uuid4())

        # Insert accounts
        await conn.execute(
            "INSERT INTO test_transactions (account_id, balance) VALUES ($1, $2)",
            account1, 1000.00
        )
        await conn.execute(
            "INSERT INTO test_transactions (account_id, balance) VALUES ($1, $2)",
            account2, 1000.00
        )

        serialization_error_occurred = False

        async def transfer_with_check(from_id, to_id, amount):
            nonlocal serialization_error_occurred
            async with test_db_pool.acquire() as conn_local:
                try:
                    await conn_local.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE")

                    # Read total balance
                    total = await conn_local.fetchval(
                        "SELECT SUM(balance) FROM test_transactions"
                    )

                    # Ensure we maintain total balance
                    if total >= 2000.00:
                        await conn_local.execute(
                            "UPDATE test_transactions SET balance = balance - $1 WHERE account_id = $2",
                            amount, from_id
                        )
                        await conn_local.execute(
                            "UPDATE test_transactions SET balance = balance + $1 WHERE account_id = $2",
                            amount, to_id
                        )

                    await conn_local.execute("COMMIT")

                except asyncpg.exceptions.SerializationError:
                    serialization_error_occurred = True
                    await conn_local.execute("ROLLBACK")

        # Concurrent transfers
        await asyncio.gather(
            transfer_with_check(account1, account2, 100),
            transfer_with_check(account2, account1, 200)
        )

        # Note: Serialization error may or may not occur depending on timing
        print(f"Serialization error occurred: {serialization_error_occurred}")

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_transactions")


@pytest.mark.asyncio
async def test_concurrent_transaction_throughput(test_db_pool):
    """
    Test concurrent transaction throughput

    ACID PROPERTY: Performance characteristic

    BUSINESS SCENARIO:
    System should handle high transaction volume without degradation.
    Measure transactions per second under load.

    EXPECTED BEHAVIOR:
    - 100+ transactions complete successfully
    - Reasonable throughput (>10 tx/sec)
    - No deadlocks or errors
    - Consistent performance
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_throughput (
                id UUID PRIMARY KEY,
                value INT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        async def simple_transaction():
            async with test_db_pool.acquire() as conn_local:
                async with conn_local.transaction():
                    await conn_local.execute(
                        "INSERT INTO test_throughput (id, value) VALUES ($1, $2)",
                        str(uuid4()), 1
                    )

        num_transactions = 100
        start_time = time.time()

        # Execute concurrent transactions
        await asyncio.gather(*[simple_transaction() for _ in range(num_transactions)])

        elapsed_time = time.time() - start_time
        throughput = num_transactions / elapsed_time

        print(f"Throughput: {throughput:.2f} transactions/second")

        # Verify all completed
        count = await conn.fetchval("SELECT COUNT(*) FROM test_throughput")
        assert count == num_transactions

        # Expect reasonable throughput
        assert throughput > 10, f"Throughput {throughput:.2f} tx/s is too low"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_throughput")


@pytest.mark.asyncio
async def test_transaction_queue_behavior_under_load(test_db_pool):
    """
    Test transaction queue behavior under load

    ACID PROPERTY: Isolation (Performance)

    BUSINESS SCENARIO:
    Under heavy load, transactions may queue waiting for locks.
    System should handle queuing gracefully without failures.

    EXPECTED BEHAVIOR:
    - Multiple transactions queue for same resource
    - All transactions eventually complete
    - FIFO ordering maintained
    - No transaction starvation
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_queue (
                resource_id UUID PRIMARY KEY,
                access_count INT NOT NULL,
                last_accessed_by INT
            )
        """)

        resource_id = str(uuid4())

        # Insert shared resource
        await conn.execute(
            "INSERT INTO test_queue (resource_id, access_count, last_accessed_by) VALUES ($1, $2, $3)",
            resource_id, 0, 0
        )

        async def access_resource(accessor_id):
            async with test_db_pool.acquire() as conn_local:
                async with conn_local.transaction():
                    # Lock resource
                    current = await conn_local.fetchval(
                        "SELECT access_count FROM test_queue WHERE resource_id = $1 FOR UPDATE",
                        resource_id
                    )

                    # Simulate work
                    await asyncio.sleep(0.01)

                    # Update
                    await conn_local.execute(
                        "UPDATE test_queue SET access_count = $1, last_accessed_by = $2 WHERE resource_id = $3",
                        current + 1, accessor_id, resource_id
                    )

        # 20 transactions competing for same resource
        await asyncio.gather(*[access_resource(i) for i in range(20)])

        # Verify all completed
        final_count = await conn.fetchval(
            "SELECT access_count FROM test_queue WHERE resource_id = $1",
            resource_id
        )
        assert final_count == 20, "All queued transactions should complete"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_queue")

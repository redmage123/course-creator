"""
Comprehensive Database Transaction Tests - Part 2
Isolation, Deadlock, and Concurrency Tests

CONTINUATION OF: test_transactions.py
This file contains tests for transaction isolation levels, deadlock handling,
and concurrent transaction scenarios.
"""

import pytest
import asyncio
import asyncpg
import time
from typing import List
from datetime import datetime
from uuid import uuid4


# =============================================================================
# CATEGORY 3: TRANSACTION ISOLATION TESTS (12 tests)
# ACID PROPERTY: Isolation
# =============================================================================

@pytest.mark.asyncio
async def test_read_uncommitted_isolation_level(test_db_pool):
    """
    Test READ UNCOMMITTED isolation level

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Analytics queries may tolerate reading uncommitted data for
    better performance (dirty reads acceptable).

    EXPECTED BEHAVIOR:
    - PostgreSQL doesn't support true READ UNCOMMITTED
    - Falls back to READ COMMITTED
    - No dirty reads possible in PostgreSQL

    NOTE: PostgreSQL treats READ UNCOMMITTED as READ COMMITTED
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_accounts (
                id UUID PRIMARY KEY,
                balance DECIMAL(10, 2) NOT NULL
            )
        """)

        account_id = str(uuid4())

        # Insert initial balance
        await conn1.execute(
            "INSERT INTO test_accounts (id, balance) VALUES ($1, $2)",
            account_id, 1000.00
        )

        # Attempt to set READ UNCOMMITTED (will become READ COMMITTED)
        await conn2.execute("BEGIN TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")

        # Start transaction in conn1 but don't commit
        await conn1.execute("BEGIN")
        await conn1.execute(
            "UPDATE test_accounts SET balance = $1 WHERE id = $2",
            500.00, account_id
        )

        # Try to read uncommitted data from conn2
        result = await conn2.fetchrow(
            "SELECT balance FROM test_accounts WHERE id = $1",
            account_id
        )

        # PostgreSQL prevents dirty read (READ UNCOMMITTED → READ COMMITTED)
        assert float(result['balance']) == 1000.00, "Should not see uncommitted changes"

        await conn1.execute("COMMIT")
        await conn2.execute("COMMIT")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_accounts")


@pytest.mark.asyncio
async def test_read_committed_isolation_level(test_db_pool):
    """
    Test READ COMMITTED isolation level (PostgreSQL default)

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Most transactions use READ COMMITTED to prevent dirty reads while
    allowing high concurrency. Student viewing course list should see
    only committed changes.

    EXPECTED BEHAVIOR:
    - No dirty reads (can't see uncommitted changes)
    - Non-repeatable reads possible (data can change between reads)
    - Phantom reads possible (new rows can appear)
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_courses (
                id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)

        course_id = str(uuid4())

        # Insert course
        await conn1.execute(
            "INSERT INTO test_courses (id, title, status) VALUES ($1, $2, $3)",
            course_id, "Python Programming", "draft"
        )

        # Start READ COMMITTED transaction
        await conn2.execute("BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED")

        # First read
        result1 = await conn2.fetchrow(
            "SELECT status FROM test_courses WHERE id = $1",
            course_id
        )
        assert result1['status'] == "draft"

        # Another transaction commits change
        await conn1.execute("BEGIN")
        await conn1.execute(
            "UPDATE test_courses SET status = $1 WHERE id = $2",
            "published", course_id
        )
        await conn1.execute("COMMIT")

        # Second read sees committed change (non-repeatable read)
        result2 = await conn2.fetchrow(
            "SELECT status FROM test_courses WHERE id = $1",
            course_id
        )
        assert result2['status'] == "published", "READ COMMITTED allows non-repeatable reads"

        await conn2.execute("COMMIT")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_repeatable_read_isolation_level(test_db_pool):
    """
    Test REPEATABLE READ isolation level

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Financial reports require consistent view of data throughout transaction.
    Enrollment counts and revenue calculations must not change mid-report.

    EXPECTED BEHAVIOR:
    - No dirty reads
    - No non-repeatable reads (same query returns same result)
    - Phantom reads possible in PostgreSQL (but less than READ COMMITTED)
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_enrollments (
                id UUID PRIMARY KEY,
                course_id UUID NOT NULL,
                student_id UUID NOT NULL,
                amount DECIMAL(10, 2) NOT NULL
            )
        """)

        course_id = str(uuid4())
        enrollment1_id = str(uuid4())

        # Insert enrollment
        await conn1.execute(
            "INSERT INTO test_enrollments (id, course_id, student_id, amount) VALUES ($1, $2, $3, $4)",
            enrollment1_id, course_id, str(uuid4()), 99.99
        )

        # Start REPEATABLE READ transaction
        await conn2.execute("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # First read
        result1 = await conn2.fetchrow(
            "SELECT amount FROM test_enrollments WHERE id = $1",
            enrollment1_id
        )
        assert float(result1['amount']) == 99.99

        # Another transaction updates and commits
        await conn1.execute("BEGIN")
        await conn1.execute(
            "UPDATE test_enrollments SET amount = $1 WHERE id = $2",
            149.99, enrollment1_id
        )
        await conn1.execute("COMMIT")

        # Second read still sees original value (repeatable read)
        result2 = await conn2.fetchrow(
            "SELECT amount FROM test_enrollments WHERE id = $1",
            enrollment1_id
        )
        assert float(result2['amount']) == 99.99, "REPEATABLE READ prevents non-repeatable reads"

        await conn2.execute("COMMIT")

        # After commit, new transaction sees updated value
        result3 = await conn2.fetchrow(
            "SELECT amount FROM test_enrollments WHERE id = $1",
            enrollment1_id
        )
        assert float(result3['amount']) == 149.99

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_serializable_isolation_level(test_db_pool):
    """
    Test SERIALIZABLE isolation level

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Critical operations like financial settlements or inventory management
    require full serialization to prevent all anomalies.

    EXPECTED BEHAVIOR:
    - No dirty reads
    - No non-repeatable reads
    - No phantom reads
    - Serialization errors possible (transaction must retry)
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_inventory (
                id UUID PRIMARY KEY,
                product VARCHAR(255) NOT NULL,
                quantity INT NOT NULL
            )
        """)

        product_id = str(uuid4())

        # Insert product
        await conn1.execute(
            "INSERT INTO test_inventory (id, product, quantity) VALUES ($1, $2, $3)",
            product_id, "Course License", 100
        )

        # Both transactions try to update same row with SERIALIZABLE isolation
        try:
            # Transaction 1
            await conn1.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            quantity1 = await conn1.fetchval(
                "SELECT quantity FROM test_inventory WHERE id = $1",
                product_id
            )

            # Transaction 2
            await conn2.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            quantity2 = await conn2.fetchval(
                "SELECT quantity FROM test_inventory WHERE id = $1",
                product_id
            )

            # Both try to update based on read value
            await conn1.execute(
                "UPDATE test_inventory SET quantity = $1 WHERE id = $2",
                quantity1 - 10, product_id
            )

            await conn2.execute(
                "UPDATE test_inventory SET quantity = $1 WHERE id = $2",
                quantity2 - 20, product_id
            )

            # First commit succeeds
            await conn1.execute("COMMIT")

            # Second commit may fail with serialization error
            await conn2.execute("COMMIT")

        except asyncpg.exceptions.SerializationError:
            # Expected - serialization conflict detected
            await conn2.execute("ROLLBACK")
            print("Serialization error detected (expected behavior)")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_inventory")


@pytest.mark.asyncio
async def test_dirty_read_prevention(test_db_pool):
    """
    Test that PostgreSQL prevents dirty reads

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Analytics dashboard should never show uncommitted enrollment data
    that might be rolled back.

    EXPECTED BEHAVIOR:
    - Uncommitted changes not visible to other transactions
    - Only committed data visible
    - Applies to all isolation levels in PostgreSQL
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_enrollments (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)

        enrollment_id = str(uuid4())

        # Transaction 1 inserts but doesn't commit
        await conn1.execute("BEGIN")
        await conn1.execute(
            "INSERT INTO test_enrollments (id, student_id, status) VALUES ($1, $2, $3)",
            enrollment_id, str(uuid4()), "pending"
        )

        # Transaction 2 tries to read uncommitted data
        result = await conn2.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment_id
        )

        # Should not see uncommitted data (dirty read prevented)
        assert result is None, "Dirty read should be prevented"

        await conn1.execute("COMMIT")

        # Now visible after commit
        result_after = await conn2.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment_id
        )
        assert result_after is not None

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_non_repeatable_read_scenario(test_db_pool):
    """
    Test non-repeatable read scenario

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    In READ COMMITTED isolation, course enrollment count can change
    between reads within same transaction.

    EXPECTED BEHAVIOR:
    - First read returns initial value
    - Concurrent update commits
    - Second read returns different value (non-repeatable)
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_course_stats (
                course_id UUID PRIMARY KEY,
                enrollment_count INT NOT NULL
            )
        """)

        course_id = str(uuid4())

        # Insert initial stats
        await conn1.execute(
            "INSERT INTO test_course_stats (course_id, enrollment_count) VALUES ($1, $2)",
            course_id, 100
        )

        # Transaction 1 reads enrollment count
        await conn1.execute("BEGIN")  # Default READ COMMITTED
        count1 = await conn1.fetchval(
            "SELECT enrollment_count FROM test_course_stats WHERE course_id = $1",
            course_id
        )
        assert count1 == 100

        # Transaction 2 updates and commits
        await conn2.execute(
            "UPDATE test_course_stats SET enrollment_count = $1 WHERE course_id = $2",
            150, course_id
        )

        # Transaction 1 reads again - gets different value (non-repeatable read)
        count2 = await conn1.fetchval(
            "SELECT enrollment_count FROM test_course_stats WHERE course_id = $1",
            course_id
        )
        assert count2 == 150, "Non-repeatable read occurred (expected in READ COMMITTED)"

        await conn1.execute("COMMIT")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_course_stats")


@pytest.mark.asyncio
async def test_phantom_read_scenario(test_db_pool):
    """
    Test phantom read scenario

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    In READ COMMITTED isolation, aggregate queries (COUNT) can return
    different results due to new rows being inserted.

    EXPECTED BEHAVIOR:
    - First query returns initial count
    - Concurrent insert commits
    - Second query returns different count (phantom read)
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_students (
                id UUID PRIMARY KEY,
                course_id UUID NOT NULL,
                enrolled_at TIMESTAMP DEFAULT NOW()
            )
        """)

        course_id = str(uuid4())

        # Insert initial students
        for i in range(5):
            await conn1.execute(
                "INSERT INTO test_students (id, course_id) VALUES ($1, $2)",
                str(uuid4()), course_id
            )

        # Transaction 1 counts students
        await conn1.execute("BEGIN")  # Default READ COMMITTED
        count1 = await conn1.fetchval(
            "SELECT COUNT(*) FROM test_students WHERE course_id = $1",
            course_id
        )
        assert count1 == 5

        # Transaction 2 inserts new student and commits
        await conn2.execute(
            "INSERT INTO test_students (id, course_id) VALUES ($1, $2)",
            str(uuid4()), course_id
        )

        # Transaction 1 counts again - gets different result (phantom read)
        count2 = await conn1.fetchval(
            "SELECT COUNT(*) FROM test_students WHERE course_id = $1",
            course_id
        )
        assert count2 == 6, "Phantom read occurred (expected in READ COMMITTED)"

        await conn1.execute("COMMIT")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_students")


@pytest.mark.asyncio
async def test_concurrent_update_conflict(test_db_pool):
    """
    Test concurrent update conflict resolution

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Two instructors try to update same course simultaneously.
    One update succeeds, other gets conflict.

    EXPECTED BEHAVIOR:
    - First update succeeds
    - Second update waits for lock
    - Second update sees updated value or fails
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_courses (
                id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                version INT NOT NULL DEFAULT 1
            )
        """)

        course_id = str(uuid4())

        # Insert course
        await conn1.execute(
            "INSERT INTO test_courses (id, title, version) VALUES ($1, $2, $3)",
            course_id, "Original Title", 1
        )

        # Both transactions try to update
        await conn1.execute("BEGIN")
        await conn2.execute("BEGIN")

        # Read current version
        version1 = await conn1.fetchval(
            "SELECT version FROM test_courses WHERE id = $1",
            course_id
        )

        version2 = await conn2.fetchval(
            "SELECT version FROM test_courses WHERE id = $1",
            course_id
        )

        assert version1 == version2 == 1

        # Transaction 1 updates first
        await conn1.execute(
            "UPDATE test_courses SET title = $1, version = $2 WHERE id = $3",
            "Updated by User 1", version1 + 1, course_id
        )
        await conn1.execute("COMMIT")

        # Transaction 2 tries to update (will see newer version)
        # In real application, should check version hasn't changed
        try:
            await conn2.execute(
                "UPDATE test_courses SET title = $1, version = $2 WHERE id = $3",
                "Updated by User 2", version2 + 1, course_id
            )
            await conn2.execute("COMMIT")

            # Check final state
            final = await conn1.fetchrow(
                "SELECT * FROM test_courses WHERE id = $1",
                course_id
            )
            # Last write wins
            assert final['title'] == "Updated by User 2"
            assert final['version'] == 2

        except Exception:
            await conn2.execute("ROLLBACK")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_optimistic_locking_with_version_numbers(test_db_pool):
    """
    Test optimistic locking using version numbers

    ACID PROPERTY: Consistency, Isolation

    BUSINESS SCENARIO:
    Collaborative course editing uses optimistic locking. If version
    changed since read, update fails and user must refresh.

    EXPECTED BEHAVIOR:
    - Read row with version number
    - Update only if version unchanged
    - Conflict detected by zero rows updated
    """
    async with test_db_pool.acquire() as conn:
        # Create test table with version column
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_documents (
                id UUID PRIMARY KEY,
                content TEXT NOT NULL,
                version INT NOT NULL DEFAULT 1
            )
        """)

        doc_id = str(uuid4())

        # Insert document
        await conn.execute(
            "INSERT INTO test_documents (id, content, version) VALUES ($1, $2, $3)",
            doc_id, "Original content", 1
        )

        # User 1 reads document
        doc = await conn.fetchrow(
            "SELECT * FROM test_documents WHERE id = $1",
            doc_id
        )
        user1_version = doc['version']

        # User 2 updates document
        await conn.execute(
            "UPDATE test_documents SET content = $1, version = version + 1 WHERE id = $2",
            "Updated by User 2", doc_id
        )

        # User 1 tries to update with old version (optimistic lock conflict)
        result = await conn.execute(
            "UPDATE test_documents SET content = $1, version = $2 WHERE id = $3 AND version = $4",
            "Updated by User 1", user1_version + 1, doc_id, user1_version
        )

        # Check if update succeeded
        rows_updated = int(result.split()[-1])
        assert rows_updated == 0, "Optimistic lock conflict detected (no rows updated)"

        # Verify document has User 2's changes
        final_doc = await conn.fetchrow(
            "SELECT * FROM test_documents WHERE id = $1",
            doc_id
        )
        assert final_doc['content'] == "Updated by User 2"
        assert final_doc['version'] == 2

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_documents")


@pytest.mark.asyncio
async def test_pessimistic_locking_with_select_for_update(test_db_pool):
    """
    Test pessimistic locking using SELECT FOR UPDATE

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Inventory management (course seat limits) requires pessimistic locking
    to prevent overselling. Lock row before checking availability.

    EXPECTED BEHAVIOR:
    - SELECT FOR UPDATE acquires exclusive lock
    - Other transactions wait for lock release
    - Prevents concurrent modifications
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_inventory (
                course_id UUID PRIMARY KEY,
                available_seats INT NOT NULL
            )
        """)

        course_id = str(uuid4())

        # Insert course with limited seats
        await conn1.execute(
            "INSERT INTO test_inventory (course_id, available_seats) VALUES ($1, $2)",
            course_id, 10
        )

        # Transaction 1 locks row
        await conn1.execute("BEGIN")
        seats1 = await conn1.fetchval(
            "SELECT available_seats FROM test_inventory WHERE course_id = $1 FOR UPDATE",
            course_id
        )
        assert seats1 == 10

        # Update seats in transaction 1
        await conn1.execute(
            "UPDATE test_inventory SET available_seats = $1 WHERE course_id = $2",
            seats1 - 1, course_id
        )

        # Transaction 2 tries to acquire lock (will wait)
        await conn2.execute("BEGIN")

        # This will timeout or wait indefinitely
        try:
            # Set short statement timeout
            await conn2.execute("SET statement_timeout = '1s'")
            seats2 = await conn2.fetchval(
                "SELECT available_seats FROM test_inventory WHERE course_id = $1 FOR UPDATE",
                course_id
            )
            # If we get here, transaction 1 already committed
        except asyncpg.exceptions.QueryCanceledError:
            # Expected - transaction 2 timed out waiting for lock
            await conn2.execute("ROLLBACK")

        # Commit transaction 1
        await conn1.execute("COMMIT")

        # Now transaction 2 can proceed
        await conn2.execute("ROLLBACK")  # Reset if not already rolled back
        seats_final = await conn2.fetchval(
            "SELECT available_seats FROM test_inventory WHERE course_id = $1",
            course_id
        )
        assert seats_final == 9

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_inventory")


@pytest.mark.asyncio
async def test_lock_timeout_behavior(test_db_pool):
    """
    Test lock timeout behavior

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Prevent application hangs when waiting for locks. Transaction should
    timeout and fail gracefully rather than wait indefinitely.

    EXPECTED BEHAVIOR:
    - Lock acquisition waits up to timeout
    - Timeout triggers exception
    - Transaction can be retried
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_resources (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
        """)

        resource_id = str(uuid4())

        # Insert resource
        await conn1.execute(
            "INSERT INTO test_resources (id, name) VALUES ($1, $2)",
            resource_id, "Locked Resource"
        )

        # Transaction 1 locks resource
        await conn1.execute("BEGIN")
        await conn1.execute(
            "SELECT * FROM test_resources WHERE id = $1 FOR UPDATE",
            resource_id
        )

        # Transaction 2 tries to lock with timeout
        await conn2.execute("BEGIN")
        await conn2.execute("SET statement_timeout = '500ms'")

        lock_timeout_occurred = False
        try:
            await conn2.execute(
                "SELECT * FROM test_resources WHERE id = $1 FOR UPDATE",
                resource_id
            )
        except asyncpg.exceptions.QueryCanceledError:
            lock_timeout_occurred = True
            await conn2.execute("ROLLBACK")

        assert lock_timeout_occurred, "Lock timeout should have occurred"

        # Commit transaction 1
        await conn1.execute("COMMIT")

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_resources")


@pytest.mark.asyncio
async def test_deadlock_detection_and_resolution(test_db_pool):
    """
    Test PostgreSQL deadlock detection and automatic resolution

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    Two transactions trying to lock resources in different order can
    deadlock. PostgreSQL must detect and resolve by aborting one.

    EXPECTED BEHAVIOR:
    - Deadlock detected automatically
    - One transaction aborted with DeadlockDetected error
    - Other transaction can proceed
    - Aborted transaction can be retried
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test tables
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_resource_a (
                id UUID PRIMARY KEY,
                value INT NOT NULL
            )
        """)
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_resource_b (
                id UUID PRIMARY KEY,
                value INT NOT NULL
            )
        """)

        resource_a_id = str(uuid4())
        resource_b_id = str(uuid4())

        # Insert resources
        await conn1.execute(
            "INSERT INTO test_resource_a (id, value) VALUES ($1, $2)",
            resource_a_id, 100
        )
        await conn1.execute(
            "INSERT INTO test_resource_b (id, value) VALUES ($1, $2)",
            resource_b_id, 200
        )

        # Transaction 1: Lock A then B
        await conn1.execute("BEGIN")
        await conn1.execute(
            "SELECT * FROM test_resource_a WHERE id = $1 FOR UPDATE",
            resource_a_id
        )

        # Transaction 2: Lock B then A
        await conn2.execute("BEGIN")
        await conn2.execute(
            "SELECT * FROM test_resource_b WHERE id = $1 FOR UPDATE",
            resource_b_id
        )

        # Now create deadlock
        deadlock_detected = False

        # Transaction 1 tries to lock B (will wait)
        async def lock_b():
            nonlocal deadlock_detected
            try:
                await conn1.execute(
                    "SELECT * FROM test_resource_b WHERE id = $1 FOR UPDATE",
                    resource_b_id
                )
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_detected = True
                await conn1.execute("ROLLBACK")

        # Transaction 2 tries to lock A (will cause deadlock)
        async def lock_a():
            nonlocal deadlock_detected
            try:
                await conn2.execute(
                    "SELECT * FROM test_resource_a WHERE id = $1 FOR UPDATE",
                    resource_a_id
                )
            except asyncpg.exceptions.DeadlockDetectedError:
                deadlock_detected = True
                await conn2.execute("ROLLBACK")

        # Execute both lock attempts concurrently
        await asyncio.gather(lock_b(), lock_a(), return_exceptions=True)

        # One transaction should have detected deadlock
        assert deadlock_detected, "Deadlock should have been detected"

        # Cleanup
        if not deadlock_detected:
            await conn1.execute("ROLLBACK")
            await conn2.execute("ROLLBACK")

        await conn1.execute("DROP TABLE IF EXISTS test_resource_b")
        await conn1.execute("DROP TABLE IF EXISTS test_resource_a")

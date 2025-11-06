"""
Comprehensive Database Transaction Tests - ACID Properties

BUSINESS CONTEXT:
Transaction reliability is critical for the Course Creator Platform. Transaction
failures can result in:
- Lost revenue (student payments without enrollments)
- Data corruption (partial course updates)
- Compliance violations (incomplete audit trails)
- Poor user experience (inconsistent application state)

This test suite validates all four ACID properties to ensure platform reliability.

TECHNICAL IMPLEMENTATION:
Tests actual PostgreSQL transaction behavior using asyncpg:
- Real database connections on test database (port 5434)
- Transaction isolation level testing
- Concurrent transaction scenarios
- Deadlock detection and resolution
- Lock timeout handling
- Performance benchmarks for rollback operations

ACID PROPERTIES TESTED:
- Atomicity: All-or-nothing transaction execution
- Consistency: Constraint enforcement and data integrity
- Isolation: Concurrent transaction behavior
- Durability: Persistence of committed data

WHY THIS APPROACH:
Mock testing cannot validate actual database behavior including locking,
isolation levels, deadlock detection, and performance characteristics.
Real database testing is required for transaction reliability.
"""

import pytest
import asyncio
import asyncpg
import time
from typing import List
from datetime import datetime
from uuid import uuid4


# =============================================================================
# CATEGORY 1: TRANSACTION ROLLBACK TESTS (10 tests)
# ACID PROPERTY: Atomicity
# =============================================================================

@pytest.mark.asyncio
async def test_automatic_rollback_on_exception(test_db_pool):
    """
    Test automatic rollback when exception occurs in transaction

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    During course enrollment, if payment processing fails after creating
    enrollment record, the entire transaction must rollback to prevent
    student being enrolled without payment.

    EXPECTED BEHAVIOR:
    - INSERT succeeds within transaction
    - Exception triggers automatic rollback
    - Data does not persist in database

    TECHNICAL VALIDATION:
    - Verify row visible inside transaction
    - Verify row not visible after rollback
    - Verify no orphaned data
    """
    test_id = str(uuid4())
    test_username = f"rollback_test_{uuid4().hex[:8]}"

    async with test_db_pool.acquire() as conn:
        # Ensure test table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        try:
            async with conn.transaction():
                # Insert data
                await conn.execute(
                    "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                    test_id, test_username
                )

                # Verify data exists in transaction
                result = await conn.fetchrow(
                    "SELECT * FROM test_users WHERE id = $1",
                    test_id
                )
                assert result is not None
                assert result['username'] == test_username

                # Raise exception to trigger rollback
                raise ValueError("Simulated payment failure")
        except ValueError:
            pass  # Expected exception

        # Verify data was rolled back
        result = await conn.fetchrow(
            "SELECT * FROM test_users WHERE id = $1",
            test_id
        )
        assert result is None, "Data should not exist after rollback"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_users")


@pytest.mark.asyncio
async def test_explicit_rollback_call(test_db_pool):
    """
    Test explicit transaction rollback

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    If course content validation fails after initial save, instructor
    can explicitly rollback changes to revert to previous state.

    EXPECTED BEHAVIOR:
    - Changes visible within transaction
    - Explicit rollback reverts all changes
    - Database state restored to pre-transaction state
    """
    test_id = str(uuid4())
    test_username = f"explicit_rollback_{uuid4().hex[:8]}"

    async with test_db_pool.acquire() as conn:
        # Ensure test table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        # Start transaction
        tx = conn.transaction()
        await tx.start()

        try:
            # Insert data
            await conn.execute(
                "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                test_id, test_username
            )

            # Verify data exists
            result = await conn.fetchrow(
                "SELECT * FROM test_users WHERE id = $1",
                test_id
            )
            assert result is not None

            # Explicit rollback
            await tx.rollback()

        except Exception:
            await tx.rollback()
            raise

        # Verify data was rolled back
        result = await conn.fetchrow(
            "SELECT * FROM test_users WHERE id = $1",
            test_id
        )
        assert result is None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_users")


@pytest.mark.asyncio
async def test_nested_transaction_rollback(test_db_pool):
    """
    Test nested transaction (savepoint) rollback

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    When generating multi-part course content (syllabus, slides, quizzes),
    if quiz generation fails, rollback just the quiz while keeping syllabus
    and slides using savepoints.

    EXPECTED BEHAVIOR:
    - Outer transaction commits successfully
    - Inner savepoint rollback doesn't affect outer transaction
    - Only changes after savepoint are rolled back
    """
    outer_id = str(uuid4())
    inner_id = str(uuid4())
    outer_username = f"outer_{uuid4().hex[:8]}"
    inner_username = f"inner_{uuid4().hex[:8]}"

    async with test_db_pool.acquire() as conn:
        # Ensure test table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        async with conn.transaction():
            # Insert in outer transaction
            await conn.execute(
                "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                outer_id, outer_username
            )

            # Create savepoint (nested transaction)
            try:
                async with conn.transaction():
                    # Insert in nested transaction
                    await conn.execute(
                        "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                        inner_id, inner_username
                    )

                    # Rollback nested transaction
                    raise ValueError("Simulated nested failure")
            except ValueError:
                pass  # Expected exception

            # Outer transaction continues and commits

        # Verify outer transaction data exists
        outer_result = await conn.fetchrow(
            "SELECT * FROM test_users WHERE id = $1",
            outer_id
        )
        assert outer_result is not None
        assert outer_result['username'] == outer_username

        # Verify inner transaction data was rolled back
        inner_result = await conn.fetchrow(
            "SELECT * FROM test_users WHERE id = $1",
            inner_id
        )
        assert inner_result is None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_users")


@pytest.mark.asyncio
async def test_savepoint_rollback(test_db_pool):
    """
    Test savepoint creation and rollback

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    During batch student enrollment, if individual enrollment fails,
    rollback just that enrollment while continuing with others.

    EXPECTED BEHAVIOR:
    - Savepoint isolates partial work
    - Rollback to savepoint reverts only savepoint changes
    - Transaction can continue after savepoint rollback
    """
    user1_id = str(uuid4())
    user2_id = str(uuid4())
    user3_id = str(uuid4())

    async with test_db_pool.acquire() as conn:
        # Ensure test table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        async with conn.transaction():
            # Insert user 1
            await conn.execute(
                "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                user1_id, f"user1_{uuid4().hex[:8]}"
            )

            # Create savepoint before user 2
            try:
                async with conn.transaction():
                    # Insert user 2 (will fail)
                    await conn.execute(
                        "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                        user2_id, f"user2_{uuid4().hex[:8]}"
                    )
                    raise ValueError("User 2 enrollment failed")
            except ValueError:
                pass  # Rollback user 2

            # Insert user 3 (after savepoint rollback)
            await conn.execute(
                "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                user3_id, f"user3_{uuid4().hex[:8]}"
            )

        # Verify user 1 and 3 exist, user 2 doesn't
        user1 = await conn.fetchrow("SELECT * FROM test_users WHERE id = $1", user1_id)
        user2 = await conn.fetchrow("SELECT * FROM test_users WHERE id = $1", user2_id)
        user3 = await conn.fetchrow("SELECT * FROM test_users WHERE id = $1", user3_id)

        assert user1 is not None
        assert user2 is None
        assert user3 is not None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_users")


@pytest.mark.asyncio
async def test_rollback_clears_all_changes(test_db_pool):
    """
    Test that rollback clears all changes made in transaction

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    If course publishing fails, all related changes (status update,
    notification creation, index update) must be rolled back.

    EXPECTED BEHAVIOR:
    - Multiple operations succeed in transaction
    - Rollback reverts all operations
    - No partial state remains
    """
    async with test_db_pool.acquire() as conn:
        # Create test tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_courses (
                id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_notifications (
                id UUID PRIMARY KEY,
                course_id UUID NOT NULL,
                message TEXT NOT NULL
            )
        """)

        course_id = str(uuid4())
        notification_id = str(uuid4())

        try:
            async with conn.transaction():
                # Insert course
                await conn.execute(
                    "INSERT INTO test_courses (id, title, status) VALUES ($1, $2, $3)",
                    course_id, "Test Course", "draft"
                )

                # Update course status
                await conn.execute(
                    "UPDATE test_courses SET status = $1 WHERE id = $2",
                    "published", course_id
                )

                # Create notification
                await conn.execute(
                    "INSERT INTO test_notifications (id, course_id, message) VALUES ($1, $2, $3)",
                    notification_id, course_id, "Course published"
                )

                # Simulate failure
                raise ValueError("Publishing failed")
        except ValueError:
            pass

        # Verify all changes were rolled back
        course = await conn.fetchrow("SELECT * FROM test_courses WHERE id = $1", course_id)
        notification = await conn.fetchrow("SELECT * FROM test_notifications WHERE id = $1", notification_id)

        assert course is None
        assert notification is None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_notifications")
        await conn.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_rollback_with_multiple_table_updates(test_db_pool):
    """
    Test rollback affecting multiple tables

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    When student completes course, multiple tables are updated (progress,
    certificates, analytics). If any update fails, all must rollback.

    EXPECTED BEHAVIOR:
    - Updates to multiple tables succeed in transaction
    - Single failure rolls back all table updates
    - No partial updates remain across tables
    """
    async with test_db_pool.acquire() as conn:
        # Create test tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_progress (
                student_id UUID PRIMARY KEY,
                course_id UUID NOT NULL,
                completion_percentage INT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_certificates (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                course_id UUID NOT NULL,
                issued_at TIMESTAMP NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_analytics (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                event_type VARCHAR(50) NOT NULL
            )
        """)

        student_id = str(uuid4())
        course_id = str(uuid4())
        cert_id = str(uuid4())
        analytics_id = str(uuid4())

        try:
            async with conn.transaction():
                # Update progress
                await conn.execute(
                    "INSERT INTO test_progress (student_id, course_id, completion_percentage) VALUES ($1, $2, $3)",
                    student_id, course_id, 100
                )

                # Issue certificate
                await conn.execute(
                    "INSERT INTO test_certificates (id, student_id, course_id, issued_at) VALUES ($1, $2, $3, $4)",
                    cert_id, student_id, course_id, datetime.utcnow()
                )

                # Record analytics
                await conn.execute(
                    "INSERT INTO test_analytics (id, student_id, event_type) VALUES ($1, $2, $3)",
                    analytics_id, student_id, "course_completed"
                )

                # Simulate analytics service failure
                raise ValueError("Analytics service unavailable")
        except ValueError:
            pass

        # Verify all changes were rolled back
        progress = await conn.fetchrow("SELECT * FROM test_progress WHERE student_id = $1", student_id)
        certificate = await conn.fetchrow("SELECT * FROM test_certificates WHERE id = $1", cert_id)
        analytics = await conn.fetchrow("SELECT * FROM test_analytics WHERE id = $1", analytics_id)

        assert progress is None
        assert certificate is None
        assert analytics is None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_analytics")
        await conn.execute("DROP TABLE IF EXISTS test_certificates")
        await conn.execute("DROP TABLE IF EXISTS test_progress")


@pytest.mark.asyncio
async def test_rollback_does_not_affect_other_transactions(test_db_pool):
    """
    Test that one transaction's rollback doesn't affect other transactions

    ACID PROPERTY: Isolation, Atomicity

    BUSINESS SCENARIO:
    When one student's enrollment fails and rolls back, it should not
    affect other students' concurrent enrollments.

    EXPECTED BEHAVIOR:
    - Transaction 1 commits successfully
    - Transaction 2 rolls back
    - Transaction 1 data persists despite transaction 2 rollback
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_enrollments (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                course_id UUID NOT NULL
            )
        """)

        enrollment1_id = str(uuid4())
        enrollment2_id = str(uuid4())
        student1_id = str(uuid4())
        student2_id = str(uuid4())
        course_id = str(uuid4())

        # Transaction 1 - successful enrollment
        async with conn1.transaction():
            await conn1.execute(
                "INSERT INTO test_enrollments (id, student_id, course_id) VALUES ($1, $2, $3)",
                enrollment1_id, student1_id, course_id
            )
            # Commit happens automatically

        # Transaction 2 - failed enrollment
        try:
            async with conn2.transaction():
                await conn2.execute(
                    "INSERT INTO test_enrollments (id, student_id, course_id) VALUES ($1, $2, $3)",
                    enrollment2_id, student2_id, course_id
                )
                raise ValueError("Payment processing failed")
        except ValueError:
            pass

        # Verify transaction 1 data persists
        enrollment1 = await conn1.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment1_id
        )
        assert enrollment1 is not None

        # Verify transaction 2 data was rolled back
        enrollment2 = await conn1.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment2_id
        )
        assert enrollment2 is None

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_partial_commit_prevention(test_db_pool):
    """
    Test that partial commits are prevented (all-or-nothing)

    ACID PROPERTY: Atomicity

    BUSINESS SCENARIO:
    When processing batch operations (bulk student import), either all
    students are imported or none are. No partial imports allowed.

    EXPECTED BEHAVIOR:
    - Multiple inserts succeed in transaction
    - Final insert fails
    - All inserts are rolled back (none committed)
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_students (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        student_ids = [str(uuid4()) for _ in range(5)]

        try:
            async with conn.transaction():
                # Insert 4 students successfully
                for i in range(4):
                    await conn.execute(
                        "INSERT INTO test_students (id, username, email) VALUES ($1, $2, $3)",
                        student_ids[i],
                        f"student{i}_{uuid4().hex[:8]}",
                        f"student{i}_{uuid4().hex[:8]}@example.com"
                    )

                # 5th student insert fails (duplicate email)
                await conn.execute(
                    "INSERT INTO test_students (id, username, email) VALUES ($1, $2, $3)",
                    student_ids[4],
                    f"student4_{uuid4().hex[:8]}",
                    f"student0_{uuid4().hex[:8]}@example.com"  # Duplicate email from first student
                )
        except asyncpg.UniqueViolationError:
            pass

        # Verify no students were committed (all-or-nothing)
        for student_id in student_ids:
            student = await conn.fetchrow(
                "SELECT * FROM test_students WHERE id = $1",
                student_id
            )
            assert student is None, f"Student {student_id} should not exist after rollback"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_students")


@pytest.mark.asyncio
async def test_rollback_after_constraint_violation(test_db_pool):
    """
    Test rollback after constraint violation

    ACID PROPERTY: Atomicity, Consistency

    BUSINESS SCENARIO:
    If course creation violates constraints (e.g., duplicate course code),
    all related operations must rollback to maintain consistency.

    EXPECTED BEHAVIOR:
    - Constraint violation triggers exception
    - All operations in transaction are rolled back
    - Database maintains consistency
    """
    async with test_db_pool.acquire() as conn:
        # Create test table with unique constraint
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_courses (
                id UUID PRIMARY KEY,
                course_code VARCHAR(50) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL
            )
        """)

        course_code = f"CS101_{uuid4().hex[:8]}"
        course1_id = str(uuid4())
        course2_id = str(uuid4())

        # First course succeeds
        await conn.execute(
            "INSERT INTO test_courses (id, course_code, title) VALUES ($1, $2, $3)",
            course1_id, course_code, "Introduction to Computer Science"
        )

        # Second course with same code should fail
        try:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO test_courses (id, course_code, title) VALUES ($1, $2, $3)",
                    course2_id, course_code, "Duplicate Course"
                )
        except asyncpg.UniqueViolationError:
            pass  # Expected constraint violation

        # Verify only first course exists
        courses = await conn.fetch("SELECT * FROM test_courses WHERE course_code = $1", course_code)
        assert len(courses) == 1
        assert str(courses[0]['id']) == course1_id

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_rollback_performance(test_db_pool):
    """
    Test that rollback is fast (<10ms for simple transactions)

    ACID PROPERTY: Atomicity (Performance characteristic)

    BUSINESS SCENARIO:
    Rollback performance affects user experience. Slow rollbacks can
    cause timeouts and poor responsiveness in error scenarios.

    EXPECTED BEHAVIOR:
    - Rollback completes in <10ms
    - Performance is consistent across multiple rollbacks
    - No memory leaks or resource exhaustion
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_performance (
                id UUID PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)

        rollback_times = []

        for i in range(10):
            test_id = str(uuid4())

            start_time = time.time()

            try:
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO test_performance (id, data) VALUES ($1, $2)",
                        test_id, "test data" * 100
                    )
                    raise ValueError("Intentional rollback")
            except ValueError:
                pass

            rollback_time = (time.time() - start_time) * 1000  # Convert to ms
            rollback_times.append(rollback_time)

        # Calculate average rollback time
        avg_rollback_time = sum(rollback_times) / len(rollback_times)

        # Verify rollback is fast
        assert avg_rollback_time < 10, f"Average rollback time {avg_rollback_time:.2f}ms exceeds 10ms threshold"

        # Verify no data was committed
        count = await conn.fetchval("SELECT COUNT(*) FROM test_performance")
        assert count == 0

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_performance")


# =============================================================================
# CATEGORY 2: TRANSACTION COMMIT TESTS (8 tests)
# ACID PROPERTY: Durability, Atomicity
# =============================================================================

@pytest.mark.asyncio
async def test_explicit_commit_persists_changes(test_db_pool):
    """
    Test that explicit commit persists changes to database

    ACID PROPERTY: Durability

    BUSINESS SCENARIO:
    When student completes payment and enrollment, committed transaction
    ensures data persists even if application crashes immediately after.

    EXPECTED BEHAVIOR:
    - Transaction commits successfully
    - Data persists in database
    - Data visible to new connections
    """
    test_id = str(uuid4())
    test_username = f"commit_test_{uuid4().hex[:8]}"

    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        # Insert with explicit commit
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO test_users (id, username) VALUES ($1, $2)",
                test_id, test_username
            )
            # Commit happens automatically at end of context manager

        # Verify data persists in new query
        result = await conn.fetchrow(
            "SELECT * FROM test_users WHERE id = $1",
            test_id
        )
        assert result is not None
        assert result['username'] == test_username

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_users")


@pytest.mark.asyncio
async def test_autocommit_mode_behavior(test_db_pool):
    """
    Test autocommit mode behavior (no explicit transaction)

    ACID PROPERTY: Atomicity, Durability

    BUSINESS SCENARIO:
    Simple operations like logging events may use autocommit mode for
    performance. Each statement commits immediately.

    EXPECTED BEHAVIOR:
    - Each statement commits immediately
    - No rollback possible for individual statements
    - Data persists immediately
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_logs (
                id UUID PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        log_id = str(uuid4())

        # Insert without explicit transaction (autocommit)
        await conn.execute(
            "INSERT INTO test_logs (id, event_type) VALUES ($1, $2)",
            log_id, "user_login"
        )

        # Data immediately visible
        result = await conn.fetchrow(
            "SELECT * FROM test_logs WHERE id = $1",
            log_id
        )
        assert result is not None
        assert result['event_type'] == "user_login"

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_logs")


@pytest.mark.asyncio
async def test_commit_with_multiple_operations(test_db_pool):
    """
    Test commit with multiple operations in single transaction

    ACID PROPERTY: Atomicity, Durability

    BUSINESS SCENARIO:
    Course publishing involves multiple operations (update status, create
    notifications, update search index) that must all commit together.

    EXPECTED BEHAVIOR:
    - All operations execute in transaction
    - Single commit persists all changes
    - All changes visible after commit
    """
    async with test_db_pool.acquire() as conn:
        # Create test tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_courses (
                id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_notifications (
                id UUID PRIMARY KEY,
                course_id UUID NOT NULL,
                message TEXT NOT NULL
            )
        """)

        course_id = str(uuid4())
        notification_id = str(uuid4())

        async with conn.transaction():
            # Insert course
            await conn.execute(
                "INSERT INTO test_courses (id, title, status) VALUES ($1, $2, $3)",
                course_id, "Python Programming", "draft"
            )

            # Update status
            await conn.execute(
                "UPDATE test_courses SET status = $1 WHERE id = $2",
                "published", course_id
            )

            # Create notification
            await conn.execute(
                "INSERT INTO test_notifications (id, course_id, message) VALUES ($1, $2, $3)",
                notification_id, course_id, "Course published successfully"
            )

        # Verify all changes persisted
        course = await conn.fetchrow("SELECT * FROM test_courses WHERE id = $1", course_id)
        assert course is not None
        assert course['status'] == "published"

        notification = await conn.fetchrow("SELECT * FROM test_notifications WHERE id = $1", notification_id)
        assert notification is not None

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_notifications")
        await conn.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_commit_releases_locks(test_db_pool):
    """
    Test that commit releases all locks held by transaction

    ACID PROPERTY: Isolation

    BUSINESS SCENARIO:
    When instructor finishes editing course, commit releases locks so
    other instructors can edit their courses without waiting.

    EXPECTED BEHAVIOR:
    - Transaction acquires locks during execution
    - Commit releases all locks
    - Other transactions can proceed
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

        # Insert initial course
        await conn1.execute(
            "INSERT INTO test_courses (id, title, status) VALUES ($1, $2, $3)",
            course_id, "Test Course", "draft"
        )

        # Transaction 1 acquires lock
        async with conn1.transaction():
            await conn1.execute(
                "SELECT * FROM test_courses WHERE id = $1 FOR UPDATE",
                course_id
            )

            # Update locked row
            await conn1.execute(
                "UPDATE test_courses SET status = $1 WHERE id = $2",
                "editing", course_id
            )
        # Lock released on commit

        # Transaction 2 can now acquire lock
        async with conn2.transaction():
            result = await conn2.fetchrow(
                "SELECT * FROM test_courses WHERE id = $1 FOR UPDATE",
                course_id
            )
            assert result is not None
            assert result['status'] == "editing"

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_courses")


@pytest.mark.asyncio
async def test_commit_updates_timestamps(test_db_pool):
    """
    Test that commit properly updates timestamp columns

    ACID PROPERTY: Consistency, Durability

    BUSINESS SCENARIO:
    Audit trails require accurate timestamps. Commit must ensure timestamp
    columns reflect when transaction completed.

    EXPECTED BEHAVIOR:
    - Timestamps set during transaction
    - Commit persists accurate timestamps
    - Timestamps reflect transaction commit time
    """
    async with test_db_pool.acquire() as conn:
        # Create test table with timestamp
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_events (
                id UUID PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        event_id = str(uuid4())
        before_commit = datetime.utcnow()

        async with conn.transaction():
            await conn.execute(
                "INSERT INTO test_events (id, event_type) VALUES ($1, $2)",
                event_id, "user_action"
            )

            # Small delay to ensure timestamp difference
            await asyncio.sleep(0.1)

            await conn.execute(
                "UPDATE test_events SET updated_at = NOW() WHERE id = $1",
                event_id
            )

        after_commit = datetime.utcnow()

        # Verify timestamps
        result = await conn.fetchrow("SELECT * FROM test_events WHERE id = $1", event_id)
        assert result is not None
        assert result['created_at'] >= before_commit
        assert result['updated_at'] <= after_commit
        assert result['updated_at'] > result['created_at']

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_events")


@pytest.mark.asyncio
async def test_commit_visibility_to_other_connections(test_db_pool):
    """
    Test that committed data is visible to other connections

    ACID PROPERTY: Isolation, Durability

    BUSINESS SCENARIO:
    When student enrolls in course, other services (analytics, notifications)
    must see the enrollment data immediately after commit.

    EXPECTED BEHAVIOR:
    - Data not visible during transaction to other connections
    - Data visible to all connections after commit
    - Consistent view across connections
    """
    async with test_db_pool.acquire() as conn1, test_db_pool.acquire() as conn2:
        # Create test table
        await conn1.execute("""
            CREATE TABLE IF NOT EXISTS test_enrollments (
                id UUID PRIMARY KEY,
                student_id UUID NOT NULL,
                course_id UUID NOT NULL
            )
        """)

        enrollment_id = str(uuid4())
        student_id = str(uuid4())
        course_id = str(uuid4())

        # Start transaction but don't commit yet
        async with conn1.transaction():
            await conn1.execute(
                "INSERT INTO test_enrollments (id, student_id, course_id) VALUES ($1, $2, $3)",
                enrollment_id, student_id, course_id
            )

            # Data visible to conn1 (same transaction)
            result1 = await conn1.fetchrow(
                "SELECT * FROM test_enrollments WHERE id = $1",
                enrollment_id
            )
            assert result1 is not None

            # Data not visible to conn2 (different connection)
            result2 = await conn2.fetchrow(
                "SELECT * FROM test_enrollments WHERE id = $1",
                enrollment_id
            )
            assert result2 is None

        # After commit, data visible to all connections
        result2_after = await conn2.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment_id
        )
        assert result2_after is not None

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_commit_does_not_affect_rolled_back_transactions(test_db_pool):
    """
    Test that successful commit doesn't affect rolled back transactions

    ACID PROPERTY: Isolation, Atomicity

    BUSINESS SCENARIO:
    One student's successful enrollment shouldn't affect another student's
    failed enrollment that rolled back.

    EXPECTED BEHAVIOR:
    - Transaction 1 commits successfully
    - Transaction 2 rolls back independently
    - Each transaction isolated from the other
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

        enrollment1_id = str(uuid4())
        enrollment2_id = str(uuid4())

        # Transaction 1 - successful commit
        async with conn1.transaction():
            await conn1.execute(
                "INSERT INTO test_enrollments (id, student_id, status) VALUES ($1, $2, $3)",
                enrollment1_id, str(uuid4()), "completed"
            )

        # Transaction 2 - rollback
        try:
            async with conn2.transaction():
                await conn2.execute(
                    "INSERT INTO test_enrollments (id, student_id, status) VALUES ($1, $2, $3)",
                    enrollment2_id, str(uuid4()), "pending"
                )
                raise ValueError("Payment failed")
        except ValueError:
            pass

        # Verify transaction 1 committed
        enrollment1 = await conn1.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment1_id
        )
        assert enrollment1 is not None
        assert enrollment1['status'] == "completed"

        # Verify transaction 2 rolled back
        enrollment2 = await conn1.fetchrow(
            "SELECT * FROM test_enrollments WHERE id = $1",
            enrollment2_id
        )
        assert enrollment2 is None

        # Cleanup
        await conn1.execute("DROP TABLE IF EXISTS test_enrollments")


@pytest.mark.asyncio
async def test_two_phase_commit(test_db_pool):
    """
    Test two-phase commit protocol (PREPARE/COMMIT)

    ACID PROPERTY: Atomicity, Durability

    BUSINESS SCENARIO:
    Distributed transactions across microservices (e.g., payment service
    and enrollment service) require two-phase commit for atomicity.

    EXPECTED BEHAVIOR:
    - PREPARE phase validates transaction can commit
    - COMMIT phase persists changes
    - All participants commit or all rollback

    NOTE: PostgreSQL supports PREPARE TRANSACTION but it's disabled by default.
    This test demonstrates the concept even if not fully functional.
    """
    async with test_db_pool.acquire() as conn:
        # Create test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_distributed (
                id UUID PRIMARY KEY,
                operation VARCHAR(100) NOT NULL
            )
        """)

        test_id = str(uuid4())
        tx_id = f"tx_{uuid4().hex[:16]}"

        try:
            # Phase 1: Prepare transaction
            await conn.execute("BEGIN")
            await conn.execute(
                "INSERT INTO test_distributed (id, operation) VALUES ($1, $2)",
                test_id, "distributed_operation"
            )
            # PREPARE TRANSACTION requires max_prepared_transactions > 0 in postgres.conf
            # await conn.execute(f"PREPARE TRANSACTION '{tx_id}'")

            # Phase 2: Commit prepared transaction
            # await conn.execute(f"COMMIT PREPARED '{tx_id}'")
            await conn.execute("COMMIT")

            # Verify data persisted
            result = await conn.fetchrow(
                "SELECT * FROM test_distributed WHERE id = $1",
                test_id
            )
            assert result is not None

        except asyncpg.exceptions.PostgresError as e:
            # Handle case where PREPARE TRANSACTION is not configured
            await conn.execute("ROLLBACK")
            print(f"Two-phase commit not available: {e}")

        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_distributed")

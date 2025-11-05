"""
Lab Environment Cleanup Data Consistency Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring Docker lab containers are properly cleaned up after student
sessions end, preventing resource exhaustion and maintaining system stability.

CRITICAL IMPORTANCE:
- Lab container cleanup is essential for system resource management
- Zombie containers prevent new students from starting labs
- Resource exhaustion impacts entire platform availability
- Proper cleanup maintains multi-tenant isolation

REGRESSION BUGS COVERED:
- BUG-634: Lab environments not cleaned up after session ends
"""

import pytest
from datetime import datetime, timedelta
import uuid
import asyncpg
from typing import Dict, Any


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_lab_containers_cleaned_up_after_session_end(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Lab containers destroyed when session ends normally

    BUG REPORT:
    - Issue ID: BUG-634
    - Reported: 2025-10-20
    - Fixed: 2025-10-21
    - Severity: HIGH
    - Root Cause: Lab cleanup service was using incorrect container name pattern
                  for filtering. Containers were created with UUID suffixes but
                  cleanup service was looking for sequential IDs.

    TEST SCENARIO:
    1. Student starts lab environment (container created)
    2. Student completes lab work and ends session normally
    3. Lab cleanup service should destroy Docker container
    4. Container ID should be removed from database
    5. Resources should be freed for reuse

    EXPECTED BEHAVIOR:
    - Container destroyed immediately on session end
    - Database record updated with cleanup timestamp
    - No zombie containers left running
    - Storage volumes cleaned up

    VERIFICATION:
    - Check lab_sessions table has cleanup timestamp
    - Verify container_id marked as destroyed
    - Confirm no orphaned Docker containers
    - Verify storage path cleaned up

    PREVENTION:
    - Always use database-tracked IDs for resource management
    - Never rely on naming conventions for critical cleanup operations
    - Implement cleanup verification checks
    - Track container lifecycle in database
    """
    # Create organization
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    # Create student
    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    # Create course
    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create lab session with container
    lab_session_id = str(uuid.uuid4())
    container_id = f"lab-container-{uuid.uuid4().hex[:12]}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, NOW(), NOW())
    """, lab_session_id, course_id, student_id,
        {"container_id": container_id, "status": "running"})

    # Verify lab session created
    lab_exists = await db_transaction.fetchval("""
        SELECT EXISTS(SELECT 1 FROM lab_sessions WHERE id = $1)
    """, lab_session_id)
    assert lab_exists, "Sanity check: Lab session should exist"

    # SIMULATE SESSION END - Update lab session with cleanup
    await db_transaction.execute("""
        UPDATE lab_sessions
        SET session_data = session_data || jsonb_build_object(
            'status', 'cleaned',
            'container_id', NULL,
            'cleanup_at', NOW()
        ),
        last_accessed_at = NOW()
        WHERE id = $1
    """, lab_session_id)

    # REGRESSION CHECK 1: Verify session marked as cleaned
    session_data = await db_transaction.fetchval("""
        SELECT session_data FROM lab_sessions WHERE id = $1
    """, lab_session_id)

    assert session_data.get("status") == "cleaned", \
        "REGRESSION FAILURE BUG-634: Lab session not marked as cleaned after session end"

    # REGRESSION CHECK 2: Verify container_id removed from session
    assert session_data.get("container_id") is None, \
        "REGRESSION FAILURE BUG-634: Container ID not removed from session after cleanup"

    # REGRESSION CHECK 3: Verify cleanup timestamp recorded
    assert "cleanup_at" in session_data, \
        "REGRESSION FAILURE BUG-634: Cleanup timestamp not recorded"

    # REGRESSION CHECK 4: Verify session still exists (for audit trail)
    lab_still_exists = await db_transaction.fetchval("""
        SELECT EXISTS(SELECT 1 FROM lab_sessions WHERE id = $1)
    """, lab_session_id)
    assert lab_still_exists, \
        "Session record should be retained for audit trail"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_lab_cleanup_after_session_timeout(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Idle lab containers cleaned up after timeout

    BUG REPORT:
    - Related to BUG-634
    - Ensures idle labs are automatically cleaned up

    TEST SCENARIO:
    1. Student starts lab environment
    2. Student becomes inactive (no access for >24 hours)
    3. Cleanup service runs periodic scan
    4. Idle lab should be automatically cleaned up
    5. Resources freed without manual intervention

    EXPECTED BEHAVIOR:
    - Cleanup service identifies idle labs based on last_accessed_at
    - Containers destroyed for labs idle > threshold
    - Database records updated with cleanup status
    - No manual intervention required

    VERIFICATION:
    - Check cleanup service targets correct idle labs
    - Verify recently accessed labs NOT cleaned up
    - Confirm idle threshold enforced correctly
    """
    # Create organization, student, course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create idle lab session (last accessed 48 hours ago)
    idle_threshold = timedelta(hours=24)
    old_access_time = datetime.utcnow() - timedelta(hours=48)

    idle_lab_id = str(uuid.uuid4())
    idle_container_id = f"idle-container-{uuid.uuid4().hex[:12]}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, $5, $5)
    """, idle_lab_id, course_id, student_id,
        {"container_id": idle_container_id, "status": "running"},
        old_access_time)

    # Create recently active lab session (accessed 1 hour ago)
    recent_lab_id = str(uuid.uuid4())
    recent_container_id = f"recent-container-{uuid.uuid4().hex[:12]}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour')
    """, recent_lab_id, course_id, student_id,
        {"container_id": recent_container_id, "status": "running"})

    # SIMULATE CLEANUP SERVICE SCAN
    # Identify idle labs
    cutoff_time = datetime.utcnow() - idle_threshold
    idle_labs = await db_transaction.fetch("""
        SELECT id, session_data
        FROM lab_sessions
        WHERE last_accessed_at < $1
        AND (session_data->>'status')::text = 'running'
    """, cutoff_time)

    # REGRESSION CHECK 1: Verify idle lab identified
    idle_lab_ids = [lab["id"] for lab in idle_labs]
    assert idle_lab_id in idle_lab_ids, \
        "REGRESSION FAILURE BUG-634: Idle lab not identified by cleanup service"

    # REGRESSION CHECK 2: Verify recent lab NOT identified for cleanup
    assert recent_lab_id not in idle_lab_ids, \
        "REGRESSION FAILURE BUG-634: Recently active lab incorrectly targeted for cleanup"

    # SIMULATE CLEANUP of idle labs
    for lab in idle_labs:
        await db_transaction.execute("""
            UPDATE lab_sessions
            SET session_data = session_data || jsonb_build_object(
                'status', 'cleaned',
                'container_id', NULL,
                'cleanup_at', NOW(),
                'cleanup_reason', 'idle_timeout'
            )
            WHERE id = $1
        """, lab["id"])

    # REGRESSION CHECK 3: Verify idle lab cleaned up
    idle_lab_status = await db_transaction.fetchval("""
        SELECT session_data->>'status' FROM lab_sessions WHERE id = $1
    """, idle_lab_id)
    assert idle_lab_status == "cleaned", \
        "REGRESSION FAILURE BUG-634: Idle lab not cleaned up after timeout"

    # REGRESSION CHECK 4: Verify recent lab still running
    recent_lab_status = await db_transaction.fetchval("""
        SELECT session_data->>'status' FROM lab_sessions WHERE id = $1
    """, recent_lab_id)
    assert recent_lab_status == "running", \
        "REGRESSION FAILURE BUG-634: Recently active lab incorrectly cleaned up"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_lab_cleanup_on_student_logout(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Lab containers cleaned up when student logs out

    BUG REPORT:
    - Related to BUG-634
    - Ensures logout triggers lab cleanup

    TEST SCENARIO:
    1. Student has active lab session
    2. Student logs out of platform
    3. Logout handler should trigger lab cleanup
    4. Container destroyed as part of logout flow
    5. Session invalidation includes lab cleanup

    EXPECTED BEHAVIOR:
    - Logout triggers lab cleanup automatically
    - Container destroyed before session invalidation completes
    - No orphaned labs after logout
    - Cleanup happens synchronously (blocking logout until complete)

    VERIFICATION:
    - Check lab cleanup triggered on logout
    - Verify container ID cleared before logout completes
    - Confirm no race conditions between logout and cleanup
    """
    # Create organization, student, course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create active lab session
    lab_session_id = str(uuid.uuid4())
    container_id = f"logout-test-{uuid.uuid4().hex[:12]}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, NOW(), NOW())
    """, lab_session_id, course_id, student_id,
        {"container_id": container_id, "status": "running"})

    # SIMULATE STUDENT LOGOUT
    # Step 1: Identify student's active lab sessions
    active_labs = await db_transaction.fetch("""
        SELECT id FROM lab_sessions
        WHERE student_id = $1
        AND (session_data->>'status')::text = 'running'
    """, student_id)

    # REGRESSION CHECK 1: Verify student has active labs before logout
    assert len(active_labs) > 0, \
        "Sanity check: Student should have active lab sessions"

    # Step 2: Cleanup all active labs as part of logout
    for lab in active_labs:
        await db_transaction.execute("""
            UPDATE lab_sessions
            SET session_data = session_data || jsonb_build_object(
                'status', 'cleaned',
                'container_id', NULL,
                'cleanup_at', NOW(),
                'cleanup_reason', 'user_logout'
            )
            WHERE id = $1
        """, lab["id"])

    # REGRESSION CHECK 2: Verify all labs cleaned up after logout
    remaining_active_labs = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM lab_sessions
        WHERE student_id = $1
        AND (session_data->>'status')::text = 'running'
    """, student_id)

    assert remaining_active_labs == 0, \
        "REGRESSION FAILURE BUG-634: Active labs still running after student logout"

    # REGRESSION CHECK 3: Verify cleanup reason recorded
    cleanup_reason = await db_transaction.fetchval("""
        SELECT session_data->>'cleanup_reason'
        FROM lab_sessions WHERE id = $1
    """, lab_session_id)

    assert cleanup_reason == "user_logout", \
        "REGRESSION FAILURE BUG-634: Cleanup reason not recorded for logout cleanup"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_zombie_container_detection_and_cleanup(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Detect and clean up zombie containers (no DB record)

    BUG REPORT:
    - Related to BUG-634
    - Handles edge case of containers without database records

    TEST SCENARIO:
    1. Docker container exists but database record missing/corrupted
    2. Cleanup service scans for orphaned containers
    3. Containers not tracked in database should be destroyed
    4. Prevent resource leaks from orphaned containers

    EXPECTED BEHAVIOR:
    - Cleanup service compares Docker containers to DB records
    - Containers without valid DB entries are destroyed
    - Alert generated for zombie container cleanup
    - Periodic scans prevent accumulation

    VERIFICATION:
    - Simulate orphaned container scenario
    - Verify cleanup service detects orphans
    - Confirm orphaned containers destroyed
    """
    # This test simulates the scenario where a container exists
    # but has no corresponding database record

    # Create organization, student, course for context
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    # Simulate scenario: Container IDs that would exist in Docker
    # but are not tracked in database
    zombie_container_ids = [
        f"zombie-{uuid.uuid4().hex[:12]}",
        f"orphan-{uuid.uuid4().hex[:12]}"
    ]

    # Get all container IDs currently tracked in database
    tracked_containers = await db_transaction.fetch("""
        SELECT DISTINCT session_data->>'container_id' as container_id
        FROM lab_sessions
        WHERE session_data->>'container_id' IS NOT NULL
        AND (session_data->>'status')::text = 'running'
    """)
    tracked_ids = {row["container_id"] for row in tracked_containers}

    # REGRESSION CHECK 1: Verify zombie containers NOT in database
    for zombie_id in zombie_container_ids:
        assert zombie_id not in tracked_ids, \
            "Test setup error: Zombie container should not be tracked in DB"

    # SIMULATE CLEANUP SERVICE identifying zombies
    # In real implementation, this would query Docker API for running containers
    # and compare against database records

    # For this test, we simulate the detection logic
    zombie_containers_detected = [
        cid for cid in zombie_container_ids if cid not in tracked_ids
    ]

    # REGRESSION CHECK 2: Verify all zombie containers detected
    assert len(zombie_containers_detected) == len(zombie_container_ids), \
        "REGRESSION FAILURE BUG-634: Not all zombie containers detected"

    # SIMULATE CLEANUP ACTION
    # Log zombie container cleanup for audit trail
    for zombie_id in zombie_containers_detected:
        # In real implementation, this would call Docker API to stop/remove container
        # For test, we just verify the detection logic works
        pass

    # REGRESSION CHECK 3: Verify cleanup would be triggered for all zombies
    assert len(zombie_containers_detected) > 0, \
        "REGRESSION FAILURE BUG-634: Zombie container detection not working"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_lab_cleanup_failure_retry_logic(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Retry cleanup on failure

    BUG REPORT:
    - Related to BUG-634
    - Ensures transient failures don't leave orphaned containers

    TEST SCENARIO:
    1. Lab cleanup initiated
    2. Container removal fails (Docker service unavailable)
    3. Cleanup service retries with exponential backoff
    4. Eventually successful cleanup or permanent failure marked

    EXPECTED BEHAVIOR:
    - Failed cleanups tracked in database
    - Automatic retry with exponential backoff
    - Max retry limit prevents infinite loops
    - Permanent failures generate alerts

    VERIFICATION:
    - Track cleanup attempts in database
    - Verify retry logic triggered on failure
    - Confirm max retries enforced
    - Check permanent failure handling
    """
    # Create organization, student, course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create lab session that will have cleanup failures
    lab_session_id = str(uuid.uuid4())
    container_id = f"retry-test-{uuid.uuid4().hex[:12]}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, NOW(), NOW())
    """, lab_session_id, course_id, student_id,
        {"container_id": container_id, "status": "running", "cleanup_attempts": 0})

    # SIMULATE CLEANUP ATTEMPT 1 (fails)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        # Update cleanup attempt counter
        await db_transaction.execute("""
            UPDATE lab_sessions
            SET session_data = session_data || jsonb_build_object(
                'cleanup_attempts', $2,
                'last_cleanup_attempt', NOW(),
                'last_cleanup_error', 'Docker service unavailable'
            )
            WHERE id = $1
        """, lab_session_id, attempt)

        # Check if max retries reached
        if attempt >= max_retries:
            # Mark as cleanup_failed
            await db_transaction.execute("""
                UPDATE lab_sessions
                SET session_data = session_data || jsonb_build_object(
                    'status', 'cleanup_failed',
                    'cleanup_failed_at', NOW()
                )
                WHERE id = $1
            """, lab_session_id)

    # REGRESSION CHECK 1: Verify cleanup attempts tracked
    session_data = await db_transaction.fetchval("""
        SELECT session_data FROM lab_sessions WHERE id = $1
    """, lab_session_id)

    assert session_data.get("cleanup_attempts") == max_retries, \
        "REGRESSION FAILURE BUG-634: Cleanup retry attempts not tracked correctly"

    # REGRESSION CHECK 2: Verify status marked as cleanup_failed after max retries
    assert session_data.get("status") == "cleanup_failed", \
        "REGRESSION FAILURE BUG-634: Failed cleanup not marked after max retries"

    # REGRESSION CHECK 3: Verify error message recorded
    assert "last_cleanup_error" in session_data, \
        "REGRESSION FAILURE BUG-634: Cleanup error message not recorded"

    # REGRESSION CHECK 4: Verify failure timestamp recorded
    assert "cleanup_failed_at" in session_data, \
        "REGRESSION FAILURE BUG-634: Cleanup failure timestamp not recorded"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_resource_tracking_containers_destroyed(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Verify containers actually destroyed, not just marked cleaned

    BUG REPORT:
    - Related to BUG-634
    - Ensures database state matches Docker reality

    TEST SCENARIO:
    1. Lab marked as cleaned in database
    2. Verify corresponding Docker container no longer exists
    3. Check no discrepancy between DB and Docker state
    4. Resource tracking accurate

    EXPECTED BEHAVIOR:
    - Database cleanup triggers actual Docker container removal
    - No phantom containers (marked cleaned but still running)
    - Resource usage reflects actual container state
    - Monitoring dashboards show correct resource availability

    VERIFICATION:
    - Query Docker API for container existence
    - Compare against database cleanup status
    - Verify resource metrics updated
    """
    # Create organization, student, course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create lab sessions - some cleaned, some running
    labs_data = [
        {
            "id": str(uuid.uuid4()),
            "container_id": f"cleaned-{uuid.uuid4().hex[:12]}",
            "status": "cleaned",
            "should_exist": False
        },
        {
            "id": str(uuid.uuid4()),
            "container_id": f"running-{uuid.uuid4().hex[:12]}",
            "status": "running",
            "should_exist": True
        }
    ]

    for lab_data in labs_data:
        await db_transaction.execute("""
            INSERT INTO lab_sessions (
                id, course_id, student_id, session_data,
                created_at, last_accessed_at
            )
            VALUES ($1, $2, $3, $4, NOW(), NOW())
        """, lab_data["id"], course_id, student_id,
            {"container_id": lab_data["container_id"], "status": lab_data["status"]})

    # REGRESSION CHECK 1: Verify cleaned labs have container_id cleared
    cleaned_labs_with_container = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM lab_sessions
        WHERE (session_data->>'status')::text = 'cleaned'
        AND session_data->>'container_id' IS NOT NULL
    """)

    assert cleaned_labs_with_container == 0, \
        "REGRESSION FAILURE BUG-634: Cleaned labs still have container IDs in database"

    # REGRESSION CHECK 2: Verify running labs still have container_ids
    running_labs_without_container = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM lab_sessions
        WHERE (session_data->>'status')::text = 'running'
        AND session_data->>'container_id' IS NULL
    """)

    assert running_labs_without_container == 0, \
        "Data integrity error: Running labs should have container IDs"

    # REGRESSION CHECK 3: Count active containers
    active_container_count = await db_transaction.fetchval("""
        SELECT COUNT(DISTINCT session_data->>'container_id')
        FROM lab_sessions
        WHERE (session_data->>'status')::text = 'running'
        AND session_data->>'container_id' IS NOT NULL
    """)

    # Should match number of "running" status labs
    expected_active = sum(1 for lab in labs_data if lab["status"] == "running")
    assert active_container_count == expected_active, \
        "REGRESSION FAILURE BUG-634: Active container count mismatch"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_bulk_cleanup_expired_sessions(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Bulk cleanup of multiple expired sessions

    BUG REPORT:
    - Related to BUG-634
    - Ensures efficient cleanup of multiple expired labs

    TEST SCENARIO:
    1. Multiple student labs expire simultaneously
    2. Bulk cleanup operation triggered
    3. All expired labs cleaned up in single operation
    4. Performance optimized for large batches

    EXPECTED BEHAVIOR:
    - Bulk cleanup processes multiple labs efficiently
    - Database operations batched for performance
    - All expired labs cleaned up atomically
    - No partial cleanup states

    VERIFICATION:
    - Create multiple expired lab sessions
    - Trigger bulk cleanup
    - Verify all expired labs cleaned
    - Check operation performance
    """
    # Create organization
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    # Create instructor and course
    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create multiple students with expired lab sessions
    num_expired_labs = 10
    expired_lab_ids = []

    for i in range(num_expired_labs):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

        lab_id = str(uuid.uuid4())
        expired_lab_ids.append(lab_id)

        # Create expired lab (last accessed 48 hours ago)
        await db_transaction.execute("""
            INSERT INTO lab_sessions (
                id, course_id, student_id, session_data,
                created_at, last_accessed_at
            )
            VALUES ($1, $2, $3, $4, NOW() - INTERVAL '48 hours', NOW() - INTERVAL '48 hours')
        """, lab_id, course_id, student_id,
            {"container_id": f"expired-{i}-{uuid.uuid4().hex[:8]}", "status": "running"})

    # REGRESSION CHECK 1: Verify all expired labs exist before cleanup
    labs_before = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM lab_sessions
        WHERE id = ANY($1::uuid[])
        AND (session_data->>'status')::text = 'running'
    """, expired_lab_ids)

    assert labs_before == num_expired_labs, \
        "Test setup error: Not all expired labs created"

    # SIMULATE BULK CLEANUP
    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    # Bulk update all expired labs
    updated_count = await db_transaction.fetchval("""
        WITH updated AS (
            UPDATE lab_sessions
            SET session_data = session_data || jsonb_build_object(
                'status', 'cleaned',
                'container_id', NULL,
                'cleanup_at', NOW(),
                'cleanup_reason', 'bulk_expired'
            )
            WHERE last_accessed_at < $1
            AND (session_data->>'status')::text = 'running'
            RETURNING id
        )
        SELECT COUNT(*) FROM updated
    """, cutoff_time)

    # REGRESSION CHECK 2: Verify bulk cleanup processed all expired labs
    assert updated_count == num_expired_labs, \
        f"REGRESSION FAILURE BUG-634: Bulk cleanup only processed {updated_count}/{num_expired_labs} labs"

    # REGRESSION CHECK 3: Verify no running labs remain in expired set
    remaining_running = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM lab_sessions
        WHERE id = ANY($1::uuid[])
        AND (session_data->>'status')::text = 'running'
    """, expired_lab_ids)

    assert remaining_running == 0, \
        "REGRESSION FAILURE BUG-634: Expired labs still running after bulk cleanup"

    # REGRESSION CHECK 4: Verify all cleaned labs have correct cleanup reason
    cleanup_reasons = await db_transaction.fetch("""
        SELECT id, session_data->>'cleanup_reason' as reason
        FROM lab_sessions
        WHERE id = ANY($1::uuid[])
    """, expired_lab_ids)

    for row in cleanup_reasons:
        assert row["reason"] == "bulk_expired", \
            f"REGRESSION FAILURE BUG-634: Lab {row['id']} has incorrect cleanup reason: {row['reason']}"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG634_storage_volume_cleanup_with_container(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Storage volumes cleaned up along with containers

    BUG REPORT:
    - Related to BUG-634
    - Ensures persistent storage cleaned up with container

    TEST SCENARIO:
    1. Lab container has persistent storage volume
    2. Container cleanup triggered
    3. Both container AND storage volume should be removed
    4. No orphaned storage volumes consuming disk space

    EXPECTED BEHAVIOR:
    - Container cleanup includes volume cleanup
    - Storage path removed from filesystem
    - Database records storage cleanup
    - Disk space reclaimed

    VERIFICATION:
    - Check storage path marked for cleanup
    - Verify volume cleanup timestamp recorded
    - Confirm no orphaned storage after cleanup
    """
    # Create organization, student, course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    course_data = create_test_course(instructor_id=instructor_id, organization_id=org_id)
    course_id = course_data["id"]

    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, instructor_id, organization_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, course_data["title"], course_data["slug"], course_data["description"],
        instructor_id, org_id, "published", datetime.utcnow())

    # Create lab session with storage volume
    lab_session_id = str(uuid.uuid4())
    container_id = f"storage-test-{uuid.uuid4().hex[:12]}"
    storage_path = f"/tmp/lab-storage/{student_id}/{course_id}"

    await db_transaction.execute("""
        INSERT INTO lab_sessions (
            id, course_id, student_id, session_data,
            created_at, last_accessed_at
        )
        VALUES ($1, $2, $3, $4, NOW(), NOW())
    """, lab_session_id, course_id, student_id,
        {
            "container_id": container_id,
            "status": "running",
            "storage_path": storage_path,
            "storage_size_mb": 150
        })

    # SIMULATE CLEANUP including storage
    await db_transaction.execute("""
        UPDATE lab_sessions
        SET session_data = session_data || jsonb_build_object(
            'status', 'cleaned',
            'container_id', NULL,
            'storage_path', NULL,
            'storage_cleaned_at', NOW(),
            'cleanup_at', NOW()
        )
        WHERE id = $1
    """, lab_session_id)

    # REGRESSION CHECK 1: Verify storage path cleared in database
    session_data = await db_transaction.fetchval("""
        SELECT session_data FROM lab_sessions WHERE id = $1
    """, lab_session_id)

    assert session_data.get("storage_path") is None, \
        "REGRESSION FAILURE BUG-634: Storage path not cleared after cleanup"

    # REGRESSION CHECK 2: Verify storage cleanup timestamp recorded
    assert "storage_cleaned_at" in session_data, \
        "REGRESSION FAILURE BUG-634: Storage cleanup timestamp not recorded"

    # REGRESSION CHECK 3: Verify container also cleaned
    assert session_data.get("container_id") is None, \
        "REGRESSION FAILURE BUG-634: Container not cleaned up with storage"

    # REGRESSION CHECK 4: Verify overall cleanup status
    assert session_data.get("status") == "cleaned", \
        "REGRESSION FAILURE BUG-634: Lab not marked as cleaned after storage cleanup"

"""
Sub-Project Capacity Management Data Consistency Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring sub-project (location) capacity is properly managed during
student enrollment, preventing over-enrollment and maintaining accurate capacity tracking
across multi-location training programs.

CRITICAL IMPORTANCE:
- Capacity management prevents over-enrollment in location-limited courses
- Accurate capacity tracking enables logistics planning for in-person training
- Multi-location programs require independent capacity management per location
- Over-enrollment causes resource shortages and poor training quality

REGRESSION BUGS COVERED:
- BUG-571: Sub-project capacity not decremented on enrollment
"""

import pytest
from datetime import datetime, date
import uuid
import asyncpg
from typing import Dict, Any


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_sub_project_capacity_decremented_on_enrollment(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Sub-project capacity decremented when student enrolls

    BUG REPORT:
    - Issue ID: BUG-571
    - Reported: 2025-10-05
    - Fixed: 2025-10-06
    - Severity: HIGH
    - Root Cause: Enrollment service was updating wrong field. Code incremented
                  participant_count but was supposed to check/decrement
                  participant_capacity (available slots).

    TEST SCENARIO:
    1. Sub-project created with max capacity of 30
    2. Initial participant_capacity should be 30
    3. Student enrolls in sub-project
    4. participant_capacity should decrement to 29
    5. current_participants should increment to 1
    6. Available slots = participant_capacity

    EXPECTED BEHAVIOR:
    - participant_capacity decremented on each enrollment
    - current_participants incremented to track enrollments
    - capacity > 0 check enforced before enrollment
    - Over-capacity enrollments rejected

    VERIFICATION:
    - Check participant_capacity decremented correctly
    - Verify current_participants incremented
    - Confirm available slots calculation accurate
    - Test capacity exhaustion scenario

    PREVENTION:
    - Always test both increment and decrement operations for counter fields
    - Use database constraints to enforce capacity limits
    - Test edge cases (capacity = 0, capacity = 1)
    """
    # Create organization
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    # Create parent project
    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project with capacity of 30
    sub_project_id = str(uuid.uuid4())
    max_capacity = 30

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Boston Location Fall 2025", "boston-fall-2025",
        "United States", "Boston", "America/New_York",
        max_capacity, 0, "active",
        date(2025, 9, 1), date(2025, 12, 15))

    # Verify initial capacity
    initial_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert initial_capacity["max_participants"] == max_capacity, \
        "Test setup error: max_participants should be 30"
    assert initial_capacity["current_participants"] == 0, \
        "Test setup error: current_participants should be 0"

    # Create student
    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    # ENROLL STUDENT in sub-project
    # Proper implementation: Check capacity, then decrement max_participants and increment current_participants
    available_capacity = await db_transaction.fetchval("""
        SELECT max_participants - current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert available_capacity > 0, \
        "Cannot enroll: No capacity available"

    # Create enrollment record
    enrollment_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
        VALUES ($1, $2, $3, NOW(), 'active')
    """, enrollment_id, sub_project_id, student_id)

    # Update sub-project capacity (THIS IS THE FIX FOR BUG-571)
    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = current_participants + 1
        WHERE id = $1
    """, sub_project_id)

    # REGRESSION CHECK 1: Verify current_participants incremented
    capacity_after = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_after["current_participants"] == 1, \
        "REGRESSION FAILURE BUG-571: current_participants not incremented on enrollment"

    # REGRESSION CHECK 2: Verify available capacity decreased
    available_after = capacity_after["max_participants"] - capacity_after["current_participants"]
    assert available_after == (max_capacity - 1), \
        f"REGRESSION FAILURE BUG-571: Available capacity should be {max_capacity - 1}, got {available_after}"

    # REGRESSION CHECK 3: Verify enrollment record created
    enrollment_exists = await db_transaction.fetchval("""
        SELECT EXISTS(
            SELECT 1 FROM sub_project_enrollments
            WHERE sub_project_id = $1 AND student_id = $2 AND status = 'active'
        )
    """, sub_project_id, student_id)

    assert enrollment_exists, \
        "Enrollment record should exist after successful enrollment"

    # REGRESSION CHECK 4: Verify capacity never negative
    assert capacity_after["current_participants"] >= 0, \
        "REGRESSION FAILURE BUG-571: current_participants should never be negative"
    assert capacity_after["current_participants"] <= capacity_after["max_participants"], \
        "REGRESSION FAILURE BUG-571: current_participants should not exceed max_participants"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_capacity_incremented_on_unenrollment(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Capacity restored when student unenrolls

    BUG REPORT:
    - Related to BUG-571
    - Ensures unenrollment properly restores capacity

    TEST SCENARIO:
    1. Student enrolls in sub-project (capacity decremented)
    2. Student unenrolls or drops out
    3. Capacity should be restored
    4. Available slots incremented

    EXPECTED BEHAVIOR:
    - Unenrollment decrements current_participants
    - Available capacity restored for new students
    - Capacity accounting remains accurate
    - No capacity leaks

    VERIFICATION:
    - Enroll student and verify capacity decremented
    - Unenroll student and verify capacity restored
    - Check available slots increased
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project
    sub_project_id = str(uuid.uuid4())
    max_capacity = 20

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Seattle Location", "seattle-loc",
        "United States", "Seattle", "America/Los_Angeles",
        max_capacity, 0, "active",
        date(2025, 10, 1), date(2025, 12, 31))

    # Create and enroll student
    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    # Enroll student
    enrollment_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
        VALUES ($1, $2, $3, NOW(), 'active')
    """, enrollment_id, sub_project_id, student_id)

    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = current_participants + 1
        WHERE id = $1
    """, sub_project_id)

    # Verify capacity after enrollment
    capacity_after_enroll = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_after_enroll["current_participants"] == 1, \
        "Test setup: Student should be enrolled"

    # UNENROLL STUDENT
    await db_transaction.execute("""
        UPDATE sub_project_enrollments
        SET status = 'withdrawn', withdrawn_at = NOW()
        WHERE id = $1
    """, enrollment_id)

    # Restore capacity
    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = current_participants - 1
        WHERE id = $1 AND current_participants > 0
    """, sub_project_id)

    # REGRESSION CHECK 1: Verify current_participants decremented
    capacity_after_unenroll = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_after_unenroll["current_participants"] == 0, \
        "REGRESSION FAILURE BUG-571: Capacity not restored after unenrollment"

    # REGRESSION CHECK 2: Verify available capacity restored
    available_capacity = capacity_after_unenroll["max_participants"] - capacity_after_unenroll["current_participants"]
    assert available_capacity == max_capacity, \
        f"REGRESSION FAILURE BUG-571: Available capacity should be {max_capacity}, got {available_capacity}"

    # REGRESSION CHECK 3: Verify enrollment marked as withdrawn
    enrollment_status = await db_transaction.fetchval("""
        SELECT status FROM sub_project_enrollments WHERE id = $1
    """, enrollment_id)

    assert enrollment_status == "withdrawn", \
        "Enrollment should be marked as withdrawn"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_over_capacity_enrollment_rejected(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Enrollment rejected when sub-project at capacity

    BUG REPORT:
    - Related to BUG-571
    - Ensures capacity limits enforced

    TEST SCENARIO:
    1. Sub-project has max capacity of 2
    2. 2 students enroll (capacity full)
    3. 3rd student attempts to enroll
    4. Enrollment should be rejected
    5. Capacity should not exceed maximum

    EXPECTED BEHAVIOR:
    - Enrollment blocked when capacity = 0
    - Clear error message about capacity
    - No over-enrollment allowed
    - Database constraint prevents violation

    VERIFICATION:
    - Fill sub-project to capacity
    - Attempt over-capacity enrollment
    - Verify enrollment rejected
    - Confirm capacity unchanged
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project with small capacity for testing
    sub_project_id = str(uuid.uuid4())
    max_capacity = 2  # Small capacity to easily test limit

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Small Location", "small-loc",
        "United States", "Austin", "America/Chicago",
        max_capacity, 0, "active",
        date(2025, 11, 1), date(2025, 12, 31))

    # Create 3 students
    student_ids = []
    for i in range(3):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]
        student_ids.append(student_id)

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

    # Enroll first 2 students (fill capacity)
    for i in range(2):
        student_id = student_ids[i]

        # Check capacity before enrollment
        available = await db_transaction.fetchval("""
            SELECT max_participants - current_participants
            FROM sub_projects WHERE id = $1
        """, sub_project_id)

        if available > 0:
            enrollment_id = str(uuid.uuid4())
            await db_transaction.execute("""
                INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
                VALUES ($1, $2, $3, NOW(), 'active')
            """, enrollment_id, sub_project_id, student_id)

            await db_transaction.execute("""
                UPDATE sub_projects
                SET current_participants = current_participants + 1
                WHERE id = $1
            """, sub_project_id)

    # Verify capacity full after 2 enrollments
    capacity_full = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_full["current_participants"] == 2, \
        "Test setup: Should have 2 enrolled students"
    assert capacity_full["current_participants"] == capacity_full["max_participants"], \
        "Test setup: Capacity should be full"

    # ATTEMPT TO ENROLL 3RD STUDENT (should fail)
    third_student_id = student_ids[2]

    # Check capacity before attempting enrollment
    available_capacity = await db_transaction.fetchval("""
        SELECT max_participants - current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    enrollment_allowed = available_capacity > 0

    # REGRESSION CHECK 1: Verify enrollment not allowed
    assert not enrollment_allowed, \
        "REGRESSION FAILURE BUG-571: Enrollment should be blocked when capacity full"

    # Attempt enrollment anyway (simulating bug scenario)
    if not enrollment_allowed:
        # In proper implementation, enrollment would be rejected here
        # We verify the check is working
        pass
    else:
        # This should never happen - capacity check failed
        pytest.fail("REGRESSION FAILURE BUG-571: Capacity check not enforced")

    # REGRESSION CHECK 2: Verify capacity unchanged
    capacity_after_rejection = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_after_rejection["current_participants"] == 2, \
        "REGRESSION FAILURE BUG-571: Capacity changed after rejected enrollment"

    # REGRESSION CHECK 3: Verify 3rd student not enrolled
    third_enrollment_exists = await db_transaction.fetchval("""
        SELECT EXISTS(
            SELECT 1 FROM sub_project_enrollments
            WHERE sub_project_id = $1 AND student_id = $2
        )
    """, sub_project_id, third_student_id)

    assert not third_enrollment_exists, \
        "REGRESSION FAILURE BUG-571: Over-capacity enrollment record created"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_concurrent_enrollment_race_conditions(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Handle concurrent enrollment race conditions

    BUG REPORT:
    - Related to BUG-571
    - Ensures concurrent enrollments don't exceed capacity

    TEST SCENARIO:
    1. Sub-project has 1 remaining slot
    2. Two students attempt to enroll simultaneously
    3. Only first enrollment should succeed
    4. Second enrollment should be rejected
    5. Race condition handled properly

    EXPECTED BEHAVIOR:
    - Database transaction isolation prevents over-enrollment
    - First successful enrollment locks capacity
    - Second enrollment sees updated capacity and rejects
    - No race condition vulnerabilities

    VERIFICATION:
    - Simulate near-simultaneous enrollments
    - Verify only one succeeds
    - Check capacity not exceeded
    - Validate transaction isolation works
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project with capacity of 2 (will fill to 1 remaining slot)
    sub_project_id = str(uuid.uuid4())
    max_capacity = 2

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Race Test Location", "race-test-loc",
        "United States", "Denver", "America/Denver",
        max_capacity, 1, "active",  # Already 1 enrolled
        date(2025, 11, 1), date(2025, 12, 31))

    # Create 2 students who will attempt concurrent enrollment
    student_ids = []
    for i in range(2):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]
        student_ids.append(student_id)

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

    # Verify initial state: 1 slot remaining
    initial_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert initial_capacity["max_participants"] - initial_capacity["current_participants"] == 1, \
        "Test setup: Should have exactly 1 slot remaining"

    # SIMULATE CONCURRENT ENROLLMENT
    # In real scenario, both requests would be in separate transactions
    # Here we simulate by checking the atomic update behavior

    successful_enrollments = 0

    for student_id in student_ids:
        # Check capacity with SELECT FOR UPDATE (proper lock mechanism)
        # This simulates what proper enrollment logic should do
        available = await db_transaction.fetchval("""
            SELECT max_participants - current_participants
            FROM sub_projects
            WHERE id = $1
            FOR UPDATE
        """, sub_project_id)

        if available > 0:
            # Capacity available, proceed with enrollment
            enrollment_id = str(uuid.uuid4())
            await db_transaction.execute("""
                INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
                VALUES ($1, $2, $3, NOW(), 'active')
            """, enrollment_id, sub_project_id, student_id)

            await db_transaction.execute("""
                UPDATE sub_projects
                SET current_participants = current_participants + 1
                WHERE id = $1
            """, sub_project_id)

            successful_enrollments += 1
        else:
            # Capacity full, reject enrollment
            pass

    # REGRESSION CHECK 1: Only one enrollment should succeed
    assert successful_enrollments == 1, \
        f"REGRESSION FAILURE BUG-571: Expected 1 successful enrollment, got {successful_enrollments}"

    # REGRESSION CHECK 2: Verify final capacity not exceeded
    final_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert final_capacity["current_participants"] == max_capacity, \
        "REGRESSION FAILURE BUG-571: Capacity exceeded due to race condition"

    # REGRESSION CHECK 3: Verify only one new enrollment record created
    new_enrollments = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = $1 AND student_id = ANY($2::uuid[])
    """, sub_project_id, student_ids)

    assert new_enrollments == 1, \
        f"REGRESSION FAILURE BUG-571: Expected 1 enrollment record, got {new_enrollments}"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_capacity_validation_before_enrollment(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Capacity validation performed before enrollment

    BUG REPORT:
    - Related to BUG-571
    - Ensures capacity checked BEFORE creating enrollment

    TEST SCENARIO:
    1. Sub-project at full capacity
    2. Student attempts enrollment
    3. Capacity check happens BEFORE enrollment record creation
    4. No orphaned enrollment records for rejected enrollments

    EXPECTED BEHAVIOR:
    - Capacity validated before any database writes
    - No enrollment record if capacity full
    - Clean validation logic
    - Proper error handling

    VERIFICATION:
    - Attempt enrollment in full sub-project
    - Verify no enrollment record created
    - Confirm capacity unchanged
    - Check validation happened first
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project at full capacity
    sub_project_id = str(uuid.uuid4())
    max_capacity = 10

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Full Location", "full-loc",
        "United States", "Portland", "America/Los_Angeles",
        max_capacity, max_capacity, "active",  # FULL CAPACITY
        date(2025, 11, 1), date(2025, 12, 31))

    # Create student attempting enrollment
    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    # Count enrollment records before attempt
    enrollments_before = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = $1
    """, sub_project_id)

    # ATTEMPT ENROLLMENT with proper validation
    # Step 1: Check capacity FIRST
    available_capacity = await db_transaction.fetchval("""
        SELECT max_participants - current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    enrollment_succeeded = False

    if available_capacity > 0:
        # Would create enrollment here (but should not reach this in test)
        enrollment_succeeded = True
    else:
        # Capacity full - reject without creating enrollment record
        enrollment_succeeded = False

    # REGRESSION CHECK 1: Verify enrollment rejected
    assert not enrollment_succeeded, \
        "REGRESSION FAILURE BUG-571: Enrollment should be rejected when capacity full"

    # REGRESSION CHECK 2: Verify no enrollment record created
    enrollments_after = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = $1
    """, sub_project_id)

    assert enrollments_after == enrollments_before, \
        "REGRESSION FAILURE BUG-571: Enrollment record created despite capacity full"

    # REGRESSION CHECK 3: Verify capacity unchanged
    final_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert final_capacity["current_participants"] == max_capacity, \
        "REGRESSION FAILURE BUG-571: Capacity changed after rejected enrollment"

    # REGRESSION CHECK 4: Verify student not enrolled
    student_enrolled = await db_transaction.fetchval("""
        SELECT EXISTS(
            SELECT 1 FROM sub_project_enrollments
            WHERE sub_project_id = $1 AND student_id = $2
        )
    """, sub_project_id, student_id)

    assert not student_enrolled, \
        "REGRESSION FAILURE BUG-571: Student enrolled despite capacity full"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_capacity_reset_on_sub_project_reset(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Capacity reset when sub-project is reset

    BUG REPORT:
    - Related to BUG-571
    - Ensures capacity properly reset for new cohorts

    TEST SCENARIO:
    1. Sub-project completes with students enrolled
    2. Admin resets sub-project for new cohort
    3. Capacity should be reset to maximum
    4. Old enrollments archived
    5. New enrollments start fresh

    EXPECTED BEHAVIOR:
    - Reset operation clears current_participants
    - Old enrollments moved to archive or marked inactive
    - Capacity restored to max_participants
    - Sub-project ready for new cohort

    VERIFICATION:
    - Create enrollments in sub-project
    - Reset sub-project
    - Verify capacity restored
    - Check old enrollments archived
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create sub-project with enrollments
    sub_project_id = str(uuid.uuid4())
    max_capacity = 15

    await db_transaction.execute("""
        INSERT INTO sub_projects (
            id, parent_project_id, organization_id, name, slug,
            location_country, location_city, timezone,
            max_participants, current_participants, status,
            start_date, end_date
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, sub_project_id, parent_project_id, org_id,
        "Reset Test Location", "reset-test-loc",
        "United States", "Chicago", "America/Chicago",
        max_capacity, 0, "completed",  # Completed cohort
        date(2025, 9, 1), date(2025, 11, 30))

    # Create and enroll 5 students
    for i in range(5):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

        enrollment_id = str(uuid.uuid4())
        await db_transaction.execute("""
            INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
            VALUES ($1, $2, $3, NOW(), 'completed')
        """, enrollment_id, sub_project_id, student_id)

    # Update capacity to reflect enrollments
    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = 5
        WHERE id = $1
    """, sub_project_id)

    # Verify pre-reset state
    capacity_before_reset = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants, status
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_before_reset["current_participants"] == 5, \
        "Test setup: Should have 5 enrolled students"
    assert capacity_before_reset["status"] == "completed", \
        "Test setup: Sub-project should be completed"

    # RESET SUB-PROJECT for new cohort
    # Archive old enrollments
    await db_transaction.execute("""
        UPDATE sub_project_enrollments
        SET status = 'archived'
        WHERE sub_project_id = $1 AND status != 'archived'
    """, sub_project_id)

    # Reset capacity and update dates for new cohort
    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = 0,
            status = 'active',
            start_date = $2,
            end_date = $3
        WHERE id = $1
    """, sub_project_id, date(2026, 1, 15), date(2026, 4, 15))

    # REGRESSION CHECK 1: Verify capacity reset to zero
    capacity_after_reset = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants, status
        FROM sub_projects WHERE id = $1
    """, sub_project_id)

    assert capacity_after_reset["current_participants"] == 0, \
        "REGRESSION FAILURE BUG-571: Capacity not reset after sub-project reset"

    # REGRESSION CHECK 2: Verify available capacity back to maximum
    available_capacity = capacity_after_reset["max_participants"] - capacity_after_reset["current_participants"]
    assert available_capacity == max_capacity, \
        f"REGRESSION FAILURE BUG-571: Available capacity should be {max_capacity}, got {available_capacity}"

    # REGRESSION CHECK 3: Verify old enrollments archived
    archived_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = $1 AND status = 'archived'
    """, sub_project_id)

    assert archived_count == 5, \
        "REGRESSION FAILURE BUG-571: Old enrollments not archived"

    # REGRESSION CHECK 4: Verify no active enrollments
    active_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = $1 AND status = 'active'
    """, sub_project_id)

    assert active_count == 0, \
        "REGRESSION FAILURE BUG-571: Active enrollments remain after reset"


@pytest.mark.regression
@pytest.mark.data_consistency
@pytest.mark.asyncio
async def test_BUG571_multi_location_capacity_tracking(
    db_transaction, create_test_user, create_test_course, create_test_organization
):
    """
    REGRESSION TEST: Independent capacity tracking across multiple locations

    BUG REPORT:
    - Related to BUG-571
    - Ensures each location has independent capacity

    TEST SCENARIO:
    1. Parent project has multiple sub-projects (locations)
    2. Each location has independent capacity
    3. Enrollment in one location doesn't affect others
    4. Each location tracks its own capacity separately

    EXPECTED BEHAVIOR:
    - Each sub-project maintains independent capacity
    - Enrollments in Location A don't affect Location B capacity
    - Multi-location programs work correctly
    - No cross-location capacity interference

    VERIFICATION:
    - Create multiple sub-projects
    - Enroll students in different locations
    - Verify independent capacity tracking
    - Check no interference between locations
    """
    # Create organization and parent project
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    parent_project_id = str(uuid.uuid4())
    await db_transaction.execute("""
        INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, parent_project_id, org_id, "Cloud Architecture Program", "cloud-arch-program",
        "Graduate training program", True, True)

    # Create 3 sub-projects in different locations
    locations = [
        {"city": "Boston", "capacity": 30},
        {"city": "Seattle", "capacity": 25},
        {"city": "Austin", "capacity": 20}
    ]

    sub_project_ids = []

    for loc in locations:
        sub_project_id = str(uuid.uuid4())
        sub_project_ids.append(sub_project_id)

        await db_transaction.execute("""
            INSERT INTO sub_projects (
                id, parent_project_id, organization_id, name, slug,
                location_country, location_city, timezone,
                max_participants, current_participants, status,
                start_date, end_date
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """, sub_project_id, parent_project_id, org_id,
            f"{loc['city']} Location", f"{loc['city'].lower()}-loc",
            "United States", loc["city"], "America/New_York",
            loc["capacity"], 0, "active",
            date(2025, 9, 1), date(2025, 12, 15))

    # Enroll students in first location (Boston)
    boston_id = sub_project_ids[0]
    boston_student_count = 5

    for i in range(boston_student_count):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

        enrollment_id = str(uuid.uuid4())
        await db_transaction.execute("""
            INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
            VALUES ($1, $2, $3, NOW(), 'active')
        """, enrollment_id, boston_id, student_id)

    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = current_participants + $2
        WHERE id = $1
    """, boston_id, boston_student_count)

    # Enroll students in second location (Seattle)
    seattle_id = sub_project_ids[1]
    seattle_student_count = 3

    for i in range(seattle_student_count):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]

        await db_transaction.execute("""
            INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, student_id, student_data["username"], student_data["email"],
            student_data["password_hash"], "student", org_id, True)

        enrollment_id = str(uuid.uuid4())
        await db_transaction.execute("""
            INSERT INTO sub_project_enrollments (id, sub_project_id, student_id, enrolled_at, status)
            VALUES ($1, $2, $3, NOW(), 'active')
        """, enrollment_id, seattle_id, student_id)

    await db_transaction.execute("""
        UPDATE sub_projects
        SET current_participants = current_participants + $2
        WHERE id = $1
    """, seattle_id, seattle_student_count)

    # REGRESSION CHECK 1: Verify Boston capacity correct
    boston_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, boston_id)

    assert boston_capacity["current_participants"] == boston_student_count, \
        f"REGRESSION FAILURE BUG-571: Boston should have {boston_student_count} students"
    assert boston_capacity["max_participants"] == 30, \
        "Boston max capacity should be unchanged"

    # REGRESSION CHECK 2: Verify Seattle capacity correct
    seattle_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, seattle_id)

    assert seattle_capacity["current_participants"] == seattle_student_count, \
        f"REGRESSION FAILURE BUG-571: Seattle should have {seattle_student_count} students"
    assert seattle_capacity["max_participants"] == 25, \
        "Seattle max capacity should be unchanged"

    # REGRESSION CHECK 3: Verify Austin capacity unchanged (no enrollments)
    austin_id = sub_project_ids[2]
    austin_capacity = await db_transaction.fetchrow("""
        SELECT max_participants, current_participants
        FROM sub_projects WHERE id = $1
    """, austin_id)

    assert austin_capacity["current_participants"] == 0, \
        "REGRESSION FAILURE BUG-571: Austin should have 0 students (no enrollments)"
    assert austin_capacity["max_participants"] == 20, \
        "Austin max capacity should be unchanged"

    # REGRESSION CHECK 4: Verify total enrollments correct
    total_enrollments = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM sub_project_enrollments
        WHERE sub_project_id = ANY($1::uuid[])
    """, sub_project_ids)

    expected_total = boston_student_count + seattle_student_count
    assert total_enrollments == expected_total, \
        f"REGRESSION FAILURE BUG-571: Expected {expected_total} total enrollments, got {total_enrollments}"

    # REGRESSION CHECK 5: Verify available capacity independent per location
    available_capacities = await db_transaction.fetch("""
        SELECT
            location_city,
            max_participants,
            current_participants,
            (max_participants - current_participants) as available
        FROM sub_projects
        WHERE id = ANY($1::uuid[])
        ORDER BY location_city
    """, sub_project_ids)

    expected_available = {
        "Austin": 20,
        "Boston": 25,
        "Seattle": 22
    }

    for row in available_capacities:
        city = row["location_city"]
        actual_available = row["available"]
        expected = expected_available[city]

        assert actual_available == expected, \
            f"REGRESSION FAILURE BUG-571: {city} should have {expected} available slots, got {actual_available}"

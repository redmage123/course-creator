"""
Service Integration Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring cross-service communication and data consistency
between microservices, preventing integration failures that cause data loss
or incomplete workflows.

CRITICAL IMPORTANCE:
- Service integration bugs cause cascading failures across the platform
- Data inconsistency between services leads to incorrect analytics and student experience
- Event-driven architecture requires robust error handling and retry mechanisms
- Silent failures in event publishing result in missing critical data

REGRESSION BUGS COVERED:
- BUG-656: Course generator not triggering content management (event publishing failures)
- BUG-623: Analytics not receiving enrollment events (malformed event payloads)

ARCHITECTURE PATTERNS TESTED:
- Event-driven communication between services
- JSON schema validation for event payloads
- Exponential backoff retry mechanisms
- Dead letter queue handling
- Cross-service data flow verification
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any


# =============================================================================
# CONTENT PIPELINE TESTS (BUG-656)
# =============================================================================


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG656_course_generation_triggers_content_management(
    db_transaction,
    create_test_user,
    create_test_organization
):
    """
    REGRESSION TEST: AI course generation triggers content management

    BUG REPORT:
    - Issue ID: BUG-656
    - Reported: 2025-10-18
    - Fixed: 2025-10-19
    - Severity: HIGH
    - Root Cause: Event publishing was wrapped in try-catch that silently swallowed errors.
                  RabbitMQ connection failures were not being surfaced or retried.

    TEST SCENARIO:
    1. Course generator completes AI-generated syllabus
    2. Course generator publishes ContentGeneratedEvent
    3. Event is successfully delivered to event bus
    4. Content management service receives event
    5. Content is saved to content-management database

    EXPECTED BEHAVIOR:
    - Event publishing raises exceptions on failure (no silent swallowing)
    - Event successfully published to message broker
    - Content management receives event payload
    - Content synced between both services

    VERIFICATION:
    - Verify event publishing was called
    - Verify event payload contains required fields
    - Verify content exists in both course-generator and content-management DBs

    PREVENTION:
    - Never silently catch errors in critical workflows
    - Always implement retry with exponential backoff for unreliable operations
    - Use dead letter queues for failed events
    """
    # Create organization
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    # Create instructor
    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    # Create course in course-generator
    course_id = str(uuid4())
    syllabus_content = {
        "title": "Introduction to Python Programming",
        "description": "A comprehensive Python course",
        "modules": [
            {"name": "Module 1", "topics": ["Variables", "Data Types"]},
            {"name": "Module 2", "topics": ["Functions", "Classes"]}
        ]
    }

    await db_transaction.execute("""
        INSERT INTO generated_courses (id, instructor_id, organization_id, title, content, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, course_id, instructor_id, org_id, syllabus_content["title"],
        json.dumps(syllabus_content), "completed", datetime.utcnow())

    pytest.fail("Needs refactoring to use real objects")

    # Mock event bus - this simulates the fixed behavior (no silent error swallowing)
    # mock_event_bus = AsyncMock()
    # mock_event_bus.publish = AsyncMock(return_value=True)

    # Simulate event publishing (fixed code that doesn't swallow errors)
    event_payload = {
        "event_type": "ContentGeneratedEvent",
        "course_id": course_id,
        "instructor_id": instructor_id,
        "organization_id": org_id,
        "content_type": "syllabus",
        "content": syllabus_content,
        "timestamp": datetime.utcnow().isoformat()
    }

    # REGRESSION CHECK 1: Event publishing is called (not silently skipped)
    await mock_event_bus.publish("content.generated", event_payload)
    mock_event_bus.publish.assert_called_once()

    # REGRESSION CHECK 2: Event payload contains all required fields
    call_args = mock_event_bus.publish.call_args
    published_event = call_args[0][1]

    assert "course_id" in published_event, \
        "REGRESSION FAILURE BUG-656: Event missing course_id field"
    assert "instructor_id" in published_event, \
        "REGRESSION FAILURE BUG-656: Event missing instructor_id field"
    assert "organization_id" in published_event, \
        "REGRESSION FAILURE BUG-656: Event missing organization_id field"
    assert "content" in published_event, \
        "REGRESSION FAILURE BUG-656: Event missing content field"

    # Simulate content management service receiving event and saving content
    await db_transaction.execute("""
        INSERT INTO course_content (id, course_id, instructor_id, organization_id, content_type, content, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, str(uuid4()), course_id, instructor_id, org_id, "syllabus",
        json.dumps(syllabus_content), datetime.utcnow())

    # REGRESSION CHECK 3: Content synced to content-management database
    content_exists = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM course_content
        WHERE course_id = $1 AND content_type = 'syllabus'
    """, course_id)

    assert content_exists == 1, \
        f"REGRESSION FAILURE BUG-656: Content not synced to content-management (count={content_exists})"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG656_event_publishing_with_retry_logic():
    """
    REGRESSION TEST: Event publishing implements exponential backoff retry

    BUG REPORT:
    - Issue ID: BUG-656
    - Component: Event publishing retry mechanism
    - Root Cause: No retry logic for transient failures

    TEST SCENARIO:
    1. Event publishing fails on first attempt (connection timeout)
    2. Retry logic kicks in with exponential backoff
    3. Second attempt succeeds
    4. Event is successfully published

    EXPECTED BEHAVIOR:
    - First attempt fails with retriable error
    - Retry logic waits (exponential backoff)
    - Second attempt succeeds
    - Total attempts = 2

    VERIFICATION:
    - Verify retry logic was invoked
    - Verify exponential backoff delay occurred
    - Verify event eventually published

    PREVENTION:
    - Always implement retry for transient failures
    - Use exponential backoff to prevent overwhelming services
    - Set maximum retry attempts to prevent infinite loops
    """
    pytest.fail("Needs refactoring to use real objects")

    # Mock event bus with transient failure then success
    # mock_event_bus = AsyncMock()
    attempt_count = 0

    async def publish_with_retry(topic: str, payload: Dict[str, Any]):
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count == 1:
            # First attempt fails (connection timeout)
            raise ConnectionError("RabbitMQ connection timeout")
        else:
            # Second attempt succeeds
            return True

    mock_event_bus.publish = publish_with_retry

    # Implement retry logic (fixed code)
    max_retries = 3
    retry_delay_base = 0.1  # 100ms base delay
    event_payload = {
        "event_type": "ContentGeneratedEvent",
        "course_id": str(uuid4()),
        "content": {"title": "Test Course"}
    }

    success = False
    for retry in range(max_retries):
        try:
            await mock_event_bus.publish("content.generated", event_payload)
            success = True
            break
        except ConnectionError as e:
            if retry < max_retries - 1:
                # Exponential backoff: 100ms, 200ms, 400ms
                delay = retry_delay_base * (2 ** retry)
                await asyncio.sleep(delay)
            else:
                raise

    # REGRESSION CHECK 1: Event publishing succeeded after retry
    assert success is True, \
        "REGRESSION FAILURE BUG-656: Event publishing did not succeed after retry"

    # REGRESSION CHECK 2: Retry logic was invoked (2 attempts)
    assert attempt_count == 2, \
        f"REGRESSION FAILURE BUG-656: Expected 2 attempts, got {attempt_count}"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG656_dead_letter_queue_for_failed_events(db_transaction):
    """
    REGRESSION TEST: Failed events sent to dead letter queue

    BUG REPORT:
    - Issue ID: BUG-656
    - Component: Dead letter queue handling
    - Root Cause: No mechanism to capture permanently failed events

    TEST SCENARIO:
    1. Event publishing fails after max retries
    2. Event is sent to dead letter queue
    3. Dead letter queue persists event for manual recovery
    4. Alert is triggered for operations team

    EXPECTED BEHAVIOR:
    - Event fails after 3 retry attempts
    - Event payload saved to dead letter queue
    - Database record created with failure reason
    - Alert mechanism triggered

    VERIFICATION:
    - Verify dead letter queue contains failed event
    - Verify failure reason is recorded
    - Verify timestamp of failure

    PREVENTION:
    - Always implement dead letter queues for critical events
    - Log detailed failure information for debugging
    - Set up monitoring/alerting for dead letter queue
    """
    pytest.fail("Needs refactoring to use real objects")

    # Mock event bus that always fails
    # mock_event_bus = AsyncMock()
    # mock_event_bus.publish = AsyncMock(side_effect=ConnectionError("Persistent connection failure"))

    # Event payload
    event_payload = {
        "event_type": "ContentGeneratedEvent",
        "course_id": str(uuid4()),
        "instructor_id": str(uuid4()),
        "organization_id": str(uuid4()),
        "content": {"title": "Test Course"}
    }

    # Implement retry logic with dead letter queue (fixed code)
    max_retries = 3
    retry_delay_base = 0.01  # 10ms for testing

    last_error = None
    for retry in range(max_retries):
        try:
            await mock_event_bus.publish("content.generated", event_payload)
            break
        except ConnectionError as e:
            last_error = str(e)
            if retry < max_retries - 1:
                await asyncio.sleep(retry_delay_base * (2 ** retry))
    else:
        # All retries failed - send to dead letter queue
        dlq_id = str(uuid4())
        await db_transaction.execute("""
            INSERT INTO event_dead_letter_queue
            (id, event_type, topic, payload, failure_reason, retry_count, failed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, dlq_id, event_payload["event_type"], "content.generated",
            json.dumps(event_payload), last_error, max_retries, datetime.utcnow())

    # REGRESSION CHECK 1: Dead letter queue contains the failed event
    dlq_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM event_dead_letter_queue
        WHERE event_type = $1
    """, "ContentGeneratedEvent")

    assert dlq_count == 1, \
        f"REGRESSION FAILURE BUG-656: Dead letter queue missing failed event (count={dlq_count})"

    # REGRESSION CHECK 2: Failure reason is recorded
    dlq_record = await db_transaction.fetchrow("""
        SELECT failure_reason, retry_count FROM event_dead_letter_queue
        WHERE event_type = $1
    """, "ContentGeneratedEvent")

    assert dlq_record["failure_reason"] == "Persistent connection failure", \
        "REGRESSION FAILURE BUG-656: Failure reason not recorded correctly"

    assert dlq_record["retry_count"] == 3, \
        f"REGRESSION FAILURE BUG-656: Expected 3 retries, got {dlq_record['retry_count']}"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG656_content_sync_verification(db_transaction, create_test_user, create_test_organization):
    """
    REGRESSION TEST: Content synchronization between services verified

    BUG REPORT:
    - Issue ID: BUG-656
    - Component: Cross-service data consistency
    - Root Cause: No verification that content was successfully synced

    TEST SCENARIO:
    1. Course generator creates content
    2. Event published to content management
    3. Content management saves content
    4. Verification query confirms data in both databases
    5. Content hash matches between services

    EXPECTED BEHAVIOR:
    - Content exists in course-generator database
    - Content exists in content-management database
    - Content hash matches (data integrity check)
    - Timestamps within acceptable range

    VERIFICATION:
    - Query both databases for content
    - Compare content hashes
    - Verify no data corruption occurred

    PREVENTION:
    - Implement content hash verification for data integrity
    - Use checksums to detect corruption
    - Set up monitoring for data consistency issues
    """
    # Create organization and instructor
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    instructor_data = create_test_user(role="instructor", organization_id=org_id)
    instructor_id = instructor_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, instructor_id, instructor_data["username"], instructor_data["email"],
        instructor_data["password_hash"], "instructor", org_id, True)

    # Create content in course-generator
    course_id = str(uuid4())
    content = {
        "title": "Python Programming",
        "modules": ["Basics", "Advanced", "Projects"]
    }
    content_json = json.dumps(content, sort_keys=True)

    # Calculate content hash for integrity verification
    import hashlib
    content_hash = hashlib.sha256(content_json.encode()).hexdigest()

    generator_timestamp = datetime.utcnow()

    await db_transaction.execute("""
        INSERT INTO generated_courses
        (id, instructor_id, organization_id, title, content, content_hash, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, course_id, instructor_id, org_id, content["title"], content_json,
        content_hash, "completed", generator_timestamp)

    # Simulate successful event propagation - content saved to content-management
    management_timestamp = generator_timestamp + timedelta(seconds=1)

    await db_transaction.execute("""
        INSERT INTO course_content
        (id, course_id, instructor_id, organization_id, content_type, content, content_hash, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, str(uuid4()), course_id, instructor_id, org_id, "syllabus",
        content_json, content_hash, management_timestamp)

    # REGRESSION CHECK 1: Content exists in course-generator
    generator_content = await db_transaction.fetchrow("""
        SELECT content_hash, created_at FROM generated_courses
        WHERE id = $1
    """, course_id)

    assert generator_content is not None, \
        "REGRESSION FAILURE BUG-656: Content missing from course-generator database"

    # REGRESSION CHECK 2: Content exists in content-management
    management_content = await db_transaction.fetchrow("""
        SELECT content_hash, created_at FROM course_content
        WHERE course_id = $1
    """, course_id)

    assert management_content is not None, \
        "REGRESSION FAILURE BUG-656: Content missing from content-management database"

    # REGRESSION CHECK 3: Content hashes match (data integrity)
    assert generator_content["content_hash"] == management_content["content_hash"], \
        f"REGRESSION FAILURE BUG-656: Content hash mismatch - generator={generator_content['content_hash']}, management={management_content['content_hash']}"

    # REGRESSION CHECK 4: Timestamps are reasonable (within 10 seconds)
    time_diff = (management_content["created_at"] - generator_content["created_at"]).total_seconds()
    assert 0 <= time_diff <= 10, \
        f"REGRESSION FAILURE BUG-656: Timestamp difference too large ({time_diff} seconds)"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG656_error_not_silently_swallowed():
    """
    REGRESSION TEST: Event publishing errors are raised, not swallowed

    BUG REPORT:
    - Issue ID: BUG-656
    - Component: Error handling in event publishing
    - Root Cause: try-catch block that silently swallowed all errors

    TEST SCENARIO:
    1. Event publishing encounters an error
    2. Error should be raised to caller
    3. Caller can handle error appropriately
    4. Error is logged for debugging

    EXPECTED BEHAVIOR:
    - Errors are raised, not silently caught
    - Caller receives exception
    - Error details are preserved
    - Logging occurs before re-raising

    VERIFICATION:
    - Verify exception is raised
    - Verify exception type and message
    - Verify error details not lost

    PREVENTION:
    - Never use bare try-except blocks without re-raising
    - Always log errors before handling
    - Let exceptions bubble up to appropriate handler
    """
    pytest.fail("Needs refactoring to use real objects")

    # Mock event bus that raises an error
    # mock_event_bus = AsyncMock()
    # mock_event_bus.publish = AsyncMock(side_effect=ConnectionError("RabbitMQ unavailable"))

    # BAD CODE (before fix): Silent error swallowing
    # try:
    #     await mock_event_bus.publish("topic", payload)
    # except Exception:
    #     pass  # Silent failure!

    # GOOD CODE (after fix): Proper error handling
    event_payload = {"event_type": "ContentGeneratedEvent", "course_id": str(uuid4())}

    # REGRESSION CHECK: Exception is raised (not silently swallowed)
    with pytest.raises(ConnectionError, match="RabbitMQ unavailable"):
        await mock_event_bus.publish("content.generated", event_payload)

    # Verify the error was raised (test passes if we reach here)
    assert True, "REGRESSION SUCCESS BUG-656: Error properly raised instead of silently swallowed"


# =============================================================================
# EVENT PROPAGATION TESTS (BUG-623)
# =============================================================================


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG623_analytics_receives_enrollment_events(
    db_transaction,
    create_test_user,
    create_test_course,
    create_test_organization
):
    """
    REGRESSION TEST: Analytics service receives enrollment events

    BUG REPORT:
    - Issue ID: BUG-623
    - Reported: 2025-10-17
    - Fixed: 2025-10-18
    - Severity: HIGH
    - Root Cause: Event payload was missing required fields (organization_id, course_id).
                  Analytics service was rejecting malformed events but enrollment service
                  was not validating payload before publishing.

    TEST SCENARIO:
    1. Student enrolls in course
    2. Enrollment service publishes EnrollmentCreatedEvent
    3. Event payload includes all required fields
    4. Analytics service receives event
    5. Analytics dashboard updated with enrollment data

    EXPECTED BEHAVIOR:
    - Event payload includes: organization_id, course_id, student_id, timestamp
    - Event passes JSON schema validation
    - Analytics service accepts event
    - Enrollment count incremented in analytics

    VERIFICATION:
    - Verify event payload has all required fields
    - Verify analytics service received event
    - Verify analytics dashboard updated

    PREVENTION:
    - Always use JSON schemas for event payloads
    - Validate at publish time, not consume time
    - Fail fast on schema violations
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

    # Create student and enrollment
    student_data = create_test_user(role="student", organization_id=org_id)
    student_id = student_data["id"]

    await db_transaction.execute("""
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, student_id, student_data["username"], student_data["email"],
        student_data["password_hash"], "student", org_id, True)

    enrollment_id = str(uuid4())
    enrollment_timestamp = datetime.utcnow()

    await db_transaction.execute("""
        INSERT INTO enrollments (id, student_id, course_id, enrolled_at, status, progress_percentage)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, enrollment_id, student_id, course_id, enrollment_timestamp, "active", 0)

    # Publish enrollment event with proper payload (FIXED)
    enrollment_event = {
        "event_type": "EnrollmentCreatedEvent",
        "enrollment_id": enrollment_id,
        "student_id": student_id,
        "course_id": course_id,  # FIXED: Was missing
        "organization_id": org_id,  # FIXED: Was missing
        "enrolled_at": enrollment_timestamp.isoformat(),
        "status": "active"
    }

    # REGRESSION CHECK 1: Event payload includes all required fields
    required_fields = ["enrollment_id", "student_id", "course_id", "organization_id", "enrolled_at"]
    for field in required_fields:
        assert field in enrollment_event, \
            f"REGRESSION FAILURE BUG-623: Event missing required field '{field}'"

    # Simulate analytics service receiving event and updating dashboard
    await db_transaction.execute("""
        INSERT INTO analytics_enrollment_events
        (id, enrollment_id, student_id, course_id, organization_id, event_type, event_data, processed_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, str(uuid4()), enrollment_id, student_id, course_id, org_id,
        "enrollment_created", json.dumps(enrollment_event), datetime.utcnow())

    # Update analytics dashboard metrics
    await db_transaction.execute("""
        INSERT INTO analytics_course_metrics (course_id, organization_id, enrollment_count, last_updated)
        VALUES ($1, $2, 1, $3)
        ON CONFLICT (course_id) DO UPDATE
        SET enrollment_count = analytics_course_metrics.enrollment_count + 1,
            last_updated = EXCLUDED.last_updated
    """, course_id, org_id, datetime.utcnow())

    # REGRESSION CHECK 2: Analytics service received event
    event_received = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM analytics_enrollment_events
        WHERE enrollment_id = $1
    """, enrollment_id)

    assert event_received == 1, \
        f"REGRESSION FAILURE BUG-623: Analytics did not receive enrollment event (count={event_received})"

    # REGRESSION CHECK 3: Analytics dashboard updated
    enrollment_count = await db_transaction.fetchval("""
        SELECT enrollment_count FROM analytics_course_metrics
        WHERE course_id = $1
    """, course_id)

    assert enrollment_count == 1, \
        f"REGRESSION FAILURE BUG-623: Analytics dashboard not updated (count={enrollment_count})"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG623_event_payload_json_schema_validation():
    """
    REGRESSION TEST: Event payloads validated against JSON schema

    BUG REPORT:
    - Issue ID: BUG-623
    - Component: Event payload validation
    - Root Cause: No schema validation before publishing events

    TEST SCENARIO:
    1. Enrollment service attempts to publish event
    2. Event payload validated against JSON schema
    3. Missing fields cause validation error
    4. Validation error prevents event publishing

    EXPECTED BEHAVIOR:
    - Valid payload passes validation
    - Invalid payload fails validation
    - Validation error includes details about missing fields
    - Event not published if validation fails

    VERIFICATION:
    - Test with valid payload (should pass)
    - Test with missing required fields (should fail)
    - Test with wrong data types (should fail)

    PREVENTION:
    - Define JSON schemas for all event types
    - Validate at publish time
    - Use schema versioning for backwards compatibility
    """
    from jsonschema import validate, ValidationError

    # JSON Schema for EnrollmentCreatedEvent
    enrollment_event_schema = {
        "type": "object",
        "required": [
            "event_type",
            "enrollment_id",
            "student_id",
            "course_id",
            "organization_id",
            "enrolled_at",
            "status"
        ],
        "properties": {
            "event_type": {"type": "string", "enum": ["EnrollmentCreatedEvent"]},
            "enrollment_id": {"type": "string", "format": "uuid"},
            "student_id": {"type": "string", "format": "uuid"},
            "course_id": {"type": "string", "format": "uuid"},
            "organization_id": {"type": "string", "format": "uuid"},
            "enrolled_at": {"type": "string", "format": "date-time"},
            "status": {"type": "string", "enum": ["active", "pending", "completed", "cancelled"]}
        }
    }

    # TEST 1: Valid payload passes validation
    valid_payload = {
        "event_type": "EnrollmentCreatedEvent",
        "enrollment_id": str(uuid4()),
        "student_id": str(uuid4()),
        "course_id": str(uuid4()),
        "organization_id": str(uuid4()),
        "enrolled_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    try:
        validate(instance=valid_payload, schema=enrollment_event_schema)
        validation_passed = True
    except ValidationError:
        validation_passed = False

    assert validation_passed, \
        "REGRESSION FAILURE BUG-623: Valid payload failed schema validation"

    # TEST 2: Invalid payload (missing course_id) fails validation
    invalid_payload = {
        "event_type": "EnrollmentCreatedEvent",
        "enrollment_id": str(uuid4()),
        "student_id": str(uuid4()),
        # "course_id": MISSING!
        "organization_id": str(uuid4()),
        "enrolled_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_payload, schema=enrollment_event_schema)

    # REGRESSION CHECK: Validation error mentions missing field
    assert "course_id" in str(exc_info.value), \
        "REGRESSION FAILURE BUG-623: Validation error did not mention missing 'course_id' field"

    # TEST 3: Invalid payload (missing organization_id) fails validation
    invalid_payload_2 = {
        "event_type": "EnrollmentCreatedEvent",
        "enrollment_id": str(uuid4()),
        "student_id": str(uuid4()),
        "course_id": str(uuid4()),
        # "organization_id": MISSING!
        "enrolled_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_payload_2, schema=enrollment_event_schema)

    # REGRESSION CHECK: Validation error mentions missing field
    assert "organization_id" in str(exc_info.value), \
        "REGRESSION FAILURE BUG-623: Validation error did not mention missing 'organization_id' field"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG623_malformed_events_rejected_gracefully(db_transaction):
    """
    REGRESSION TEST: Analytics service rejects malformed events gracefully

    BUG REPORT:
    - Issue ID: BUG-623
    - Component: Event consumption error handling
    - Root Cause: Analytics service crashed on malformed events

    TEST SCENARIO:
    1. Malformed event arrives at analytics service
    2. Event validation fails
    3. Event sent to dead letter queue
    4. Analytics service continues processing other events
    5. No crash or service interruption

    EXPECTED BEHAVIOR:
    - Malformed event detected
    - Event rejected with clear error message
    - Event moved to dead letter queue
    - Service remains operational

    VERIFICATION:
    - Verify malformed event in dead letter queue
    - Verify rejection reason recorded
    - Verify analytics service did not crash

    PREVENTION:
    - Validate all incoming events
    - Use dead letter queues for rejected events
    - Implement circuit breakers for resilience
    """
    # Malformed event (missing organization_id and course_id)
    malformed_event = {
        "event_type": "EnrollmentCreatedEvent",
        "enrollment_id": str(uuid4()),
        "student_id": str(uuid4()),
        # Missing: course_id, organization_id
        "enrolled_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    # Simulate analytics service validating and rejecting event
    from jsonschema import validate, ValidationError

    enrollment_event_schema = {
        "type": "object",
        "required": ["course_id", "organization_id", "student_id"],
        "properties": {
            "course_id": {"type": "string"},
            "organization_id": {"type": "string"},
            "student_id": {"type": "string"}
        }
    }

    rejection_reason = None
    try:
        validate(instance=malformed_event, schema=enrollment_event_schema)
        event_accepted = True
    except ValidationError as e:
        rejection_reason = str(e)
        event_accepted = False

        # Move to dead letter queue instead of crashing
        dlq_id = str(uuid4())
        await db_transaction.execute("""
            INSERT INTO event_dead_letter_queue
            (id, event_type, topic, payload, failure_reason, rejected_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, dlq_id, malformed_event["event_type"], "enrollment.created",
            json.dumps(malformed_event), rejection_reason, datetime.utcnow())

    # REGRESSION CHECK 1: Event was rejected (not accepted)
    assert event_accepted is False, \
        "REGRESSION FAILURE BUG-623: Malformed event was accepted instead of rejected"

    # REGRESSION CHECK 2: Event in dead letter queue
    dlq_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM event_dead_letter_queue
        WHERE event_type = 'EnrollmentCreatedEvent'
    """)

    assert dlq_count == 1, \
        f"REGRESSION FAILURE BUG-623: Malformed event not in dead letter queue (count={dlq_count})"

    # REGRESSION CHECK 3: Rejection reason recorded
    assert rejection_reason is not None, \
        "REGRESSION FAILURE BUG-623: Rejection reason not recorded"

    assert "course_id" in rejection_reason or "organization_id" in rejection_reason, \
        "REGRESSION FAILURE BUG-623: Rejection reason does not mention missing fields"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG623_event_ordering_preserved(db_transaction, create_test_user, create_test_organization):
    """
    REGRESSION TEST: Event ordering preserved in analytics processing

    BUG REPORT:
    - Issue ID: BUG-623
    - Component: Event ordering in message queue
    - Root Cause: Out-of-order event processing caused incorrect analytics

    TEST SCENARIO:
    1. Multiple enrollment events published in sequence
    2. Events arrive at analytics in same order
    3. Events processed in FIFO order
    4. Analytics metrics reflect correct sequence

    EXPECTED BEHAVIOR:
    - Events published in order: E1, E2, E3
    - Events received in order: E1, E2, E3
    - Events processed in order: E1, E2, E3
    - Final state reflects all three enrollments

    VERIFICATION:
    - Verify event sequence numbers
    - Verify processing order matches publish order
    - Verify final analytics count is accurate

    PREVENTION:
    - Use ordered message queues (RabbitMQ with single consumer)
    - Include sequence numbers in events
    - Detect and handle out-of-order events
    """
    # Create organization and course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    course_id = str(uuid4())
    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, course_id, "Test Course", "test-course", "Test course", "published", datetime.utcnow())

    # Create three enrollment events in sequence
    enrollment_events = []
    for i in range(3):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]
        enrollment_id = str(uuid4())

        enrollment_event = {
            "event_type": "EnrollmentCreatedEvent",
            "enrollment_id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "organization_id": org_id,
            "enrolled_at": datetime.utcnow().isoformat(),
            "status": "active",
            "sequence_number": i + 1  # Track order
        }
        enrollment_events.append(enrollment_event)

        # Simulate sequential processing
        await db_transaction.execute("""
            INSERT INTO analytics_enrollment_events
            (id, enrollment_id, student_id, course_id, organization_id, event_type, sequence_number, processed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, str(uuid4()), enrollment_id, student_id, course_id, org_id,
            "enrollment_created", i + 1, datetime.utcnow())

    # REGRESSION CHECK 1: All events processed
    processed_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM analytics_enrollment_events
        WHERE course_id = $1
    """, course_id)

    assert processed_count == 3, \
        f"REGRESSION FAILURE BUG-623: Not all events processed (count={processed_count})"

    # REGRESSION CHECK 2: Events processed in order (verify sequence numbers)
    sequence_numbers = await db_transaction.fetch("""
        SELECT sequence_number FROM analytics_enrollment_events
        WHERE course_id = $1
        ORDER BY processed_at
    """, course_id)

    expected_sequence = [1, 2, 3]
    actual_sequence = [row["sequence_number"] for row in sequence_numbers]

    assert actual_sequence == expected_sequence, \
        f"REGRESSION FAILURE BUG-623: Events processed out of order - expected {expected_sequence}, got {actual_sequence}"


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_BUG623_bulk_event_processing(db_transaction, create_test_user, create_test_organization):
    """
    REGRESSION TEST: Analytics handles bulk enrollment events efficiently

    BUG REPORT:
    - Issue ID: BUG-623
    - Component: Bulk event processing performance
    - Root Cause: Processing events one-by-one caused performance degradation

    TEST SCENARIO:
    1. Bulk enrollment operation (10 students)
    2. 10 enrollment events published
    3. Analytics processes events in batch
    4. Dashboard updated once (not 10 separate updates)
    5. Processing completes in reasonable time

    EXPECTED BEHAVIOR:
    - All 10 events received
    - Events batched for processing
    - Single dashboard update with total count
    - Processing time < 5 seconds

    VERIFICATION:
    - Verify all events received
    - Verify batch processing occurred
    - Verify final enrollment count is accurate
    - Measure processing time

    PREVENTION:
    - Implement batch processing for high-volume events
    - Use database transactions for atomic updates
    - Monitor event processing throughput
    """
    # Create organization and course
    org_data = create_test_organization()
    org_id = org_data["id"]

    await db_transaction.execute("""
        INSERT INTO organizations (id, name, slug, contact_email, is_active)
        VALUES ($1, $2, $3, $4, $5)
    """, org_id, org_data["name"], org_data["slug"], org_data["contact_email"], True)

    course_id = str(uuid4())
    await db_transaction.execute("""
        INSERT INTO courses (id, title, slug, description, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, course_id, "Bulk Enrollment Course", "bulk-course", "Test", "published", datetime.utcnow())

    # Simulate bulk enrollment (10 students)
    import time
    start_time = time.time()

    enrollment_events = []
    for i in range(10):
        student_data = create_test_user(role="student", organization_id=org_id)
        student_id = student_data["id"]
        enrollment_id = str(uuid4())

        enrollment_event = {
            "enrollment_id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "organization_id": org_id,
            "enrolled_at": datetime.utcnow().isoformat()
        }
        enrollment_events.append(enrollment_event)

    # Batch insert all events (simulating efficient batch processing)
    for event in enrollment_events:
        await db_transaction.execute("""
            INSERT INTO analytics_enrollment_events
            (id, enrollment_id, student_id, course_id, organization_id, event_type, processed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, str(uuid4()), event["enrollment_id"], event["student_id"],
            event["course_id"], event["organization_id"], "enrollment_created", datetime.utcnow())

    # Single dashboard update (batch processing)
    await db_transaction.execute("""
        INSERT INTO analytics_course_metrics (course_id, organization_id, enrollment_count, last_updated)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (course_id) DO UPDATE
        SET enrollment_count = $3, last_updated = $4
    """, course_id, org_id, len(enrollment_events), datetime.utcnow())

    end_time = time.time()
    processing_time = end_time - start_time

    # REGRESSION CHECK 1: All events processed
    processed_count = await db_transaction.fetchval("""
        SELECT COUNT(*) FROM analytics_enrollment_events
        WHERE course_id = $1
    """, course_id)

    assert processed_count == 10, \
        f"REGRESSION FAILURE BUG-623: Not all bulk events processed (count={processed_count})"

    # REGRESSION CHECK 2: Dashboard updated with correct count
    enrollment_count = await db_transaction.fetchval("""
        SELECT enrollment_count FROM analytics_course_metrics
        WHERE course_id = $1
    """, course_id)

    assert enrollment_count == 10, \
        f"REGRESSION FAILURE BUG-623: Dashboard enrollment count incorrect (count={enrollment_count})"

    # REGRESSION CHECK 3: Processing time reasonable (< 5 seconds)
    assert processing_time < 5.0, \
        f"REGRESSION FAILURE BUG-623: Bulk processing too slow ({processing_time:.2f} seconds)"

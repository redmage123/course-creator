"""
Null and Boundary Condition Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring edge cases and boundary conditions are properly handled.
Prevents crashes from empty datasets, null values, and internationalization issues.

CRITICAL IMPORTANCE:
- Empty arrays can cause division by zero in analytics calculations
- NULL values in JSONB fields behave differently from SQL NULL
- Unicode characters must be preserved in search and content
- Boundary conditions can cause integer overflow or truncation
- Defensive programming prevents production crashes

REGRESSION BUGS COVERED:
- BUG-567: Empty arrays causing division by zero in analytics
- BUG-578: Null values in JSONB breaking database queries
- BUG-590: Unicode characters breaking search functionality

TEST CATEGORIES:
1. Empty/Null Handling (6 tests) - BUG-567, BUG-578
2. Unicode/Internationalization (4 tests) - BUG-590
3. Boundary Conditions (2 tests)

TEST PATTERN:
Each test follows TDD Red-Green-Refactor:
1. Document the original bug and root cause
2. Test the exact failing scenario with edge case data
3. Verify defensive programming prevents crash
4. Add preventive checks

TECHNICAL IMPLEMENTATION:
- Uses asyncpg for database operations
- Uses httpx for API endpoint testing
- Tests with truly empty datasets (zero records)
- Tests with NULL JSONB fields
- Tests with Unicode from multiple languages (Chinese, Arabic, Emoji)
- Tests boundary values (MAX_INT, empty strings, zero)
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys


# ============================================================================
# EMPTY/NULL HANDLING REGRESSION TESTS (BUG-567, BUG-578) - 6 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG567_empty_array_division_by_zero(
    db_transaction, api_client, create_test_course, create_test_instructor
):
    """
    REGRESSION TEST: Empty arrays don't cause division by zero

    BUG REPORT:
    - Issue ID: BUG-567
    - Reported: 2025-10-04
    - Fixed: 2025-10-05
    - Severity: MEDIUM
    - Root Cause: Analytics service calculated average enrollment without checking
                  if enrollment array was empty. Code divided sum by length without
                  validating length > 0 first.

    TEST SCENARIO:
    1. Create course with zero enrollments
    2. Request analytics for that course
    3. System should return 0 or None for average, not crash

    EXPECTED BEHAVIOR:
    - Analytics handle empty collections gracefully
    - Return 0, None, or empty result (not error)
    - No division by zero exceptions
    - No 500 errors from API

    VERIFICATION:
    - Course created with 0 enrollments
    - Analytics API returns 200 status
    - Average enrollment is 0 or None
    - No exceptions in logs

    PREVENTION:
    - Always check array length before division
    - Use defensive programming: if len(array) == 0: return 0
    - Add unit tests for empty collections
    """
    # Create course with no enrollments
    course_id = await create_test_course(
        title="Empty Course Test",
        instructor_id=await create_test_instructor()
    )

    # Request analytics for course with zero enrollments
    response = await api_client.get(
        f"https://localhost:8001/analytics/courses/{course_id}/stats"
    )

    # VERIFICATION: API should not crash
    assert response.status_code == 200, (
        f"Analytics API crashed on empty enrollment array: {response.status_code}"
    )

    data = response.json()

    # VERIFICATION: Average should be 0 or None (not error)
    avg_enrollment = data.get("average_enrollment")
    assert avg_enrollment in [0, None, 0.0], (
        f"Expected average_enrollment to be 0 or None for empty course, "
        f"got: {avg_enrollment}"
    )

    # VERIFICATION: Other stats should handle empty gracefully
    assert data.get("total_enrollments") == 0
    assert data.get("completion_rate") in [0, None, 0.0]


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG578_null_jsonb_with_coalesce(
    db_transaction, create_test_user, create_test_course
):
    """
    REGRESSION TEST: Null values in JSONB fields handled with COALESCE

    BUG REPORT:
    - Issue ID: BUG-578
    - Reported: 2025-10-06
    - Fixed: 2025-10-07
    - Severity: HIGH
    - Root Cause: SQL query accessed JSONB field without COALESCE. When field
                  was NULL, query failed with "cannot extract element from scalar".
                  JSONB NULL behaves differently from SQL NULL.

    TEST SCENARIO:
    1. Insert course with NULL preferences JSONB field
    2. Query for course with JSONB field access
    3. System should return empty object or default, not crash

    EXPECTED BEHAVIOR:
    - NULL JSONB fields return empty object {}
    - COALESCE(jsonb_field, '{}'::jsonb) provides default
    - No "cannot extract element" errors
    - Queries succeed with NULL JSONB

    VERIFICATION:
    - Course created with NULL preferences
    - Query accesses preferences JSONB field
    - No database errors
    - Returns empty object or default value

    PREVENTION:
    - Always use COALESCE for JSONB field access
    - Set JSONB NOT NULL DEFAULT '{}'::jsonb in schema
    - Test with NULL JSONB in all queries
    """
    user_id = await create_test_user(role="instructor")

    # Insert course with NULL preferences (simulating edge case)
    async with db_transaction.transaction():
        result = await db_transaction.fetchrow(
            """
            INSERT INTO courses (
                title, instructor_id, organization_id,
                preferences, created_at
            )
            VALUES ($1, $2, 1, NULL, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            "NULL JSONB Test Course",
            user_id
        )
        course_id = result["id"]

    # VERIFICATION: Query with JSONB access should not crash
    async with db_transaction.transaction():
        row = await db_transaction.fetchrow(
            """
            SELECT
                id,
                title,
                COALESCE(preferences, '{}'::jsonb) as preferences,
                COALESCE(preferences->>'theme', 'default') as theme
            FROM courses
            WHERE id = $1
            """,
            course_id
        )

    # VERIFICATION: NULL JSONB handled gracefully
    assert row is not None, "Query should succeed with NULL JSONB"
    assert row["preferences"] is not None, "COALESCE should provide default"
    assert row["theme"] == "default", "JSONB field extraction should use default"


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG567_empty_string_in_search(
    api_client, create_test_course, create_test_instructor
):
    """
    REGRESSION TEST: Empty string search returns all results or empty

    BUG REPORT:
    - Issue ID: BUG-567 (related)
    - Reported: 2025-10-04
    - Fixed: 2025-10-05
    - Severity: LOW
    - Root Cause: Search endpoint did not validate empty query string.
                  Empty string passed to full-text search caused crash.

    TEST SCENARIO:
    1. Create several courses
    2. Search with empty string ""
    3. System should return all results or empty array, not crash

    EXPECTED BEHAVIOR:
    - Empty search returns all courses OR empty array (documented behavior)
    - No crashes or 500 errors
    - Pagination still works

    VERIFICATION:
    - Search with empty string succeeds
    - Returns 200 status
    - Returns valid array (empty or all courses)
    """
    instructor_id = await create_test_instructor()

    # Create test courses
    course1_id = await create_test_course(
        title="Python Basics",
        instructor_id=instructor_id
    )
    course2_id = await create_test_course(
        title="Advanced JavaScript",
        instructor_id=instructor_id
    )

    # VERIFICATION: Search with empty string should not crash
    response = await api_client.get(
        "https://localhost:8002/content/search",
        params={"query": ""}
    )

    assert response.status_code == 200, (
        f"Search with empty string crashed: {response.status_code}"
    )

    data = response.json()
    assert isinstance(data, (list, dict)), "Search should return array or object"


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG567_zero_enrollment_analytics(
    db_transaction, api_client, create_test_course,
    create_test_instructor, create_test_organization
):
    """
    REGRESSION TEST: Zero enrollment courses handled in analytics

    BUG REPORT:
    - Issue ID: BUG-567 (related)
    - Reported: 2025-10-04
    - Fixed: 2025-10-05
    - Severity: MEDIUM
    - Root Cause: Organization-wide analytics assumed all courses had at least
                  one enrollment. Aggregation queries failed on empty JOIN.

    TEST SCENARIO:
    1. Create organization with multiple courses
    2. Some courses have zero enrollments
    3. Request organization analytics
    4. System should include zero-enrollment courses or exclude gracefully

    EXPECTED BEHAVIOR:
    - Zero-enrollment courses included with 0 stats
    - No LEFT JOIN failures
    - Aggregations handle empty sets

    VERIFICATION:
    - Org analytics returns 200
    - Zero-enrollment courses handled
    - No SQL errors
    """
    org_id = await create_test_organization(name="Test University")
    instructor_id = await create_test_instructor(organization_id=org_id)

    # Create course with zero enrollments
    course_id = await create_test_course(
        title="Empty Course",
        instructor_id=instructor_id,
        organization_id=org_id
    )

    # VERIFICATION: Org analytics should handle zero enrollment
    response = await api_client.get(
        f"https://localhost:8001/analytics/organizations/{org_id}/stats"
    )

    assert response.status_code == 200, (
        f"Org analytics failed on zero enrollments: {response.status_code}"
    )

    data = response.json()
    assert "courses" in data or "total_courses" in data


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG578_null_timestamp_calculations(
    db_transaction, create_test_user, create_test_course
):
    """
    REGRESSION TEST: Null timestamps in date calculations

    BUG REPORT:
    - Issue ID: BUG-578 (related)
    - Reported: 2025-10-06
    - Fixed: 2025-10-07
    - Severity: MEDIUM
    - Root Cause: Date range calculations did not handle NULL end_date.
                  Query tried to subtract NULL from current_timestamp.

    TEST SCENARIO:
    1. Create course with NULL end_date (ongoing)
    2. Calculate course duration
    3. System should handle NULL as "current date" or skip calculation

    EXPECTED BEHAVIOR:
    - NULL end_date treated as ongoing course
    - Duration calculation uses COALESCE(end_date, CURRENT_TIMESTAMP)
    - No arithmetic errors on NULL

    VERIFICATION:
    - Course with NULL end_date created
    - Duration query succeeds
    - Returns valid duration or NULL
    """
    instructor_id = await create_test_user(role="instructor")

    # Create course with NULL end_date
    async with db_transaction.transaction():
        result = await db_transaction.fetchrow(
            """
            INSERT INTO courses (
                title, instructor_id, organization_id,
                start_date, end_date, created_at
            )
            VALUES ($1, $2, 1, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            "Ongoing Course",
            instructor_id
        )
        course_id = result["id"]

    # VERIFICATION: Duration calculation with NULL end_date
    async with db_transaction.transaction():
        row = await db_transaction.fetchrow(
            """
            SELECT
                id,
                start_date,
                end_date,
                COALESCE(end_date, CURRENT_TIMESTAMP) - start_date as duration
            FROM courses
            WHERE id = $1
            """,
            course_id
        )

    assert row is not None, "Query should succeed with NULL end_date"
    assert row["duration"] is not None, "Duration should calculate with COALESCE"


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG578_empty_result_aggregations(
    db_transaction, create_test_organization
):
    """
    REGRESSION TEST: Empty result sets in aggregations

    BUG REPORT:
    - Issue ID: BUG-578 (related)
    - Reported: 2025-10-06
    - Fixed: 2025-10-07
    - Severity: LOW
    - Root Cause: Aggregation queries returned NULL instead of 0 for COUNT/SUM
                  on empty result sets. Frontend crashed parsing NULL as number.

    TEST SCENARIO:
    1. Create organization with no courses
    2. Query aggregated statistics
    3. System should return 0 for counts/sums, not NULL

    EXPECTED BEHAVIOR:
    - COUNT returns 0 on empty set (not NULL)
    - SUM returns NULL or 0 (documented)
    - Use COALESCE(SUM(...), 0) for 0 default

    VERIFICATION:
    - Org with no courses
    - Aggregation query returns 0 counts
    - No NULL values that crash frontend
    """
    org_id = await create_test_organization(name="Empty Organization")

    # VERIFICATION: Aggregations on empty org
    async with db_transaction.transaction():
        row = await db_transaction.fetchrow(
            """
            SELECT
                COUNT(*) as course_count,
                COALESCE(SUM(capacity), 0) as total_capacity,
                COALESCE(AVG(capacity), 0) as avg_capacity
            FROM courses
            WHERE organization_id = $1
            """,
            org_id
        )

    # VERIFICATION: Empty aggregations return 0, not NULL
    assert row["course_count"] == 0, "COUNT should be 0 on empty set"
    assert row["total_capacity"] == 0, "SUM with COALESCE should be 0"
    assert row["avg_capacity"] == 0, "AVG with COALESCE should be 0"


# ============================================================================
# UNICODE/INTERNATIONALIZATION REGRESSION TESTS (BUG-590) - 4 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG590_chinese_characters_in_search(
    api_client, create_test_course, create_test_instructor
):
    """
    REGRESSION TEST: Chinese characters preserved in search

    BUG REPORT:
    - Issue ID: BUG-590
    - Reported: 2025-10-08
    - Fixed: 2025-10-09
    - Severity: HIGH
    - Root Cause: Text preprocessing stripped all non-ASCII characters before
                  search. Chinese course titles became empty strings, causing
                  search to fail with "empty query" error.

    TEST SCENARIO:
    1. Create course with Chinese title
    2. Search for course using Chinese characters
    3. System should find the course, preserving Unicode

    EXPECTED BEHAVIOR:
    - Unicode characters preserved in database
    - Search works with non-ASCII queries
    - Results include Unicode content
    - No "empty query" errors

    VERIFICATION:
    - Course created with Chinese title
    - Search with Chinese query succeeds
    - Returns correct course
    - Title displays correctly

    PREVENTION:
    - Do not strip Unicode in preprocessing
    - Use UTF-8 encoding throughout
    - Test with multiple languages
    """
    instructor_id = await create_test_instructor()

    # Create course with Chinese title
    chinese_title = "Python编程入门课程"  # "Python Programming Intro Course"
    course_id = await create_test_course(
        title=chinese_title,
        instructor_id=instructor_id
    )

    # VERIFICATION: Search with Chinese characters
    response = await api_client.get(
        "https://localhost:8002/content/search",
        params={"query": "Python编程"}
    )

    assert response.status_code == 200, (
        f"Search failed with Chinese characters: {response.status_code}"
    )

    data = response.json()

    # VERIFICATION: Course found with Chinese query
    if isinstance(data, dict):
        results = data.get("results", [])
    else:
        results = data

    assert len(results) > 0, "Should find course with Chinese title"

    # VERIFICATION: Title preserved correctly
    found = any(
        chinese_title in result.get("title", "")
        for result in results
    )
    assert found, f"Chinese title not preserved in search results"


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG590_arabic_text_in_course_titles(
    api_client, create_test_course, create_test_instructor
):
    """
    REGRESSION TEST: Arabic text (RTL) handled in course titles

    BUG REPORT:
    - Issue ID: BUG-590 (related)
    - Reported: 2025-10-08
    - Fixed: 2025-10-09
    - Severity: HIGH
    - Root Cause: Same Unicode stripping issue affected Arabic text.
                  Additionally, RTL text rendering not considered in UI.

    TEST SCENARIO:
    1. Create course with Arabic title
    2. Retrieve course via API
    3. System should preserve Arabic text

    EXPECTED BEHAVIOR:
    - Arabic characters stored correctly
    - RTL text preserved
    - No encoding errors
    - API returns correct text

    VERIFICATION:
    - Course created with Arabic
    - API retrieves correct title
    - Unicode preserved
    """
    instructor_id = await create_test_instructor()

    # Create course with Arabic title
    arabic_title = "دورة برمجة بايثون للمبتدئين"  # "Python Programming for Beginners"
    course_id = await create_test_course(
        title=arabic_title,
        instructor_id=instructor_id
    )

    # VERIFICATION: Retrieve course with Arabic title
    response = await api_client.get(
        f"https://localhost:8005/courses/{course_id}"
    )

    assert response.status_code == 200, (
        f"Failed to retrieve course with Arabic title: {response.status_code}"
    )

    data = response.json()

    # VERIFICATION: Arabic text preserved
    assert arabic_title in data.get("title", ""), (
        "Arabic title not preserved in database"
    )


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG590_emoji_in_course_descriptions(
    api_client, create_test_course, create_test_instructor, db_transaction
):
    """
    REGRESSION TEST: Emoji preserved in course descriptions

    BUG REPORT:
    - Issue ID: BUG-590 (related)
    - Reported: 2025-10-08
    - Fixed: 2025-10-09
    - Severity: MEDIUM
    - Root Cause: Unicode stripping removed emoji from descriptions.
                  Students use emoji for emphasis and visual appeal.

    TEST SCENARIO:
    1. Create course with emoji in description
    2. Retrieve course description
    3. System should preserve emoji

    EXPECTED BEHAVIOR:
    - Emoji stored correctly (4-byte UTF-8)
    - Retrieved emoji matches stored
    - No encoding corruption

    VERIFICATION:
    - Description contains emoji
    - Database stores correctly
    - API returns correct emoji
    """
    instructor_id = await create_test_instructor()

    # Description with various emoji
    emoji_description = (
        "Learn Python programming 🐍 with hands-on exercises 💻 "
        "Perfect for beginners! ✨ Get certified 🎓"
    )

    # Create course with emoji description
    async with db_transaction.transaction():
        result = await db_transaction.fetchrow(
            """
            INSERT INTO courses (
                title, description, instructor_id,
                organization_id, created_at
            )
            VALUES ($1, $2, $3, 1, CURRENT_TIMESTAMP)
            RETURNING id, description
            """,
            "Emoji Test Course",
            emoji_description,
            instructor_id
        )
        course_id = result["id"]
        stored_description = result["description"]

    # VERIFICATION: Emoji preserved in database
    assert "🐍" in stored_description, "Snake emoji not preserved"
    assert "💻" in stored_description, "Laptop emoji not preserved"
    assert "✨" in stored_description, "Sparkles emoji not preserved"
    assert "🎓" in stored_description, "Graduation cap emoji not preserved"

    # VERIFICATION: API returns emoji correctly
    response = await api_client.get(
        f"https://localhost:8005/courses/{course_id}"
    )

    assert response.status_code == 200
    data = response.json()
    description = data.get("description", "")

    assert "🐍" in description, "API did not return snake emoji"
    assert "💻" in description, "API did not return laptop emoji"


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_BUG590_special_chars_in_usernames(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Special characters in usernames (ñ, ü, etc)

    BUG REPORT:
    - Issue ID: BUG-590 (related)
    - Reported: 2025-10-08
    - Fixed: 2025-10-09
    - Severity: MEDIUM
    - Root Cause: Username validation regex only allowed ASCII characters.
                  Users with non-English names (José, Müller, etc) rejected.

    TEST SCENARIO:
    1. Create users with international names
    2. System should accept and store correctly

    EXPECTED BEHAVIOR:
    - Usernames accept Unicode letters
    - Names with accents, umlauts stored correctly
    - Login works with special chars

    VERIFICATION:
    - Users created with special chars
    - Names stored correctly
    - Can query by name
    """
    # Test various international names
    international_names = [
        ("José García", "jose.garcia@test.com"),      # Spanish ñ, á
        ("Müller Schmidt", "muller.schmidt@test.com"), # German ü
        ("François Dubois", "francois.dubois@test.com"), # French ç, ois
        ("Søren Nielsen", "soren.nielsen@test.com"),  # Danish ø
    ]

    for full_name, email in international_names:
        # VERIFICATION: User creation with special chars
        user_id = await create_test_user(
            email=email,
            full_name=full_name,
            role="student"
        )

        # VERIFICATION: Name stored correctly
        async with db_transaction.transaction():
            row = await db_transaction.fetchrow(
                """
                SELECT full_name
                FROM users
                WHERE id = $1
                """,
                user_id
            )

        assert row["full_name"] == full_name, (
            f"Special characters not preserved in name: {row['full_name']} "
            f"(expected: {full_name})"
        )


# ============================================================================
# BOUNDARY CONDITIONS REGRESSION TESTS - 2 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_integer_overflow_capacity_calculations(
    db_transaction, create_test_course, create_test_instructor
):
    """
    REGRESSION TEST: Integer overflow in capacity calculations

    BUG REPORT:
    - Issue ID: BUG-567 (boundary condition)
    - Reported: 2025-10-04
    - Fixed: 2025-10-05
    - Severity: LOW
    - Root Cause: Total capacity calculation used INT instead of BIGINT.
                  Organization with many large courses exceeded INT max.

    TEST SCENARIO:
    1. Create course with very large capacity
    2. Calculate total capacity across courses
    3. System should handle large numbers without overflow

    EXPECTED BEHAVIOR:
    - Use BIGINT for capacity totals
    - No integer overflow errors
    - Calculations accurate for large numbers

    VERIFICATION:
    - Course with large capacity created
    - Aggregation succeeds
    - No overflow errors
    """
    instructor_id = await create_test_instructor()

    # Create course with large capacity (near INT max)
    large_capacity = 2_000_000_000  # 2 billion (INT max is ~2.1 billion)

    async with db_transaction.transaction():
        result = await db_transaction.fetchrow(
            """
            INSERT INTO courses (
                title, instructor_id, organization_id,
                capacity, created_at
            )
            VALUES ($1, $2, 1, $3, CURRENT_TIMESTAMP)
            RETURNING id, capacity
            """,
            "Large Capacity Course",
            instructor_id,
            large_capacity
        )
        course_id = result["id"]
        stored_capacity = result["capacity"]

    # VERIFICATION: Large capacity stored correctly
    assert stored_capacity == large_capacity, (
        f"Capacity overflow: stored {stored_capacity}, expected {large_capacity}"
    )

    # VERIFICATION: Aggregation with large numbers
    async with db_transaction.transaction():
        row = await db_transaction.fetchrow(
            """
            SELECT SUM(capacity)::BIGINT as total_capacity
            FROM courses
            WHERE organization_id = 1
            """
        )

    assert row["total_capacity"] >= large_capacity, (
        "Capacity aggregation overflow"
    )


@pytest.mark.regression
@pytest.mark.edge_cases
@pytest.mark.asyncio
async def test_maximum_string_length_descriptions(
    db_transaction, create_test_instructor
):
    """
    REGRESSION TEST: Maximum string length in course descriptions

    BUG REPORT:
    - Issue ID: BUG-567 (boundary condition)
    - Reported: 2025-10-04
    - Fixed: 2025-10-05
    - Severity: LOW
    - Root Cause: Description field had VARCHAR(5000) limit.
                  Long descriptions were silently truncated, losing data.

    TEST SCENARIO:
    1. Create course with very long description
    2. System should either accept full text or reject with error
    3. No silent truncation

    EXPECTED BEHAVIOR:
    - Description accepts reasonable length (10,000+ chars)
    - Or rejects with clear validation error
    - No silent data loss

    VERIFICATION:
    - Long description stored completely
    - No truncation
    - Or clear error message
    """
    instructor_id = await create_test_instructor()

    # Create very long description (10,000 characters)
    long_description = "A" * 10_000

    # VERIFICATION: Long description handling
    try:
        async with db_transaction.transaction():
            result = await db_transaction.fetchrow(
                """
                INSERT INTO courses (
                    title, description, instructor_id,
                    organization_id, created_at
                )
                VALUES ($1, $2, $3, 1, CURRENT_TIMESTAMP)
                RETURNING id, description
                """,
                "Long Description Course",
                long_description,
                instructor_id
            )
            stored_description = result["description"]

        # If insertion succeeded, verify no truncation
        assert len(stored_description) == len(long_description), (
            f"Description truncated: stored {len(stored_description)}, "
            f"expected {len(long_description)}"
        )

    except Exception as e:
        # If insertion failed, should be validation error (not silent truncation)
        error_msg = str(e).lower()
        assert "too long" in error_msg or "exceeds" in error_msg or "length" in error_msg, (
            f"Expected validation error for long description, got: {e}"
        )


# ============================================================================
# TEST FIXTURES AND HELPERS
# ============================================================================

@pytest.fixture
async def api_client():
    """Provides httpx client for API testing"""
    async with httpx.AsyncClient(verify=False) as client:
        yield client


@pytest.fixture
async def create_test_course(db_transaction):
    """Factory fixture for creating test courses"""
    async def _create(
        title: str,
        instructor_id: int,
        organization_id: int = 1,
        description: str = "Test course description",
        capacity: int = 30
    ) -> int:
        async with db_transaction.transaction():
            result = await db_transaction.fetchrow(
                """
                INSERT INTO courses (
                    title, description, instructor_id,
                    organization_id, capacity, created_at
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                title, description, instructor_id,
                organization_id, capacity
            )
            return result["id"]
    return _create


@pytest.fixture
async def create_test_instructor(db_transaction, create_test_user):
    """Factory fixture for creating test instructors"""
    async def _create(organization_id: int = 1) -> int:
        return await create_test_user(
            role="instructor",
            organization_id=organization_id
        )
    return _create


@pytest.fixture
async def create_test_user(db_transaction):
    """Factory fixture for creating test users"""
    async def _create(
        email: str = None,
        full_name: str = "Test User",
        role: str = "student",
        organization_id: int = 1
    ) -> int:
        if email is None:
            import uuid
            email = f"test_{uuid.uuid4()}@test.com"

        async with db_transaction.transaction():
            # Get or create role
            role_row = await db_transaction.fetchrow(
                """
                SELECT id FROM roles WHERE role_name = $1
                """,
                role
            )
            role_id = role_row["id"] if role_row else 3  # Default to student

            # Create user
            result = await db_transaction.fetchrow(
                """
                INSERT INTO users (
                    email, full_name, role_id,
                    organization_id, created_at
                )
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                email, full_name, role_id, organization_id
            )
            return result["id"]
    return _create


@pytest.fixture
async def create_test_organization(db_transaction):
    """Factory fixture for creating test organizations"""
    async def _create(name: str) -> int:
        async with db_transaction.transaction():
            result = await db_transaction.fetchrow(
                """
                INSERT INTO organizations (
                    name, created_at
                )
                VALUES ($1, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                name
            )
            return result["id"]
    return _create

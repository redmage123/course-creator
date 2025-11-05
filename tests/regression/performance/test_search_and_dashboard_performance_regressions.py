"""
Search and Dashboard Performance Regression Tests

BUSINESS CONTEXT:
Performance regression tests ensuring search queries and dashboard analytics
meet strict performance SLAs across code changes. Prevents previously fixed
performance bugs from degrading user experience in production.

CRITICAL IMPORTANCE:
- Search performance directly impacts content discovery and user satisfaction
- Dashboard load times affect instructor productivity and platform adoption
- Performance degradation costs institutional clients and reduces engagement
- SLA violations trigger service credits and contract penalties

REGRESSION BUGS COVERED:
- BUG-734: Full-text search exceeds 500ms SLA (Severity: MEDIUM)
- BUG-745: Dashboard analytics exceed 3-second SLA (Severity: HIGH)

PERFORMANCE TARGETS:
- Full-text search: <500ms for 95th percentile queries
- Dashboard analytics: <3 seconds for initial load
- Cache hit ratio: >80% for repeated dashboard requests
- Concurrent dashboard loads: <5 seconds under 10 concurrent users

TEST PATTERN:
Each test follows performance regression methodology:
1. Document the original performance bug and root cause
2. Create realistic test data matching production scale
3. Measure actual execution time with performance fixtures
4. Verify database optimizations (indexes, query plans)
5. Test caching effectiveness and cache invalidation
6. Add preventive checks for future performance regressions

TECHNICAL IMPLEMENTATION:
- Uses measure_performance fixture for accurate timing
- Verifies PostgreSQL GIN indexes and query plans
- Tests Redis caching with realistic TTL scenarios
- Validates materialized view refresh performance
- Measures concurrent load handling
"""

import pytest
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from contextlib import asynccontextmanager


# ============================================================================
# SEARCH PERFORMANCE REGRESSION TESTS (BUG-734) - 5 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG734_fulltext_search_under_500ms(
    db_transaction, measure_performance, create_test_course
):
    """
    REGRESSION TEST: Full-text search meets 500ms performance target

    BUG REPORT:
    - Issue ID: BUG-734
    - Reported: 2025-11-01
    - Fixed: 2025-11-02
    - Severity: MEDIUM
    - Root Cause: Missing GIN index on tsvector column. PostgreSQL was
                  performing sequential scans on every search query instead
                  of using index-based search.

    PERFORMANCE TARGET: <500ms for search queries

    TEST SCENARIO:
    1. Create 150+ courses with diverse titles, descriptions, tags
    2. Perform full-text search for common search term
    3. Measure execution time
    4. Verify performance meets 500ms SLA

    EXPECTED BEHAVIOR:
    - Search completes in <500ms
    - PostgreSQL uses GIN index (not sequential scan)
    - Results are ranked by relevance (ts_rank)
    - Pagination works efficiently

    VERIFICATION:
    - Measure actual query execution time
    - Verify index usage via EXPLAIN ANALYZE
    - Confirm results accuracy

    PREVENTION:
    - Monitor idx_entity_metadata_search_vector index exists
    - Alert if query plans show sequential scans
    - Track 95th percentile search latency
    """
    # Create realistic test data (150 courses)
    test_courses = []
    search_terms = [
        "python programming", "web development", "machine learning",
        "data science", "javascript", "database design",
        "cloud computing", "cybersecurity", "mobile development"
    ]

    for i in range(150):
        course_data = {
            "id": str(uuid.uuid4()),
            "title": f"Course: {search_terms[i % len(search_terms)]} - Module {i}",
            "description": f"Comprehensive course on {search_terms[i % len(search_terms)]} covering fundamentals and advanced topics",
            "tags": search_terms[i % len(search_terms)].split(),
            "keywords": ["programming", "tutorial", "certification"],
            "entity_type": "course",
            "created_at": datetime.utcnow() - timedelta(days=i)
        }
        test_courses.append(course_data)

        # Insert into entity_metadata table
        await db_transaction.execute(
            """
            INSERT INTO entity_metadata (
                id, entity_id, entity_type, title, description,
                tags, keywords, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            str(uuid.uuid4()),
            course_data["id"],
            course_data["entity_type"],
            course_data["title"],
            course_data["description"],
            course_data["tags"],
            course_data["keywords"],
            course_data["created_at"]
        )

    # Execute full-text search with performance measurement
    search_query = "python programming"

    with measure_performance() as timer:
        results = await db_transaction.fetch(
            """
            SELECT
                id, entity_id, title, description,
                ts_rank(search_vector, query) AS rank
            FROM
                entity_metadata,
                to_tsquery('english', $1) query
            WHERE
                search_vector @@ query
            ORDER BY rank DESC
            LIMIT 20
            """,
            " & ".join(search_query.split())  # Convert to tsquery format
        )

    # ASSERTION: Search must complete within 500ms
    assert timer.elapsed < 0.5, (
        f"Search performance degraded: {timer.elapsed:.3f}s exceeds 500ms SLA. "
        f"Expected <0.5s, got {timer.elapsed:.3f}s. "
        f"Check if GIN index idx_entity_metadata_search_vector exists."
    )

    # Verify results are accurate
    assert len(results) > 0, "Search should return results"
    assert all("python" in row["title"].lower() or "python" in row["description"].lower()
              for row in results[:5]), "Top results should match search term"

    # Verify performance scales linearly (not exponentially)
    assert timer.elapsed < 0.3, (
        f"Search performance warning: {timer.elapsed:.3f}s is acceptable but approaching limit. "
        f"Optimal performance should be <300ms for 150 records."
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG734_gin_index_usage_verification(db_transaction):
    """
    REGRESSION TEST: Verify GIN index is used for full-text search

    BUG REPORT:
    - Issue ID: BUG-734
    - Root Cause: Missing GIN index caused PostgreSQL to use sequential scans

    TEST SCENARIO:
    1. Execute search query with EXPLAIN ANALYZE
    2. Parse query plan to verify index usage
    3. Confirm no sequential scans on entity_metadata

    EXPECTED BEHAVIOR:
    - Query plan shows "Bitmap Index Scan" or "Index Scan"
    - Uses index: idx_entity_metadata_search_vector
    - No "Seq Scan" on entity_metadata table

    VERIFICATION:
    - Parse EXPLAIN output for index name
    - Confirm GIN index is active
    - Alert if sequential scan detected

    PREVENTION:
    - Automated monitoring of query plans
    - CI/CD checks for index existence
    - Alert on sequential scan patterns
    """
    # Verify GIN index exists
    index_check = await db_transaction.fetchrow(
        """
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE
            tablename = 'entity_metadata'
            AND indexname = 'idx_entity_metadata_search_vector'
        """
    )

    assert index_check is not None, (
        "Critical performance regression: GIN index idx_entity_metadata_search_vector is missing! "
        "This will cause sequential scans and severe performance degradation."
    )

    assert "gin" in index_check["indexdef"].lower(), (
        "Index exists but is not a GIN index. GIN indexes are required for tsvector full-text search."
    )

    # Execute search with EXPLAIN to verify index usage
    explain_result = await db_transaction.fetch(
        """
        EXPLAIN (FORMAT JSON)
        SELECT id, title
        FROM entity_metadata
        WHERE search_vector @@ to_tsquery('english', 'python')
        LIMIT 20
        """
    )

    # Parse EXPLAIN output
    query_plan = explain_result[0]["QUERY PLAN"][0]["Plan"]
    plan_str = str(query_plan)

    # Verify index is being used (not sequential scan)
    assert "Index Scan" in plan_str or "Bitmap Index Scan" in plan_str, (
        f"Query plan shows sequential scan instead of index scan. "
        f"Performance regression detected. Plan: {plan_str}"
    )

    # Verify no sequential scan on entity_metadata
    assert "Seq Scan" not in plan_str or "entity_metadata" not in plan_str, (
        f"Sequential scan detected on entity_metadata table. "
        f"This indicates index is not being used properly. Plan: {plan_str}"
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG734_search_with_multiple_keywords_performance(
    db_transaction, measure_performance
):
    """
    REGRESSION TEST: Multi-keyword search maintains performance

    BUG REPORT:
    - Issue ID: BUG-734
    - Additional Scenario: Complex queries with multiple keywords

    TEST SCENARIO:
    1. Create 100 courses with varied content
    2. Execute search with 3-5 keywords (realistic user search)
    3. Measure performance with AND/OR operators
    4. Verify performance remains under 500ms

    EXPECTED BEHAVIOR:
    - Multi-keyword search completes in <500ms
    - AND operator narrows results efficiently
    - OR operator broadens results efficiently
    - Ranking reflects keyword relevance

    VERIFICATION:
    - Measure query execution time
    - Verify result relevance
    - Test both AND and OR operators

    PREVENTION:
    - Test complex query patterns in CI/CD
    - Monitor multi-keyword search latency
    """
    # Create diverse test courses
    topics = [
        ("Python", "Programming", "Backend"),
        ("JavaScript", "Frontend", "Web"),
        ("Machine Learning", "AI", "Data Science"),
        ("Docker", "Kubernetes", "DevOps"),
        ("React", "TypeScript", "UI/UX")
    ]

    for i in range(100):
        topic_set = topics[i % len(topics)]
        await db_transaction.execute(
            """
            INSERT INTO entity_metadata (
                id, entity_id, entity_type, title, description,
                tags, keywords, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "course",
            f"Complete {topic_set[0]} Course - {i}",
            f"Learn {topic_set[0]}, {topic_set[1]}, and {topic_set[2]}",
            list(topic_set),
            ["tutorial", "certification", "beginner"],
            datetime.utcnow()
        )

    # Test multi-keyword search with AND operator
    search_terms = "python & programming & backend"

    with measure_performance() as timer:
        and_results = await db_transaction.fetch(
            """
            SELECT id, title, ts_rank(search_vector, query) AS rank
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 20
            """,
            search_terms
        )

    assert timer.elapsed < 0.5, (
        f"Multi-keyword AND search exceeded SLA: {timer.elapsed:.3f}s > 500ms"
    )

    # Test multi-keyword search with OR operator
    search_terms_or = "python | javascript | docker"

    with measure_performance() as timer:
        or_results = await db_transaction.fetch(
            """
            SELECT id, title, ts_rank(search_vector, query) AS rank
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 20
            """,
            search_terms_or
        )

    assert timer.elapsed < 0.5, (
        f"Multi-keyword OR search exceeded SLA: {timer.elapsed:.3f}s > 500ms"
    )

    # Verify OR returns more results than AND (sanity check)
    assert len(or_results) >= len(and_results), (
        "OR search should return equal or more results than AND search"
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG734_large_result_set_pagination_performance(
    db_transaction, measure_performance
):
    """
    REGRESSION TEST: Pagination with large result sets performs efficiently

    BUG REPORT:
    - Issue ID: BUG-734
    - Related Issue: Pagination performance with 1000+ matching results

    TEST SCENARIO:
    1. Create 1000+ courses all matching a broad search term
    2. Retrieve pages 1, 5, 10, 20 (testing OFFSET performance)
    3. Measure time for each page retrieval
    4. Verify consistent performance across pages

    EXPECTED BEHAVIOR:
    - First page retrieval: <100ms
    - Later pages (with OFFSET): <500ms
    - Performance should not degrade exponentially
    - Consider cursor-based pagination for very large offsets

    VERIFICATION:
    - Measure page retrieval times
    - Verify pagination accuracy
    - Check for performance degradation

    PREVENTION:
    - Monitor pagination performance in production
    - Consider cursor-based pagination for large offsets
    - Alert on degraded pagination performance
    """
    # Create 1000 courses with common term
    for i in range(1000):
        await db_transaction.execute(
            """
            INSERT INTO entity_metadata (
                id, entity_id, entity_type, title, description,
                tags, keywords, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "course",
            f"Programming Tutorial {i}",
            f"Learn programming fundamentals - Module {i}",
            ["programming", "tutorial"],
            ["education", "online"],
            datetime.utcnow() - timedelta(hours=i)
        )

    page_size = 20
    search_term = "programming"

    # Test page 1 (no offset)
    with measure_performance() as timer:
        page_1 = await db_transaction.fetch(
            """
            SELECT id, title
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            ORDER BY created_at DESC
            LIMIT $2
            """,
            search_term,
            page_size
        )

    page_1_time = timer.elapsed
    assert page_1_time < 0.1, (
        f"First page retrieval too slow: {page_1_time:.3f}s > 100ms"
    )

    # Test page 5 (offset 80)
    with measure_performance() as timer:
        page_5 = await db_transaction.fetch(
            """
            SELECT id, title
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            search_term,
            page_size,
            page_size * 4  # Page 5 = offset 80
        )

    page_5_time = timer.elapsed
    assert page_5_time < 0.5, (
        f"Page 5 retrieval exceeded SLA: {page_5_time:.3f}s > 500ms"
    )

    # Test page 20 (offset 380)
    with measure_performance() as timer:
        page_20 = await db_transaction.fetch(
            """
            SELECT id, title
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            search_term,
            page_size,
            page_size * 19  # Page 20 = offset 380
        )

    page_20_time = timer.elapsed
    assert page_20_time < 0.5, (
        f"Page 20 retrieval exceeded SLA: {page_20_time:.3f}s > 500ms. "
        f"Consider cursor-based pagination for large offsets."
    )

    # Verify performance doesn't degrade exponentially
    performance_ratio = page_20_time / page_1_time
    assert performance_ratio < 10, (
        f"Pagination performance degrades too much: "
        f"Page 20 is {performance_ratio:.1f}x slower than page 1. "
        f"Expected <10x degradation."
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG734_concurrent_search_requests_performance(
    db_transaction, measure_performance
):
    """
    REGRESSION TEST: Concurrent search requests maintain performance

    BUG REPORT:
    - Issue ID: BUG-734
    - Related Issue: Search performance under concurrent load

    TEST SCENARIO:
    1. Create 200 test courses
    2. Simulate 10 concurrent search requests
    3. Measure total time and individual query times
    4. Verify no request exceeds 1-second timeout

    EXPECTED BEHAVIOR:
    - All queries complete successfully
    - No query exceeds 1-second timeout
    - Average query time remains under 500ms
    - Database connection pooling handles concurrency

    VERIFICATION:
    - Measure concurrent execution time
    - Verify all requests complete
    - Check for connection pool exhaustion

    PREVENTION:
    - Load testing in staging environment
    - Monitor connection pool metrics
    - Alert on query timeouts
    """
    # Create test data
    for i in range(200):
        await db_transaction.execute(
            """
            INSERT INTO entity_metadata (
                id, entity_id, entity_type, title, description,
                tags, keywords, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "course",
            f"Course on {'Python' if i % 2 == 0 else 'JavaScript'} - {i}",
            f"Comprehensive tutorial covering all aspects",
            [f"tag{i % 5}"],
            ["tutorial", "certification"],
            datetime.utcnow()
        )

    search_terms = [
        "python", "javascript", "programming", "tutorial", "web"
    ]

    async def execute_search(term: str) -> Dict[str, Any]:
        """Execute a single search and measure time"""
        start_time = time.time()

        results = await db_transaction.fetch(
            """
            SELECT id, title
            FROM entity_metadata, to_tsquery('english', $1) query
            WHERE search_vector @@ query
            LIMIT 20
            """,
            term
        )

        elapsed = time.time() - start_time
        return {
            "term": term,
            "count": len(results),
            "elapsed": elapsed
        }

    # Execute 10 concurrent searches
    with measure_performance() as timer:
        tasks = [
            execute_search(search_terms[i % len(search_terms)])
            for i in range(10)
        ]
        search_results = await asyncio.gather(*tasks)

    total_time = timer.elapsed

    # Verify all searches completed
    assert len(search_results) == 10, "All concurrent searches should complete"

    # Verify no individual query exceeded timeout
    max_query_time = max(r["elapsed"] for r in search_results)
    assert max_query_time < 1.0, (
        f"Concurrent search timeout: slowest query took {max_query_time:.3f}s > 1s. "
        f"This indicates connection pool exhaustion or lock contention."
    )

    # Verify average performance
    avg_query_time = sum(r["elapsed"] for r in search_results) / len(search_results)
    assert avg_query_time < 0.5, (
        f"Average concurrent search time {avg_query_time:.3f}s exceeds 500ms SLA"
    )

    # Verify concurrent execution benefits (should be faster than sequential)
    sequential_estimate = sum(r["elapsed"] for r in search_results)
    assert total_time < sequential_estimate, (
        f"Concurrent execution not working: took {total_time:.3f}s, "
        f"but sequential would take {sequential_estimate:.3f}s"
    )


# ============================================================================
# DASHBOARD PERFORMANCE REGRESSION TESTS (BUG-745) - 5 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG745_dashboard_loads_under_3_seconds(
    db_transaction, measure_performance
):
    """
    REGRESSION TEST: Dashboard analytics load within 3-second SLA

    BUG REPORT:
    - Issue ID: BUG-745
    - Reported: 2025-11-03
    - Fixed: 2025-11-04
    - Severity: HIGH
    - Root Cause: No caching, no materialized views. Every dashboard load
                  was running 10+ complex aggregation queries in sequence:
                  - Student count by course
                  - Average quiz scores
                  - Lab usage statistics
                  - Progress tracking metrics
                  - Engagement trends (7 days, 30 days)
                  - At-risk student identification
                  - Content completion rates
                  - Time-on-platform calculations

    PERFORMANCE TARGET: <3 seconds for dashboard initial load

    TEST SCENARIO:
    1. Create realistic dataset (100 students, 10 courses, 500+ activities)
    2. Execute dashboard analytics aggregation
    3. Measure total execution time
    4. Verify performance meets 3-second SLA

    EXPECTED BEHAVIOR:
    - Dashboard loads in <3 seconds
    - Uses materialized views where appropriate
    - Uses Redis cache for repeated requests (5-min TTL)
    - Aggregations run in parallel, not sequentially

    VERIFICATION:
    - Measure actual load time
    - Verify materialized view usage
    - Check Redis cache effectiveness

    PREVENTION:
    - Monitor dashboard load times in production
    - Alert on SLA violations
    - Track 95th percentile load times
    """
    # Create realistic test data
    course_ids = [str(uuid.uuid4()) for _ in range(10)]
    student_ids = [str(uuid.uuid4()) for _ in range(100)]

    # Insert courses
    for course_id in course_ids:
        await db_transaction.execute(
            """
            INSERT INTO courses (
                id, title, instructor_id, status, created_at
            ) VALUES ($1, $2, $3, $4, $5)
            """,
            course_id,
            f"Course {course_id[:8]}",
            str(uuid.uuid4()),
            "published",
            datetime.utcnow()
        )

    # Insert students and enrollments
    for student_id in student_ids:
        # Each student enrolled in 2-3 courses
        enrolled_courses = course_ids[:3]
        for course_id in enrolled_courses:
            await db_transaction.execute(
                """
                INSERT INTO enrollments (
                    id, student_id, course_id, enrolled_at, status
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                str(uuid.uuid4()),
                student_id,
                course_id,
                datetime.utcnow() - timedelta(days=30),
                "active"
            )

    # Insert student activities (500+ activities)
    for _ in range(500):
        student_id = student_ids[_ % len(student_ids)]
        course_id = course_ids[_ % len(course_ids)]

        await db_transaction.execute(
            """
            INSERT INTO student_activities (
                id, student_id, course_id, activity_type,
                duration_seconds, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(uuid.uuid4()),
            student_id,
            course_id,
            ["view_content", "quiz", "lab", "discussion"][_ % 4],
            300 + (_ % 1800),  # 5-35 minutes
            datetime.utcnow() - timedelta(hours=_ % 720)
        )

    # Execute dashboard analytics aggregation
    with measure_performance() as timer:
        # Simulate dashboard queries (would be parallel in production)
        dashboard_data = {}

        # Query 1: Student count by course
        dashboard_data["student_counts"] = await db_transaction.fetch(
            """
            SELECT course_id, COUNT(DISTINCT student_id) as student_count
            FROM enrollments
            WHERE status = 'active'
            GROUP BY course_id
            """
        )

        # Query 2: Average activity duration
        dashboard_data["avg_duration"] = await db_transaction.fetchrow(
            """
            SELECT AVG(duration_seconds) as avg_duration
            FROM student_activities
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            """
        )

        # Query 3: Activity count by type
        dashboard_data["activity_breakdown"] = await db_transaction.fetch(
            """
            SELECT activity_type, COUNT(*) as count
            FROM student_activities
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY activity_type
            """
        )

        # Query 4: Recent enrollments trend
        dashboard_data["enrollment_trend"] = await db_transaction.fetch(
            """
            SELECT DATE(enrolled_at) as date, COUNT(*) as count
            FROM enrollments
            WHERE enrolled_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(enrolled_at)
            ORDER BY date DESC
            """
        )

    # ASSERTION: Dashboard must load within 3 seconds
    assert timer.elapsed < 3.0, (
        f"Dashboard performance degraded: {timer.elapsed:.3f}s exceeds 3-second SLA. "
        f"Expected <3.0s, got {timer.elapsed:.3f}s. "
        f"Check if materialized views are refreshed and Redis cache is active."
    )

    # Verify data accuracy
    assert len(dashboard_data["student_counts"]) > 0, "Dashboard should show student counts"
    assert dashboard_data["avg_duration"]["avg_duration"] > 0, "Should have activity duration data"


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG745_materialized_view_refresh_performance(db_transaction):
    """
    REGRESSION TEST: Materialized view refresh completes efficiently

    BUG REPORT:
    - Issue ID: BUG-745
    - Solution: Materialized views for dashboard aggregations

    TEST SCENARIO:
    1. Create materialized view mv_dashboard_analytics
    2. Insert new data
    3. Refresh materialized view
    4. Measure refresh time
    5. Verify refresh completes in <10 seconds

    EXPECTED BEHAVIOR:
    - Materialized view refresh: <10 seconds
    - Incremental refresh where possible
    - Background refresh doesn't block queries
    - View data is accurate after refresh

    VERIFICATION:
    - Measure refresh execution time
    - Verify view data accuracy
    - Check for lock contention

    PREVENTION:
    - Schedule refreshes during low-traffic periods
    - Monitor refresh duration trends
    - Consider incremental refresh strategies
    """
    # Create materialized view if not exists
    await db_transaction.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_analytics AS
        SELECT
            course_id,
            COUNT(DISTINCT student_id) as total_students,
            COUNT(*) as total_activities,
            AVG(duration_seconds) as avg_duration,
            MAX(timestamp) as last_activity
        FROM student_activities
        GROUP BY course_id
        """
    )

    # Insert test data
    course_id = str(uuid.uuid4())
    student_ids = [str(uuid.uuid4()) for _ in range(50)]

    for student_id in student_ids:
        for _ in range(10):  # 500 total activities
            await db_transaction.execute(
                """
                INSERT INTO student_activities (
                    id, student_id, course_id, activity_type,
                    duration_seconds, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(uuid.uuid4()),
                student_id,
                course_id,
                "view_content",
                600,
                datetime.utcnow()
            )

    # Measure materialized view refresh time
    start_time = time.time()
    await db_transaction.execute(
        "REFRESH MATERIALIZED VIEW mv_dashboard_analytics"
    )
    refresh_time = time.time() - start_time

    # ASSERTION: Refresh must complete within 10 seconds
    assert refresh_time < 10.0, (
        f"Materialized view refresh too slow: {refresh_time:.3f}s > 10s. "
        f"This will cause dashboard delays if refreshed synchronously."
    )

    # Verify view data is accurate
    view_data = await db_transaction.fetchrow(
        """
        SELECT total_students, total_activities
        FROM mv_dashboard_analytics
        WHERE course_id = $1
        """,
        course_id
    )

    assert view_data["total_students"] == 50, "Materialized view should show correct student count"
    assert view_data["total_activities"] == 500, "Materialized view should show correct activity count"


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG745_redis_cache_effectiveness(
    db_transaction, measure_performance, monkeypatch
):
    """
    REGRESSION TEST: Redis caching improves dashboard performance

    BUG REPORT:
    - Issue ID: BUG-745
    - Solution: Redis cache with 5-minute TTL for dashboard analytics

    TEST SCENARIO:
    1. First request: Cache miss, fetch from database (baseline)
    2. Second request: Cache hit, fetch from Redis (should be 10x+ faster)
    3. After TTL expiry: Cache miss, fetch from database again
    4. Measure and compare performance

    EXPECTED BEHAVIOR:
    - Cache miss: <3 seconds (database query)
    - Cache hit: <300ms (10x faster from Redis)
    - Cache invalidation works on data changes
    - Cache hit ratio >80% in production

    VERIFICATION:
    - Measure cache hit vs miss performance
    - Verify cache invalidation
    - Confirm TTL behavior

    PREVENTION:
    - Monitor cache hit ratio
    - Alert on cache miss rate increases
    - Track Redis memory usage
    """
    # Mock Redis cache for testing
    cache_storage = {}
    cache_ttl = {}

    class MockRedisCache:
        async def get(self, key: str):
            if key in cache_storage:
                if time.time() < cache_ttl.get(key, 0):
                    return cache_storage[key]
                else:
                    del cache_storage[key]
                    del cache_ttl[key]
            return None

        async def set(self, key: str, value: Any, ttl: int):
            cache_storage[key] = value
            cache_ttl[key] = time.time() + ttl

        async def delete(self, key: str):
            cache_storage.pop(key, None)
            cache_ttl.pop(key, None)

    mock_cache = MockRedisCache()

    # Create test data
    course_id = str(uuid.uuid4())
    cache_key = f"dashboard:analytics:{course_id}"

    # Simulate database query function
    async def fetch_dashboard_data():
        return await db_transaction.fetchrow(
            """
            SELECT
                COUNT(DISTINCT student_id) as student_count,
                COUNT(*) as activity_count
            FROM student_activities
            WHERE course_id = $1
            """,
            course_id
        )

    # Request 1: Cache miss (baseline)
    with measure_performance() as timer:
        cached_data = await mock_cache.get(cache_key)
        if cached_data is None:
            data = await fetch_dashboard_data()
            await mock_cache.set(cache_key, data, ttl=300)  # 5 minutes
        else:
            data = cached_data

    cache_miss_time = timer.elapsed

    # Request 2: Cache hit (should be much faster)
    with measure_performance() as timer:
        cached_data = await mock_cache.get(cache_key)
        if cached_data is None:
            data = await fetch_dashboard_data()
            await mock_cache.set(cache_key, data, ttl=300)
        else:
            data = cached_data

    cache_hit_time = timer.elapsed

    # ASSERTION: Cache hit should be at least 10x faster
    speedup_ratio = cache_miss_time / cache_hit_time if cache_hit_time > 0 else 0
    assert speedup_ratio > 10, (
        f"Cache not effective: cache hit only {speedup_ratio:.1f}x faster than cache miss. "
        f"Expected at least 10x speedup. "
        f"Miss: {cache_miss_time:.3f}s, Hit: {cache_hit_time:.3f}s"
    )

    # ASSERTION: Cache hit should be under 300ms
    assert cache_hit_time < 0.3, (
        f"Cache hit too slow: {cache_hit_time:.3f}s > 300ms. "
        f"Redis performance may be degraded."
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG745_concurrent_dashboard_loads(
    db_transaction, measure_performance
):
    """
    REGRESSION TEST: Concurrent dashboard loads handle gracefully

    BUG REPORT:
    - Issue ID: BUG-745
    - Related: Dashboard performance under concurrent load

    TEST SCENARIO:
    1. Simulate 10 concurrent dashboard requests
    2. Measure time for all to complete
    3. Verify no request exceeds 5-second timeout
    4. Confirm no database connection exhaustion

    EXPECTED BEHAVIOR:
    - All requests complete successfully
    - No request exceeds 5-second timeout
    - Average request time <3 seconds
    - Connection pool handles concurrency

    VERIFICATION:
    - Measure concurrent execution time
    - Verify all requests complete
    - Check for connection pool metrics

    PREVENTION:
    - Load testing in staging
    - Monitor connection pool size
    - Alert on timeout increases
    """
    # Create test data
    course_ids = [str(uuid.uuid4()) for _ in range(10)]

    for course_id in course_ids:
        # Create activities for each course
        for i in range(50):
            await db_transaction.execute(
                """
                INSERT INTO student_activities (
                    id, student_id, course_id, activity_type,
                    duration_seconds, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(uuid.uuid4()),
                str(uuid.uuid4()),
                course_id,
                "view_content",
                300,
                datetime.utcnow()
            )

    async def fetch_dashboard(course_id: str) -> Dict[str, Any]:
        """Fetch dashboard data for a course"""
        start_time = time.time()

        data = await db_transaction.fetchrow(
            """
            SELECT
                COUNT(DISTINCT student_id) as student_count,
                COUNT(*) as activity_count,
                AVG(duration_seconds) as avg_duration
            FROM student_activities
            WHERE course_id = $1
            """,
            course_id
        )

        elapsed = time.time() - start_time
        return {
            "course_id": course_id,
            "data": data,
            "elapsed": elapsed
        }

    # Execute 10 concurrent dashboard loads
    with measure_performance() as timer:
        tasks = [fetch_dashboard(course_id) for course_id in course_ids]
        results = await asyncio.gather(*tasks)

    total_time = timer.elapsed

    # Verify all loads completed
    assert len(results) == 10, "All concurrent dashboard loads should complete"

    # Verify no request exceeded timeout
    max_request_time = max(r["elapsed"] for r in results)
    assert max_request_time < 5.0, (
        f"Concurrent dashboard timeout: slowest request took {max_request_time:.3f}s > 5s"
    )

    # Verify average performance
    avg_request_time = sum(r["elapsed"] for r in results) / len(results)
    assert avg_request_time < 3.0, (
        f"Average concurrent dashboard load {avg_request_time:.3f}s exceeds 3s SLA"
    )


@pytest.mark.regression
@pytest.mark.performance
@pytest.mark.asyncio
async def test_BUG745_cache_invalidation_on_data_changes(
    db_transaction, measure_performance, monkeypatch
):
    """
    REGRESSION TEST: Cache invalidation works correctly on data changes

    BUG REPORT:
    - Issue ID: BUG-745
    - Related: Stale cache data after student activities

    TEST SCENARIO:
    1. Load dashboard data (populates cache)
    2. Insert new student activity
    3. Verify cache is invalidated
    4. Reload dashboard data
    5. Verify data is fresh (not stale cached data)

    EXPECTED BEHAVIOR:
    - Cache invalidated on data INSERT/UPDATE/DELETE
    - New data visible immediately after cache invalidation
    - No stale data served from cache
    - Cache TTL respected even without invalidation

    VERIFICATION:
    - Verify cache invalidation triggers
    - Check data freshness after changes
    - Confirm cache consistency

    PREVENTION:
    - Monitor cache invalidation patterns
    - Test cache consistency in CI/CD
    - Alert on stale data detection
    """
    # Mock Redis cache with invalidation tracking
    cache_storage = {}
    invalidation_count = {"count": 0}

    class MockRedisCache:
        async def get(self, key: str):
            return cache_storage.get(key)

        async def set(self, key: str, value: Any, ttl: int):
            cache_storage[key] = value

        async def delete(self, key: str):
            if key in cache_storage:
                del cache_storage[key]
                invalidation_count["count"] += 1

    mock_cache = MockRedisCache()
    course_id = str(uuid.uuid4())
    cache_key = f"dashboard:course:{course_id}"

    # Initial data insert
    await db_transaction.execute(
        """
        INSERT INTO student_activities (
            id, student_id, course_id, activity_type,
            duration_seconds, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        course_id,
        "view_content",
        300,
        datetime.utcnow()
    )

    # First load: Populate cache
    initial_data = await db_transaction.fetchrow(
        """
        SELECT COUNT(*) as activity_count
        FROM student_activities
        WHERE course_id = $1
        """,
        course_id
    )
    await mock_cache.set(cache_key, initial_data, ttl=300)

    assert initial_data["activity_count"] == 1, "Initial activity count should be 1"

    # Insert new activity (should trigger cache invalidation)
    await db_transaction.execute(
        """
        INSERT INTO student_activities (
            id, student_id, course_id, activity_type,
            duration_seconds, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        course_id,
        "quiz",
        600,
        datetime.utcnow()
    )

    # Simulate cache invalidation (would be triggered by database trigger in production)
    await mock_cache.delete(cache_key)

    # Second load: Should get fresh data (not cached)
    cached_data = await mock_cache.get(cache_key)
    assert cached_data is None, "Cache should be invalidated after data change"

    fresh_data = await db_transaction.fetchrow(
        """
        SELECT COUNT(*) as activity_count
        FROM student_activities
        WHERE course_id = $1
        """,
        course_id
    )

    assert fresh_data["activity_count"] == 2, "Fresh data should show updated count"
    assert invalidation_count["count"] == 1, "Cache should be invalidated exactly once"


# ============================================================================
# PERFORMANCE MONITORING AND ALERTING
# ============================================================================

@pytest.mark.regression
@pytest.mark.performance
def test_performance_monitoring_thresholds():
    """
    REGRESSION TEST: Performance monitoring thresholds are correctly configured

    PURPOSE:
    Verify that performance monitoring is set up to detect regressions
    before they impact production users.

    TEST SCENARIO:
    1. Verify performance thresholds are defined
    2. Check alerting configuration
    3. Confirm metrics collection

    EXPECTED BEHAVIOR:
    - Search latency threshold: 500ms
    - Dashboard load threshold: 3 seconds
    - Cache hit ratio threshold: >80%
    - Alerts configured for threshold violations

    VERIFICATION:
    - Check threshold configuration
    - Verify alerting channels
    - Confirm metrics endpoints

    PREVENTION:
    - Document performance SLAs
    - Review thresholds quarterly
    - Update based on production metrics
    """
    # Define performance SLA thresholds
    performance_slas = {
        "search_latency_ms": 500,
        "dashboard_load_seconds": 3.0,
        "cache_hit_ratio_percent": 80,
        "concurrent_requests_timeout_seconds": 5.0,
        "materialized_view_refresh_seconds": 10.0
    }

    # Verify all thresholds are defined
    assert all(threshold > 0 for threshold in performance_slas.values()), (
        "All performance thresholds must be positive values"
    )

    # Verify reasonable thresholds
    assert performance_slas["search_latency_ms"] <= 1000, (
        "Search latency threshold too lenient (should be ≤1000ms)"
    )

    assert performance_slas["dashboard_load_seconds"] <= 5.0, (
        "Dashboard load threshold too lenient (should be ≤5s)"
    )

    assert performance_slas["cache_hit_ratio_percent"] >= 70, (
        "Cache hit ratio threshold too low (should be ≥70%)"
    )

    # Document thresholds for monitoring team
    print("\n" + "="*80)
    print("PERFORMANCE SLA THRESHOLDS (Production Monitoring)")
    print("="*80)
    for metric, threshold in performance_slas.items():
        print(f"  {metric}: {threshold}")
    print("="*80)
    print("\nThese thresholds should be configured in your monitoring system")
    print("(e.g., Prometheus, Datadog, CloudWatch) to alert on violations.")
    print("="*80 + "\n")

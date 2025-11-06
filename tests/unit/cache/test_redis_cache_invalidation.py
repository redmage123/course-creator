"""
Redis Cache Invalidation Pattern Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis cache invalidation patterns ensuring data consistency
when underlying data changes. Critical for maintaining cache coherence across distributed
systems and ensuring users see fresh data after updates.

TECHNICAL IMPLEMENTATION:
- Tests pattern-based invalidation (wildcard matching)
- Validates cascade invalidation (related cache entries)
- Tests bulk invalidation operations
- Validates version-based invalidation strategies
- Tests invalidation for specific business entities (users, courses, organizations)

TDD APPROACH:
These tests validate that cache invalidation:
- Clears only the intended cache entries
- Maintains unrelated cache entries
- Handles invalidation failures gracefully
- Provides atomic invalidation operations
- Supports complex invalidation patterns

BUSINESS REQUIREMENTS:
1. User permission changes must invalidate all permission cache immediately
2. Course updates must invalidate all course-related cache entries
3. Student progress updates must invalidate analytics cache
4. Organization changes must cascade to all organization-related caches
5. Invalidation failures should not break application functionality
"""

import pytest
import json
from datetime import datetime
from uuid import uuid4
import asyncio
import sys
from pathlib import Path

# Add shared cache module to path
shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
sys.path.insert(0, str(shared_path))

try:
    from cache.redis_cache import RedisCacheManager
except ImportError:
    pytest.skip("Redis cache module not available", allow_module_level=True)


class TestUserCacheInvalidation:
    """
    Test Suite: User-Related Cache Invalidation

    BUSINESS REQUIREMENT:
    When user data changes (profile, permissions, roles), all cached user data
    must be invalidated to prevent stale data from being served.

    SECURITY CRITICAL:
    Permission cache invalidation is critical for security - users should not
    retain elevated permissions after they are revoked.
    """

    @pytest.mark.asyncio
    async def test_invalidate_all_user_cache_entries(self, redis_cache):
        """
        TEST: Invalidate all cache entries for a specific user

        BUSINESS REQUIREMENT:
        User profile update should clear all user-related cache

        VALIDATES:
        - All user cache keys are deleted
        - Other user cache remains intact
        - Returns correct count of deleted keys
        """
        user_id = str(uuid4())
        other_user_id = str(uuid4())

        # Cache multiple items for target user
        await redis_cache.set(f"user:{user_id}:profile", json.dumps({"name": "John"}))
        await redis_cache.set(f"user:{user_id}:preferences", json.dumps({"theme": "dark"}))
        await redis_cache.set(f"user:{user_id}:settings", json.dumps({"language": "en"}))

        # Cache items for other user
        await redis_cache.set(f"user:{other_user_id}:profile", json.dumps({"name": "Jane"}))

        # Invalidate all cache for target user
        pattern = f"user:{user_id}:*"
        deleted_keys = []
        async for key in redis_cache.scan_iter(match=pattern):
            deleted_keys.append(key)
            await redis_cache.delete(key)

        # Verify target user cache is cleared
        assert await redis_cache.get(f"user:{user_id}:profile") is None
        assert await redis_cache.get(f"user:{user_id}:preferences") is None
        assert await redis_cache.get(f"user:{user_id}:settings") is None

        # Verify other user cache remains
        assert await redis_cache.get(f"user:{other_user_id}:profile") is not None

        # Verify correct count
        assert len(deleted_keys) == 3

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_single_organization(self, redis_cache):
        """
        TEST: Invalidate user permissions for specific organization

        BUSINESS REQUIREMENT:
        When user role changes in one organization, only that organization's
        permission cache should be invalidated

        SECURITY CRITICAL:
        Permission changes must take effect immediately
        """
        user_id = str(uuid4())
        org1_id = str(uuid4())
        org2_id = str(uuid4())

        # Cache permissions for user in multiple organizations
        await redis_cache.set(
            f"rbac:permission:user_{user_id}_org_{org1_id}_read",
            json.dumps({"allowed": True})
        )
        await redis_cache.set(
            f"rbac:permission:user_{user_id}_org_{org1_id}_write",
            json.dumps({"allowed": False})
        )
        await redis_cache.set(
            f"rbac:permission:user_{user_id}_org_{org2_id}_read",
            json.dumps({"allowed": True})
        )

        # Invalidate permissions for org1 only
        pattern = f"rbac:permission:user_{user_id}_org_{org1_id}_*"
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)

        # Verify org1 permissions are cleared
        assert await redis_cache.get(f"rbac:permission:user_{user_id}_org_{org1_id}_read") is None
        assert await redis_cache.get(f"rbac:permission:user_{user_id}_org_{org1_id}_write") is None

        # Verify org2 permissions remain
        assert await redis_cache.get(f"rbac:permission:user_{user_id}_org_{org2_id}_read") is not None

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_all_organizations(self, redis_cache):
        """
        TEST: Invalidate all user permissions across all organizations

        BUSINESS REQUIREMENT:
        When user is deactivated or globally suspended, all permissions
        across all organizations must be invalidated

        SECURITY CRITICAL:
        Global permission revocation must be comprehensive
        """
        user_id = str(uuid4())
        org1_id = str(uuid4())
        org2_id = str(uuid4())
        org3_id = str(uuid4())

        # Cache permissions across multiple organizations
        for org_id in [org1_id, org2_id, org3_id]:
            await redis_cache.set(
                f"rbac:permission:user_{user_id}_org_{org_id}_read",
                json.dumps({"allowed": True})
            )
            await redis_cache.set(
                f"rbac:permission:user_{user_id}_org_{org_id}_write",
                json.dumps({"allowed": True})
            )

        # Invalidate all permissions for user
        pattern = f"rbac:permission:user_{user_id}_*"
        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        # Verify all permissions are cleared
        for org_id in [org1_id, org2_id, org3_id]:
            assert await redis_cache.get(f"rbac:permission:user_{user_id}_org_{org_id}_read") is None
            assert await redis_cache.get(f"rbac:permission:user_{user_id}_org_{org_id}_write") is None

        # Verify correct count (3 orgs × 2 permissions = 6)
        assert deleted_count == 6


class TestCourseCacheInvalidation:
    """
    Test Suite: Course-Related Cache Invalidation

    BUSINESS REQUIREMENT:
    Course modifications must invalidate all cached course data including
    content, analytics, and enrollment information.
    """

    @pytest.mark.asyncio
    async def test_invalidate_course_details_on_update(self, redis_cache):
        """
        TEST: Clear course details cache when course is updated

        BUSINESS REQUIREMENT:
        Course modifications must be reflected immediately in API responses

        VALIDATES:
        - Course details cache is cleared
        - New data can be cached after invalidation
        """
        course_id = str(uuid4())
        cache_key = f"course:{course_id}:details"

        # Cache original course data
        original_data = json.dumps({
            'title': 'Original Course Title',
            'description': 'Original description',
            'version': 1
        })
        await redis_cache.set(cache_key, original_data)

        # Verify cached
        assert await redis_cache.get(cache_key) is not None

        # Simulate course update - invalidate cache
        await redis_cache.delete(cache_key)

        # Verify cache is cleared
        assert await redis_cache.get(cache_key) is None

        # Cache updated data
        updated_data = json.dumps({
            'title': 'Updated Course Title',
            'description': 'Updated description',
            'version': 2
        })
        await redis_cache.set(cache_key, updated_data)

        # Verify new data is cached
        cached = await redis_cache.get(cache_key)
        cached_dict = json.loads(cached)
        assert cached_dict['title'] == 'Updated Course Title'
        assert cached_dict['version'] == 2

    @pytest.mark.asyncio
    async def test_cascade_invalidate_course_and_enrollment_cache(self, redis_cache):
        """
        TEST: Cascade invalidation when course is updated

        BUSINESS REQUIREMENT:
        Course changes should invalidate course details, enrollment data,
        and related analytics

        VALIDATES:
        - Multiple related cache entries are invalidated
        - Unrelated cache remains intact
        """
        course_id = str(uuid4())
        other_course_id = str(uuid4())

        # Cache multiple course-related items
        await redis_cache.set(f"course:{course_id}:details", json.dumps({"title": "Course A"}))
        await redis_cache.set(f"course:{course_id}:enrollment_count", "150")
        await redis_cache.set(f"course:{course_id}:analytics", json.dumps({"avg_score": 85.5}))
        await redis_cache.set(f"course:{course_id}:syllabus", json.dumps({"modules": 12}))

        # Cache items for other course
        await redis_cache.set(f"course:{other_course_id}:details", json.dumps({"title": "Course B"}))

        # Cascade invalidate all cache for target course
        pattern = f"course:{course_id}:*"
        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        # Verify all target course cache is cleared
        assert await redis_cache.get(f"course:{course_id}:details") is None
        assert await redis_cache.get(f"course:{course_id}:enrollment_count") is None
        assert await redis_cache.get(f"course:{course_id}:analytics") is None
        assert await redis_cache.get(f"course:{course_id}:syllabus") is None

        # Verify other course cache remains
        assert await redis_cache.get(f"course:{other_course_id}:details") is not None

        # Verify correct count
        assert deleted_count == 4

    @pytest.mark.asyncio
    async def test_invalidate_ai_generated_content_for_subject(self, redis_cache):
        """
        TEST: Invalidate all AI-generated content for a specific subject

        BUSINESS REQUIREMENT:
        When AI content generation templates are updated, all cached
        content for affected subjects should be invalidated

        VALIDATES:
        - Pattern-based invalidation works correctly
        - Subject-specific invalidation doesn't affect other subjects
        """
        subject = "Python Programming"
        other_subject = "JavaScript Basics"

        # Cache AI-generated content for target subject
        await redis_cache.set(
            f"course_gen:syllabus_generation:subject_{subject}:difficulty_beginner",
            json.dumps({"modules": 8})
        )
        await redis_cache.set(
            f"course_gen:quiz_generation:subject_{subject}:difficulty_intermediate",
            json.dumps({"questions": 20})
        )

        # Cache content for other subject
        await redis_cache.set(
            f"course_gen:syllabus_generation:subject_{other_subject}:difficulty_beginner",
            json.dumps({"modules": 6})
        )

        # Invalidate content for target subject (use wildcard pattern)
        pattern = f"course_gen:*:subject_{subject}:*"
        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        # Verify target subject content is cleared
        assert await redis_cache.get(f"course_gen:syllabus_generation:subject_{subject}:difficulty_beginner") is None
        assert await redis_cache.get(f"course_gen:quiz_generation:subject_{subject}:difficulty_intermediate") is None

        # Verify other subject content remains
        assert await redis_cache.get(f"course_gen:syllabus_generation:subject_{other_subject}:difficulty_beginner") is not None

        # Verify correct count
        assert deleted_count == 2


class TestStudentAnalyticsCacheInvalidation:
    """
    Test Suite: Student Analytics Cache Invalidation

    BUSINESS REQUIREMENT:
    Student activity updates must invalidate analytics cache to ensure
    dashboards and reports show current data.
    """

    @pytest.mark.asyncio
    async def test_invalidate_student_analytics_single_course(self, redis_cache):
        """
        TEST: Invalidate analytics for student in specific course

        BUSINESS REQUIREMENT:
        When student completes activities in a course, only that course's
        analytics should be invalidated

        VALIDATES:
        - Course-specific invalidation works
        - Analytics for other courses remain cached
        """
        student_id = str(uuid4())
        course1_id = str(uuid4())
        course2_id = str(uuid4())

        # Cache analytics for multiple courses
        await redis_cache.set(
            f"analytics:student_data:student_{student_id}_course_{course1_id}_progress",
            json.dumps({"completion": 75})
        )
        await redis_cache.set(
            f"analytics:engagement_score:student_{student_id}_course_{course1_id}_week",
            json.dumps({"score": 8.5})
        )
        await redis_cache.set(
            f"analytics:student_data:student_{student_id}_course_{course2_id}_progress",
            json.dumps({"completion": 50})
        )

        # Invalidate analytics for course1 only
        patterns = [
            f"analytics:student_data:student_{student_id}_course_{course1_id}_*",
            f"analytics:engagement_score:student_{student_id}_course_{course1_id}_*"
        ]

        deleted_count = 0
        for pattern in patterns:
            async for key in redis_cache.scan_iter(match=pattern):
                await redis_cache.delete(key)
                deleted_count += 1

        # Verify course1 analytics are cleared
        assert await redis_cache.get(f"analytics:student_data:student_{student_id}_course_{course1_id}_progress") is None
        assert await redis_cache.get(f"analytics:engagement_score:student_{student_id}_course_{course1_id}_week") is None

        # Verify course2 analytics remain
        assert await redis_cache.get(f"analytics:student_data:student_{student_id}_course_{course2_id}_progress") is not None

        # Verify correct count
        assert deleted_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_all_student_analytics(self, redis_cache):
        """
        TEST: Invalidate all analytics for a student across all courses

        BUSINESS REQUIREMENT:
        When student profile is recalculated or reset, all analytics
        across all courses must be invalidated

        VALIDATES:
        - Comprehensive invalidation across all courses
        - Correct count of invalidated entries
        """
        student_id = str(uuid4())
        course1_id = str(uuid4())
        course2_id = str(uuid4())
        course3_id = str(uuid4())

        # Cache analytics across multiple courses
        for course_id in [course1_id, course2_id, course3_id]:
            await redis_cache.set(
                f"analytics:student_data:student_{student_id}_course_{course_id}_progress",
                json.dumps({"completion": 60})
            )
            await redis_cache.set(
                f"analytics:engagement_score:student_{student_id}_course_{course_id}_week",
                json.dumps({"score": 7.5})
            )

        # Invalidate all analytics for student
        patterns = [
            f"analytics:student_data:student_{student_id}_*",
            f"analytics:engagement_score:student_{student_id}_*"
        ]

        deleted_count = 0
        for pattern in patterns:
            async for key in redis_cache.scan_iter(match=pattern):
                await redis_cache.delete(key)
                deleted_count += 1

        # Verify all analytics are cleared
        for course_id in [course1_id, course2_id, course3_id]:
            assert await redis_cache.get(f"analytics:student_data:student_{student_id}_course_{course_id}_progress") is None
            assert await redis_cache.get(f"analytics:engagement_score:student_{student_id}_course_{course_id}_week") is None

        # Verify correct count (3 courses × 2 metrics = 6)
        assert deleted_count == 6


class TestBulkInvalidation:
    """
    Test Suite: Bulk Cache Invalidation Operations

    BUSINESS REQUIREMENT:
    System must support bulk invalidation operations for efficiency
    when multiple related entities are updated.
    """

    @pytest.mark.asyncio
    async def test_bulk_invalidate_multiple_users(self, redis_cache):
        """
        TEST: Invalidate cache for multiple users efficiently

        BUSINESS REQUIREMENT:
        Bulk operations (e.g., organization role update) should efficiently
        invalidate cache for all affected users

        VALIDATES:
        - Multiple user invalidations work correctly
        - Efficient pattern matching
        """
        user_ids = [str(uuid4()) for _ in range(5)]

        # Cache data for all users
        for user_id in user_ids:
            await redis_cache.set(f"user:{user_id}:profile", json.dumps({"name": f"User {user_id}"}))
            await redis_cache.set(f"user:{user_id}:settings", json.dumps({"theme": "light"}))

        # Bulk invalidate all users
        total_deleted = 0
        for user_id in user_ids:
            pattern = f"user:{user_id}:*"
            async for key in redis_cache.scan_iter(match=pattern):
                await redis_cache.delete(key)
                total_deleted += 1

        # Verify all user cache is cleared
        for user_id in user_ids:
            assert await redis_cache.get(f"user:{user_id}:profile") is None
            assert await redis_cache.get(f"user:{user_id}:settings") is None

        # Verify correct count (5 users × 2 keys = 10)
        assert total_deleted == 10

    @pytest.mark.asyncio
    async def test_bulk_invalidate_organization_courses(self, redis_cache):
        """
        TEST: Invalidate all courses for an organization

        BUSINESS REQUIREMENT:
        Organization-wide updates should invalidate all related course cache

        VALIDATES:
        - Organization-scoped invalidation
        - Courses from other organizations remain cached
        """
        org_id = str(uuid4())
        other_org_id = str(uuid4())
        course_ids = [str(uuid4()) for _ in range(3)]
        other_course_id = str(uuid4())

        # Cache courses for target organization
        for course_id in course_ids:
            await redis_cache.set(
                f"course:{course_id}:org_{org_id}:details",
                json.dumps({"title": f"Course {course_id}"})
            )

        # Cache course for other organization
        await redis_cache.set(
            f"course:{other_course_id}:org_{other_org_id}:details",
            json.dumps({"title": "Other Course"})
        )

        # Invalidate all courses for target organization
        pattern = f"course:*:org_{org_id}:*"
        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        # Verify target organization courses are cleared
        for course_id in course_ids:
            assert await redis_cache.get(f"course:{course_id}:org_{org_id}:details") is None

        # Verify other organization course remains
        assert await redis_cache.get(f"course:{other_course_id}:org_{other_org_id}:details") is not None

        # Verify correct count
        assert deleted_count == 3


class TestVersionBasedInvalidation:
    """
    Test Suite: Version-Based Cache Invalidation

    BUSINESS REQUIREMENT:
    Support versioned cache keys to enable gradual rollout and A/B testing
    without full cache invalidation.
    """

    @pytest.mark.asyncio
    async def test_version_based_cache_key_invalidation(self, redis_cache):
        """
        TEST: Invalidate specific version of cached data

        BUSINESS REQUIREMENT:
        System should support multiple versions of cached data for
        A/B testing and gradual rollouts

        VALIDATES:
        - Version-specific invalidation
        - Other versions remain cached
        """
        course_id = str(uuid4())

        # Cache multiple versions
        await redis_cache.set(
            f"course:{course_id}:content:v1",
            json.dumps({"version": 1, "title": "Old Content"})
        )
        await redis_cache.set(
            f"course:{course_id}:content:v2",
            json.dumps({"version": 2, "title": "New Content"})
        )
        await redis_cache.set(
            f"course:{course_id}:content:v3",
            json.dumps({"version": 3, "title": "Latest Content"})
        )

        # Invalidate v1 only
        await redis_cache.delete(f"course:{course_id}:content:v1")

        # Verify v1 is cleared
        assert await redis_cache.get(f"course:{course_id}:content:v1") is None

        # Verify other versions remain
        assert await redis_cache.get(f"course:{course_id}:content:v2") is not None
        assert await redis_cache.get(f"course:{course_id}:content:v3") is not None

    @pytest.mark.asyncio
    async def test_invalidate_all_versions_for_entity(self, redis_cache):
        """
        TEST: Invalidate all versions of cached data for an entity

        BUSINESS REQUIREMENT:
        When entity is deleted, all versions should be removed

        VALIDATES:
        - Pattern-based version invalidation
        - Complete version cleanup
        """
        course_id = str(uuid4())

        # Cache multiple versions
        for version in range(1, 6):
            await redis_cache.set(
                f"course:{course_id}:content:v{version}",
                json.dumps({"version": version})
            )

        # Invalidate all versions
        pattern = f"course:{course_id}:content:v*"
        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        # Verify all versions are cleared
        for version in range(1, 6):
            assert await redis_cache.get(f"course:{course_id}:content:v{version}") is None

        # Verify correct count
        assert deleted_count == 5


class TestInvalidationErrorHandling:
    """
    Test Suite: Cache Invalidation Error Handling

    BUSINESS REQUIREMENT:
    Cache invalidation failures should not break application functionality.
    System must handle edge cases gracefully.
    """

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_pattern_returns_zero(self, redis_cache):
        """
        TEST: Invalidating non-existent pattern returns zero count

        VALIDATES:
        - No error is raised for non-existent patterns
        - Returns correct count (0)
        """
        pattern = f"nonexistent:pattern:{uuid4()}:*"

        deleted_count = 0
        async for key in redis_cache.scan_iter(match=pattern):
            await redis_cache.delete(key)
            deleted_count += 1

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_already_deleted_key_succeeds(self, redis_cache):
        """
        TEST: Deleting already-deleted key succeeds (idempotent)

        BUSINESS REQUIREMENT:
        Invalidation operations should be idempotent

        VALIDATES:
        - Deleting non-existent key doesn't raise error
        - Operation is idempotent
        """
        key = f"test:delete:{uuid4()}"

        # Set and delete
        await redis_cache.set(key, "value")
        result1 = await redis_cache.delete(key)
        assert result1 == 1

        # Delete again (already gone)
        result2 = await redis_cache.delete(key)
        assert result2 == 0  # Redis returns 0 for non-existent key deletion

    @pytest.mark.asyncio
    async def test_concurrent_invalidation_operations(self, redis_cache):
        """
        TEST: Concurrent invalidation operations don't conflict

        BUSINESS REQUIREMENT:
        Multiple services may invalidate cache concurrently

        VALIDATES:
        - Concurrent invalidations complete successfully
        - No race conditions or data corruption
        """
        user_id = str(uuid4())

        # Cache multiple items
        for i in range(10):
            await redis_cache.set(f"user:{user_id}:item_{i}", json.dumps({"data": i}))

        # Concurrent invalidation of same pattern
        async def invalidate_user_cache():
            pattern = f"user:{user_id}:*"
            async for key in redis_cache.scan_iter(match=pattern):
                await redis_cache.delete(key)

        # Run multiple invalidations concurrently
        await asyncio.gather(
            invalidate_user_cache(),
            invalidate_user_cache(),
            invalidate_user_cache()
        )

        # Verify all items are deleted (no errors occurred)
        for i in range(10):
            assert await redis_cache.get(f"user:{user_id}:item_{i}") is None

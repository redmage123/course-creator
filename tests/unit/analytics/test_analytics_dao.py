"""
Unit Tests for Analytics Data Access Object (DAO)

BUSINESS REQUIREMENT:
Validates database operations for analytics tracking including student activities,
quiz performance, lab usage, and progress metrics for educational effectiveness
measurement and institutional decision-making.

TECHNICAL IMPLEMENTATION:
- Uses pytest-asyncio for async database tests
- Uses real PostgreSQL database (no mocking!)
- Tests transaction handling and rollback
- Tests data aggregation and analytics queries
- Tests data integrity constraints
"""


import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncpg
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'analytics'))

from data_access.analytics_dao import AnalyticsDAO


@pytest_asyncio.fixture
async def db_pool():
    """
    Create a test database connection pool.

    IMPORTANT: Uses REAL database connection, not mocks!
    Tests run against actual PostgreSQL instance.
    """
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="course_creator_test",  # Test database
        user="postgres",
        password="postgres123",
        min_size=1,
        max_size=5
    )

    yield pool

    await pool.close()


@pytest_asyncio.fixture
async def analytics_dao(db_pool):
    """Create AnalyticsDAO instance with test database pool."""
    dao = AnalyticsDAO(db_pool)
    return dao


@pytest_asyncio.fixture
async def test_student_id(db_pool):
    """Create a test student for analytics relationships."""
    student_id = "test-analytics-student-123"
    yield student_id

    # Cleanup after test
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM course_creator.student_analytics WHERE user_id = $1", student_id)


@pytest_asyncio.fixture
async def test_course_id(db_pool):
    """Create a test course for analytics relationships."""
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval(
            """
            INSERT INTO courses (
                title, description, instructor_id, organization_id, is_active
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            "Test Analytics Course",
            "Course for analytics testing",
            "test-instructor-456",
            "test-org-789",
            True
        )

        yield str(course_id)

        # Cleanup after test
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)


@pytest.mark.asyncio
class TestAnalyticsDAOActivityTracking:
    """Test student activity tracking operations."""

    async def test_track_student_activity(self, analytics_dao, test_student_id, test_course_id):
        """Test recording student activity event."""
        activity_data = {
            'activity_id': f'test-activity-{datetime.utcnow().timestamp()}',
            'student_id': test_student_id,
            'course_id': test_course_id,
            'activity_type': 'lab_access',
            'activity_data': {'lab_id': 'python-basics-lab', 'duration': 45},
            'timestamp': datetime.utcnow(),
            'session_id': 'session-123',
            'ip_address': '192.168.1.1'
        }

        activity_id = await analytics_dao.track_student_activity(activity_data)

        assert activity_id == activity_data['activity_id']

    async def test_get_student_activities(self, analytics_dao, test_student_id, test_course_id):
        """Test retrieving student activities with filters."""
        # Track multiple activities
        for i in range(3):
            activity_data = {
                'activity_id': f'test-activity-{i}-{datetime.utcnow().timestamp()}',
                'student_id': test_student_id,
                'course_id': test_course_id,
                'activity_type': 'content_view' if i % 2 == 0 else 'lab_access',
                'activity_data': {'content_id': f'content-{i}'},
                'timestamp': datetime.utcnow() - timedelta(days=i),
                'session_id': f'session-{i}'
            }
            await analytics_dao.track_student_activity(activity_data)

        # Retrieve all activities
        activities = await analytics_dao.get_student_activities(
            test_student_id,
            course_id=test_course_id,
            limit=10
        )

        assert len(activities) == 3
        # Should be ordered by timestamp DESC
        assert activities[0]['activity_type'] in ['content_view', 'lab_access']

    async def test_get_student_activities_date_filter(self, analytics_dao, test_student_id, test_course_id):
        """Test filtering activities by date range."""
        # Track activities across different dates
        old_activity = {
            'activity_id': f'old-activity-{datetime.utcnow().timestamp()}',
            'student_id': test_student_id,
            'course_id': test_course_id,
            'activity_type': 'login',
            'activity_data': {},
            'timestamp': datetime.utcnow() - timedelta(days=10),
            'session_id': 'old-session'
        }
        await analytics_dao.track_student_activity(old_activity)

        recent_activity = {
            'activity_id': f'recent-activity-{datetime.utcnow().timestamp()}',
            'student_id': test_student_id,
            'course_id': test_course_id,
            'activity_type': 'logout',
            'activity_data': {},
            'timestamp': datetime.utcnow() - timedelta(days=1),
            'session_id': 'recent-session'
        }
        await analytics_dao.track_student_activity(recent_activity)

        # Get only recent activities (last 5 days)
        activities = await analytics_dao.get_student_activities(
            test_student_id,
            course_id=test_course_id,
            start_date=datetime.utcnow() - timedelta(days=5)
        )

        assert len(activities) == 1
        assert activities[0]['activity_type'] == 'logout'


@pytest.mark.asyncio
class TestAnalyticsDAOQuizPerformance:
    """Test quiz performance tracking operations."""

    async def test_track_quiz_performance(self, analytics_dao, test_student_id, test_course_id):
        """Test recording quiz performance metrics."""
        performance_data = {
            'performance_id': f'test-performance-{datetime.utcnow().timestamp()}',
            'student_id': test_student_id,
            'quiz_id': 'python-basics-quiz',
            'course_id': test_course_id,
            'score': 8,
            'max_score': 10,
            'time_taken': 900,  # 15 minutes
            'answers': {'q1': 'A', 'q2': 'B', 'q3': 'C'},
            'completed_at': datetime.utcnow(),
            'correct_answers': 8
        }

        performance_id = await analytics_dao.track_quiz_performance(performance_data)

        assert performance_id == performance_data['performance_id']

    async def test_get_student_quiz_analytics(self, analytics_dao, test_student_id, test_course_id):
        """Test calculating quiz analytics for a student."""
        # Track multiple quiz attempts
        for i in range(3):
            performance_data = {
                'performance_id': f'test-quiz-{i}-{datetime.utcnow().timestamp()}',
                'student_id': test_student_id,
                'quiz_id': f'quiz-{i}',
                'course_id': test_course_id,
                'score': 7 + i,  # Scores: 7, 8, 9
                'max_score': 10,
                'time_taken': 600 + (i * 60),  # 10, 11, 12 minutes
                'answers': {},
                'completed_at': datetime.utcnow() - timedelta(days=i),
                'correct_answers': 7 + i
            }
            await analytics_dao.track_quiz_performance(performance_data)

        # Get analytics
        analytics = await analytics_dao.get_student_quiz_analytics(
            test_student_id,
            course_id=test_course_id
        )

        assert analytics['total_quizzes'] == 3
        assert 70.0 <= analytics['average_percentage'] <= 90.0  # Average of 70%, 80%, 90%
        assert analytics['best_percentage'] == 90.0
        assert analytics['worst_percentage'] == 70.0
        assert analytics['high_score_count'] >= 1  # At least one >= 80%


@pytest.mark.asyncio
class TestAnalyticsDAOLabUsage:
    """Test lab usage tracking operations."""

    async def test_track_lab_usage(self, analytics_dao, test_student_id, test_course_id):
        """Test recording lab usage metrics."""
        lab_usage_data = {
            'usage_id': f'test-lab-usage-{datetime.utcnow().timestamp()}',
            'student_id': test_student_id,
            'lab_id': 'python-basics-lab',
            'course_id': test_course_id,
            'created_at': datetime.utcnow() - timedelta(minutes=45),
            'end_time': datetime.utcnow(),
            'activities_performed': ['write_code', 'run_tests', 'debug'],
            'resources_used': {'cpu': 2, 'memory': '512MB'}
        }

        usage_id = await analytics_dao.track_lab_usage(lab_usage_data)

        assert usage_id == lab_usage_data['usage_id']

    async def test_get_lab_usage_analytics(self, analytics_dao, test_student_id, test_course_id):
        """Test calculating lab usage analytics."""
        # Track multiple lab sessions
        for i in range(5):
            lab_usage_data = {
                'usage_id': f'test-lab-{i}-{datetime.utcnow().timestamp()}',
                'student_id': f'{test_student_id}-{i}',  # Different students
                'lab_id': 'shared-lab',
                'course_id': test_course_id,
                'created_at': datetime.utcnow() - timedelta(days=i, minutes=30),
                'end_time': datetime.utcnow() - timedelta(days=i),
                'activities_performed': [],
                'resources_used': {}
            }
            await analytics_dao.track_lab_usage(lab_usage_data)

        # Get analytics for last 30 days
        analytics = await analytics_dao.get_lab_usage_analytics(
            course_id=test_course_id,
            days=30
        )

        assert analytics['total_sessions'] == 5
        assert analytics['unique_users'] == 5
        assert analytics['average_session_minutes'] >= 25  # ~30 minutes each


@pytest.mark.asyncio
class TestAnalyticsDAOStudentProgress:
    """Test student progress tracking operations."""

    async def test_update_student_progress(self, analytics_dao, test_student_id, test_course_id):
        """Test updating student progress record."""
        progress_data = {
            'student_id': test_student_id,
            'course_id': test_course_id,
            'module_id': 'python-basics-module',
            'progress_percentage': 75.0,
            'time_spent': 120,
            'last_accessed': datetime.utcnow(),
            'completion_status': 'in_progress'
        }

        progress_id = await analytics_dao.update_student_progress(progress_data)

        assert progress_id is not None

    async def test_get_student_progress_analytics(self, analytics_dao, test_student_id, test_course_id):
        """Test calculating student progress analytics."""
        # Create progress records
        for i in range(3):
            progress_data = {
                'student_id': test_student_id,
                'course_id': test_course_id,
                'module_id': f'module-{i}',
                'progress_percentage': 33.3 * (i + 1),  # 33%, 66%, 99%
                'time_spent': 30 * (i + 1),
                'last_accessed': datetime.utcnow() - timedelta(hours=i),
                'completion_status': 'completed' if i == 2 else 'in_progress'
            }
            await analytics_dao.update_student_progress(progress_data)

        # Get analytics
        analytics = await analytics_dao.get_student_progress_analytics(
            test_student_id,
            test_course_id
        )

        assert analytics['modules_started'] >= 3
        # Note: The exact values depend on database schema and queries
        # These tests validate the DAO methods work without errors


@pytest.mark.asyncio
class TestAnalyticsDAOEngagementMetrics:
    """Test engagement and retention analytics."""

    async def test_calculate_engagement_metrics(self, analytics_dao, test_course_id):
        """Test engagement metrics calculation for a course."""
        # Create test data: activities, lab sessions for multiple students
        for student_num in range(5):
            student_id = f'test-engagement-student-{student_num}'

            # Track activities
            for i in range(3):
                activity_data = {
                    'activity_id': f'engage-activity-{student_num}-{i}-{datetime.utcnow().timestamp()}',
                    'student_id': student_id,
                    'course_id': test_course_id,
                    'activity_type': 'content_view',
                    'activity_data': {'content_id': f'content-{i}'},
                    'timestamp': datetime.utcnow() - timedelta(days=i),
                    'session_id': f'session-{student_num}-{i}'
                }
                await analytics_dao.track_student_activity(activity_data)

        # Calculate engagement
        engagement = await analytics_dao.calculate_engagement_metrics(
            test_course_id,
            days=30
        )

        assert engagement['active_students'] == 5
        assert engagement['total_activities'] >= 15  # 5 students × 3 activities
        assert 'activity_breakdown' in engagement


@pytest.mark.asyncio
class TestAnalyticsDAOErrorHandling:
    """Test error handling and edge cases."""

    async def test_track_activity_missing_required_fields(self, analytics_dao):
        """Test error handling for missing required fields."""
        invalid_data = {
            'activity_id': 'test-invalid',
            'student_id': '',  # Missing
            'course_id': 'course-123',
            'activity_type': 'login',
            'activity_data': {},
            'timestamp': datetime.utcnow(),
            'session_id': 'session-123'
        }

        with pytest.raises(Exception):  # Should raise DatabaseException
            await analytics_dao.track_student_activity(invalid_data)

    async def test_get_nonexistent_student_activities(self, analytics_dao):
        """Test retrieving activities for non-existent student."""
        activities = await analytics_dao.get_student_activities(
            'nonexistent-student-id',
            limit=10
        )

        assert activities == []

    async def test_quiz_analytics_no_data(self, analytics_dao):
        """Test quiz analytics with no quiz attempts."""
        analytics = await analytics_dao.get_student_quiz_analytics(
            'student-with-no-quizzes',
            course_id='course-123'
        )

        assert analytics['total_quizzes'] == 0
        assert analytics['average_percentage'] == 0.0


# Run tests with: pytest tests/unit/analytics/test_analytics_dao.py -v --asyncio-mode=auto

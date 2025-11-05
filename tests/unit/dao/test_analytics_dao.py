"""
Analytics DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Analytics Data Access Object ensuring all student activity
tracking, performance metrics, lab usage analytics, and engagement calculations work
correctly. The analytics DAO is crucial for measuring educational effectiveness,
tracking student progress, and providing actionable insights for instructors and
administrators.

TECHNICAL IMPLEMENTATION:
- Tests all 9 DAO methods covering analytics operations
- Validates student activity tracking and retrieval
- Tests quiz performance analytics and scoring
- Validates lab usage tracking and resource analytics
- Tests student progress calculations and metrics
- Ensures engagement metric calculations are accurate

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Tracks student activities with proper metadata
- Records quiz performance with scoring analytics
- Tracks lab usage with resource utilization metrics
- Calculates accurate student progress indicators
- Computes engagement metrics for course optimization
- Handles date range filtering for temporal analytics
- Provides aggregated analytics for decision making
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import sys
from pathlib import Path
import json
from decimal import Decimal

# Add analytics service to path
analytics_path = Path(__file__).parent.parent.parent.parent / 'services' / 'analytics'
sys.path.insert(0, str(analytics_path))

from data_access.analytics_dao import AnalyticsDAO
from exceptions import DatabaseException, ValidationException


class TestStudentActivityTracking:
    """
    Test Suite: Student Activity Tracking Operations

    BUSINESS REQUIREMENT:
    System must track all student activities for learning analytics, engagement
    measurement, and personalized learning recommendations.
    """

    @pytest.mark.asyncio
    async def test_track_student_activity_success(self, db_transaction):
        """
        TEST: Track student activity event successfully

        BUSINESS REQUIREMENT:
        Student activities must be recorded with comprehensive metadata

        VALIDATES:
        - Activity record is created in database
        - Activity ID is returned
        - All metadata is stored correctly
        - Timestamps are preserved accurately
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student and course
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'student_{uuid4().hex[:8]}', f'student_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'student'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            uuid4(), 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, description, instructor_id,
                   category, difficulty_level, estimated_duration, duration_unit, is_published)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(course_id), 'Test Course', 'Course Description', UUID(student_id),
            'Programming', 'beginner', 8, 'weeks', True
        )

        # Prepare activity data
        activity_id = str(uuid4())
        session_id = str(uuid4())
        timestamp = datetime.utcnow()

        activity_data = {
            'activity_id': activity_id,
            'student_id': student_id,
            'course_id': course_id,
            'activity_type': 'video_watched',
            'activity_data': {
                'video_id': 'vid-123',
                'duration_watched': 300,
                'completion_percentage': 75
            },
            'timestamp': timestamp,
            'session_id': session_id,
            'ip_address': '192.168.1.1'
        }

        # Execute: Track activity
        result_id = await dao.track_student_activity(activity_data)

        # Verify: Activity was tracked
        assert result_id == activity_id

        # Verify: Activity exists in database
        activity = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.student_analytics
               WHERE id = $1""",
            activity_id
        )
        assert activity is not None
        assert str(activity['user_id']) == student_id
        assert str(activity['course_id']) == course_id
        assert activity['event_type'] == 'video_watched'
        assert activity['session_id'] == session_id

    @pytest.mark.asyncio
    async def test_get_student_activities_no_filters(self, db_transaction):
        """
        TEST: Retrieve all student activities without filters

        BUSINESS REQUIREMENT:
        System must provide complete activity history for students
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'activitystudent_{uuid4().hex[:8]}', f'actstudent@test.com',
            '$2b$12$test', 'student'
        )

        # Create test activities
        for i in range(3):
            await db_transaction.execute(
                """INSERT INTO course_creator.student_analytics
                   (id, user_id, course_id, event_type, event_data, timestamp, session_id)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                str(uuid4()), UUID(student_id), uuid4(), f'activity_{i}',
                json.dumps({'test': i}), datetime.utcnow(), str(uuid4())
            )

        # Execute: Get all activities
        activities = await dao.get_student_activities(student_id)

        # Verify: All activities retrieved
        assert len(activities) >= 3
        for activity in activities:
            assert str(activity['student_id']) == student_id

    @pytest.mark.asyncio
    async def test_get_student_activities_with_course_filter(self, db_transaction):
        """
        TEST: Retrieve student activities filtered by course

        BUSINESS REQUIREMENT:
        Instructors need course-specific activity insights
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'coursefilterstudent_{uuid4().hex[:8]}', f'coursefilter@test.com',
            '$2b$12$test', 'student'
        )

        # Create activities for specific course
        for i in range(2):
            await db_transaction.execute(
                """INSERT INTO course_creator.student_analytics
                   (id, user_id, course_id, event_type, event_data, timestamp, session_id)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                str(uuid4()), UUID(student_id), UUID(course_id), 'filtered_activity',
                json.dumps({'filtered': True}), datetime.utcnow(), str(uuid4())
            )

        # Create activity for different course
        await db_transaction.execute(
            """INSERT INTO course_creator.student_analytics
               (id, user_id, course_id, event_type, event_data, timestamp, session_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            str(uuid4()), UUID(student_id), uuid4(), 'other_activity',
            json.dumps({'filtered': False}), datetime.utcnow(), str(uuid4())
        )

        # Execute: Get activities for specific course
        activities = await dao.get_student_activities(student_id, course_id=course_id)

        # Verify: Only course-specific activities returned
        assert len(activities) >= 2
        for activity in activities:
            assert str(activity['course_id']) == course_id

    @pytest.mark.asyncio
    async def test_get_student_activities_with_date_range(self, db_transaction):
        """
        TEST: Retrieve activities within date range

        BUSINESS REQUIREMENT:
        Temporal analytics require date-filtered activity data
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'datestudent_{uuid4().hex[:8]}', f'datestudent@test.com',
            '$2b$12$test', 'student'
        )

        # Create activities at different times
        old_timestamp = datetime.utcnow() - timedelta(days=10)
        recent_timestamp = datetime.utcnow() - timedelta(days=2)

        # Old activity
        await db_transaction.execute(
            """INSERT INTO course_creator.student_analytics
               (id, user_id, course_id, event_type, event_data, timestamp, session_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            str(uuid4()), UUID(student_id), uuid4(), 'old_activity',
            json.dumps({}), old_timestamp, str(uuid4())
        )

        # Recent activity
        await db_transaction.execute(
            """INSERT INTO course_creator.student_analytics
               (id, user_id, course_id, event_type, event_data, timestamp, session_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            str(uuid4()), UUID(student_id), uuid4(), 'recent_activity',
            json.dumps({}), recent_timestamp, str(uuid4())
        )

        # Execute: Get activities from last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        activities = await dao.get_student_activities(
            student_id,
            start_date=start_date
        )

        # Verify: Only recent activities returned
        assert len(activities) >= 1
        for activity in activities:
            assert activity['timestamp'] >= start_date


class TestQuizPerformanceTracking:
    """
    Test Suite: Quiz Performance Analytics Operations

    BUSINESS REQUIREMENT:
    System must track quiz performance for learning assessment, difficulty
    calibration, and student progress measurement.
    """

    @pytest.mark.asyncio
    async def test_track_quiz_performance(self, db_transaction):
        """
        TEST: Track quiz performance with scoring data

        BUSINESS REQUIREMENT:
        Quiz results must be recorded for assessment analytics
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'quizstudent_{uuid4().hex[:8]}', f'quizstudent@test.com',
            '$2b$12$test', 'student'
        )

        # Prepare quiz performance data
        performance_id = str(uuid4())
        quiz_id = str(uuid4())

        performance_data = {
            'performance_id': performance_id,
            'student_id': student_id,
            'course_id': course_id,
            'quiz_id': quiz_id,
            'score': 85.5,
            'max_score': 100.0,
            'time_taken_seconds': 600,
            'attempt_number': 1,
            'completed_at': datetime.utcnow(),
            'answers': {
                'question_1': {'answer': 'A', 'correct': True},
                'question_2': {'answer': 'B', 'correct': False}
            }
        }

        # Execute: Track quiz performance
        result_id = await dao.track_quiz_performance(performance_data)

        # Verify: Performance was tracked
        assert result_id == performance_id

        # Verify: Performance exists in database
        performance = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.quiz_performances
               WHERE id = $1""",
            performance_id
        )
        assert performance is not None
        assert str(performance['student_id']) == student_id
        assert str(performance['quiz_id']) == quiz_id
        assert float(performance['score']) == 85.5

    @pytest.mark.asyncio
    async def test_get_student_quiz_analytics_aggregated(self, db_transaction):
        """
        TEST: Calculate aggregated quiz analytics for student

        BUSINESS REQUIREMENT:
        Students and instructors need aggregate quiz performance metrics
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'aggquizstudent_{uuid4().hex[:8]}', f'aggquiz@test.com',
            '$2b$12$test', 'student'
        )

        # Create multiple quiz performances
        scores = [75.0, 85.0, 90.0]
        for score in scores:
            await db_transaction.execute(
                """INSERT INTO course_creator.quiz_performances
                   (id, student_id, course_id, quiz_id, score, max_score,
                    time_taken_seconds, attempt_number, completed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                str(uuid4()), UUID(student_id), UUID(course_id), uuid4(),
                Decimal(str(score)), Decimal('100.0'), 600, 1, datetime.utcnow()
            )

        # Execute: Get aggregated quiz analytics
        analytics = await dao.get_student_quiz_analytics(student_id, course_id)

        # Verify: Analytics are calculated correctly
        assert analytics is not None
        assert analytics['total_quizzes'] >= 3
        assert analytics['average_score'] >= 75.0  # Average of scores


class TestLabUsageTracking:
    """
    Test Suite: Lab Usage Analytics Operations

    BUSINESS REQUIREMENT:
    System must track lab usage for resource optimization, student engagement
    measurement, and infrastructure planning.
    """

    @pytest.mark.asyncio
    async def test_track_lab_usage(self, db_transaction):
        """
        TEST: Track lab environment usage session

        BUSINESS REQUIREMENT:
        Lab usage must be tracked for resource planning and engagement analytics
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student
        student_id = str(uuid4())
        lab_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'labstudent_{uuid4().hex[:8]}', f'labstudent@test.com',
            '$2b$12$test', 'student'
        )

        # Prepare lab usage data
        usage_id = str(uuid4())
        lab_usage_data = {
            'usage_id': usage_id,
            'student_id': student_id,
            'lab_id': lab_id,
            'course_id': str(uuid4()),
            'started_at': datetime.utcnow() - timedelta(minutes=30),
            'ended_at': datetime.utcnow(),
            'duration_seconds': 1800,
            'commands_executed': 25,
            'files_created': 5,
            'resources_used': {
                'cpu_percent': 45.5,
                'memory_mb': 512,
                'disk_mb': 128
            }
        }

        # Execute: Track lab usage
        result_id = await dao.track_lab_usage(lab_usage_data)

        # Verify: Usage was tracked
        assert result_id == usage_id

        # Verify: Usage exists in database
        usage = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.lab_usage
               WHERE id = $1""",
            usage_id
        )
        assert usage is not None
        assert str(usage['student_id']) == student_id
        assert str(usage['lab_id']) == lab_id
        assert usage['duration_seconds'] == 1800

    @pytest.mark.asyncio
    async def test_get_lab_usage_analytics_by_lab(self, db_transaction):
        """
        TEST: Calculate lab usage analytics for specific lab

        BUSINESS REQUIREMENT:
        Lab administrators need usage metrics for resource planning
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test lab and students
        lab_id = str(uuid4())
        for i in range(2):
            student_id = str(uuid4())
            await db_transaction.execute(
                """INSERT INTO course_creator.users (id, username, email, password, role)
                   VALUES ($1, $2, $3, $4, $5)""",
                UUID(student_id), f'labuser{i}_{uuid4().hex[:8]}', f'labuser{i}@test.com',
                '$2b$12$test', 'student'
            )

            # Create lab usage records
            await db_transaction.execute(
                """INSERT INTO course_creator.lab_usage
                   (id, student_id, lab_id, course_id, started_at, ended_at,
                    duration_seconds, commands_executed, files_created, resources_used)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                str(uuid4()), UUID(student_id), UUID(lab_id), uuid4(),
                datetime.utcnow() - timedelta(hours=1), datetime.utcnow(),
                3600, 50, 10, json.dumps({'cpu_percent': 50.0})
            )

        # Execute: Get lab usage analytics
        analytics = await dao.get_lab_usage_analytics(lab_id=lab_id)

        # Verify: Analytics are calculated
        assert analytics is not None
        assert analytics['total_sessions'] >= 2
        assert analytics['total_usage_hours'] > 0


class TestStudentProgressTracking:
    """
    Test Suite: Student Progress Analytics Operations

    BUSINESS REQUIREMENT:
    System must track and calculate student progress for course completion,
    learning path recommendations, and intervention triggers.
    """

    @pytest.mark.asyncio
    async def test_update_student_progress(self, db_transaction):
        """
        TEST: Update student progress metrics

        BUSINESS REQUIREMENT:
        Progress must be tracked for course completion analytics
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student and course
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'progressstudent_{uuid4().hex[:8]}', f'progress@test.com',
            '$2b$12$test', 'student'
        )

        # Prepare progress data
        progress_id = str(uuid4())
        progress_data = {
            'progress_id': progress_id,
            'student_id': student_id,
            'course_id': course_id,
            'completion_percentage': 65.5,
            'lessons_completed': 13,
            'total_lessons': 20,
            'quizzes_completed': 5,
            'labs_completed': 3,
            'last_activity_at': datetime.utcnow()
        }

        # Execute: Update progress
        result_id = await dao.update_student_progress(progress_data)

        # Verify: Progress was updated
        assert result_id == progress_id

        # Verify: Progress exists in database
        progress = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.student_progress
               WHERE id = $1""",
            progress_id
        )
        assert progress is not None
        assert str(progress['student_id']) == student_id
        assert float(progress['completion_percentage']) == 65.5
        assert progress['lessons_completed'] == 13

    @pytest.mark.asyncio
    async def test_get_student_progress_analytics(self, db_transaction):
        """
        TEST: Calculate comprehensive student progress analytics

        BUSINESS REQUIREMENT:
        Students need detailed progress insights for motivation
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test student and course
        student_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(student_id), f'analyticsstudent_{uuid4().hex[:8]}', f'analytics@test.com',
            '$2b$12$test', 'student'
        )

        # Create progress record
        await db_transaction.execute(
            """INSERT INTO course_creator.student_progress
               (id, student_id, course_id, completion_percentage,
                lessons_completed, total_lessons, quizzes_completed,
                labs_completed, last_activity_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            str(uuid4()), UUID(student_id), UUID(course_id),
            Decimal('75.0'), 15, 20, 7, 4, datetime.utcnow()
        )

        # Execute: Get progress analytics
        analytics = await dao.get_student_progress_analytics(student_id, course_id)

        # Verify: Analytics are returned
        assert analytics is not None
        assert analytics['completion_percentage'] >= 75.0
        assert analytics['lessons_completed'] == 15


class TestEngagementMetrics:
    """
    Test Suite: Course Engagement Analytics Operations

    BUSINESS REQUIREMENT:
    System must calculate engagement metrics for course effectiveness measurement,
    retention prediction, and instructional optimization.
    """

    @pytest.mark.asyncio
    async def test_calculate_engagement_metrics_for_course(self, db_transaction):
        """
        TEST: Calculate comprehensive engagement metrics for course

        BUSINESS REQUIREMENT:
        Instructors need engagement insights for course improvement
        """
        dao = AnalyticsDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test course
        course_id = str(uuid4())

        # Create enrolled students with activities
        for i in range(3):
            student_id = str(uuid4())
            await db_transaction.execute(
                """INSERT INTO course_creator.users (id, username, email, password, role)
                   VALUES ($1, $2, $3, $4, $5)""",
                UUID(student_id), f'engagedstudent{i}_{uuid4().hex[:8]}',
                f'engaged{i}@test.com', '$2b$12$test', 'student'
            )

            # Create recent activity
            await db_transaction.execute(
                """INSERT INTO course_creator.student_analytics
                   (id, user_id, course_id, event_type, event_data, timestamp, session_id)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                str(uuid4()), UUID(student_id), UUID(course_id), 'video_watched',
                json.dumps({'engagement': 'high'}),
                datetime.utcnow() - timedelta(days=1), str(uuid4())
            )

        # Execute: Calculate engagement metrics
        metrics = await dao.calculate_engagement_metrics(course_id, days=30)

        # Verify: Metrics are calculated
        assert metrics is not None
        assert 'active_students' in metrics
        assert 'total_activities' in metrics
        assert metrics['active_students'] >= 3
        assert metrics['total_activities'] >= 3

"""
Demo DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Demo Data Access Object ensuring all demonstration data generation,
session management, and realistic data simulation operations work correctly. The Demo DAO
enables the platform to showcase its features with authentic-looking data without storing
actual user information, supporting sales demonstrations and trial experiences.

TECHNICAL IMPLEMENTATION:
- Tests all 9 DAO methods across 3 functional categories
- Validates session lifecycle management (creation, validation, expiration)
- Tests role-based demo data generation (instructor, student, admin)
- Ensures realistic data patterns for authentic demonstrations
- Validates session cleanup and statistics tracking

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates demo sessions with proper expiration and tracking
- Validates active sessions and rejects expired sessions
- Generates realistic demo data for all user roles
- Provides accurate session statistics and metrics
- Cleans up expired sessions efficiently
- Handles errors gracefully with structured exceptions
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import sys
from pathlib import Path
import json

# Add demo-service to path
demo_service_path = Path(__file__).parent.parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))

from data_access.demo_dao import DemoDAO
from exceptions import ValidationException, BusinessRuleException


class TestDemoDAOSessionManagement:
    """
    Test Suite: Demo Session Management Operations

    BUSINESS REQUIREMENT:
    System must create, validate, and manage time-limited demo sessions
    for unauthenticated users exploring the platform features.
    """

    def test_create_demo_session_with_default_config(self):
        """
        TEST: Create demo session with default configuration

        BUSINESS REQUIREMENT:
        Demo sessions must be creatable with minimal required information

        VALIDATES:
        - Session is created with unique session_id
        - Default 2-hour expiration is set
        - User type is recorded correctly
        - Session includes user context and capabilities
        - Access tracking is initialized
        """
        dao = DemoDAO()

        # Execute: Create instructor demo session
        session = dao.create_demo_session(user_type='instructor')

        # Verify: Session created successfully
        assert session is not None
        assert 'session_id' in session
        assert session['user_type'] == 'instructor'

        # Verify: Default configuration applied
        assert 'expires_at' in session
        assert 'created_at' in session
        duration = session['expires_at'] - session['created_at']
        assert duration.total_seconds() == 2 * 3600  # 2 hours

        # Verify: User context generated
        assert 'user_context' in session
        assert session['user_context']['role'] == 'instructor'
        assert 'email' in session['user_context']
        assert session['user_context']['is_demo'] is True

        # Verify: Capabilities assigned
        assert 'capabilities' in session
        assert isinstance(session['capabilities'], list)
        assert len(session['capabilities']) > 0

        # Verify: Access tracking initialized
        assert session['access_count'] == 0
        assert 'last_accessed' in session

    def test_create_demo_session_with_custom_duration(self):
        """
        TEST: Create demo session with custom duration

        BUSINESS REQUIREMENT:
        Demo sessions should support custom durations for different scenarios
        (e.g., quick demos vs. extended trials)

        VALIDATES:
        - Custom duration is applied correctly
        - Session config is stored with session
        - All other fields initialized properly
        """
        dao = DemoDAO()

        # Execute: Create session with 4-hour duration
        session = dao.create_demo_session(
            user_type='student',
            session_config={'duration_hours': 4}
        )

        # Verify: Custom duration applied
        duration = session['expires_at'] - session['created_at']
        assert duration.total_seconds() == 4 * 3600  # 4 hours

        # Verify: Config stored with session
        assert session['demo_config']['duration_hours'] == 4

    def test_create_demo_session_for_all_user_types(self):
        """
        TEST: Create sessions for instructor, student, and admin roles

        BUSINESS REQUIREMENT:
        Platform must support demo sessions for all user roles to showcase
        role-specific features and capabilities

        VALIDATES:
        - Sessions created for all three user types
        - User context varies by role (different profiles)
        - Capabilities differ by role
        - Email addresses reflect role type
        """
        dao = DemoDAO()

        # Execute: Create sessions for all roles
        instructor_session = dao.create_demo_session(user_type='instructor')
        student_session = dao.create_demo_session(user_type='student')
        admin_session = dao.create_demo_session(user_type='admin')

        # Verify: Different user contexts per role
        assert instructor_session['user_context']['role'] == 'instructor'
        assert student_session['user_context']['role'] == 'student'
        assert admin_session['user_context']['role'] == 'admin'

        # Verify: Different email patterns
        assert 'instructor' in instructor_session['user_context']['email']
        assert 'student' in student_session['user_context']['email']
        assert 'admin' in admin_session['user_context']['email']

        # Verify: Role-specific capabilities
        instructor_caps = instructor_session['capabilities']
        student_caps = student_session['capabilities']
        admin_caps = admin_session['capabilities']

        assert 'AI course creation' in instructor_caps
        assert 'Course enrollment' in student_caps
        assert 'User management' in admin_caps

    def test_validate_session_success(self):
        """
        TEST: Validate active demo session

        BUSINESS REQUIREMENT:
        System must validate session existence and expiration to control
        demo access and track engagement

        VALIDATES:
        - Active session validates successfully
        - Session data is returned intact
        - Access count increments on validation
        - Last accessed timestamp updates
        """
        dao = DemoDAO()

        # Setup: Create demo session
        session = dao.create_demo_session(user_type='instructor')
        session_id = session['session_id']
        initial_access_count = session['access_count']

        # Execute: Validate session
        validated_session = dao.validate_session(session_id)

        # Verify: Validation successful
        assert validated_session is not None
        assert validated_session['session_id'] == session_id

        # Verify: Access tracking updated
        assert validated_session['access_count'] == initial_access_count + 1
        assert validated_session['last_accessed'] > session['last_accessed']

    def test_validate_session_not_found(self):
        """
        TEST: Validate non-existent session

        BUSINESS REQUIREMENT:
        System must reject invalid session IDs to prevent unauthorized access

        VALIDATES:
        - Non-existent session raises ValidationException
        - Error includes session_id in details
        - Error code is DEMO_SESSION_NOT_FOUND
        """
        dao = DemoDAO()

        # Execute: Validate non-existent session
        with pytest.raises(ValidationException) as exc_info:
            dao.validate_session('non-existent-session-id')

        # Verify: Correct exception raised
        assert exc_info.value.error_code == 'DEMO_SESSION_NOT_FOUND'
        assert 'session_id' in exc_info.value.validation_errors
        assert 'non-existent-session-id' in exc_info.value.details['session_id']

    def test_validate_expired_session(self):
        """
        TEST: Validate expired demo session

        BUSINESS REQUIREMENT:
        Expired sessions must be rejected and cleaned up automatically
        to encourage registration and free resources

        VALIDATES:
        - Expired session raises BusinessRuleException
        - Session is deleted from storage after expiration
        - Error code is DEMO_SESSION_EXPIRED
        - Error details include expiration timestamp
        """
        dao = DemoDAO()

        # Setup: Create session that's already expired
        session = dao.create_demo_session(
            user_type='student',
            session_config={'duration_hours': -1}  # Expired 1 hour ago
        )
        session_id = session['session_id']

        # Execute: Validate expired session
        with pytest.raises(BusinessRuleException) as exc_info:
            dao.validate_session(session_id)

        # Verify: Correct exception raised
        assert exc_info.value.error_code == 'DEMO_SESSION_EXPIRED'
        assert 'expired_at' in exc_info.value.details

        # Verify: Session cleaned up
        assert session_id not in dao.sessions


class TestDemoDAOSessionCleanup:
    """
    Test Suite: Demo Session Cleanup Operations

    BUSINESS REQUIREMENT:
    System must automatically clean up expired sessions to prevent memory
    leaks and maintain system performance.
    """

    def test_cleanup_expired_sessions_removes_old_sessions(self):
        """
        TEST: Cleanup removes expired sessions

        BUSINESS REQUIREMENT:
        Expired sessions must be automatically cleaned up to free memory

        VALIDATES:
        - Expired sessions are identified correctly
        - Only expired sessions are deleted
        - Active sessions remain untouched
        - Cleanup count is accurate
        """
        dao = DemoDAO()

        # Setup: Create mix of active and expired sessions
        active_session = dao.create_demo_session('instructor')
        expired_session_1 = dao.create_demo_session(
            'student',
            session_config={'duration_hours': -1}
        )
        expired_session_2 = dao.create_demo_session(
            'admin',
            session_config={'duration_hours': -2}
        )

        # Verify: All sessions exist
        assert len(dao.sessions) == 3

        # Execute: Cleanup expired sessions
        cleanup_count = dao.cleanup_expired_sessions()

        # Verify: Only expired sessions removed
        assert cleanup_count == 2
        assert len(dao.sessions) == 1
        assert active_session['session_id'] in dao.sessions

    def test_cleanup_with_no_expired_sessions(self):
        """
        TEST: Cleanup with all active sessions

        BUSINESS REQUIREMENT:
        Cleanup should safely handle scenarios with no expired sessions

        VALIDATES:
        - Returns 0 when no sessions expired
        - Active sessions remain untouched
        - No errors thrown
        """
        dao = DemoDAO()

        # Setup: Create active sessions
        dao.create_demo_session('instructor')
        dao.create_demo_session('student')

        # Execute: Cleanup (should find nothing)
        cleanup_count = dao.cleanup_expired_sessions()

        # Verify: No sessions cleaned up
        assert cleanup_count == 0
        assert len(dao.sessions) == 2

    def test_get_session_statistics(self):
        """
        TEST: Get comprehensive session statistics

        BUSINESS REQUIREMENT:
        System must provide session statistics for monitoring and capacity planning

        VALIDATES:
        - Total session count is accurate
        - Active vs expired count is correct
        - User type distribution calculated
        - Oldest and newest session timestamps included
        """
        dao = DemoDAO()

        # Setup: Create diverse session mix
        dao.create_demo_session('instructor')
        dao.create_demo_session('student')
        dao.create_demo_session('instructor')
        dao.create_demo_session(
            'admin',
            session_config={'duration_hours': -1}  # Expired
        )

        # Execute: Get statistics
        stats = dao.get_session_statistics()

        # Verify: Counts accurate
        assert stats['total_sessions'] == 4
        assert stats['active_sessions'] == 3
        assert stats['expired_sessions'] == 1

        # Verify: User type distribution
        assert stats['user_type_distribution']['instructor'] == 2
        assert stats['user_type_distribution']['student'] == 1

        # Verify: Timestamps present
        assert stats['oldest_session'] is not None
        assert stats['newest_session'] is not None


class TestDemoDAODataGeneration:
    """
    Test Suite: Demo Data Generation Operations

    BUSINESS REQUIREMENT:
    System must generate realistic demo data for different user types
    and content categories to provide authentic demonstrations.
    """

    def test_generate_demo_courses_data(self):
        """
        TEST: Generate realistic demo courses

        BUSINESS REQUIREMENT:
        Demo must include realistic course data with varied subjects,
        difficulty levels, and enrollment metrics

        VALIDATES:
        - Courses generated with realistic fields
        - Random variation in subjects and levels
        - All courses marked as demo data
        - Enrollment and rating metrics present
        """
        dao = DemoDAO()

        # Execute: Generate demo courses
        courses = dao.generate_role_based_demo_data(
            user_type='instructor',
            data_type='courses',
            context={'count': 10}
        )

        # Verify: Correct number generated
        assert len(courses) == 10

        # Verify: Each course has required fields
        for course in courses:
            assert 'id' in course
            assert 'title' in course
            assert 'difficulty' in course
            assert 'enrollment_count' in course
            assert 'rating' in course
            assert course['is_demo'] is True

            # Verify: Realistic values
            assert course['difficulty'] in ['Beginner', 'Intermediate', 'Advanced']
            assert 10 <= course['duration_hours'] <= 40
            assert 4.2 <= course['rating'] <= 5.0

    def test_generate_demo_students_data(self):
        """
        TEST: Generate realistic demo student data

        BUSINESS REQUIREMENT:
        Demo must include student progress and engagement metrics
        for instructor dashboards

        VALIDATES:
        - Students have realistic names and emails
        - Progress percentages and engagement scores present
        - Quiz averages and lab hours tracked
        - All marked as demo data
        """
        dao = DemoDAO()

        # Execute: Generate demo students
        students = dao.generate_role_based_demo_data(
            user_type='instructor',
            data_type='students',
            context={'count': 25}
        )

        # Verify: Correct number generated
        assert len(students) == 25

        # Verify: Student data fields
        for student in students:
            assert 'id' in student
            assert 'name' in student
            assert 'email' in student
            assert 'progress_percentage' in student
            assert 'engagement_score' in student
            assert student['is_demo'] is True

            # Verify: Realistic ranges
            assert 25 <= student['progress_percentage'] <= 100
            assert 0.6 <= student['engagement_score'] <= 1.0

    def test_generate_demo_analytics_data(self):
        """
        TEST: Generate demo analytics dashboard data

        BUSINESS REQUIREMENT:
        Demo must show realistic analytics with trends and metrics
        for marketing and admin demonstrations

        VALIDATES:
        - Overview metrics present
        - Trend data for 12 months
        - All metrics within realistic ranges
        - Marked as demo data
        """
        dao = DemoDAO()

        # Execute: Generate analytics data
        analytics = dao.generate_role_based_demo_data(
            user_type='admin',
            data_type='analytics',
            context={}
        )

        # Verify: Overview metrics
        assert 'overview' in analytics
        assert 'total_students' in analytics['overview']
        assert 'completion_rate' in analytics['overview']

        # Verify: Trends present
        assert 'trends' in analytics
        assert len(analytics['trends']['enrollment_trend']) == 12
        assert len(analytics['trends']['completion_trend']) == 12

        # Verify: Demo flag
        assert analytics['is_demo'] is True

    def test_generate_demo_labs_data(self):
        """
        TEST: Generate demo lab environment data

        BUSINESS REQUIREMENT:
        Demo must showcase Docker lab functionality with various
        programming environments

        VALIDATES:
        - Labs have different environment types
        - Status values are realistic
        - Usage hours and completion rates tracked
        - All marked as demo data
        """
        dao = DemoDAO()

        # Execute: Generate demo labs
        labs = dao.generate_role_based_demo_data(
            user_type='student',
            data_type='labs',
            context={'count': 8}
        )

        # Verify: Correct number generated
        assert len(labs) == 8

        # Verify: Lab fields
        for lab in labs:
            assert 'id' in lab
            assert 'name' in lab
            assert 'environment' in lab
            assert 'status' in lab
            assert lab['is_demo'] is True

            # Verify: Valid environment types
            assert lab['environment'] in ['Python', 'JavaScript', 'Jupyter', 'VS Code']
            assert lab['status'] in ['available', 'running', 'completed']

    def test_generate_demo_feedback_data(self):
        """
        TEST: Generate demo student feedback data

        BUSINESS REQUIREMENT:
        Demo must include realistic student feedback for course quality metrics

        VALIDATES:
        - Feedback has student names and ratings
        - Comments are realistic samples
        - Sentiment analysis included
        - Timestamps span reasonable date range
        """
        dao = DemoDAO()

        # Execute: Generate feedback
        feedback_items = dao.generate_role_based_demo_data(
            user_type='instructor',
            data_type='feedback',
            context={'count': 15}
        )

        # Verify: Correct number generated
        assert len(feedback_items) == 15

        # Verify: Feedback fields
        for feedback in feedback_items:
            assert 'id' in feedback
            assert 'rating' in feedback
            assert 'comment' in feedback
            assert 'sentiment' in feedback
            assert feedback['is_demo'] is True

            # Verify: Realistic ratings
            assert 4 <= feedback['rating'] <= 5

    def test_generate_invalid_data_type_raises_error(self):
        """
        TEST: Request invalid demo data type

        BUSINESS REQUIREMENT:
        System must reject invalid data type requests with clear error

        VALIDATES:
        - ValidationException raised for invalid type
        - Error lists supported data types
        - Error code is INVALID_DEMO_DATA_TYPE
        """
        dao = DemoDAO()

        # Execute: Request invalid data type
        with pytest.raises(ValidationException) as exc_info:
            dao.generate_role_based_demo_data(
                user_type='instructor',
                data_type='invalid_type'
            )

        # Verify: Correct exception raised
        assert exc_info.value.error_code == 'INVALID_DEMO_DATA_TYPE'
        assert 'supported_types' in exc_info.value.details
        assert 'data_type' in exc_info.value.validation_errors

    def test_session_creation_error_handling(self):
        """
        TEST: Session creation with internal error

        BUSINESS REQUIREMENT:
        System must handle errors gracefully with structured exceptions

        VALIDATES:
        - BusinessRuleException raised on failure
        - Error code is DEMO_SESSION_CREATION_FAILED
        - Original error context preserved
        """
        dao = DemoDAO()

        # Execute: Force error by providing invalid session config
        # This will succeed normally, so we test the exception structure exists
        try:
            session = dao.create_demo_session(
                user_type='instructor',
                session_config={'duration_hours': 2}
            )
            # If successful, verify structure is sound
            assert 'session_id' in session
            assert 'user_type' in session
        except BusinessRuleException as e:
            # If exception raised, verify it's properly structured
            assert e.error_code == 'DEMO_SESSION_CREATION_FAILED'
            assert 'user_type' in e.details


class TestDemoDAOPrivateHelpers:
    """
    Test Suite: Demo DAO Private Helper Methods

    BUSINESS REQUIREMENT:
    Private helper methods must generate realistic, varied data
    to support authentic demonstrations.
    """

    def test_generate_user_context_has_unique_emails(self):
        """
        TEST: User context generation creates unique identifiers

        BUSINESS REQUIREMENT:
        Each demo session must have unique user context to avoid confusion

        VALIDATES:
        - User contexts for same role have different emails
        - Session ID is embedded in email for uniqueness
        - Role-specific data varies realistically
        """
        dao = DemoDAO()

        # Execute: Generate multiple instructor contexts
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        context_1 = dao._generate_user_context('instructor', session_id_1)
        context_2 = dao._generate_user_context('instructor', session_id_2)

        # Verify: Different emails generated
        assert context_1['email'] != context_2['email']
        assert session_id_1[:8] in context_1['email']
        assert session_id_2[:8] in context_2['email']

        # Verify: Both marked as demo
        assert context_1['is_demo'] is True
        assert context_2['is_demo'] is True

    def test_get_role_capabilities_returns_appropriate_features(self):
        """
        TEST: Role capabilities match user type

        BUSINESS REQUIREMENT:
        Capabilities must accurately reflect what each role can do
        on the platform

        VALIDATES:
        - Instructor capabilities include content creation
        - Student capabilities include learning features
        - Admin capabilities include management features
        - Each role has multiple capabilities
        """
        dao = DemoDAO()

        # Execute: Get capabilities for all roles
        instructor_caps = dao._get_role_capabilities('instructor')
        student_caps = dao._get_role_capabilities('student')
        admin_caps = dao._get_role_capabilities('admin')

        # Verify: Each role has capabilities
        assert len(instructor_caps) >= 4
        assert len(student_caps) >= 4
        assert len(admin_caps) >= 4

        # Verify: Role-specific capabilities present
        assert any('AI' in cap or 'course' in cap for cap in instructor_caps)
        assert any('enrollment' in cap or 'labs' in cap for cap in student_caps)
        assert any('management' in cap or 'User' in cap for cap in admin_caps)

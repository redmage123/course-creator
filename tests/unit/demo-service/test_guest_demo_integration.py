"""
TDD RED Phase: Guest → Demo Service Integration Tests

BUSINESS REQUIREMENT:
Guest users (unauthenticated) should have LIMITED access to demo service features.
This allows potential customers to explore the platform without creating an account,
while encouraging conversion to full user accounts.

GUEST ACCESS RESTRICTIONS:
- AI chatbot: 10 questions per session
- Demo workflows: View-only (cannot modify)
- Analytics: Sample data only (no real user data)
- Lab environments: Cannot create/execute (view sample output only)
- Knowledge graph: Read-only queries
- Content generation: View sample output only (cannot generate)

These tests should FAIL until we implement guest access controls.
"""

import pytest
import sys
from pathlib import Path

# Add demo-service to path for imports
demo_service_path = Path(__file__).parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))

from demo_data_generator import (
    generate_chatbot_response,
    generate_demo_workflow,
    generate_demo_analytics,
    generate_demo_lab_environment,
    query_demo_knowledge_graph,
    generate_demo_syllabus,
    DemoSession
)
from organization_management.domain.entities.guest_session import GuestSession


class TestGuestChatbotAccess:
    """
    Test: Guest users have rate-limited access to demo chatbot

    BUSINESS REQUIREMENT:
    Guests can ask up to 10 questions per session to explore the platform.
    After 10 questions, they must register to continue.
    """

    def test_guest_can_ask_chatbot_questions_within_limit(self):
        """
        Test: Guest can ask questions while under rate limit

        EXPECTED BEHAVIOR:
        - Guest session tracks AI request count
        - Chatbot responds normally when count < 10
        - Response includes remaining questions count
        """
        guest_session = GuestSession()

        # Ask 5 questions (under limit)
        for i in range(5):
            response = generate_chatbot_response(
                question="What is this platform?",
                conversation_history=[],
                guest_session=guest_session
            )

            assert response is not None
            assert 'answer' in response
            assert guest_session.ai_requests_count == i + 1
            assert response['remaining_requests'] == 10 - (i + 1)

    def test_guest_chatbot_blocks_after_limit_exceeded(self):
        """
        Test: Chatbot blocks guest after 10 questions

        EXPECTED BEHAVIOR:
        - After 10 questions, chatbot returns conversion prompt
        - Response suggests registration to continue
        - No answer provided, only registration CTA
        """
        guest_session = GuestSession()
        guest_session.ai_requests_count = 10  # Already at limit

        response = generate_chatbot_response(
            question="What features do you have?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert response['blocked'] is True
        assert 'register' in response['conversion_prompt'].lower()
        assert 'answer' not in response or response['answer'] is None

    def test_guest_chatbot_response_includes_conversion_prompt(self):
        """
        Test: Guest chatbot always includes conversion prompt

        BUSINESS REQUIREMENT:
        Every guest chatbot response should encourage registration,
        showing remaining questions and benefits of full account.
        """
        guest_session = GuestSession()
        guest_session.ai_requests_count = 7

        response = generate_chatbot_response(
            question="Tell me about pricing",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'conversion_prompt' in response
        assert 'register' in response['conversion_prompt'].lower() or 'sign up' in response['conversion_prompt'].lower()
        # After this question (8th), user has 2 questions remaining (10 - 8 = 2)
        assert response['remaining_requests'] == 2


class TestGuestWorkflowAccess:
    """
    Test: Guest users can view demo workflows but cannot execute them

    BUSINESS REQUIREMENT:
    Guests see what instructors/students can do, but cannot modify or execute.
    This showcases platform features while maintaining data integrity.
    """

    def test_guest_can_view_instructor_workflow(self):
        """
        Test: Guest can view instructor workflow demo

        EXPECTED BEHAVIOR:
        - Workflow shows all steps (course creation → content gen → student mgmt)
        - Each step marked as 'view_only'
        - No execute buttons/actions available
        """
        guest_session = GuestSession()
        workflow = generate_demo_workflow(role='instructor', guest_session=guest_session)

        assert workflow is not None
        assert workflow['role'] == 'instructor'
        assert workflow['access_level'] == 'view_only'
        assert all(step['executable'] is False for step in workflow['steps'])
        assert 'register_to_execute' in workflow

    def test_guest_can_view_student_workflow(self):
        """
        Test: Guest can view student workflow demo

        EXPECTED BEHAVIOR:
        - Workflow shows learning journey (enroll → learn → quiz → lab → cert)
        - All steps read-only
        - Conversion prompt to register and try for real
        """
        guest_session = GuestSession()
        workflow = generate_demo_workflow(role='student', guest_session=guest_session)

        assert workflow is not None
        assert workflow['role'] == 'student'
        assert workflow['access_level'] == 'view_only'
        assert all(step['executable'] is False for step in workflow['steps'])
        assert 'register_to_try' in workflow

    def test_guest_cannot_switch_roles_in_workflow(self):
        """
        Test: Guest cannot switch between workflow roles

        BUSINESS REQUIREMENT:
        To prevent confusion and encourage registration, guests view one
        workflow at a time. Switching roles requires registration.
        """
        guest_session = GuestSession()

        # Guest viewing instructor workflow cannot switch to student
        with pytest.raises(Exception) as exc_info:
            workflow = generate_demo_workflow(role='instructor', guest_session=guest_session)
            workflow = generate_demo_workflow(role='student', guest_session=guest_session)

        assert 'register to explore multiple roles' in str(exc_info.value).lower()


class TestGuestAnalyticsAccess:
    """
    Test: Guest users see sample analytics only

    BUSINESS REQUIREMENT:
    Guests cannot access real user data. They see pre-generated sample
    analytics to understand platform capabilities.
    """

    def test_guest_views_sample_analytics_only(self):
        """
        Test: Guest analytics queries return sample data

        EXPECTED BEHAVIOR:
        - All analytics data marked as 'sample'
        - No real user/course data exposed
        - Watermark or label indicating demo data
        """
        guest_session = GuestSession()
        analytics = generate_demo_analytics(
            analytics_type='progress_chart',
            course_id='demo-course-123',
            guest_session=guest_session
        )

        assert analytics is not None
        assert analytics['data_type'] == 'sample'
        assert analytics['is_real_data'] is False
        assert 'demo_watermark' in analytics
        assert analytics['demo_watermark'] == 'Sample data for demonstration purposes'

    def test_guest_cannot_generate_custom_analytics(self):
        """
        Test: Guest cannot create custom analytics queries

        BUSINESS REQUIREMENT:
        Custom analytics (date ranges, filters, exports) require full account.
        Guests see pre-defined sample analytics only.
        """
        guest_session = GuestSession()

        with pytest.raises(Exception) as exc_info:
            analytics = generate_demo_analytics(
                analytics_type='custom_report',
                course_id='demo-course-123',
                guest_session=guest_session,
                custom_filters={'date_range': '2025-01-01 to 2025-03-01'}
            )

        assert 'register to create custom analytics' in str(exc_info.value).lower()


class TestGuestLabEnvironmentAccess:
    """
    Test: Guest users cannot create or execute code in lab environments

    BUSINESS REQUIREMENT:
    Lab environments require authentication for security and resource management.
    Guests see sample lab configurations and pre-recorded execution results.
    """

    def test_guest_can_view_sample_lab_config(self):
        """
        Test: Guest can view lab environment configuration

        EXPECTED BEHAVIOR:
        - Lab config shows Docker setup, IDE type, starter code
        - Marked as 'view_only'
        - Execution disabled
        """
        guest_session = GuestSession()
        lab = generate_demo_lab_environment(
            lab_config={'topic': 'Python basics', 'ide': 'vscode'},
            guest_session=guest_session
        )

        assert lab is not None
        assert lab['access_level'] == 'view_only'
        assert lab['can_execute'] is False
        assert 'sample_output' in lab
        assert 'register_to_execute' in lab

    def test_guest_cannot_execute_code_in_lab(self):
        """
        Test: Guest cannot run code in lab environment

        BUSINESS REQUIREMENT:
        Code execution requires authenticated session for security,
        resource tracking, and abuse prevention.
        """
        guest_session = GuestSession()

        with pytest.raises(Exception) as exc_info:
            from demo_data_generator import simulate_demo_code_execution
            result = simulate_demo_code_execution(
                code="print('Hello world')",
                language='python',
                guest_session=guest_session
            )

        assert 'authentication required' in str(exc_info.value).lower() or 'register to execute' in str(exc_info.value).lower()


class TestGuestKnowledgeGraphAccess:
    """
    Test: Guest users have read-only access to knowledge graph

    BUSINESS REQUIREMENT:
    Guests can explore concept relationships and see how the knowledge
    graph works, but cannot create custom learning paths or queries.
    """

    def test_guest_can_query_knowledge_graph_basic(self):
        """
        Test: Guest can perform basic knowledge graph queries

        EXPECTED BEHAVIOR:
        - Guest can query for concept prerequisites
        - Guest can query for related concepts
        - Results limited to sample course data
        """
        guest_session = GuestSession()
        result = query_demo_knowledge_graph(
            query={'type': 'prerequisites', 'concept': 'Object-Oriented Programming'},
            guest_session=guest_session
        )

        assert result is not None
        assert result['access_level'] == 'limited'
        assert 'prerequisites' in result
        assert result['sample_data'] is True

    def test_guest_cannot_create_custom_learning_path(self):
        """
        Test: Guest cannot generate personalized learning paths

        BUSINESS REQUIREMENT:
        Personalized learning paths require student profile and progress data.
        Guests see sample learning path only.
        """
        guest_session = GuestSession()

        with pytest.raises(Exception) as exc_info:
            from demo_data_generator import generate_demo_learning_path
            learning_path = generate_demo_learning_path(
                student_profile={'interests': ['Python', 'AI'], 'skill_level': 'beginner'},
                guest_session=guest_session
            )

        assert 'register to create personalized learning path' in str(exc_info.value).lower()


class TestGuestContentGenerationAccess:
    """
    Test: Guest users cannot generate content, only view samples

    BUSINESS REQUIREMENT:
    AI content generation (syllabus, slides, quizzes) consumes expensive
    resources. Guests see pre-generated samples to understand capability.
    """

    def test_guest_can_view_sample_syllabus(self):
        """
        Test: Guest sees pre-generated sample syllabus

        EXPECTED BEHAVIOR:
        - Guest request for syllabus returns sample (not AI-generated)
        - Sample marked as 'demo_sample'
        - Conversion prompt to register for custom generation
        """
        guest_session = GuestSession()
        syllabus = generate_demo_syllabus(
            topic='Python Programming',
            learning_objectives=['Learn variables', 'Learn functions'],
            guest_session=guest_session
        )

        assert syllabus is not None
        assert syllabus['generation_type'] == 'sample'
        assert syllabus['is_ai_generated'] is False
        assert 'register_for_custom_generation' in syllabus

    def test_guest_cannot_generate_custom_content(self):
        """
        Test: Guest cannot trigger AI content generation

        BUSINESS REQUIREMENT:
        Only authenticated instructors can generate custom course content
        to prevent abuse and manage costs.
        """
        guest_session = GuestSession()

        # Attempting to force AI generation should fail
        with pytest.raises(Exception) as exc_info:
            syllabus = generate_demo_syllabus(
                topic='Advanced Machine Learning',
                learning_objectives=['Build neural networks', 'Deploy models'],
                guest_session=guest_session,
                force_generate=True
            )

        assert 'instructor account required' in str(exc_info.value).lower() or 'register to generate' in str(exc_info.value).lower()


class TestGuestSessionTracking:
    """
    Test: Guest sessions track feature views for conversion analytics

    BUSINESS REQUIREMENT:
    Track which features guests explore to optimize conversion funnels
    and prioritize product improvements.
    """

    def test_guest_session_tracks_chatbot_usage(self):
        """
        Test: Guest session records chatbot interactions

        EXPECTED BEHAVIOR:
        - Session tracks 'chatbot' in features_viewed
        - AI request count increments
        - Last activity timestamp updates
        """
        guest_session = GuestSession()

        generate_chatbot_response(
            question="What is this?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'chatbot' in guest_session.features_viewed
        assert guest_session.ai_requests_count == 1

    def test_guest_session_tracks_workflow_views(self):
        """
        Test: Guest session records workflow views

        EXPECTED BEHAVIOR:
        - Session tracks 'instructor_workflow' or 'student_workflow'
        - Can export to analytics for conversion tracking
        """
        guest_session = GuestSession()

        generate_demo_workflow(role='instructor', guest_session=guest_session)

        assert 'instructor_workflow' in guest_session.features_viewed

    def test_guest_session_tracks_lab_views(self):
        """
        Test: Guest session records lab environment views

        EXPECTED BEHAVIOR:
        - Session tracks 'lab_environment'
        - High-value feature view (strong conversion signal)
        """
        guest_session = GuestSession()

        generate_demo_lab_environment(
            lab_config={'topic': 'Python', 'ide': 'vscode'},
            guest_session=guest_session
        )

        assert 'lab_environment' in guest_session.features_viewed

    def test_guest_session_exports_to_analytics(self):
        """
        Test: Guest session data exports for conversion analytics

        BUSINESS REQUIREMENT:
        Marketing/sales teams need conversion data to optimize demo experience
        and identify high-intent visitors.
        """
        guest_session = GuestSession()
        guest_session.record_feature_view('chatbot')
        guest_session.record_feature_view('instructor_workflow')
        guest_session.record_feature_view('lab_environment')

        analytics_data = guest_session.to_analytics_dict()

        assert 'features_viewed' in analytics_data
        assert analytics_data['features_count'] == 3
        assert 'chatbot' in analytics_data['features_viewed']
        assert 'lab_environment' in analytics_data['features_viewed']
        assert 'conversion_score' in analytics_data  # High feature count = high conversion potential


class TestGuestSessionExpiration:
    """
    Test: Guest sessions expire after 30 minutes of inactivity

    BUSINESS REQUIREMENT:
    Guest sessions are temporary to encourage registration.
    After 30 minutes inactive, prompt to register to save progress.
    """

    def test_guest_session_expires_after_30_minutes(self):
        """
        Test: Expired guest session blocks all demo access

        EXPECTED BEHAVIOR:
        - After 30 min, is_expired() returns True
        - All demo functions return conversion prompt
        - Session data preserved for analytics
        """
        from datetime import timedelta

        guest_session = GuestSession()
        # Simulate 31 minutes passing
        guest_session.created_at = guest_session.created_at - timedelta(minutes=31)
        guest_session.expires_at = guest_session.created_at + timedelta(minutes=30)

        assert guest_session.is_expired() is True

        # Attempting to use chatbot with expired session
        response = generate_chatbot_response(
            question="What is this?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert response['blocked'] is True
        assert 'session expired' in response['conversion_prompt'].lower()
        assert 'register to continue' in response['conversion_prompt'].lower()

    def test_guest_session_renews_on_activity(self):
        """
        Test: Guest session renews expiration on activity

        EXPECTED BEHAVIOR:
        - Any demo interaction renews 30-minute timer
        - Keeps engaged guests active
        - Prevents frustrating mid-exploration expiration
        """
        from datetime import timedelta

        guest_session = GuestSession()
        original_expiry = guest_session.expires_at

        # Simulate 10 minutes passing
        guest_session.last_activity_at = guest_session.created_at + timedelta(minutes=10)

        # Renew session
        guest_session.renew()

        assert guest_session.expires_at > original_expiry
        assert not guest_session.is_expired()

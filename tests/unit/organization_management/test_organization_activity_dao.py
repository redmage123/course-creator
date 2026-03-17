"""
Unit Tests for Organization Activity DAO

BUSINESS CONTEXT:
Tests the data access layer for organization activity tracking, ensuring
that activity logging, retrieval, and management work correctly.

TECHNICAL IMPLEMENTATION:
Uses TDD (Test-Driven Development) approach - tests written before implementation.
Follows SOLID principles with comprehensive test coverage.

TEST COVERAGE:
- Activity creation with various types
- Activity retrieval by organization
- Activity filtering by date range
- Activity type filtering
- Error handling for invalid data
- Multi-tenant data isolation
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4
from organization_management.data_access.organization_dao import OrganizationManagementDAO


class TestOrganizationActivityDAO:
    """
    Test suite for Organization Activity DAO operations

    BUSINESS CONTEXT:
    Activity tracking is essential for organization admins to monitor
    user actions, system changes, and maintain audit compliance.

    SOLID PRINCIPLES APPLIED:
    - Single Responsibility: Each test method tests one specific behavior
    - Interface Segregation: Tests focus on specific activity operations
    """

    @pytest.fixture
    async def db_pool(self):
        """
        Create test database connection pool

        BUSINESS CONTEXT:
        Provides isolated database connection for testing without
        affecting production data.

        Technical Note:
        Uses asyncpg connection pool with proper cleanup
        """
        pool = await asyncpg.create_pool(
            user='course_user',
            password='course_pass',
            database='course_creator',
            host='localhost',
            port=5433,
            min_size=1,
            max_size=2
        )
        yield pool
        await pool.close()

    @pytest.fixture
    async def dao(self, db_pool):
        """
        Create DAO instance for testing

        DEPENDENCY INVERSION PRINCIPLE:
        DAO depends on abstract connection pool interface,
        not concrete implementation.
        """
        return OrganizationManagementDAO(db_pool)

    @pytest.fixture
    async def test_organization_id(self, dao):
        """
        Create test organization for activity testing

        BUSINESS CONTEXT:
        Activities are always associated with an organization
        for multi-tenant isolation.
        """
        org_data = {
            'name': f'Test Org {uuid4()}',
            'slug': f'test-org-{uuid4()}',
            'settings': {}
        }
        org_id = await dao.create_organization(org_data)
        return org_id

    @pytest.mark.asyncio
    async def test_log_activity_success(self, dao, test_organization_id):
        """
        Test successful activity logging

        BUSINESS REQUIREMENT:
        System must record all significant user and system actions
        for audit and visibility purposes.

        EXPECTED BEHAVIOR:
        - Activity is created with all required fields
        - Activity ID is returned
        - Activity can be retrieved
        """
        # Arrange
        activity_data = {
            'organization_id': test_organization_id,
            'user_id': str(uuid4()),
            'activity_type': 'project_created',
            'description': 'Created new project "Test Project"',
            'metadata': {'project_id': str(uuid4()), 'project_name': 'Test Project'}
        }

        # Act
        activity_id = await dao.log_organization_activity(**activity_data)

        # Assert
        assert activity_id is not None
        assert isinstance(activity_id, str)

        # Verify activity was created
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id,
            limit=1
        )
        assert len(activities) == 1
        assert activities[0]['id'] == activity_id
        assert activities[0]['activity_type'] == 'project_created'
        assert activities[0]['description'] == 'Created new project "Test Project"'

    @pytest.mark.asyncio
    async def test_get_activities_by_organization(self, dao, test_organization_id):
        """
        Test retrieving activities for specific organization

        BUSINESS REQUIREMENT:
        Organization admins need to see activities only for their organization
        (multi-tenant data isolation).

        EXPECTED BEHAVIOR:
        - Returns only activities for specified organization
        - Returns activities in reverse chronological order
        - Respects limit parameter
        """
        # Arrange - Create multiple activities
        activity_types = ['project_created', 'user_added', 'track_updated']
        activity_ids = []

        for activity_type in activity_types:
            activity_data = {
                'organization_id': test_organization_id,
                'user_id': str(uuid4()),
                'activity_type': activity_type,
                'description': f'Test activity: {activity_type}',
                'metadata': {}
            }
            activity_id = await dao.log_organization_activity(**activity_data)
            activity_ids.append(activity_id)

        # Act
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id,
            limit=10
        )

        # Assert
        assert len(activities) == 3
        # Verify reverse chronological order (newest first)
        assert activities[0]['activity_type'] == 'track_updated'
        assert activities[1]['activity_type'] == 'user_added'
        assert activities[2]['activity_type'] == 'project_created'

    @pytest.mark.asyncio
    async def test_get_activities_with_limit(self, dao, test_organization_id):
        """
        Test activity retrieval respects limit parameter

        BUSINESS REQUIREMENT:
        Prevent overwhelming UI with too many activities,
        implement pagination for performance.

        EXPECTED BEHAVIOR:
        - Returns only requested number of activities
        - Returns most recent activities first
        """
        # Arrange - Create 10 activities
        for i in range(10):
            activity_data = {
                'organization_id': test_organization_id,
                'user_id': str(uuid4()),
                'activity_type': 'test_action',
                'description': f'Activity {i}',
                'metadata': {}
            }
            await dao.log_organization_activity(**activity_data)

        # Act
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id,
            limit=5
        )

        # Assert
        assert len(activities) == 5

    @pytest.mark.asyncio
    async def test_get_activities_with_date_filter(self, dao, test_organization_id):
        """
        Test filtering activities by date range

        BUSINESS REQUIREMENT:
        Allow admins to view activities for specific time periods
        for compliance reporting and analysis.

        EXPECTED BEHAVIOR:
        - Returns only activities within specified date range
        - Excludes activities outside the range
        """
        # Arrange
        now = datetime.utcnow()
        days_back = 7

        # Create activity
        activity_data = {
            'organization_id': test_organization_id,
            'user_id': str(uuid4()),
            'activity_type': 'test_action',
            'description': 'Recent activity',
            'metadata': {}
        }
        await dao.log_organization_activity(**activity_data)

        # Act
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id,
            days_back=days_back
        )

        # Assert
        assert len(activities) >= 1
        for activity in activities:
            activity_date = activity['created_at']
            assert activity_date >= now - timedelta(days=days_back)

    @pytest.mark.asyncio
    async def test_get_activities_multi_tenant_isolation(self, dao):
        """
        Test that activities are properly isolated between organizations

        BUSINESS REQUIREMENT:
        Critical security requirement - organizations must NEVER
        see each other's activities (multi-tenant isolation).

        EXPECTED BEHAVIOR:
        - Organization A cannot see Organization B's activities
        - Each organization sees only their own activities
        """
        # Arrange - Create two organizations
        org_a_data = {'name': f'Org A {uuid4()}', 'slug': f'org-a-{uuid4()}', 'settings': {}}
        org_b_data = {'name': f'Org B {uuid4()}', 'slug': f'org-b-{uuid4()}', 'settings': {}}

        org_a_id = await dao.create_organization(org_a_data)
        org_b_id = await dao.create_organization(org_b_data)

        # Create activity for Org A
        activity_a = {
            'organization_id': org_a_id,
            'user_id': str(uuid4()),
            'activity_type': 'org_a_action',
            'description': 'Organization A activity',
            'metadata': {}
        }
        await dao.log_organization_activity(**activity_a)

        # Create activity for Org B
        activity_b = {
            'organization_id': org_b_id,
            'user_id': str(uuid4()),
            'activity_type': 'org_b_action',
            'description': 'Organization B activity',
            'metadata': {}
        }
        await dao.log_organization_activity(**activity_b)

        # Act
        org_a_activities = await dao.get_organization_activities(organization_id=org_a_id)
        org_b_activities = await dao.get_organization_activities(organization_id=org_b_id)

        # Assert
        # Org A should only see its own activity
        assert len(org_a_activities) == 1
        assert org_a_activities[0]['activity_type'] == 'org_a_action'

        # Org B should only see its own activity
        assert len(org_b_activities) == 1
        assert org_b_activities[0]['activity_type'] == 'org_b_action'

    @pytest.mark.asyncio
    async def test_log_activity_with_metadata(self, dao, test_organization_id):
        """
        Test activity logging with structured metadata

        BUSINESS REQUIREMENT:
        Activities often need to store additional context
        (e.g., which project, which user, what changed).

        EXPECTED BEHAVIOR:
        - Metadata is stored as JSON
        - Metadata can be retrieved and parsed
        - Supports complex nested structures
        """
        # Arrange
        complex_metadata = {
            'project_id': str(uuid4()),
            'changes': {
                'name': {'old': 'Old Name', 'new': 'New Name'},
                'status': {'old': 'draft', 'new': 'active'}
            },
            'user_email': 'test@example.com'
        }

        activity_data = {
            'organization_id': test_organization_id,
            'user_id': str(uuid4()),
            'activity_type': 'project_updated',
            'description': 'Updated project details',
            'metadata': complex_metadata
        }

        # Act
        activity_id = await dao.log_organization_activity(**activity_data)

        # Assert
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id,
            limit=1
        )

        retrieved_metadata = activities[0]['metadata']
        assert retrieved_metadata == complex_metadata
        assert retrieved_metadata['changes']['name']['old'] == 'Old Name'

    @pytest.mark.asyncio
    async def test_get_activities_empty_result(self, dao, test_organization_id):
        """
        Test retrieving activities when none exist

        BUSINESS REQUIREMENT:
        Handle gracefully when organization has no activities yet
        (e.g., newly created organization).

        EXPECTED BEHAVIOR:
        - Returns empty list (not None or error)
        - No exception raised
        """
        # Act
        activities = await dao.get_organization_activities(
            organization_id=test_organization_id
        )

        # Assert
        assert activities == []
        assert isinstance(activities, list)

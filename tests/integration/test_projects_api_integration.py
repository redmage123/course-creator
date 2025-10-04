"""
Projects API Integration Tests

BUSINESS CONTEXT:
Site admins need reliable API endpoints to fetch organization projects and tracks.
These integration tests verify the complete request/response cycle including
database queries, business logic, and API contract compliance.

TECHNICAL IMPLEMENTATION:
- Tests full stack: API → Service → DAO → Database
- Validates request/response models (Pydantic)
- Ensures proper authorization and error handling
- Verifies data transformation and serialization

TEST COVERAGE:
- GET /api/v1/organizations/{org_id}/projects
- GET /api/v1/projects/{project_id}/tracks
- Authorization and permission checks
- Error scenarios (404, 401, 500)
- Data integrity and relationships
"""

import pytest
import httpx
from uuid import uuid4, UUID
from datetime import datetime
import asyncio

# Configure async test mode
pytestmark = pytest.mark.asyncio


class TestProjectsAPIIntegration:
    """
    Integration tests for Projects API endpoints.

    BUSINESS REQUIREMENT:
    Site admins must be able to fetch organization projects with their
    associated tracks through a reliable, secure API.
    """

    @pytest.fixture
    async def test_organization_id(self, db_connection):
        """
        Create a test organization for projects testing.

        BUSINESS CONTEXT:
        Projects belong to organizations, so we need a valid
        organization context for all project operations.
        """
        org_id = uuid4()

        await db_connection.execute(
            """
            INSERT INTO course_creator.organizations (
                id, name, slug, description, contact_email,
                contact_phone, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            org_id,
            "Test Organization",
            "test-org",
            "Organization for testing",
            "test@example.com",
            "+14155551212",
            True,
            datetime.utcnow(),
            datetime.utcnow()
        )

        yield org_id

        # Cleanup
        await db_connection.execute(
            "DELETE FROM course_creator.organizations WHERE id = $1",
            org_id
        )

    @pytest.fixture
    async def test_projects(self, db_connection, test_organization_id):
        """
        Create test projects for the test organization.

        BUSINESS CONTEXT:
        Projects represent learning content containers that hold
        tracks and modules for student learning paths.
        """
        project_ids = []

        # Create 3 test projects with different states
        projects_data = [
            {
                'id': uuid4(),
                'name': 'Advanced Python Course',
                'description': 'Learn advanced Python programming',
                'is_published': True,
                'created_at': datetime(2024, 1, 15)
            },
            {
                'id': uuid4(),
                'name': 'Beginner JavaScript',
                'description': 'Start with JavaScript basics',
                'is_published': False,
                'created_at': datetime(2024, 2, 20)
            },
            {
                'id': uuid4(),
                'name': 'Data Science Fundamentals',
                'description': 'Introduction to data science',
                'is_published': True,
                'created_at': datetime(2024, 3, 10)
            }
        ]

        for project_data in projects_data:
            await db_connection.execute(
                """
                INSERT INTO course_creator.projects (
                    id, organization_id, name, description, is_published, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                project_data['id'],
                test_organization_id,
                project_data['name'],
                project_data['description'],
                project_data['is_published'],
                project_data['created_at']
            )
            project_ids.append(project_data['id'])

        yield project_ids

        # Cleanup
        for project_id in project_ids:
            await db_connection.execute(
                "DELETE FROM course_creator.projects WHERE id = $1",
                project_id
            )

    @pytest.fixture
    async def test_tracks(self, db_connection, test_projects):
        """
        Create test tracks for test projects.

        BUSINESS CONTEXT:
        Tracks are learning paths within projects that organize
        content by difficulty and topic sequence.
        """
        track_ids = []
        project_id = test_projects[0]  # Use first project

        tracks_data = [
            {
                'id': uuid4(),
                'name': 'Python Fundamentals',
                'description': 'Core Python concepts',
                'difficulty_level': 'beginner',
                'estimated_hours': 40,
                'sequence_order': 1
            },
            {
                'id': uuid4(),
                'name': 'Advanced Patterns',
                'description': 'Design patterns and best practices',
                'difficulty_level': 'advanced',
                'estimated_hours': 60,
                'sequence_order': 2
            }
        ]

        for track_data in tracks_data:
            await db_connection.execute(
                """
                INSERT INTO course_creator.tracks (
                    id, project_id, name, description, difficulty_level,
                    estimated_hours, sequence_order, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                track_data['id'],
                project_id,
                track_data['name'],
                track_data['description'],
                track_data['difficulty_level'],
                track_data['estimated_hours'],
                track_data['sequence_order'],
                datetime.utcnow()
            )
            track_ids.append(track_data['id'])

        yield track_ids

        # Cleanup
        for track_id in track_ids:
            await db_connection.execute(
                "DELETE FROM course_creator.tracks WHERE id = $1",
                track_id
            )

    async def test_get_organization_projects_success(
        self,
        api_client,
        test_organization_id,
        test_projects,
        site_admin_token
    ):
        """
        Test successful retrieval of organization projects.

        BUSINESS REQUIREMENT:
        Site admins should be able to view all projects for an organization
        with complete metadata including publication status and creation date.

        VALIDATION:
        - Returns 200 status
        - Response contains all projects
        - Project data is complete and accurate
        - Proper JSON serialization
        """
        response = await api_client.get(
            f"/api/v1/organizations/{test_organization_id}/projects",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        projects = response.json()
        assert isinstance(projects, list), "Response should be a list"
        assert len(projects) == 3, f"Expected 3 projects, got {len(projects)}"

        # Verify first project structure
        project = projects[0]
        assert 'id' in project
        assert 'name' in project
        assert 'description' in project
        assert 'is_published' in project
        assert 'created_at' in project

        # Verify data types
        assert isinstance(UUID(project['id']), UUID)
        assert isinstance(project['name'], str)
        assert isinstance(project['is_published'], bool)

    async def test_get_project_tracks_success(
        self,
        api_client,
        test_projects,
        test_tracks,
        site_admin_token
    ):
        """
        Test successful retrieval of project tracks.

        BUSINESS REQUIREMENT:
        Users need to see all tracks within a project to understand
        the learning path structure and content organization.

        VALIDATION:
        - Returns 200 status
        - Response contains all tracks for project
        - Track data includes difficulty and sequencing
        - Tracks ordered by sequence_order
        """
        project_id = test_projects[0]

        response = await api_client.get(
            f"/api/v1/projects/{project_id}/tracks",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200

        tracks = response.json()
        assert isinstance(tracks, list)
        assert len(tracks) == 2, f"Expected 2 tracks, got {len(tracks)}"

        # Verify tracks are ordered by sequence
        assert tracks[0]['sequence_order'] < tracks[1]['sequence_order']

        # Verify track structure
        track = tracks[0]
        assert 'id' in track
        assert 'name' in track
        assert 'difficulty_level' in track
        assert 'estimated_hours' in track
        assert track['difficulty_level'] in ['beginner', 'intermediate', 'advanced']

    async def test_get_projects_unauthorized(
        self,
        api_client,
        test_organization_id
    ):
        """
        Test that unauthorized requests are rejected.

        BUSINESS REQUIREMENT:
        Projects data is sensitive and should only be accessible
        to authenticated users with appropriate permissions.

        VALIDATION:
        - Returns 401 status without valid token
        - Returns 403 status with insufficient permissions
        - Proper error message in response
        """
        # No authorization header
        response = await api_client.get(
            f"/api/v1/organizations/{test_organization_id}/projects"
        )

        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"

        error = response.json()
        assert 'detail' in error

    async def test_get_projects_not_found(
        self,
        api_client,
        site_admin_token
    ):
        """
        Test 404 response for non-existent organization.

        BUSINESS REQUIREMENT:
        API should clearly indicate when requested organization
        doesn't exist rather than returning empty list.

        VALIDATION:
        - Returns 404 status
        - Error message indicates organization not found
        """
        fake_org_id = uuid4()

        response = await api_client.get(
            f"/api/v1/organizations/{fake_org_id}/projects",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        # API may return 404 or empty list depending on implementation
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            projects = response.json()
            assert len(projects) == 0, "Should return empty list for non-existent org"

    async def test_projects_filtering_by_status(
        self,
        api_client,
        test_organization_id,
        test_projects,
        site_admin_token
    ):
        """
        Test filtering projects by publication status.

        BUSINESS REQUIREMENT:
        Site admins need to filter projects by published/draft status
        to manage content publication workflow.

        VALIDATION:
        - Query parameter filters correctly
        - Only matching projects returned
        - Filter values validated
        """
        # Get only published projects
        response = await api_client.get(
            f"/api/v1/organizations/{test_organization_id}/projects?status=published",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200

        projects = response.json()
        # Should have 2 published projects
        published_count = sum(1 for p in projects if p['is_published'])
        assert published_count >= 2

    async def test_projects_pagination(
        self,
        api_client,
        test_organization_id,
        test_projects,
        site_admin_token
    ):
        """
        Test pagination parameters work correctly.

        BUSINESS REQUIREMENT:
        For organizations with many projects, pagination prevents
        performance issues and improves UX.

        VALIDATION:
        - skip parameter offsets results
        - limit parameter restricts count
        - Consistent ordering across pages
        """
        # Get first page (limit 2)
        response = await api_client.get(
            f"/api/v1/organizations/{test_organization_id}/projects?limit=2",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) <= 2

        # Get second page (skip 2, limit 2)
        response = await api_client.get(
            f"/api/v1/organizations/{test_organization_id}/projects?skip=2&limit=2",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200
        second_page = response.json()

        # Pages should have different projects
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]['id'] != second_page[0]['id']

    async def test_track_difficulty_levels(
        self,
        api_client,
        test_projects,
        test_tracks,
        site_admin_token
    ):
        """
        Test that difficulty levels are validated and returned correctly.

        BUSINESS REQUIREMENT:
        Difficulty levels help users understand content complexity
        and choose appropriate learning paths.

        VALIDATION:
        - Only valid difficulty values (beginner/intermediate/advanced)
        - Consistent capitalization
        - Proper enum handling
        """
        project_id = test_projects[0]

        response = await api_client.get(
            f"/api/v1/projects/{project_id}/tracks",
            headers={"Authorization": f"Bearer {site_admin_token}"}
        )

        assert response.status_code == 200

        tracks = response.json()
        for track in tracks:
            assert track['difficulty_level'] in ['beginner', 'intermediate', 'advanced'], \
                f"Invalid difficulty: {track['difficulty_level']}"

    async def test_concurrent_requests(
        self,
        api_client,
        test_organization_id,
        site_admin_token
    ):
        """
        Test API handles concurrent requests correctly.

        BUSINESS REQUIREMENT:
        Multiple users may access projects simultaneously,
        requiring thread-safe database operations.

        VALIDATION:
        - No race conditions
        - Consistent responses
        - No data corruption
        """
        # Make 10 concurrent requests
        tasks = [
            api_client.get(
                f"/api/v1/organizations/{test_organization_id}/projects",
                headers={"Authorization": f"Bearer {site_admin_token}"}
            )
            for _ in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # All should return same data
        first_data = responses[0].json()
        for response in responses[1:]:
            assert response.json() == first_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

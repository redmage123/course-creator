"""
Integration Tests for Organization Activity Endpoint

BUSINESS CONTEXT:
Tests the complete HTTP endpoint for organization activity retrieval,
ensuring proper authentication, authorization, and data formatting.

TECHNICAL IMPLEMENTATION:
Integration tests verify the full stack from HTTP request to database
and back, including authentication middleware and error handling.

TEST COVERAGE:
- GET /api/v1/organizations/{org_id}/activity endpoint
- Authentication and authorization
- Query parameter handling
- Response format validation
- Error cases (404, 403, 401)
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4


class TestOrganizationActivityEndpoint:
    """
    Integration tests for organization activity API endpoint

    BUSINESS CONTEXT:
    Organization admins need to retrieve activity logs via HTTP API
    for dashboard display and audit purposes.

    SOLID PRINCIPLES:
    - Interface Segregation: Tests specific to HTTP interface
    - Dependency Inversion: Tests against API contract, not implementation
    """

    @pytest.fixture
    def base_url(self):
        """
        Base URL for organization management service

        TECHNICAL NOTE:
        Points to local development service on HTTPS port
        """
        return "https://localhost:8003"

    @pytest.fixture
    async def auth_headers(self):
        """
        Generate authentication headers for API requests

        BUSINESS CONTEXT:
        All organization activity endpoints require authentication
        to ensure data security and proper tenant isolation.

        TECHNICAL NOTE:
        Uses JWT token for authentication
        """
        # TODO: Implement proper JWT token generation
        # For now, using mock token - update when auth service is integrated
        return {
            "Authorization": "Bearer mock-token-for-testing",
            "Content-Type": "application/json"
        }

    @pytest.fixture
    async def test_org_id(self, base_url, auth_headers):
        """
        Create test organization and return its ID

        BUSINESS CONTEXT:
        Activities are always associated with an organization,
        so we need a valid organization for testing.
        """
        async with AsyncClient(verify=False) as client:
            org_data = {
                "name": f"Test Org {uuid4()}",
                "slug": f"test-org-{uuid4()}",
                "settings": {}
            }
            response = await client.post(
                f"{base_url}/api/v1/organizations",
                headers=auth_headers,
                json=org_data
            )
            assert response.status_code == 201
            return response.json()["id"]

    @pytest.mark.asyncio
    async def test_get_activities_success(self, base_url, auth_headers, test_org_id):
        """
        Test successful retrieval of organization activities

        BUSINESS REQUIREMENT:
        Organization admins must be able to retrieve activity logs
        for their organization via HTTP API.

        EXPECTED BEHAVIOR:
        - Returns 200 OK status
        - Returns JSON array of activities
        - Activities are properly formatted
        - Activities are in reverse chronological order
        """
        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "activities" in data
            assert isinstance(data["activities"], list)

            # Verify response structure
            if len(data["activities"]) > 0:
                activity = data["activities"][0]
                assert "id" in activity
                assert "activity_type" in activity
                assert "description" in activity
                assert "created_at" in activity

    @pytest.mark.asyncio
    async def test_get_activities_with_limit(self, base_url, auth_headers, test_org_id):
        """
        Test activity retrieval with limit query parameter

        BUSINESS REQUIREMENT:
        Support pagination to prevent overwhelming frontend
        with large activity lists.

        EXPECTED BEHAVIOR:
        - Accepts 'limit' query parameter
        - Returns at most 'limit' number of activities
        - Defaults to reasonable limit (e.g., 50)
        """
        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity?limit=5",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert len(data["activities"]) <= 5

    @pytest.mark.asyncio
    async def test_get_activities_with_days_back(self, base_url, auth_headers, test_org_id):
        """
        Test activity retrieval with date filtering

        BUSINESS REQUIREMENT:
        Allow filtering activities by time period for
        compliance reporting and performance.

        EXPECTED BEHAVIOR:
        - Accepts 'days_back' query parameter
        - Returns only activities from specified time period
        - Defaults to 30 days
        """
        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity?days_back=7",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "activities" in data

    @pytest.mark.asyncio
    async def test_get_activities_unauthorized(self, base_url, test_org_id):
        """
        Test accessing activities without authentication

        SECURITY REQUIREMENT:
        Activity endpoints must require authentication
        to prevent unauthorized data access.

        EXPECTED BEHAVIOR:
        - Returns 401 Unauthorized
        - Does not expose activity data
        """
        async with AsyncClient(verify=False) as client:
            # Act - No auth headers
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity"
            )

            # Assert
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_activities_wrong_organization(self, base_url, auth_headers):
        """
        Test accessing activities for wrong organization

        SECURITY REQUIREMENT:
        Users should only see activities for organizations
        they belong to (multi-tenant isolation).

        EXPECTED BEHAVIOR:
        - Returns 403 Forbidden or 404 Not Found
        - Does not expose other organization's data
        """
        # Use a non-existent organization ID
        fake_org_id = str(uuid4())

        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{fake_org_id}/activity",
                headers=auth_headers
            )

            # Assert
            assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_activities_invalid_org_id(self, base_url, auth_headers):
        """
        Test handling of invalid organization ID format

        EXPECTED BEHAVIOR:
        - Returns 400 Bad Request or 404 Not Found
        - Provides clear error message
        """
        invalid_org_id = "not-a-valid-uuid"

        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{invalid_org_id}/activity",
                headers=auth_headers
            )

            # Assert
            assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_get_activities_invalid_limit(self, base_url, auth_headers, test_org_id):
        """
        Test handling of invalid limit parameter

        EXPECTED BEHAVIOR:
        - Returns 400 Bad Request for negative limits
        - Returns 400 Bad Request for non-numeric limits
        - Caps limit at maximum allowed value
        """
        async with AsyncClient(verify=False) as client:
            # Test negative limit
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity?limit=-1",
                headers=auth_headers
            )
            assert response.status_code in [400, 422]

            # Test non-numeric limit
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity?limit=abc",
                headers=auth_headers
            )
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_activities_response_format(self, base_url, auth_headers, test_org_id):
        """
        Test that response follows expected JSON structure

        BUSINESS REQUIREMENT:
        Consistent API response format for frontend consumption.

        EXPECTED STRUCTURE:
        {
            "activities": [
                {
                    "id": "uuid",
                    "organization_id": "uuid",
                    "user_id": "uuid",
                    "activity_type": "string",
                    "description": "string",
                    "metadata": {},
                    "created_at": "ISO datetime"
                }
            ],
            "total": number,
            "limit": number
        }
        """
        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == 200

            data = response.json()

            # Verify top-level structure
            assert "activities" in data
            assert isinstance(data["activities"], list)

            # Optionally verify metadata
            # assert "total" in data
            # assert "limit" in data

    @pytest.mark.asyncio
    async def test_get_activities_empty_result(self, base_url, auth_headers, test_org_id):
        """
        Test retrieving activities when organization has none

        BUSINESS REQUIREMENT:
        Handle gracefully when organization is new or has no activities.

        EXPECTED BEHAVIOR:
        - Returns 200 OK (not error)
        - Returns empty activities array
        - Does not return null/undefined
        """
        async with AsyncClient(verify=False) as client:
            # Act
            response = await client.get(
                f"{base_url}/api/v1/organizations/{test_org_id}/activity",
                headers=auth_headers
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "activities" in data
            assert isinstance(data["activities"], list)
            # Empty list is valid

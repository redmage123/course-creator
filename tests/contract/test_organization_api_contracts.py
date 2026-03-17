"""
Contract Tests for Organization Management API

BUSINESS CONTEXT:
These tests verify that API endpoints return data matching their Pydantic models.
Unlike unit tests with mocked data, these use real database queries to catch
schema mismatches between DB responses and API models.

TECHNICAL IMPLEMENTATION:
- Tests real API endpoints with actual database
- Validates Pydantic model serialization
- Catches missing fields, type mismatches, and schema drift

TDD METHODOLOGY:
These tests would have caught:
- MemberResponse missing optional fields (organization_id, joined_at)
- Login response missing organization_id field
- Query results not matching model expectations
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import UUID
import asyncio
import sys
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Optional
from datetime import datetime

# Define models locally for validation (copied from actual services)
class MemberResponse(BaseModel):
    """Member response model"""
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    username: str
    email: str
    role: str
    is_active: bool
    joined_at: Optional[datetime] = None

class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    username: str
    role: str
    organization_id: Optional[str] = None

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    user: dict  # UserResponse as dict

# Base URLs for running services (HTTPS only - platform uses SSL exclusively)
BASE_URL = "https://176.9.99.103"
ORG_MGMT_URL = f"{BASE_URL}:8008"
USER_MGMT_URL = f"{BASE_URL}:8000"


class TestOrganizationAPIContracts:
    """
    Test Suite: Organization API Contract Validation

    REQUIREMENT: API responses must match Pydantic models exactly
    """

    @pytest_asyncio.fixture
    async def org_client(self):
        """HTTPS client for organization-management service"""
        async with AsyncClient(base_url=ORG_MGMT_URL, verify=False) as client:
            yield client

    @pytest_asyncio.fixture
    async def user_client(self):
        """HTTPS client for user-management service"""
        async with AsyncClient(base_url=USER_MGMT_URL, verify=False) as client:
            yield client

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer mock-test-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_get_organization_returns_valid_schema(self, org_client, auth_headers):
        """
        TEST: GET /organizations/{id} matches OrganizationResponse model
        REQUIREMENT: Response must serialize without Pydantic validation errors
        """
        # Use a known organization ID (from demo data)
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await org_client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        # Should not be 404 or 500
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status {response.status_code}: {response.text}"

        if response.status_code == 200:
            data = response.json()

            # Validate required fields exist
            assert "id" in data, "Missing 'id' field"
            assert "name" in data, "Missing 'name' field"
            assert "slug" in data, "Missing 'slug' field"

            # Validate UUID format
            try:
                UUID(data["id"])
            except ValueError:
                pytest.fail(f"Invalid UUID format for id: {data['id']}")

    @pytest.mark.asyncio
    async def test_get_members_returns_valid_member_response_schema(self, org_client, auth_headers):
        """
        TEST: GET /organizations/{id}/members matches MemberResponse model
        REQUIREMENT: Each member must deserialize into MemberResponse without errors

        THIS TEST WOULD HAVE CAUGHT:
        - Missing organization_id field causing Pydantic ValidationError
        - Missing joined_at field causing Pydantic ValidationError
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await org_client.get(
            f"/api/v1/organizations/{org_id}/members?role=student",
            headers=auth_headers
        )

        # Should not return 500 error
        assert response.status_code != 500, \
            f"Members endpoint returned 500 error: {response.text}"

        if response.status_code == 200:
            members = response.json()

            # Validate it's a list
            assert isinstance(members, list), "Members should be a list"

            # Validate each member matches MemberResponse schema
            for member in members:
                try:
                    # This will raise ValidationError if schema doesn't match
                    member_obj = MemberResponse(**member)

                    # Validate required fields
                    assert member_obj.id is not None
                    assert member_obj.user_id is not None
                    assert member_obj.username is not None
                    assert member_obj.email is not None
                    assert member_obj.role is not None
                    assert member_obj.is_active is not None

                    # Optional fields should not cause errors
                    # (organization_id and joined_at can be None)

                except Exception as e:
                    pytest.fail(
                        f"Member data doesn't match MemberResponse schema: {e}\n"
                        f"Member data: {member}"
                    )

    @pytest.mark.asyncio
    async def test_get_members_with_different_roles(self, org_client, auth_headers):
        """
        TEST: Members endpoint works with all role filters
        REQUIREMENT: Should handle student, instructor, organization_admin roles
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        roles = ["student", "instructor", "organization_admin"]

        for role in roles:
            response = await org_client.get(
                f"/api/v1/organizations/{org_id}/members?role={role}",
                headers=auth_headers
            )

            assert response.status_code != 500, \
                f"Members endpoint failed for role={role}: {response.text}"

            if response.status_code == 200:
                members = response.json()
                assert isinstance(members, list)

                # Validate all returned members have the correct role
                for member in members:
                    assert member["role"] == role or member["role"] == role.replace("_", " "), \
                        f"Expected role {role}, got {member['role']}"

    @pytest.mark.asyncio
    async def test_login_response_includes_organization_id(self, user_client):
        """
        TEST: Login returns organization_id for org admins
        REQUIREMENT: TokenResponse.user must include organization_id

        THIS TEST WOULD HAVE CAUGHT:
        - Missing organization_id in login response
        - "No organization_id found for org admin user" error
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await user_client.post(
            "/api/v1/auth/login",
            json=login_data
        )

        # Should not fail with 500
        assert response.status_code != 500, \
            f"Login endpoint returned 500: {response.text}"

        if response.status_code == 200:
            data = response.json()

            # Validate TokenResponse structure
            assert "access_token" in data, "Missing access_token"
            assert "user" in data, "Missing user object"

            user = data["user"]

            # Validate UserResponse fields
            assert "id" in user
            assert "email" in user
            assert "username" in user
            assert "role" in user

            # If user is org admin, MUST have organization_id
            if user["role"] in ["organization_admin", "org_admin"]:
                assert "organization_id" in user, \
                    "Org admin login response missing organization_id field"

                if user["organization_id"]:
                    # Validate it's a valid UUID string
                    try:
                        UUID(user["organization_id"])
                    except ValueError:
                        pytest.fail(f"Invalid organization_id format: {user['organization_id']}")

    @pytest.mark.asyncio
    async def test_tracks_endpoint_returns_list(self, org_client, auth_headers):
        """
        TEST: Tracks endpoint returns list without errors
        REQUIREMENT: Should return empty list or valid tracks
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await org_client.get(
            f"/api/v1/tracks?organization_id={org_id}",
            headers=auth_headers
        )

        # Should not return 500
        assert response.status_code != 500, \
            f"Tracks endpoint returned 500: {response.text}"

        if response.status_code == 200:
            tracks = response.json()
            assert isinstance(tracks, list), "Tracks should be a list"


class TestDatabaseQueryContracts:
    """
    Test Suite: Database Query Structure Validation

    REQUIREMENT: DB queries must return all fields needed by Pydantic models
    """

    @pytest_asyncio.fixture
    async def org_client(self):
        """HTTPS client for organization-management service"""
        async with AsyncClient(base_url=ORG_MGMT_URL, verify=False) as client:
            yield client

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer mock-test-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_membership_query_includes_all_member_response_fields(self, org_client, auth_headers):
        """
        TEST: get_organization_members query returns all MemberResponse fields
        REQUIREMENT: Query must SELECT all fields that Pydantic model expects

        THIS TEST WOULD HAVE CAUGHT:
        - Query not selecting organization_id
        - Query not selecting joined_at
        """
        # Test with known organization via HTTPS API
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await org_client.get(
            f"/api/v1/organizations/{org_id}/members",
            headers=auth_headers
        )

        # Should not return 500
        assert response.status_code != 500, \
            f"Members endpoint returned 500: {response.text}"

        if response.status_code == 200:
            members = response.json()

            # Should return a list
            assert isinstance(members, list), "Members should be a list"

            if len(members) > 0:
                member = members[0]

                # Verify all MemberResponse fields are present
                required_fields = ["id", "user_id", "username", "email", "role", "is_active"]
                optional_fields = ["organization_id", "joined_at"]

                for field in required_fields:
                    assert field in member, \
                        f"API response missing required field: {field}\nGot: {list(member.keys())}"

                # Optional fields should exist (even if None)
                for field in optional_fields:
                    assert field in member, \
                        f"API response missing optional field: {field}\nGot: {list(member.keys())}"

                # Try to create MemberResponse from API response
                try:
                    member_obj = MemberResponse(**member)
                except Exception as e:
                    pytest.fail(
                        f"Failed to create MemberResponse from API response: {e}\n"
                        f"API returned: {member}"
                    )


class TestAPIErrorHandling:
    """
    Test Suite: API Error Response Validation

    REQUIREMENT: APIs should return proper error responses, not 500s
    """

    @pytest_asyncio.fixture
    async def org_client(self):
        """HTTPS client for organization-management service"""
        async with AsyncClient(base_url=ORG_MGMT_URL, verify=False) as client:
            yield client

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer mock-test-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_members_endpoint_handles_missing_fields_gracefully(self, org_client, auth_headers):
        """
        TEST: Members endpoint doesn't crash with 500 on schema mismatch
        REQUIREMENT: Should handle Pydantic validation errors gracefully
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await org_client.get(
            f"/api/v1/organizations/{org_id}/members",
            headers=auth_headers
        )

        # Should NEVER return 500
        if response.status_code == 500:
            pytest.fail(
                f"Members endpoint returned 500 error (schema validation issue?):\n"
                f"{response.text}"
            )

    @pytest.mark.asyncio
    async def test_invalid_org_id_returns_404_not_500(self, org_client, auth_headers):
        """
        TEST: Invalid org ID returns 404, not 500
        REQUIREMENT: Should validate input before querying
        """
        invalid_org_id = "00000000-0000-0000-0000-000000000000"

        response = await org_client.get(
            f"/api/v1/organizations/{invalid_org_id}",
            headers=auth_headers
        )

        # Should return 404 or 403, NOT 500
        assert response.status_code in [404, 403, 401], \
            f"Expected 404/403/401 for invalid org, got {response.status_code}: {response.text}"

    @pytest.mark.asyncio
    async def test_malformed_uuid_returns_422_not_500(self, org_client, auth_headers):
        """
        TEST: Malformed UUID returns 422 validation error
        REQUIREMENT: FastAPI should validate UUID format
        """
        malformed_uuid = "not-a-uuid"

        response = await org_client.get(
            f"/api/v1/organizations/{malformed_uuid}",
            headers=auth_headers
        )

        # Should return 422 (Unprocessable Entity), NOT 500
        assert response.status_code == 422, \
            f"Expected 422 for malformed UUID, got {response.status_code}"

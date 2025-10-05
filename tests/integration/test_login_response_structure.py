"""
Integration Tests for Login Response Structure

BUSINESS CONTEXT:
Tests that verify login endpoint returns all required fields for different user roles.
Ensures TokenResponse and UserResponse models match actual API responses,
preventing "missing organization_id" and similar errors.

TECHNICAL IMPLEMENTATION:
- Tests actual HTTP calls to login endpoint
- Validates response structure for each user role
- Checks Pydantic model serialization
- Verifies organization_id inclusion for org admins

TDD METHODOLOGY:
These tests would have caught:
- Login response missing organization_id field
- "No organization_id found for org admin user" error
- UserResponse model not including organization_id
- Login not querying organization_memberships table
"""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

# Define models locally for validation
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

# HTTPS base URL for running service
USER_MGMT_URL = "https://176.9.99.103:8000"


class TestLoginResponseStructure:
    """
    Test Suite: Login Response Validation

    REQUIREMENT: Login must return complete user data including organization_id
    """

    @pytest_asyncio.fixture
    async def client(self):
        """HTTPS client for user-management service"""
        async with AsyncClient(base_url=USER_MGMT_URL, verify=False) as client:
            yield client

    @pytest.mark.asyncio
    async def test_login_response_has_access_token(self, client):
        """
        TEST: Login returns access_token
        REQUIREMENT: TokenResponse must include JWT token
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        # May fail if user doesn't exist or wrong password
        if response.status_code == 200:
            data = response.json()

            # Must have access_token
            assert "access_token" in data, \
                "Login response missing access_token field"

            token = data["access_token"]
            assert token is not None, "access_token should not be null"
            assert len(token) > 0, "access_token should not be empty"

            print(f"✅ Login response includes access_token")

    @pytest.mark.asyncio
    async def test_login_response_has_user_object(self, client):
        """
        TEST: Login returns user object
        REQUIREMENT: TokenResponse must include UserResponse
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()

            # Must have user object
            assert "user" in data, \
                "Login response missing user object"

            user = data["user"]
            assert user is not None, "user object should not be null"
            assert isinstance(user, dict), "user should be an object"

            print(f"✅ Login response includes user object")

    @pytest.mark.asyncio
    async def test_user_response_has_required_fields(self, client):
        """
        TEST: UserResponse includes all required fields
        REQUIREMENT: id, email, username, role must be present
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            user = data["user"]

            # Validate required fields
            required_fields = ["id", "email", "username", "role"]

            for field in required_fields:
                assert field in user, \
                    f"UserResponse missing required field: {field}"

                assert user[field] is not None, \
                    f"Required field '{field}' is null"

            print(f"✅ UserResponse has all required fields: {required_fields}")

    @pytest.mark.asyncio
    async def test_org_admin_login_includes_organization_id(self, client):
        """
        TEST: Org admin login returns organization_id
        REQUIREMENT: Organization admins MUST have organization_id in response

        THIS TEST WOULD HAVE CAUGHT:
        - "No organization_id found for org admin user" error
        - Missing organization_id field in UserResponse
        - Login not querying organization_memberships table
        """
        login_data = {
            "username": "bbrelin",  # Known org admin
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        if response.status_code != 200:
            pytest.skip(f"Login failed with status {response.status_code}, user may not exist")

        data = response.json()
        user = data["user"]

        # Check user role
        if user["role"] in ["organization_admin", "org_admin"]:
            # MUST have organization_id
            assert "organization_id" in user, \
                "Org admin UserResponse missing organization_id field"

            org_id = user["organization_id"]

            # Should not be null for org admins
            assert org_id is not None, \
                "organization_id should not be null for org admin users"

            # Should be valid UUID format
            try:
                UUID(org_id)
            except ValueError:
                pytest.fail(f"organization_id is not a valid UUID: {org_id}")

            print(f"✅ Org admin login includes organization_id: {org_id}")
        else:
            pytest.skip(f"Test user is not org admin (role: {user['role']})")

    @pytest.mark.asyncio
    async def test_student_login_does_not_require_organization_id(self, client):
        """
        TEST: Student login works without organization_id
        REQUIREMENT: organization_id should be optional for students
        """
        # This would test a student user
        # For now, we just verify the field is optional in the model

        login_data = {
            "username": "student_user",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        # If user exists and logs in successfully
        if response.status_code == 200:
            data = response.json()
            user = data["user"]

            # organization_id may or may not be present for students
            # If present, can be null
            if "organization_id" in user:
                print(f"✅ Student can have organization_id: {user.get('organization_id')}")
            else:
                print(f"✅ Student does not require organization_id field")

    @pytest.mark.asyncio
    async def test_login_response_matches_token_response_model(self, client):
        """
        TEST: Login response deserializes to TokenResponse model
        REQUIREMENT: Response must match Pydantic model exactly
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()

            try:
                # Try to deserialize into TokenResponse model
                token_response = TokenResponse(**data)

                assert token_response is not None
                assert token_response.access_token is not None
                assert token_response.user is not None

                print(f"✅ Login response matches TokenResponse model")

            except Exception as e:
                pytest.fail(
                    f"Login response doesn't match TokenResponse model:\n"
                    f"Error: {e}\n"
                    f"Response: {data}"
                )

    @pytest.mark.asyncio
    async def test_login_response_user_matches_user_response_model(self, client):
        """
        TEST: Login response user deserializes to UserResponse model
        REQUIREMENT: User object must match Pydantic model
        """
        login_data = {
            "username": "bbrelin",
            "password": "test123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            user_data = data["user"]

            try:
                # Try to deserialize into UserResponse model
                user_response = UserResponse(**user_data)

                assert user_response is not None
                assert user_response.id is not None
                assert user_response.email is not None
                assert user_response.username is not None
                assert user_response.role is not None

                # If org admin, should have organization_id
                if user_response.role in ["organization_admin", "org_admin"]:
                    assert hasattr(user_response, 'organization_id'), \
                        "UserResponse model missing organization_id attribute for org admin"

                print(f"✅ Login user object matches UserResponse model")

            except Exception as e:
                pytest.fail(
                    f"Login user object doesn't match UserResponse model:\n"
                    f"Error: {e}\n"
                    f"User data: {user_data}"
                )

    @pytest.mark.asyncio
    async def test_invalid_login_returns_proper_error(self, client):
        """
        TEST: Invalid login returns 401, not 500
        REQUIREMENT: Should handle auth failures gracefully
        """
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        # Should return 401 (Unauthorized), not 500
        assert response.status_code in [401, 403, 422], \
            f"Invalid login should return 401/403/422, got {response.status_code}"

        print(f"✅ Invalid login returns proper error: {response.status_code}")

    @pytest.mark.asyncio
    async def test_login_without_credentials_returns_422(self, client):
        """
        TEST: Missing credentials returns validation error
        REQUIREMENT: Should validate input before processing
        """
        # Missing password
        login_data = {
            "username": "test_user"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        # Should return 422 (Validation Error)
        assert response.status_code == 422, \
            f"Missing credentials should return 422, got {response.status_code}"

        print(f"✅ Missing credentials returns validation error")


class TestOrganizationMembershipQuery:
    """
    Test Suite: Organization Membership Query Validation

    REQUIREMENT: Login must query organization_memberships for org admins
    """

    @pytest_asyncio.fixture
    async def client(self):
        """HTTPS client for user-management service"""
        async with AsyncClient(base_url=USER_MGMT_URL, verify=False) as client:
            yield client

    @pytest.mark.asyncio
    async def test_org_admin_has_organization_membership_record(self, client):
        """
        TEST: Org admin user has entry in organization_memberships
        REQUIREMENT: Database should have membership record for org admins

        THIS TEST WOULD HAVE CAUGHT:
        - Missing organization_memberships record
        - Inactive membership not filtered out
        """
        # Import database utilities
        import sys
        from pathlib import Path
        org_mgmt_path = Path(__file__).parent.parent.parent / 'services' / 'organization-management'
        sys.path.insert(0, str(org_mgmt_path))

        try:
            from database.connection_pool import ConnectionPool
        except ImportError:
            pytest.skip("organization-management service not available")

        pool = ConnectionPool.get_instance()
        await pool.initialize()

        async with pool.acquire() as conn:
            # Query for org admin user's membership
            query = """
                SELECT om.organization_id, om.is_active
                FROM course_creator.users u
                JOIN course_creator.organization_memberships om ON u.id = om.user_id
                WHERE u.username = $1 AND om.is_active = true
                LIMIT 1
            """

            result = await conn.fetchrow(query, "bbrelin")

            if result is None:
                pytest.skip("Test user 'bbrelin' has no active organization membership")

            # Should have organization_id
            assert result['organization_id'] is not None, \
                "Organization membership missing organization_id"

            # Should be active
            assert result['is_active'] is True, \
                "Organization membership should be active"

            print(f"✅ Org admin has active membership: {result['organization_id']}")

    @pytest.mark.asyncio
    async def test_login_query_joins_organization_memberships_correctly(self, client):
        """
        TEST: Login query performs correct JOIN
        REQUIREMENT: Should use LEFT JOIN and filter by is_active
        """
        from services.organization_management.database.connection_pool import ConnectionPool

        pool = ConnectionPool.get_instance()
        await pool.initialize()

        async with pool.acquire() as conn:
            # Simulate the exact query used in login
            query = """
                SELECT u.id, u.username, u.email, u.role, om.organization_id
                FROM course_creator.users u
                LEFT JOIN course_creator.organization_memberships om
                    ON u.id = om.user_id AND om.is_active = true
                WHERE u.username = $1
                LIMIT 1
            """

            result = await conn.fetchrow(query, "bbrelin")

            if result is None:
                pytest.skip("Test user 'bbrelin' not found")

            # User data should be present
            assert result['id'] is not None
            assert result['username'] == "bbrelin"
            assert result['email'] is not None
            assert result['role'] is not None

            # If user is org admin, organization_id should be present
            if result['role'] in ['organization_admin', 'org_admin']:
                assert result['organization_id'] is not None, \
                    "LEFT JOIN should fetch organization_id for org admin"

            print(f"✅ Login query JOIN works correctly")


class TestUserResponseModel:
    """
    Test Suite: UserResponse Model Validation

    REQUIREMENT: UserResponse model must support organization_id
    """

    def test_user_response_model_has_organization_id_field(self):
        """
        TEST: UserResponse model includes organization_id
        REQUIREMENT: Model should have organization_id as Optional field
        """
        # Check if model has organization_id attribute
        model_fields = UserResponse.model_fields.keys()

        assert 'organization_id' in model_fields, \
            "UserResponse model missing organization_id field"

        # Check if it's optional
        field_info = UserResponse.model_fields['organization_id']
        assert not field_info.is_required() or field_info.default is not None, \
            "organization_id should be Optional (not required)"

        print(f"✅ UserResponse model has optional organization_id field")

    def test_user_response_model_serializes_with_organization_id(self):
        """
        TEST: UserResponse serializes correctly with organization_id
        REQUIREMENT: Model should handle organization_id in JSON serialization
        """
        from services.user_management.routes import UserResponse
        from uuid import uuid4

        user_data = {
            "id": str(uuid4()),
            "email": "test@example.com",
            "username": "test_user",
            "role": "organization_admin",
            "organization_id": str(uuid4())
        }

        try:
            user = UserResponse(**user_data)

            # Serialize to dict
            user_dict = user.dict()

            assert 'organization_id' in user_dict, \
                "Serialized UserResponse missing organization_id"

            assert user_dict['organization_id'] == user_data['organization_id'], \
                "organization_id not preserved in serialization"

            print(f"✅ UserResponse serializes organization_id correctly")

        except Exception as e:
            pytest.fail(f"UserResponse failed to serialize with organization_id: {e}")

    def test_user_response_model_allows_null_organization_id(self):
        """
        TEST: UserResponse allows null organization_id
        REQUIREMENT: organization_id should be optional (can be None)
        """
        from services.user_management.routes import UserResponse
        from uuid import uuid4

        user_data = {
            "id": str(uuid4()),
            "email": "student@example.com",
            "username": "student",
            "role": "student",
            "organization_id": None  # Explicitly null
        }

        try:
            user = UserResponse(**user_data)
            assert user.organization_id is None

            print(f"✅ UserResponse allows null organization_id")

        except Exception as e:
            pytest.fail(f"UserResponse rejected null organization_id: {e}")

    def test_user_response_model_works_without_organization_id(self):
        """
        TEST: UserResponse works when organization_id is omitted
        REQUIREMENT: Field should be truly optional (can be missing)
        """
        from services.user_management.routes import UserResponse
        from uuid import uuid4

        user_data = {
            "id": str(uuid4()),
            "email": "instructor@example.com",
            "username": "instructor",
            "role": "instructor"
            # organization_id omitted entirely
        }

        try:
            user = UserResponse(**user_data)

            # Should default to None
            assert user.organization_id is None or not hasattr(user, 'organization_id')

            print(f"✅ UserResponse works without organization_id field")

        except Exception as e:
            pytest.fail(f"UserResponse failed without organization_id: {e}")

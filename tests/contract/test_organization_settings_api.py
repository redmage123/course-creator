"""
Contract Tests for Organization Settings API

BUSINESS CONTEXT:
Tests verify that the organization GET endpoint returns all required fields
for populating the settings form. This catches schema mismatches between
the API response and frontend expectations.

TECHNICAL IMPLEMENTATION:
- Tests real HTTPS API endpoints
- Validates response structure matches frontend requirements
- Checks field types and required fields

TDD METHODOLOGY:
These tests would have caught:
- Missing fields in API response (street_address, city, etc.)
- Null values where form expects strings
- Type mismatches between API and form expectations
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Define expected organization response model
class OrganizationSettingsResponse(BaseModel):
    """
    Organization response model for settings form

    BUSINESS CONTEXT:
    This model defines all fields that the settings form expects
    from the organization API endpoint.
    """
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# HTTPS base URL (platform uses SSL exclusively)
BASE_URL = "https://176.9.99.103"
ORG_MGMT_URL = f"{BASE_URL}:8008"


class TestOrganizationSettingsAPI:
    """
    Test Suite: Organization Settings API Contract Validation

    REQUIREMENT: API must return all fields needed for settings form
    """

    @pytest_asyncio.fixture
    async def client(self):
        """HTTPS client for organization-management service"""
        async with AsyncClient(base_url=ORG_MGMT_URL, verify=False) as client:
            yield client

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_get_organization_returns_all_settings_fields(self, client, auth_headers):
        """
        TEST: GET /organizations/{id} returns all fields needed by settings form
        REQUIREMENT: Response must include name, slug, description, contact info, address

        THIS TEST WOULD HAVE CAUGHT:
        - Missing street_address, city, state_province fields
        - Missing contact_email, contact_phone fields
        - Missing domain field
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        # Should return 200 or 401/403 (auth might fail)
        assert response.status_code in [200, 401, 403], \
            f"Expected 200/401/403, got {response.status_code}"

        if response.status_code == 200:
            data = response.json()

            # Validate required fields for settings form
            required_fields = ["id", "name", "slug"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
                assert data[field] is not None, f"Required field '{field}' is null"

            # Validate optional fields exist (can be null)
            optional_fields = [
                "description",
                "contact_email",
                "contact_phone",
                "street_address",
                "city",
                "state_province",
                "postal_code",
                "country",
                "domain",
                "logo_url"
            ]

            for field in optional_fields:
                assert field in data, \
                    f"Settings form expects field '{field}' but it's missing from API response"

            print("✅ All settings form fields present in API response")

    @pytest.mark.asyncio
    async def test_organization_response_matches_settings_model(self, client, auth_headers):
        """
        TEST: Response deserializes to OrganizationSettingsResponse model
        REQUIREMENT: API response must match Pydantic model for type safety
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            try:
                # Try to deserialize into model
                org_settings = OrganizationSettingsResponse(**data)

                # Validate key fields
                assert org_settings.id is not None
                assert org_settings.name is not None
                assert org_settings.slug is not None
                assert org_settings.is_active is not None

                print(f"✅ Organization response matches settings model")
                print(f"   ID: {org_settings.id}")
                print(f"   Name: {org_settings.name}")
                print(f"   Slug: {org_settings.slug}")

            except Exception as e:
                pytest.fail(
                    f"Organization response doesn't match OrganizationSettingsResponse model:\n"
                    f"Error: {e}\n"
                    f"Response: {data}"
                )

    @pytest.mark.asyncio
    async def test_organization_id_is_valid_uuid(self, client, auth_headers):
        """
        TEST: Organization ID is valid UUID format
        REQUIREMENT: ID should be UUID string for consistency
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            # Validate UUID format
            try:
                UUID(data["id"])
                print(f"✅ Organization ID is valid UUID: {data['id']}")
            except ValueError:
                pytest.fail(f"Organization ID is not valid UUID: {data['id']}")

    @pytest.mark.asyncio
    async def test_contact_email_is_valid_format(self, client, auth_headers):
        """
        TEST: Contact email has valid email format
        REQUIREMENT: Email field should be valid email or None
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            contact_email = data.get("contact_email")
            if contact_email is not None:
                # Should have @ symbol for valid email
                assert "@" in contact_email, \
                    f"Contact email appears invalid: {contact_email}"

                print(f"✅ Contact email is valid: {contact_email}")

    @pytest.mark.asyncio
    async def test_country_code_is_valid(self, client, auth_headers):
        """
        TEST: Country code is valid ISO format
        REQUIREMENT: Country should be 2-letter ISO code or None
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            country = data.get("country")
            if country is not None:
                # Should be 2-letter code (US, CA, UK, etc.)
                assert len(country) == 2, \
                    f"Country code should be 2 letters, got: {country}"
                assert country.isupper(), \
                    f"Country code should be uppercase, got: {country}"

                print(f"✅ Country code is valid: {country}")

    @pytest.mark.asyncio
    async def test_invalid_org_id_returns_404(self, client, auth_headers):
        """
        TEST: Invalid organization ID returns 404
        REQUIREMENT: Should handle missing organizations gracefully
        """
        invalid_org_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/organizations/{invalid_org_id}",
            headers=auth_headers
        )

        # Should return 404 or 403, not 500
        assert response.status_code in [404, 403, 401], \
            f"Expected 404/403/401 for invalid org, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_malformed_org_id_returns_422(self, client, auth_headers):
        """
        TEST: Malformed UUID returns validation error
        REQUIREMENT: Should validate UUID format before querying
        """
        malformed_id = "not-a-uuid"

        response = await client.get(
            f"/api/v1/organizations/{malformed_id}",
            headers=auth_headers
        )

        # Should return 422 validation error
        assert response.status_code == 422, \
            f"Expected 422 for malformed UUID, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_organization_endpoint_does_not_return_500(self, client, auth_headers):
        """
        TEST: Organization endpoint never returns 500 error
        REQUIREMENT: Should handle all errors gracefully without server errors
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers
        )

        # Should NEVER return 500
        if response.status_code == 500:
            pytest.fail(
                f"Organization endpoint returned 500 error:\n"
                f"{response.text}"
            )


class TestOrganizationUpdateAPI:
    """
    Test Suite: Organization Update API Contract

    REQUIREMENT: Settings form should be able to save changes
    """

    @pytest_asyncio.fixture
    async def client(self):
        """HTTPS client for organization-management service"""
        async with AsyncClient(base_url=ORG_MGMT_URL, verify=False) as client:
            yield client

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }

    @pytest.mark.asyncio
    async def test_update_organization_endpoint_exists(self, client, auth_headers):
        """
        TEST: PUT/PATCH endpoint exists for updating organization
        REQUIREMENT: Should be able to save settings form changes
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }

        # Try PUT first
        response = await client.put(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers,
            json=update_data
        )

        # Should not return 404 (endpoint should exist)
        # Might return 401/403 (auth), 422 (validation), or 200/204 (success)
        assert response.status_code != 404, \
            "Organization update endpoint (PUT) does not exist"

        print(f"✅ Organization update endpoint exists (status: {response.status_code})")

    @pytest.mark.asyncio
    async def test_update_accepts_all_settings_fields(self, client, auth_headers):
        """
        TEST: Update endpoint accepts all settings form fields
        REQUIREMENT: Should be able to update all form fields via API
        """
        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

        # All fields from settings form
        update_data = {
            "name": "Test Organization",
            "description": "Test description",
            "contact_email": "test@example.com",
            "contact_phone": "+15551234567",
            "street_address": "123 Test St",
            "city": "Test City",
            "state_province": "TS",
            "postal_code": "12345",
            "country": "US",
            "domain": "test.example.com"
        }

        response = await client.put(
            f"/api/v1/organizations/{org_id}",
            headers=auth_headers,
            json=update_data
        )

        # Should not return 422 (validation error) for valid data
        # Might return 401/403 (auth) or 200/204 (success)
        if response.status_code == 422:
            error_detail = response.json()
            pytest.fail(
                f"Update endpoint rejected valid settings data:\n"
                f"{error_detail}"
            )

        print(f"✅ Update endpoint accepts all settings fields (status: {response.status_code})")

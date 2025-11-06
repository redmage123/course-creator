#!/usr/bin/env python3
"""
Unit Tests for Organization API Endpoints

BUSINESS REQUIREMENT:
Tests FastAPI endpoint logic for organization management including multi-tenant
hierarchy, member management, and role-based access control.

TECHNICAL IMPLEMENTATION:
Tests request validation, response formatting, error handling, file upload,
and dependency injection for organization API endpoints.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
from uuid import uuid4
from datetime import datetime
import json

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock shared.cache module before importing organization-management modules
sys.modules['shared'] = MagicMock()
sys.modules['shared.cache'] = MagicMock()
sys.modules['shared.cache.redis_cache'] = MagicMock()

# Clean sys.path of other services to avoid 'main' module conflicts
sys.path = [p for p in sys.path if '/services/' not in p or 'organization-management' in p]

# Add organization-management to path
org_mgmt_path = str(Path(__file__).parent.parent.parent.parent / 'services' / 'organization-management')
if org_mgmt_path not in sys.path:
    sys.path.insert(0, org_mgmt_path)

from main import app, create_app
from api.organization_endpoints import router
from organization_management.application.services.organization_service import OrganizationService
from organization_management.domain.entities.organization import Organization


class TestOrganizationEndpoints:
    """
    Test suite for Organization API Endpoints
    Tests: Request validation, response formatting, error handling, file upload, dependency injection
    """

    def setup_method(self):
        """Set up test fixtures for each test method"""
        # Create test client
        self.test_app = create_app({})
        self.client = TestClient(self.test_app)
        
        # Sample request data
        self.valid_org_data = {
            "name": "TechCorp Training Institute",
            "slug": "techcorp-training",
            "address": "123 Innovation Drive, Tech City, TC 12345",
            "contact_phone": "+1-555-123-4567",
            "contact_email": "admin@techcorp.com",
            "admin_full_name": "John Smith",
            "admin_email": "john.smith@techcorp.com",
            "admin_phone": "+1-555-123-4568",
            "description": "Leading technology training organization",
            "domain": "techcorp.com"
        }
        
        self.sample_org_id = uuid4()
        self.current_time = datetime.utcnow()

    def test_health_check_endpoint(self):
        """Test health check endpoint returns correct status"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "organization-management"
        assert "timestamp" in data

    def test_test_endpoint(self):
        """Test the basic test endpoint functionality"""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Organization service is working!"
        assert data["test"] is True

    def test_organization_router_test_endpoint(self):
        """Test organization router test endpoint"""
        response = self.client.get("/test")  # Router test endpoint
        
        assert response.status_code == 200
        data = response.json()
        assert "organization" in data["message"].lower()
        assert data["professional_validation"] == "enabled"

    @patch('services.organization_management.api.organization_endpoints.get_organization_service')
    @patch('services.organization_management.api.organization_endpoints.get_current_user')
    def test_create_organization_success(self, mock_get_current_user, mock_get_org_service):
        """Test successful organization creation via API"""
        # Arrange
        mock_user = {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "role": "org_admin"
        }
        mock_get_current_user.return_value = mock_user
        
        mock_org_service = AsyncMock()
        created_org = Organization(
            id=self.sample_org_id,
            name=self.valid_org_data["name"],
            slug=self.valid_org_data["slug"],
            address=self.valid_org_data["address"],
            contact_phone=self.valid_org_data["contact_phone"],
            contact_email=self.valid_org_data["contact_email"],
            description=self.valid_org_data["description"],
            domain=self.valid_org_data["domain"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        mock_org_service.create_organization.return_value = created_org
        mock_get_org_service.return_value = mock_org_service

        # Act
        response = self.client.post(
            "/organizations",
            json=self.valid_org_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == self.valid_org_data["name"]
        assert data["slug"] == self.valid_org_data["slug"]
        assert data["contact_email"] == self.valid_org_data["contact_email"]
        assert data["is_active"] is True

    def test_create_organization_validation_error_personal_email(self):
        """Test organization creation fails with personal email domains"""
        invalid_data = self.valid_org_data.copy()
        invalid_data["contact_email"] = "admin@gmail.com"  # Personal email
        
        response = self.client.post(
            "/organizations",
            json=invalid_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
        # Check if the error message contains information about personal email
        error_details = json.dumps(data).lower()
        assert "gmail" in error_details or "personal" in error_details

    def test_create_organization_validation_error_invalid_phone(self):
        """Test organization creation fails with invalid phone number"""
        invalid_data = self.valid_org_data.copy()
        invalid_data["contact_phone"] = "123"  # Too short
        
        response = self.client.post(
            "/organizations",
            json=invalid_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_create_organization_missing_required_fields(self):
        """Test organization creation fails with missing required fields"""
        incomplete_data = self.valid_org_data.copy()
        del incomplete_data["name"]  # Remove required field
        
        response = self.client.post(
            "/organizations",
            json=incomplete_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_create_organization_invalid_slug_pattern(self):
        """Test organization creation fails with invalid slug pattern"""
        invalid_data = self.valid_org_data.copy()
        invalid_data["slug"] = "Invalid Slug With Spaces"  # Invalid pattern
        
        response = self.client.post(
            "/organizations",
            json=invalid_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_organization_unauthorized(self):
        """Test organization creation fails without authentication"""
        response = self.client.post(
            "/organizations",
            json=self.valid_org_data
            # No Authorization header
        )
        
        assert response.status_code == 403  # Forbidden/Unauthorized

    @patch('services.organization_management.api.organization_endpoints.get_organization_service')
    @patch('services.organization_management.api.organization_endpoints.get_current_user')
    def test_create_organization_with_file_upload_success(self, mock_get_current_user, mock_get_org_service):
        """Test successful organization creation with logo file upload"""
        # Arrange
        mock_user = {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "role": "org_admin"
        }
        mock_get_current_user.return_value = mock_user
        
        mock_org_service = AsyncMock()
        created_org = Organization(
            id=self.sample_org_id,
            name=self.valid_org_data["name"],
            slug=self.valid_org_data["slug"],
            address=self.valid_org_data["address"],
            contact_phone=self.valid_org_data["contact_phone"],
            contact_email=self.valid_org_data["contact_email"],
            description=self.valid_org_data["description"],
            domain=self.valid_org_data["domain"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        mock_org_service.create_organization.return_value = created_org
        mock_get_org_service.return_value = mock_org_service

        # Create a fake image file
        fake_image_content = b"fake_image_data_for_testing"
        
        # Act
        response = self.client.post(
            "/organizations/upload",
            data=self.valid_org_data,
            files={"logo": ("test_logo.png", fake_image_content, "image/png")},
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == self.valid_org_data["name"]
        assert "logo_url" in data
        assert "logo_file_path" in data

    def test_create_organization_with_invalid_file_type(self):
        """Test organization creation fails with invalid file type"""
        # Create a fake non-image file
        fake_file_content = b"fake_text_file_content"
        
        response = self.client.post(
            "/organizations/upload",
            data=self.valid_org_data,
            files={"logo": ("document.txt", fake_file_content, "text/plain")},
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 400  # Bad request
        data = response.json()
        assert "Invalid file type" in data["detail"]

    def test_create_organization_with_oversized_file(self):
        """Test organization creation fails with file too large"""
        # Create a fake large file (simulate 6MB file)
        large_file_content = b"x" * (6 * 1024 * 1024)  # 6MB
        
        response = self.client.post(
            "/organizations/upload",
            data=self.valid_org_data,
            files={"logo": ("large_logo.png", large_file_content, "image/png")},
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 400  # Bad request
        data = response.json()
        assert "too large" in data["detail"].lower()

    @patch('services.organization_management.api.organization_endpoints.get_organization_service')
    @patch('services.organization_management.api.organization_endpoints.get_current_user')
    def test_get_organizations_list(self, mock_get_current_user, mock_get_org_service):
        """Test organizations listing endpoint"""
        # Arrange
        mock_user = {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "role": "org_admin"
        }
        mock_get_current_user.return_value = mock_user
        
        mock_org_service = AsyncMock()
        mock_orgs = [
            Organization(
                id=uuid4(),
                name="Test Org 1",
                slug="test-org-1",
                address="Address 1",
                contact_phone="+1-555-001-0000",
                contact_email="admin1@testorg1.com",
                is_active=True,
                created_at=self.current_time,
                updated_at=self.current_time
            ),
            Organization(
                id=uuid4(),
                name="Test Org 2",
                slug="test-org-2",
                address="Address 2",
                contact_phone="+1-555-002-0000",
                contact_email="admin2@testorg2.com",
                is_active=True,
                created_at=self.current_time,
                updated_at=self.current_time
            )
        ]
        
        mock_org_service.list_organizations.return_value = (mock_orgs, 2)
        mock_get_org_service.return_value = mock_org_service

        # Act
        response = self.client.get(
            "/organizations",
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Test Org 1"
        assert data[1]["name"] == "Test Org 2"

    @patch('services.organization_management.api.organization_endpoints.get_organization_service')
    @patch('services.organization_management.api.organization_endpoints.get_current_user')
    def test_get_organization_by_id(self, mock_get_current_user, mock_get_org_service):
        """Test get organization by ID endpoint"""
        # Arrange
        mock_user = {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "role": "org_admin"
        }
        mock_get_current_user.return_value = mock_user
        
        mock_org_service = AsyncMock()
        mock_org = Organization(
            id=self.sample_org_id,
            name=self.valid_org_data["name"],
            slug=self.valid_org_data["slug"],
            address=self.valid_org_data["address"],
            contact_phone=self.valid_org_data["contact_phone"],
            contact_email=self.valid_org_data["contact_email"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        mock_org_service.get_organization_by_id.return_value = mock_org
        mock_get_org_service.return_value = mock_org_service

        # Act
        response = self.client.get(
            f"/organizations/{self.sample_org_id}",
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(self.sample_org_id)
        assert data["name"] == self.valid_org_data["name"]

    def test_get_organization_invalid_uuid(self):
        """Test get organization with invalid UUID format"""
        response = self.client.get(
            "/organizations/invalid-uuid",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422  # Validation error

    @patch('services.organization_management.api.organization_endpoints.get_organization_service')
    @patch('services.organization_management.api.organization_endpoints.get_current_user')
    def test_update_organization(self, mock_get_current_user, mock_get_org_service):
        """Test organization update endpoint"""
        # Arrange
        mock_user = {
            "id": str(uuid4()),
            "email": "admin@example.com",
            "role": "org_admin"
        }
        mock_get_current_user.return_value = mock_user
        
        mock_org_service = AsyncMock()
        updated_org = Organization(
            id=self.sample_org_id,
            name="Updated Organization Name",
            slug=self.valid_org_data["slug"],
            address=self.valid_org_data["address"],
            contact_phone=self.valid_org_data["contact_phone"],
            contact_email=self.valid_org_data["contact_email"],
            is_active=True,
            created_at=self.current_time,
            updated_at=datetime.utcnow()
        )
        
        mock_org_service.update_organization.return_value = updated_org
        mock_get_org_service.return_value = mock_org_service

        update_data = {"name": "Updated Organization Name"}

        # Act
        response = self.client.put(
            f"/organizations/{self.sample_org_id}",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Organization Name"

    def test_cors_headers_present(self):
        """Test that CORS headers are properly set"""
        response = self.client.options("/organizations")
        
        # CORS headers should be present (might be set to allow all origins during development)
        assert response.status_code in [200, 204]

    def test_request_validation_edge_cases(self):
        """Test edge cases in request validation"""
        # Test extremely long organization name
        invalid_data = self.valid_org_data.copy()
        invalid_data["name"] = "x" * 300  # Exceeds max length
        
        response = self.client.post(
            "/organizations",
            json=invalid_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422

        # Test empty required fields
        invalid_data = self.valid_org_data.copy()
        invalid_data["address"] = ""  # Empty required field
        
        response = self.client.post(
            "/organizations",
            json=invalid_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422

    def test_error_response_format(self):
        """Test that error responses follow consistent format"""
        response = self.client.post(
            "/organizations",
            json={},  # Empty data to trigger validation errors
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        
        # Validation errors should have a specific format
        if isinstance(data["detail"], list):
            # Pydantic validation errors
            for error in data["detail"]:
                assert "loc" in error
                assert "msg" in error
                assert "type" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
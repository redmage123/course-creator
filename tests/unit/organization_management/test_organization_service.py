#!/usr/bin/env python3
"""
Unit Tests for Organization Service

BUSINESS REQUIREMENT:
Tests business logic, validation, and service operations for multi-tenant
organization management including hierarchy, member management, and settings.

TECHNICAL IMPLEMENTATION:
Tests service layer operations, business rules, and validation logic for
organization management system.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any, Optional


from organization_management.application.services.organization_service import OrganizationService
from organization_management.domain.entities.organization import Organization
from data_access.organization_dao import OrganizationManagementDAO
from exceptions import (
    OrganizationException, ValidationException,
    OrganizationNotFoundException
)


class TestOrganizationService:
    """
    Test suite for OrganizationService business logic
    Covers: CRUD operations, validation, professional email requirements, multi-tenant scenarios
    """

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.mock_repository = Mock(spec=OrganizationManagementDAO)
        self.organization_service = OrganizationService(self.mock_repository)
        
        # Sample organization data for testing
        self.sample_org_data = {
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

    @pytest.mark.asyncio
    async def test_create_organization_success(self):
        """Test successful organization creation with all required fields"""
        # Arrange
        self.mock_repository.get_by_slug.return_value = None  # No existing organization
        self.mock_repository.create.return_value = Organization(
            id=self.sample_org_id,
            name=self.sample_org_data["name"],
            slug=self.sample_org_data["slug"],
            address=self.sample_org_data["address"],
            contact_phone=self.sample_org_data["contact_phone"],
            contact_email=self.sample_org_data["contact_email"],
            description=self.sample_org_data["description"],
            domain=self.sample_org_data["domain"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )

        # Act
        result = await self.organization_service.create_organization(self.sample_org_data)

        # Assert
        assert result.id == self.sample_org_id
        assert result.name == self.sample_org_data["name"]
        assert result.slug == self.sample_org_data["slug"]
        assert result.contact_email == self.sample_org_data["contact_email"]
        assert result.is_active is True
        
        # Verify repository interactions
        self.mock_repository.get_by_slug.assert_called_once_with(self.sample_org_data["slug"])
        self.mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_organization_duplicate_slug(self):
        """Test organization creation fails with duplicate slug"""
        # Arrange
        existing_org = Organization(
            id=uuid4(),
            name="Existing Corp",
            slug=self.sample_org_data["slug"],
            address="456 Old St",
            contact_phone="+1-555-999-0000",
            contact_email="admin@existing.com",
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        self.mock_repository.get_by_slug.return_value = existing_org

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await self.organization_service.create_organization(self.sample_org_data)

        assert "slug already exists" in str(exc_info.value).lower()
        self.mock_repository.create.assert_not_called()

    def test_validate_professional_email_valid(self):
        """Test professional email validation accepts business domains"""
        # Valid professional emails
        valid_emails = [
            "admin@techcorp.com",
            "contact@university.edu",
            "info@nonprofit.org",
            "training@enterprise.co.uk"
        ]
        
        for email in valid_emails:
            # Should not raise any exception
            self.organization_service._validate_professional_email(email)

    def test_validate_professional_email_invalid(self):
        """Test professional email validation rejects personal domains"""
        # Invalid personal email domains
        invalid_emails = [
            "user@gmail.com",
            "admin@yahoo.com",
            "contact@hotmail.com",
            "info@outlook.com",
            "test@aol.com",
            "user@icloud.com",
            "admin@live.com",
            "contact@googlemail.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationException) as exc_info:
                self.organization_service._validate_professional_email(email)
            assert "Personal email provider" in str(exc_info.value)
            assert "not allowed" in str(exc_info.value)

    def test_validate_phone_number_valid(self):
        """Test phone number validation accepts various formats"""
        valid_phones = [
            "+1-555-123-4567",
            "+44-20-7946-0958",
            "+1 (555) 123-4567",
            "15551234567",
            "+86-138-0013-8000"
        ]
        
        for phone in valid_phones:
            # Should not raise any exception
            result = self.organization_service._validate_phone_number(phone)
            assert result is not None
            assert len(result.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')) >= 10

    def test_validate_phone_number_invalid(self):
        """Test phone number validation rejects invalid formats"""
        invalid_phones = [
            "123",  # Too short
            "abc-def-ghij",  # Non-numeric
            "+1-555",  # Incomplete
            ""  # Empty
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationException) as exc_info:
                self.organization_service._validate_phone_number(phone)
            assert "Invalid phone number" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_organization_by_id_success(self):
        """Test successful organization retrieval by ID"""
        # Arrange
        org = Organization(
            id=self.sample_org_id,
            name=self.sample_org_data["name"],
            slug=self.sample_org_data["slug"],
            address=self.sample_org_data["address"],
            contact_phone=self.sample_org_data["contact_phone"],
            contact_email=self.sample_org_data["contact_email"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        self.mock_repository.get_by_id.return_value = org

        # Act
        result = await self.organization_service.get_organization_by_id(self.sample_org_id)

        # Assert
        assert result.id == self.sample_org_id
        assert result.name == self.sample_org_data["name"]
        self.mock_repository.get_by_id.assert_called_once_with(self.sample_org_id)

    @pytest.mark.asyncio
    async def test_get_organization_by_id_not_found(self):
        """Test organization retrieval fails when organization doesn't exist"""
        # Arrange
        self.mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(OrganizationNotFoundException) as exc_info:
            await self.organization_service.get_organization_by_id(self.sample_org_id)
        
        assert str(self.sample_org_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_organization_success(self):
        """Test successful organization update"""
        # Arrange
        existing_org = Organization(
            id=self.sample_org_id,
            name="Old Name",
            slug=self.sample_org_data["slug"],
            address="Old Address",
            contact_phone="+1-555-000-0000",
            contact_email="old@example.com",
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        updated_data = {
            "name": "Updated Corp Name",
            "address": "456 New Innovation Blvd, Tech City, TC 12345",
            "contact_phone": "+1-555-987-6543"
        }
        
        updated_org = Organization(
            id=self.sample_org_id,
            name=updated_data["name"],
            slug=self.sample_org_data["slug"],
            address=updated_data["address"],
            contact_phone=updated_data["contact_phone"],
            contact_email="old@example.com",  # Unchanged
            is_active=True,
            created_at=self.current_time,
            updated_at=datetime.utcnow()
        )
        
        self.mock_repository.get_by_id.return_value = existing_org
        self.mock_repository.update.return_value = updated_org

        # Act
        result = await self.organization_service.update_organization(self.sample_org_id, updated_data)

        # Assert
        assert result.name == updated_data["name"]
        assert result.address == updated_data["address"]
        assert result.contact_phone == updated_data["contact_phone"]
        self.mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_organizations_with_pagination(self):
        """Test organization listing with pagination"""
        # Arrange
        orgs = [
            Organization(
                id=uuid4(),
                name=f"Organization {i}",
                slug=f"org-{i}",
                address=f"Address {i}",
                contact_phone=f"+1-555-{i:03d}-0000",
                contact_email=f"admin{i}@org{i}.com",
                is_active=True,
                created_at=self.current_time,
                updated_at=self.current_time
            )
            for i in range(1, 6)
        ]
        
        self.mock_repository.list_organizations.return_value = (orgs[:3], 5)  # 3 results, 5 total

        # Act
        results, total = await self.organization_service.list_organizations(skip=0, limit=3)

        # Assert
        assert len(results) == 3
        assert total == 5
        assert all(org.is_active for org in results)
        self.mock_repository.list_organizations.assert_called_once_with(skip=0, limit=3, active_only=True)

    @pytest.mark.asyncio
    async def test_deactivate_organization(self):
        """Test organization deactivation"""
        # Arrange
        active_org = Organization(
            id=self.sample_org_id,
            name=self.sample_org_data["name"],
            slug=self.sample_org_data["slug"],
            address=self.sample_org_data["address"],
            contact_phone=self.sample_org_data["contact_phone"],
            contact_email=self.sample_org_data["contact_email"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        deactivated_org = Organization(
            id=self.sample_org_id,
            name=self.sample_org_data["name"],
            slug=self.sample_org_data["slug"],
            address=self.sample_org_data["address"],
            contact_phone=self.sample_org_data["contact_phone"],
            contact_email=self.sample_org_data["contact_email"],
            is_active=False,
            created_at=self.current_time,
            updated_at=datetime.utcnow()
        )
        
        self.mock_repository.get_by_id.return_value = active_org
        self.mock_repository.update.return_value = deactivated_org

        # Act
        result = await self.organization_service.deactivate_organization(self.sample_org_id)

        # Assert
        assert result.is_active is False
        self.mock_repository.update.assert_called_once()

    def test_slug_generation(self):
        """Test automatic slug generation from organization name"""
        test_cases = [
            ("TechCorp Training Institute", "techcorp-training-institute"),
            ("University of Technology", "university-of-technology"),
            ("ABC Corp & Associates", "abc-corp-associates"),
            ("   Spaced   Name   ", "spaced-name"),
            ("Name@#$%With^&*Special()", "namewithspecial")
        ]
        
        for name, expected_slug in test_cases:
            result = self.organization_service._generate_slug(name)
            assert result == expected_slug

    @pytest.mark.asyncio
    async def test_create_organization_with_admin_user(self):
        """Test organization creation includes admin user creation"""
        # Arrange
        self.mock_repository.get_by_slug.return_value = None
        
        created_org = Organization(
            id=self.sample_org_id,
            name=self.sample_org_data["name"],
            slug=self.sample_org_data["slug"],
            address=self.sample_org_data["address"],
            contact_phone=self.sample_org_data["contact_phone"],
            contact_email=self.sample_org_data["contact_email"],
            is_active=True,
            created_at=self.current_time,
            updated_at=self.current_time
        )
        
        self.mock_repository.create.return_value = created_org
        
        # Mock user creation service
        with patch('services.organization_management.application.services.organization_service.UserService') as mock_user_service:
            mock_user_service.create_admin_user.return_value = {
                "id": uuid4(),
                "email": self.sample_org_data["admin_email"],
                "full_name": self.sample_org_data["admin_full_name"],
                "role": "organization_admin"
            }

            # Act
            result = await self.organization_service.create_organization_with_admin(self.sample_org_data)

            # Assert
            assert result.id == self.sample_org_id
            # Verify admin user creation was attempted
            # Note: This would need the actual UserService integration

    @pytest.mark.asyncio
    async def test_search_organizations_by_name(self):
        """Test organization search functionality"""
        # Arrange
        search_term = "tech"
        matching_orgs = [
            Organization(
                id=uuid4(),
                name="TechCorp Training",
                slug="techcorp-training",
                address="123 Tech St",
                contact_phone="+1-555-123-0000",
                contact_email="admin@techcorp.com",
                is_active=True,
                created_at=self.current_time,
                updated_at=self.current_time
            ),
            Organization(
                id=uuid4(),
                name="Advanced Technology Institute",
                slug="advanced-tech",
                address="456 Innovation Ave",
                contact_phone="+1-555-456-0000",
                contact_email="info@advancedtech.edu",
                is_active=True,
                created_at=self.current_time,
                updated_at=self.current_time
            )
        ]
        
        self.mock_repository.search_by_name.return_value = matching_orgs

        # Act
        results = await self.organization_service.search_organizations(search_term)

        # Assert
        assert len(results) == 2
        assert all("tech" in org.name.lower() for org in results)
        self.mock_repository.search_by_name.assert_called_once_with(search_term)

    def test_validate_organization_data_complete(self):
        """Test comprehensive organization data validation"""
        # This tests the overall validation logic
        valid_data = self.sample_org_data.copy()
        
        # Should not raise any exceptions
        result = self.organization_service._validate_organization_data(valid_data)
        assert result is True

    def test_validate_organization_data_missing_required(self):
        """Test validation fails with missing required fields"""
        incomplete_data = self.sample_org_data.copy()
        del incomplete_data["name"]  # Remove required field
        
        with pytest.raises(ValidationException) as exc_info:
            self.organization_service._validate_organization_data(incomplete_data)
        
        assert "name" in str(exc_info.value).lower()
        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_error_handling_repository_failure(self):
        """Test service handles repository failures gracefully"""
        # Arrange
        self.mock_repository.create.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(OrganizationException) as exc_info:
            await self.organization_service.create_organization(self.sample_org_data)
        
        assert "Database connection failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
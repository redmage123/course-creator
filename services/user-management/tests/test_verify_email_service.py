"""
Tests for verify_email service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.verify_email_service import Verify_EmailService

@pytest.mark.asyncio
async def test_verify_email_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Verify_EmailService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_verify_email():
    """Test create verify_email method"""
    mock_db = AsyncMock()
    service = Verify_EmailService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_verify_email(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_verify_email():
    """Test get verify_email method"""
    mock_db = AsyncMock()
    service = Verify_EmailService(mock_db)
    
    result = await service.get_verify_email("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_verify_emails():
    """Test list verify_emails method"""
    mock_db = AsyncMock()
    service = Verify_EmailService(mock_db)
    
    result = await service.list_verify_emails()
    assert isinstance(result, list)

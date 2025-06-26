"""
Tests for update_enrollment service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.update_enrollment_service import Update_EnrollmentService

@pytest.mark.asyncio
async def test_update_enrollment_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Update_EnrollmentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_update_enrollment():
    """Test create update_enrollment method"""
    mock_db = AsyncMock()
    service = Update_EnrollmentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_update_enrollment(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_update_enrollment():
    """Test get update_enrollment method"""
    mock_db = AsyncMock()
    service = Update_EnrollmentService(mock_db)
    
    result = await service.get_update_enrollment("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_update_enrollments():
    """Test list update_enrollments method"""
    mock_db = AsyncMock()
    service = Update_EnrollmentService(mock_db)
    
    result = await service.list_update_enrollments()
    assert isinstance(result, list)

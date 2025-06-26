"""
Tests for get_enrollment service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.get_enrollment_service import Get_EnrollmentService

@pytest.mark.asyncio
async def test_get_enrollment_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_EnrollmentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_enrollment():
    """Test create get_enrollment method"""
    mock_db = AsyncMock()
    service = Get_EnrollmentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_enrollment(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_enrollment():
    """Test get get_enrollment method"""
    mock_db = AsyncMock()
    service = Get_EnrollmentService(mock_db)
    
    result = await service.get_get_enrollment("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_enrollments():
    """Test list get_enrollments method"""
    mock_db = AsyncMock()
    service = Get_EnrollmentService(mock_db)
    
    result = await service.list_get_enrollments()
    assert isinstance(result, list)

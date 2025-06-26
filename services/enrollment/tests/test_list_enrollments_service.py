"""
Tests for list_enrollments service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.list_enrollments_service import List_EnrollmentsService

@pytest.mark.asyncio
async def test_list_enrollments_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = List_EnrollmentsService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_list_enrollments():
    """Test create list_enrollments method"""
    mock_db = AsyncMock()
    service = List_EnrollmentsService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_list_enrollments(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_list_enrollments():
    """Test get list_enrollments method"""
    mock_db = AsyncMock()
    service = List_EnrollmentsService(mock_db)
    
    result = await service.get_list_enrollments("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_list_enrollmentss():
    """Test list list_enrollmentss method"""
    mock_db = AsyncMock()
    service = List_EnrollmentsService(mock_db)
    
    result = await service.list_list_enrollmentss()
    assert isinstance(result, list)

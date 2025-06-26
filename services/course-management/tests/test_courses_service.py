"""
Tests for courses service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.courses_service import CoursesService

@pytest.mark.asyncio
async def test_courses_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = CoursesService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_courses():
    """Test create courses method"""
    mock_db = AsyncMock()
    service = CoursesService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_courses(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_courses():
    """Test get courses method"""
    mock_db = AsyncMock()
    service = CoursesService(mock_db)
    
    result = await service.get_courses("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_coursess():
    """Test list coursess method"""
    mock_db = AsyncMock()
    service = CoursesService(mock_db)
    
    result = await service.list_coursess()
    assert isinstance(result, list)

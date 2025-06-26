"""
Tests for get_course service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.get_course_service import Get_CourseService

@pytest.mark.asyncio
async def test_get_course_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_CourseService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_course():
    """Test create get_course method"""
    mock_db = AsyncMock()
    service = Get_CourseService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_course(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_course():
    """Test get get_course method"""
    mock_db = AsyncMock()
    service = Get_CourseService(mock_db)
    
    result = await service.get_get_course("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_courses():
    """Test list get_courses method"""
    mock_db = AsyncMock()
    service = Get_CourseService(mock_db)
    
    result = await service.list_get_courses()
    assert isinstance(result, list)

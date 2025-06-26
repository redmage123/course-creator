"""
Tests for create_course service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.create_course_service import Create_CourseService

@pytest.mark.asyncio
async def test_create_course_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Create_CourseService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_create_course():
    """Test create create_course method"""
    mock_db = AsyncMock()
    service = Create_CourseService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_create_course(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_create_course():
    """Test get create_course method"""
    mock_db = AsyncMock()
    service = Create_CourseService(mock_db)
    
    result = await service.get_create_course("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_create_courses():
    """Test list create_courses method"""
    mock_db = AsyncMock()
    service = Create_CourseService(mock_db)
    
    result = await service.list_create_courses()
    assert isinstance(result, list)

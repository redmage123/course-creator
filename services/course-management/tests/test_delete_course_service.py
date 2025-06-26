"""
Tests for delete_course service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.delete_course_service import Delete_CourseService

@pytest.mark.asyncio
async def test_delete_course_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Delete_CourseService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_delete_course():
    """Test create delete_course method"""
    mock_db = AsyncMock()
    service = Delete_CourseService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_delete_course(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_delete_course():
    """Test get delete_course method"""
    mock_db = AsyncMock()
    service = Delete_CourseService(mock_db)
    
    result = await service.get_delete_course("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_delete_courses():
    """Test list delete_courses method"""
    mock_db = AsyncMock()
    service = Delete_CourseService(mock_db)
    
    result = await service.list_delete_courses()
    assert isinstance(result, list)

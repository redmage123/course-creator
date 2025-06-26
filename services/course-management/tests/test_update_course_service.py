"""
Tests for update_course service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.update_course_service import Update_CourseService

@pytest.mark.asyncio
async def test_update_course_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Update_CourseService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_update_course():
    """Test create update_course method"""
    mock_db = AsyncMock()
    service = Update_CourseService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_update_course(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_update_course():
    """Test get update_course method"""
    mock_db = AsyncMock()
    service = Update_CourseService(mock_db)
    
    result = await service.get_update_course("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_update_courses():
    """Test list update_courses method"""
    mock_db = AsyncMock()
    service = Update_CourseService(mock_db)
    
    result = await service.list_update_courses()
    assert isinstance(result, list)

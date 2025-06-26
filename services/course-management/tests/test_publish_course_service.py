"""
Tests for publish_course service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.publish_course_service import Publish_CourseService

@pytest.mark.asyncio
async def test_publish_course_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Publish_CourseService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_publish_course():
    """Test create publish_course method"""
    mock_db = AsyncMock()
    service = Publish_CourseService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_publish_course(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_publish_course():
    """Test get publish_course method"""
    mock_db = AsyncMock()
    service = Publish_CourseService(mock_db)
    
    result = await service.get_publish_course("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_publish_courses():
    """Test list publish_courses method"""
    mock_db = AsyncMock()
    service = Publish_CourseService(mock_db)
    
    result = await service.list_publish_courses()
    assert isinstance(result, list)

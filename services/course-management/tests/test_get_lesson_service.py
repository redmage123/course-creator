"""
Tests for get_lesson service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.get_lesson_service import Get_LessonService

@pytest.mark.asyncio
async def test_get_lesson_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_LessonService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_lesson():
    """Test create get_lesson method"""
    mock_db = AsyncMock()
    service = Get_LessonService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_lesson(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_lesson():
    """Test get get_lesson method"""
    mock_db = AsyncMock()
    service = Get_LessonService(mock_db)
    
    result = await service.get_get_lesson("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_lessons():
    """Test list get_lessons method"""
    mock_db = AsyncMock()
    service = Get_LessonService(mock_db)
    
    result = await service.list_get_lessons()
    assert isinstance(result, list)

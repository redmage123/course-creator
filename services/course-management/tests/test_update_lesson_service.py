"""
Tests for update_lesson service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.update_lesson_service import Update_LessonService

@pytest.mark.asyncio
async def test_update_lesson_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Update_LessonService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_update_lesson():
    """Test create update_lesson method"""
    mock_db = AsyncMock()
    service = Update_LessonService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_update_lesson(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_update_lesson():
    """Test get update_lesson method"""
    mock_db = AsyncMock()
    service = Update_LessonService(mock_db)
    
    result = await service.get_update_lesson("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_update_lessons():
    """Test list update_lessons method"""
    mock_db = AsyncMock()
    service = Update_LessonService(mock_db)
    
    result = await service.list_update_lessons()
    assert isinstance(result, list)

"""
Tests for delete_lesson service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.delete_lesson_service import Delete_LessonService

@pytest.mark.asyncio
async def test_delete_lesson_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Delete_LessonService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_delete_lesson():
    """Test create delete_lesson method"""
    mock_db = AsyncMock()
    service = Delete_LessonService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_delete_lesson(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_delete_lesson():
    """Test get delete_lesson method"""
    mock_db = AsyncMock()
    service = Delete_LessonService(mock_db)
    
    result = await service.get_delete_lesson("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_delete_lessons():
    """Test list delete_lessons method"""
    mock_db = AsyncMock()
    service = Delete_LessonService(mock_db)
    
    result = await service.list_delete_lessons()
    assert isinstance(result, list)

"""
Tests for add_lesson service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.add_lesson_service import Add_LessonService

@pytest.mark.asyncio
async def test_add_lesson_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Add_LessonService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_add_lesson():
    """Test create add_lesson method"""
    mock_db = AsyncMock()
    service = Add_LessonService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_add_lesson(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_add_lesson():
    """Test get add_lesson method"""
    mock_db = AsyncMock()
    service = Add_LessonService(mock_db)
    
    result = await service.get_add_lesson("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_add_lessons():
    """Test list add_lessons method"""
    mock_db = AsyncMock()
    service = Add_LessonService(mock_db)
    
    result = await service.list_add_lessons()
    assert isinstance(result, list)

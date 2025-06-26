"""
Tests for attach_to_lesson service of content-management
"""

import pytest
from unittest.mock import AsyncMock
from services.attach_to_lesson_service import Attach_To_LessonService

@pytest.mark.asyncio
async def test_attach_to_lesson_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Attach_To_LessonService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_attach_to_lesson():
    """Test create attach_to_lesson method"""
    mock_db = AsyncMock()
    service = Attach_To_LessonService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_attach_to_lesson(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_attach_to_lesson():
    """Test get attach_to_lesson method"""
    mock_db = AsyncMock()
    service = Attach_To_LessonService(mock_db)
    
    result = await service.get_attach_to_lesson("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_attach_to_lessons():
    """Test list attach_to_lessons method"""
    mock_db = AsyncMock()
    service = Attach_To_LessonService(mock_db)
    
    result = await service.list_attach_to_lessons()
    assert isinstance(result, list)

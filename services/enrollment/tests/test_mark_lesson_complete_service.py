"""
Tests for mark_lesson_complete service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.mark_lesson_complete_service import Mark_Lesson_CompleteService

@pytest.mark.asyncio
async def test_mark_lesson_complete_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Mark_Lesson_CompleteService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_mark_lesson_complete():
    """Test create mark_lesson_complete method"""
    mock_db = AsyncMock()
    service = Mark_Lesson_CompleteService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_mark_lesson_complete(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_mark_lesson_complete():
    """Test get mark_lesson_complete method"""
    mock_db = AsyncMock()
    service = Mark_Lesson_CompleteService(mock_db)
    
    result = await service.get_mark_lesson_complete("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_mark_lesson_completes():
    """Test list mark_lesson_completes method"""
    mock_db = AsyncMock()
    service = Mark_Lesson_CompleteService(mock_db)
    
    result = await service.list_mark_lesson_completes()
    assert isinstance(result, list)

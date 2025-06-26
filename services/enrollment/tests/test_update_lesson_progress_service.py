"""
Tests for update_lesson_progress service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.update_lesson_progress_service import Update_Lesson_ProgressService

@pytest.mark.asyncio
async def test_update_lesson_progress_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Update_Lesson_ProgressService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_update_lesson_progress():
    """Test create update_lesson_progress method"""
    mock_db = AsyncMock()
    service = Update_Lesson_ProgressService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_update_lesson_progress(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_update_lesson_progress():
    """Test get update_lesson_progress method"""
    mock_db = AsyncMock()
    service = Update_Lesson_ProgressService(mock_db)
    
    result = await service.get_update_lesson_progress("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_update_lesson_progresss():
    """Test list update_lesson_progresss method"""
    mock_db = AsyncMock()
    service = Update_Lesson_ProgressService(mock_db)
    
    result = await service.list_update_lesson_progresss()
    assert isinstance(result, list)

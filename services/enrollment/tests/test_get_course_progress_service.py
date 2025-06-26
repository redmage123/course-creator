"""
Tests for get_course_progress service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.get_course_progress_service import Get_Course_ProgressService

@pytest.mark.asyncio
async def test_get_course_progress_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_Course_ProgressService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_course_progress():
    """Test create get_course_progress method"""
    mock_db = AsyncMock()
    service = Get_Course_ProgressService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_course_progress(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_course_progress():
    """Test get get_course_progress method"""
    mock_db = AsyncMock()
    service = Get_Course_ProgressService(mock_db)
    
    result = await service.get_get_course_progress("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_course_progresss():
    """Test list get_course_progresss method"""
    mock_db = AsyncMock()
    service = Get_Course_ProgressService(mock_db)
    
    result = await service.list_get_course_progresss()
    assert isinstance(result, list)

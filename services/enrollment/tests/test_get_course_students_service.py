"""
Tests for get_course_students service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.get_course_students_service import Get_Course_StudentsService

@pytest.mark.asyncio
async def test_get_course_students_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_Course_StudentsService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_course_students():
    """Test create get_course_students method"""
    mock_db = AsyncMock()
    service = Get_Course_StudentsService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_course_students(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_course_students():
    """Test get get_course_students method"""
    mock_db = AsyncMock()
    service = Get_Course_StudentsService(mock_db)
    
    result = await service.get_get_course_students("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_course_studentss():
    """Test list get_course_studentss method"""
    mock_db = AsyncMock()
    service = Get_Course_StudentsService(mock_db)
    
    result = await service.list_get_course_studentss()
    assert isinstance(result, list)

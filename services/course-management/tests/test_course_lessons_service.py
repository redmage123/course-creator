"""
Tests for course_lessons service of course-management
"""

import pytest
from unittest.mock import AsyncMock
from services.course_lessons_service import Course_LessonsService

@pytest.mark.asyncio
async def test_course_lessons_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Course_LessonsService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_course_lessons():
    """Test create course_lessons method"""
    mock_db = AsyncMock()
    service = Course_LessonsService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_course_lessons(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_course_lessons():
    """Test get course_lessons method"""
    mock_db = AsyncMock()
    service = Course_LessonsService(mock_db)
    
    result = await service.get_course_lessons("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_course_lessonss():
    """Test list course_lessonss method"""
    mock_db = AsyncMock()
    service = Course_LessonsService(mock_db)
    
    result = await service.list_course_lessonss()
    assert isinstance(result, list)

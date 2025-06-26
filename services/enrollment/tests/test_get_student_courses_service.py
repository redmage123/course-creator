"""
Tests for get_student_courses service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.get_student_courses_service import Get_Student_CoursesService

@pytest.mark.asyncio
async def test_get_student_courses_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_Student_CoursesService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_student_courses():
    """Test create get_student_courses method"""
    mock_db = AsyncMock()
    service = Get_Student_CoursesService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_student_courses(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_student_courses():
    """Test get get_student_courses method"""
    mock_db = AsyncMock()
    service = Get_Student_CoursesService(mock_db)
    
    result = await service.get_get_student_courses("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_student_coursess():
    """Test list get_student_coursess method"""
    mock_db = AsyncMock()
    service = Get_Student_CoursesService(mock_db)
    
    result = await service.list_get_student_coursess()
    assert isinstance(result, list)

"""
Tests for enroll_student service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.enroll_student_service import Enroll_StudentService

@pytest.mark.asyncio
async def test_enroll_student_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Enroll_StudentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_enroll_student():
    """Test create enroll_student method"""
    mock_db = AsyncMock()
    service = Enroll_StudentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_enroll_student(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_enroll_student():
    """Test get enroll_student method"""
    mock_db = AsyncMock()
    service = Enroll_StudentService(mock_db)
    
    result = await service.get_enroll_student("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_enroll_students():
    """Test list enroll_students method"""
    mock_db = AsyncMock()
    service = Enroll_StudentService(mock_db)
    
    result = await service.list_enroll_students()
    assert isinstance(result, list)

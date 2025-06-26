"""
Tests for unenroll_student service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.unenroll_student_service import Unenroll_StudentService

@pytest.mark.asyncio
async def test_unenroll_student_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Unenroll_StudentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_unenroll_student():
    """Test create unenroll_student method"""
    mock_db = AsyncMock()
    service = Unenroll_StudentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_unenroll_student(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_unenroll_student():
    """Test get unenroll_student method"""
    mock_db = AsyncMock()
    service = Unenroll_StudentService(mock_db)
    
    result = await service.get_unenroll_student("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_unenroll_students():
    """Test list unenroll_students method"""
    mock_db = AsyncMock()
    service = Unenroll_StudentService(mock_db)
    
    result = await service.list_unenroll_students()
    assert isinstance(result, list)

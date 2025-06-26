"""
Tests for get_content service of content-management
"""

import pytest
from unittest.mock import AsyncMock
from services.get_content_service import Get_ContentService

@pytest.mark.asyncio
async def test_get_content_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_ContentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_content():
    """Test create get_content method"""
    mock_db = AsyncMock()
    service = Get_ContentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_content(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_content():
    """Test get get_content method"""
    mock_db = AsyncMock()
    service = Get_ContentService(mock_db)
    
    result = await service.get_get_content("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_contents():
    """Test list get_contents method"""
    mock_db = AsyncMock()
    service = Get_ContentService(mock_db)
    
    result = await service.list_get_contents()
    assert isinstance(result, list)

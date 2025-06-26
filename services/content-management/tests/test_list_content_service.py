"""
Tests for list_content service of content-management
"""

import pytest
from unittest.mock import AsyncMock
from services.list_content_service import List_ContentService

@pytest.mark.asyncio
async def test_list_content_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = List_ContentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_list_content():
    """Test create list_content method"""
    mock_db = AsyncMock()
    service = List_ContentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_list_content(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_list_content():
    """Test get list_content method"""
    mock_db = AsyncMock()
    service = List_ContentService(mock_db)
    
    result = await service.get_list_content("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_list_contents():
    """Test list list_contents method"""
    mock_db = AsyncMock()
    service = List_ContentService(mock_db)
    
    result = await service.list_list_contents()
    assert isinstance(result, list)

"""
Tests for delete_content service of content-management
"""

import pytest
from unittest.mock import AsyncMock
from services.delete_content_service import Delete_ContentService

@pytest.mark.asyncio
async def test_delete_content_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Delete_ContentService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_delete_content():
    """Test create delete_content method"""
    mock_db = AsyncMock()
    service = Delete_ContentService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_delete_content(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_delete_content():
    """Test get delete_content method"""
    mock_db = AsyncMock()
    service = Delete_ContentService(mock_db)
    
    result = await service.get_delete_content("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_delete_contents():
    """Test list delete_contents method"""
    mock_db = AsyncMock()
    service = Delete_ContentService(mock_db)
    
    result = await service.list_delete_contents()
    assert isinstance(result, list)

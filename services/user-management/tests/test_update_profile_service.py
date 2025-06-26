"""
Tests for update_profile service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.update_profile_service import Update_ProfileService

@pytest.mark.asyncio
async def test_update_profile_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Update_ProfileService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_update_profile():
    """Test create update_profile method"""
    mock_db = AsyncMock()
    service = Update_ProfileService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_update_profile(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_update_profile():
    """Test get update_profile method"""
    mock_db = AsyncMock()
    service = Update_ProfileService(mock_db)
    
    result = await service.get_update_profile("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_update_profiles():
    """Test list update_profiles method"""
    mock_db = AsyncMock()
    service = Update_ProfileService(mock_db)
    
    result = await service.list_update_profiles()
    assert isinstance(result, list)

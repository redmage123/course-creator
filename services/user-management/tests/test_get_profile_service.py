"""
Tests for get_profile service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.get_profile_service import Get_ProfileService

@pytest.mark.asyncio
async def test_get_profile_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_ProfileService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_profile():
    """Test create get_profile method"""
    mock_db = AsyncMock()
    service = Get_ProfileService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_profile(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_profile():
    """Test get get_profile method"""
    mock_db = AsyncMock()
    service = Get_ProfileService(mock_db)
    
    result = await service.get_get_profile("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_profiles():
    """Test list get_profiles method"""
    mock_db = AsyncMock()
    service = Get_ProfileService(mock_db)
    
    result = await service.list_get_profiles()
    assert isinstance(result, list)

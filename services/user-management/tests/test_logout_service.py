"""
Tests for logout service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.logout_service import LogoutService

@pytest.mark.asyncio
async def test_logout_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = LogoutService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_logout():
    """Test create logout method"""
    mock_db = AsyncMock()
    service = LogoutService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_logout(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_logout():
    """Test get logout method"""
    mock_db = AsyncMock()
    service = LogoutService(mock_db)
    
    result = await service.get_logout("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_logouts():
    """Test list logouts method"""
    mock_db = AsyncMock()
    service = LogoutService(mock_db)
    
    result = await service.list_logouts()
    assert isinstance(result, list)

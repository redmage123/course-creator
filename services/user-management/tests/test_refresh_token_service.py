"""
Tests for refresh_token service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.refresh_token_service import Refresh_TokenService

@pytest.mark.asyncio
async def test_refresh_token_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Refresh_TokenService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_refresh_token():
    """Test create refresh_token method"""
    mock_db = AsyncMock()
    service = Refresh_TokenService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_refresh_token(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_refresh_token():
    """Test get refresh_token method"""
    mock_db = AsyncMock()
    service = Refresh_TokenService(mock_db)
    
    result = await service.get_refresh_token("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_refresh_tokens():
    """Test list refresh_tokens method"""
    mock_db = AsyncMock()
    service = Refresh_TokenService(mock_db)
    
    result = await service.list_refresh_tokens()
    assert isinstance(result, list)

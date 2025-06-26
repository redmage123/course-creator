"""
Tests for login service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.login_service import LoginService

@pytest.mark.asyncio
async def test_login_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = LoginService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_login():
    """Test create login method"""
    mock_db = AsyncMock()
    service = LoginService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_login(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_login():
    """Test get login method"""
    mock_db = AsyncMock()
    service = LoginService(mock_db)
    
    result = await service.get_login("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_logins():
    """Test list logins method"""
    mock_db = AsyncMock()
    service = LoginService(mock_db)
    
    result = await service.list_logins()
    assert isinstance(result, list)

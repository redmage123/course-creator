"""
Tests for list_users service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.list_users_service import List_UsersService

@pytest.mark.asyncio
async def test_list_users_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = List_UsersService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_list_users():
    """Test create list_users method"""
    mock_db = AsyncMock()
    service = List_UsersService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_list_users(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_list_users():
    """Test get list_users method"""
    mock_db = AsyncMock()
    service = List_UsersService(mock_db)
    
    result = await service.get_list_users("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_list_userss():
    """Test list list_userss method"""
    mock_db = AsyncMock()
    service = List_UsersService(mock_db)
    
    result = await service.list_list_userss()
    assert isinstance(result, list)

"""
Tests for register service of user-management
"""

import pytest
from unittest.mock import AsyncMock
from services.register_service import RegisterService

@pytest.mark.asyncio
async def test_register_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = RegisterService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_register():
    """Test create register method"""
    mock_db = AsyncMock()
    service = RegisterService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_register(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_register():
    """Test get register method"""
    mock_db = AsyncMock()
    service = RegisterService(mock_db)
    
    result = await service.get_register("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_registers():
    """Test list registers method"""
    mock_db = AsyncMock()
    service = RegisterService(mock_db)
    
    result = await service.list_registers()
    assert isinstance(result, list)

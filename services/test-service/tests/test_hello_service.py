"""
Tests for hello service of test-service
"""

import pytest
from unittest.mock import AsyncMock
from services.hello_service import HelloService

@pytest.mark.asyncio
async def test_hello_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = HelloService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_hello():
    """Test create hello method"""
    mock_db = AsyncMock()
    service = HelloService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_hello(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_hello():
    """Test get hello method"""
    mock_db = AsyncMock()
    service = HelloService(mock_db)
    
    result = await service.get_hello("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_hellos():
    """Test list hellos method"""
    mock_db = AsyncMock()
    service = HelloService(mock_db)
    
    result = await service.list_hellos()
    assert isinstance(result, list)

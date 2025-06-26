"""
Tests for get_certificates service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.get_certificates_service import Get_CertificatesService

@pytest.mark.asyncio
async def test_get_certificates_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Get_CertificatesService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_get_certificates():
    """Test create get_certificates method"""
    mock_db = AsyncMock()
    service = Get_CertificatesService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_get_certificates(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_get_certificates():
    """Test get get_certificates method"""
    mock_db = AsyncMock()
    service = Get_CertificatesService(mock_db)
    
    result = await service.get_get_certificates("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_get_certificatess():
    """Test list get_certificatess method"""
    mock_db = AsyncMock()
    service = Get_CertificatesService(mock_db)
    
    result = await service.list_get_certificatess()
    assert isinstance(result, list)

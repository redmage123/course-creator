"""
Tests for issue_certificate service of enrollment
"""

import pytest
from unittest.mock import AsyncMock
from services.issue_certificate_service import Issue_CertificateService

@pytest.mark.asyncio
async def test_issue_certificate_service_creation():
    """Test service creation"""
    mock_db = AsyncMock()
    service = Issue_CertificateService(mock_db)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_create_issue_certificate():
    """Test create issue_certificate method"""
    mock_db = AsyncMock()
    service = Issue_CertificateService(mock_db)
    
    data = {"test": "data"}
    result = await service.create_issue_certificate(data)
    
    assert result is not None
    assert "message" in result

@pytest.mark.asyncio
async def test_get_issue_certificate():
    """Test get issue_certificate method"""
    mock_db = AsyncMock()
    service = Issue_CertificateService(mock_db)
    
    result = await service.get_issue_certificate("test-id")
    # This will be None until implemented
    assert result is None

@pytest.mark.asyncio
async def test_list_issue_certificates():
    """Test list issue_certificates method"""
    mock_db = AsyncMock()
    service = Issue_CertificateService(mock_db)
    
    result = await service.list_issue_certificates()
    assert isinstance(result, list)

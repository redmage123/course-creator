"""
Integration tests for content-management service
"""

import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_integration(async_client):
    """Test full service integration"""
    
    # Test health check
    response = await async_client.get("/health")
    assert response.status_code == 200
    
    # Test service is responsive
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.integration
async def test_endpoints_integration(async_client):
    """Test all endpoints are accessible"""
    
    endpoints = ["/upload_content/", "/get_content/", "/update_content/", "/delete_content/", "/list_content/", "/get_content_by_lesson/", "/attach_to_lesson/", "/process_video/", "/get_processing_status/"]
    
    for endpoint in endpoints:
        response = await async_client.get(endpoint)
        # Should not return 500 (server error)
        assert response.status_code < 500

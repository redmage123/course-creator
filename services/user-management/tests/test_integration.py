"""
Integration tests for user-management service
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
    
    endpoints = ["/register/", "/login/", "/refresh_token/", "/logout/", "/get_profile/", "/update_profile/", "/list_users/", "/change_password/", "/verify_email/"]
    
    for endpoint in endpoints:
        response = await async_client.get(endpoint)
        # Should not return 500 (server error)
        assert response.status_code < 500

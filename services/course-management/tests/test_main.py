"""
Tests for main application of course-management service
"""

import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "course-management"

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "course-management"
    assert "message" in data

@pytest.mark.asyncio
async def test_async_health_check(async_client):
    """Test health check with async client"""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

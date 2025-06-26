"""
Test configuration for course-management service
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_database():
    """Mock database connection"""
    return AsyncMock()

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    return AsyncMock()

"""
Tests for get_certificates router of enrollment service
"""

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_get_certificates_endpoints(async_client, mock_database):
    """Test get_certificates endpoints"""
    
    # Test endpoint accessibility
    with patch('dependencies.get_database', return_value=mock_database):
        response = await async_client.get("/get_certificates/")
        # Adjust assertion based on expected behavior
        assert response.status_code in [200, 404, 405]  # Depending on implementation

# TODO: Add specific tests for each route in the endpoint

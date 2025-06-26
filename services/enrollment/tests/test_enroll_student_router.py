"""
Tests for enroll_student router of enrollment service
"""

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_enroll_student_endpoints(async_client, mock_database):
    """Test enroll_student endpoints"""
    
    # Test endpoint accessibility
    with patch('dependencies.get_database', return_value=mock_database):
        response = await async_client.get("/enroll_student/")
        # Adjust assertion based on expected behavior
        assert response.status_code in [200, 404, 405]  # Depending on implementation

# TODO: Add specific tests for each route in the endpoint

"""
Pytest configuration and fixtures for Course Management tests.

This file provides test fixtures and mocks for unit testing course
management services without requiring external dependencies.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock


@pytest.fixture
def mock_http_client():
    """
    Mock httpx.AsyncClient for testing HTTP requests.

    BUSINESS CONTEXT:
    Unit tests should not make actual HTTP requests to external services.
    This fixture provides a mock client that simulates successful API responses.
    """
    with patch('httpx.AsyncClient') as mock_client:
        # Configure mock client
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student'
        }

        # Configure async context manager
        mock_instance = MagicMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.post = AsyncMock(return_value=mock_response)

        mock_client.return_value = mock_instance

        yield mock_client


@pytest.fixture
def mock_user_service_account_not_found():
    """
    Mock User Management Service returning 404 (account not found).

    BUSINESS CONTEXT:
    Tests bulk enrollment with new students who don't have existing accounts.
    """
    with patch('httpx.AsyncClient') as mock_client:
        # Mock response for GET (account lookup) - returns 404
        mock_get_response = MagicMock()
        mock_get_response.status_code = 404

        # Mock response for POST (account creation) - returns 201
        mock_create_response = MagicMock()
        mock_create_response.status_code = 201
        # json() should return a dict, not a coroutine
        mock_create_response.json = MagicMock(return_value={
            'id': 'new-user-123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student'
        })

        mock_instance = MagicMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=mock_get_response)
        mock_instance.post = AsyncMock(return_value=mock_create_response)

        mock_client.return_value = mock_instance

        yield mock_client


@pytest.fixture
def mock_user_service_account_exists():
    """
    Mock User Management Service returning existing account.

    BUSINESS CONTEXT:
    Tests bulk enrollment with existing students to verify account creation is skipped.
    """
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        # json() should return a dict, not a coroutine
        mock_response.json = MagicMock(return_value={
            'id': 'existing-user-123',
            'email': 'existing@example.com',
            'first_name': 'Existing',
            'last_name': 'User',
            'role': 'student'
        })

        mock_instance = MagicMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.post = AsyncMock(return_value=mock_response)

        mock_client.return_value = mock_instance

        yield mock_client


@pytest.fixture
def mock_db_connection():
    """
    Mock database connection for DAO testing.

    BUSINESS CONTEXT:
    Unit tests for DAOs should not require actual database connections.
    This fixture provides a properly mocked psycopg2 connection that supports
    context manager protocol (with statements) and cursor operations.

    USAGE:
    The mock supports the pattern: with conn.cursor(cursor_factory=...) as cursor:
    """
    # Create the cursor mock
    cursor_mock = MagicMock()
    
    # Create a context manager mock for cursor
    cursor_context_manager = MagicMock()
    cursor_context_manager.__enter__ = MagicMock(return_value=cursor_mock)
    cursor_context_manager.__exit__ = MagicMock(return_value=False)
    
    # Create the connection mock
    conn_mock = MagicMock()
    
    # Make conn.cursor() return the context manager
    conn_mock.cursor = MagicMock(return_value=cursor_context_manager)
    conn_mock.commit = MagicMock()
    conn_mock.rollback = MagicMock()
    
    return conn_mock

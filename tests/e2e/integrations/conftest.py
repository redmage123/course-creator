"""
Pytest fixtures for external API integration E2E tests

BUSINESS CONTEXT:
Provides shared fixtures and configuration for E2E tests that interact with
external APIs (Slack, Zoom, Microsoft Teams, LTI providers, etc.).

These tests require real API credentials and are designed to verify actual
integration functionality in a production-like environment.

SETUP REQUIREMENTS:
Set the following environment variables to run these tests:
- SLACK_BOT_TOKEN: Slack bot OAuth token (xoxb-...)
- SLACK_WORKSPACE_ID: Slack workspace ID (T...)
- ZOOM_API_KEY: Zoom API key
- ZOOM_API_SECRET: Zoom API secret
- TEAMS_CLIENT_ID: Microsoft Teams app client ID
- TEAMS_CLIENT_SECRET: Microsoft Teams app client secret
- TEAMS_TENANT_ID: Microsoft Teams tenant ID
- LTI_PLATFORM_URL: LTI platform base URL
- LTI_CLIENT_ID: LTI client ID
- LTI_ISSUER: LTI issuer URL

If credentials are not available, tests will be automatically skipped with
appropriate skip messages.
"""

import os
import pytest
from typing import Optional


# ============================================================================
# CREDENTIAL AVAILABILITY CHECKS
# ============================================================================

def has_slack_credentials() -> bool:
    """Check if Slack API credentials are available"""
    return bool(
        os.getenv("SLACK_BOT_TOKEN") and
        os.getenv("SLACK_WORKSPACE_ID")
    )


def has_zoom_credentials() -> bool:
    """Check if Zoom API credentials are available"""
    return bool(
        os.getenv("ZOOM_API_KEY") and
        os.getenv("ZOOM_API_SECRET")
    )


def has_teams_credentials() -> bool:
    """Check if Microsoft Teams API credentials are available"""
    return bool(
        os.getenv("TEAMS_CLIENT_ID") and
        os.getenv("TEAMS_CLIENT_SECRET") and
        os.getenv("TEAMS_TENANT_ID")
    )


def has_lti_credentials() -> bool:
    """Check if LTI provider credentials are available"""
    return bool(
        os.getenv("LTI_PLATFORM_URL") and
        os.getenv("LTI_CLIENT_ID") and
        os.getenv("LTI_ISSUER")
    )


def has_calendar_credentials() -> bool:
    """Check if calendar provider credentials are available"""
    return bool(
        os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and
        os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
    )


# ============================================================================
# SKIP MARKERS
# ============================================================================

skip_if_no_slack = pytest.mark.skipif(
    not has_slack_credentials(),
    reason="Slack API credentials not available. Set SLACK_BOT_TOKEN and SLACK_WORKSPACE_ID"
)

skip_if_no_zoom = pytest.mark.skipif(
    not has_zoom_credentials(),
    reason="Zoom API credentials not available. Set ZOOM_API_KEY and ZOOM_API_SECRET"
)

skip_if_no_teams = pytest.mark.skipif(
    not has_teams_credentials(),
    reason="Microsoft Teams credentials not available. Set TEAMS_CLIENT_ID, TEAMS_CLIENT_SECRET, TEAMS_TENANT_ID"
)

skip_if_no_lti = pytest.mark.skipif(
    not has_lti_credentials(),
    reason="LTI credentials not available. Set LTI_PLATFORM_URL, LTI_CLIENT_ID, LTI_ISSUER"
)

skip_if_no_calendar = pytest.mark.skipif(
    not has_calendar_credentials(),
    reason="Calendar API credentials not available. Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET"
)


# ============================================================================
# CREDENTIAL FIXTURES
# ============================================================================

@pytest.fixture
def slack_credentials() -> Optional[dict]:
    """
    Fixture providing Slack API credentials from environment variables

    Returns:
        dict with bot_token and workspace_id, or None if not available
    """
    if not has_slack_credentials():
        return None

    return {
        "bot_token": os.getenv("SLACK_BOT_TOKEN"),
        "workspace_id": os.getenv("SLACK_WORKSPACE_ID")
    }


@pytest.fixture
def zoom_credentials() -> Optional[dict]:
    """
    Fixture providing Zoom API credentials from environment variables

    Returns:
        dict with api_key and api_secret, or None if not available
    """
    if not has_zoom_credentials():
        return None

    return {
        "api_key": os.getenv("ZOOM_API_KEY"),
        "api_secret": os.getenv("ZOOM_API_SECRET")
    }


@pytest.fixture
def teams_credentials() -> Optional[dict]:
    """
    Fixture providing Microsoft Teams API credentials from environment variables

    Returns:
        dict with client_id, client_secret, and tenant_id, or None if not available
    """
    if not has_teams_credentials():
        return None

    return {
        "client_id": os.getenv("TEAMS_CLIENT_ID"),
        "client_secret": os.getenv("TEAMS_CLIENT_SECRET"),
        "tenant_id": os.getenv("TEAMS_TENANT_ID")
    }


@pytest.fixture
def lti_credentials() -> Optional[dict]:
    """
    Fixture providing LTI platform credentials from environment variables

    Returns:
        dict with platform_url, client_id, and issuer, or None if not available
    """
    if not has_lti_credentials():
        return None

    return {
        "platform_url": os.getenv("LTI_PLATFORM_URL"),
        "client_id": os.getenv("LTI_CLIENT_ID"),
        "issuer": os.getenv("LTI_ISSUER"),
        "jwks_url": os.getenv("LTI_JWKS_URL"),
        "auth_login_url": os.getenv("LTI_AUTH_LOGIN_URL"),
        "auth_token_url": os.getenv("LTI_AUTH_TOKEN_URL")
    }


@pytest.fixture
def calendar_credentials() -> Optional[dict]:
    """
    Fixture providing calendar provider credentials from environment variables

    Returns:
        dict with client_id and client_secret, or None if not available
    """
    if not has_calendar_credentials():
        return None

    return {
        "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8000/auth/callback")
    }


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def e2e_integrations_config():
    """
    Session-scoped configuration for E2E integration tests

    Returns:
        dict with test configuration options
    """
    return {
        "timeout": int(os.getenv("E2E_TIMEOUT", "30")),  # seconds
        "retry_count": int(os.getenv("E2E_RETRY_COUNT", "3")),
        "cleanup_after_test": os.getenv("E2E_CLEANUP", "true").lower() == "true",
        "verbose_logging": os.getenv("E2E_VERBOSE", "false").lower() == "true"
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Register custom markers for E2E integration tests
    """
    config.addinivalue_line(
        "markers",
        "e2e: mark test as E2E integration test requiring external API access"
    )
    config.addinivalue_line(
        "markers",
        "slack_api: mark test as requiring Slack API credentials"
    )
    config.addinivalue_line(
        "markers",
        "zoom_api: mark test as requiring Zoom API credentials"
    )
    config.addinivalue_line(
        "markers",
        "teams_api: mark test as requiring Microsoft Teams API credentials"
    )
    config.addinivalue_line(
        "markers",
        "lti_api: mark test as requiring LTI platform credentials"
    )
    config.addinivalue_line(
        "markers",
        "calendar_api: mark test as requiring calendar provider credentials"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests in this directory with @pytest.mark.e2e
    """
    for item in items:
        if "tests/e2e/integrations" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

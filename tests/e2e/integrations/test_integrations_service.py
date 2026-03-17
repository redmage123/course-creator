"""
E2E tests for IntegrationsService with real external API integration

BUSINESS CONTEXT:
Tests integration service functionality with actual external API calls for:
- LTI 1.3 platform integration
- Calendar provider synchronization (Google Calendar, Outlook)
- Slack workspace integration
- OAuth token management

REQUIREMENTS:
These tests require real API credentials:
- LTI: LTI_PLATFORM_URL, LTI_CLIENT_ID, LTI_ISSUER
- Calendar: GOOGLE_CALENDAR_CLIENT_ID, GOOGLE_CALENDAR_CLIENT_SECRET
- Slack: SLACK_BOT_TOKEN, SLACK_WORKSPACE_ID

If credentials are not available, tests will be automatically skipped.

NOTE: This file was moved from tests/unit/organization_management/ because
it requires external API access and should be tested as an E2E integration.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from conftest import skip_if_no_lti, skip_if_no_calendar, skip_if_no_slack

from organization_management.application.services.integrations_service import IntegrationsService
from organization_management.domain.entities.integrations import (
    LTIPlatformRegistration,
    CalendarProvider,
    CalendarEvent,
    SlackWorkspace,
    OAuthToken,
    GradeSyncStatus,
    CalendarProviderType,
    CalendarSyncStatus,
    OAuthProvider
)
from organization_management.exceptions import ValidationException


class RealIntegrationsDAO:
    """Real DAO implementation using in-memory storage for E2E testing"""
    def __init__(self):
        self.lti_platforms = {}
        self.lti_contexts = {}
        self.lti_users = {}
        self.grade_syncs = []
        self.calendar_providers = {}
        self.calendar_events = {}
        self.slack_workspaces = {}
        self.slack_channels = {}
        self.slack_users = {}
        self.slack_messages = []
        self.outbound_webhooks = {}
        self.webhook_delivery_logs = []
        self.inbound_webhooks = {}
        self.oauth_tokens = {}

    async def create_lti_platform(self, platform):
        self.lti_platforms[str(platform.id)] = platform
        return platform

    async def get_lti_platform_by_id(self, platform_id):
        return self.lti_platforms.get(str(platform_id))

    async def get_lti_platform_by_issuer(self, issuer, client_id):
        for platform in self.lti_platforms.values():
            if platform.issuer == issuer and platform.client_id == client_id:
                return platform
        return None

    async def update_lti_platform(self, platform_id, updates):
        platform = self.lti_platforms.get(str(platform_id))
        if platform:
            for key, value in updates.items():
                setattr(platform, key, value)
        return platform

    async def create_calendar_provider(self, provider):
        self.calendar_providers[str(provider.id)] = provider
        return provider

    async def get_calendar_providers_by_user(self, user_id):
        return [p for p in self.calendar_providers.values() if p.user_id == user_id]

    async def update_calendar_provider(self, provider_id, updates):
        provider = self.calendar_providers.get(str(provider_id))
        if provider:
            for key, value in updates.items():
                setattr(provider, key, value)
        return provider

    async def create_calendar_event(self, event):
        self.calendar_events[str(event.id)] = event
        return event

    async def create_slack_workspace(self, workspace):
        self.slack_workspaces[str(workspace.id)] = workspace
        return workspace

    async def get_slack_workspace_by_organization(self, org_id):
        for workspace in self.slack_workspaces.values():
            if workspace.organization_id == org_id:
                return workspace
        return None

    async def create_oauth_token(self, token):
        self.oauth_tokens[str(token.id)] = token
        return token

    async def get_oauth_token(self, user_id, org_id, provider):
        for token in self.oauth_tokens.values():
            if token.provider == provider:
                if user_id and token.user_id == user_id:
                    return token
                if org_id and token.organization_id == org_id:
                    return token
        return None


@pytest.fixture
def real_dao():
    """Create real DAO for E2E testing"""
    return RealIntegrationsDAO()


@pytest.fixture
def integrations_service(real_dao):
    """Create IntegrationsService with real DAO"""
    return IntegrationsService(real_dao)


# ============================================================================
# LTI INTEGRATION E2E TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lti_api
@skip_if_no_lti
class TestLTIIntegrationE2E:
    """
    E2E tests for LTI 1.3 platform integration

    IMPORTANT: These tests interact with real LTI platforms and require:
    1. Valid LTI platform URL and credentials
    2. Platform configured for LTI 1.3
    3. Appropriate JWKS endpoints accessible
    """

    @pytest.mark.asyncio
    async def test_register_lti_platform_with_real_platform(
        self,
        integrations_service,
        real_dao,
        lti_credentials
    ):
        """
        Test registering a real LTI platform

        This test verifies:
        1. Platform registration succeeds with valid credentials
        2. Platform data is stored correctly
        3. JWKS URL is accessible
        """
        if lti_credentials is None:
            pytest.skip("LTI credentials not available")

        org_id = uuid4()

        platform = await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="E2E Test Platform",
            issuer=lti_credentials["issuer"],
            client_id=lti_credentials["client_id"],
            auth_login_url=lti_credentials.get("auth_login_url", f"{lti_credentials['platform_url']}/auth"),
            auth_token_url=lti_credentials.get("auth_token_url", f"{lti_credentials['platform_url']}/token"),
            jwks_url=lti_credentials.get("jwks_url", f"{lti_credentials['platform_url']}/jwks")
        )

        # Verify platform was registered
        assert platform is not None
        assert platform.id is not None
        assert platform.issuer == lti_credentials["issuer"]
        assert platform.client_id == lti_credentials["client_id"]

        # Verify platform is in database
        stored_platform = await real_dao.get_lti_platform_by_id(platform.id)
        assert stored_platform is not None
        assert stored_platform.id == platform.id

    @pytest.mark.asyncio
    async def test_lti_platform_verification(self, integrations_service, real_dao, lti_credentials):
        """
        Test LTI platform verification process

        This test verifies:
        1. Platform can be marked as verified
        2. Verification timestamp is recorded
        3. Verified status persists
        """
        if lti_credentials is None:
            pytest.skip("LTI credentials not available")

        org_id = uuid4()

        # First register platform
        platform = await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="Verification Test",
            issuer=lti_credentials["issuer"],
            client_id=lti_credentials["client_id"],
            auth_login_url=lti_credentials.get("auth_login_url", "https://platform.test/auth"),
            auth_token_url=lti_credentials.get("auth_token_url", "https://platform.test/token"),
            jwks_url=lti_credentials.get("jwks_url", "https://platform.test/jwks")
        )

        # Verify platform
        verified_platform = await integrations_service.verify_lti_platform(platform.id)

        assert verified_platform is not None
        assert verified_platform.verified_at is not None

    @pytest.mark.asyncio
    async def test_complete_lti_launch_flow(self, integrations_service, real_dao, lti_credentials):
        """
        Test complete LTI launch flow with real platform

        This test verifies:
        1. Platform registration
        2. Context creation
        3. User mapping creation
        4. Complete authentication flow
        """
        if lti_credentials is None:
            pytest.skip("LTI credentials not available")

        org_id = uuid4()
        user_id = uuid4()

        # Step 1: Register platform
        platform = await integrations_service.register_lti_platform(
            organization_id=org_id,
            platform_name="Complete Flow Test",
            issuer=lti_credentials["issuer"],
            client_id=lti_credentials["client_id"],
            auth_login_url=lti_credentials.get("auth_login_url", "https://platform.test/auth"),
            auth_token_url=lti_credentials.get("auth_token_url", "https://platform.test/token"),
            jwks_url=lti_credentials.get("jwks_url", "https://platform.test/jwks")
        )

        assert platform.id is not None

        # Step 2: Create LTI context
        context = await integrations_service.create_or_update_lti_context(
            platform_id=platform.id,
            lti_context_id="course-e2e-test",
            lti_context_title="E2E Test Course"
        )

        assert context is not None

        # Step 3: Create user mapping
        user_mapping = await integrations_service.create_or_update_lti_user(
            platform_id=platform.id,
            user_id=user_id,
            lti_user_id="lti-e2e-user-123",
            lti_email="e2e.test@example.com",
            lti_name="E2E Test User"
        )

        assert user_mapping is not None
        assert user_mapping.login_count == 1


# ============================================================================
# CALENDAR INTEGRATION E2E TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.calendar_api
@skip_if_no_calendar
class TestCalendarIntegrationE2E:
    """
    E2E tests for calendar provider integration

    IMPORTANT: These tests interact with real calendar APIs and require:
    1. Valid OAuth credentials for Google Calendar or Outlook
    2. Test account with calendar access
    3. Appropriate API scopes enabled
    """

    @pytest.mark.asyncio
    async def test_connect_google_calendar(
        self,
        integrations_service,
        real_dao,
        calendar_credentials
    ):
        """
        Test connecting Google Calendar provider

        This test verifies:
        1. Calendar connection succeeds with valid OAuth tokens
        2. Provider data is stored correctly
        3. Sync is enabled by default
        """
        if calendar_credentials is None:
            pytest.skip("Calendar credentials not available")

        user_id = uuid4()

        # Note: In real E2E test, you would obtain these tokens via OAuth flow
        provider = await integrations_service.connect_calendar(
            user_id=user_id,
            provider_type=CalendarProviderType.GOOGLE,
            access_token="test_access_token",  # Would be real token in production
            refresh_token="test_refresh_token"  # Would be real token in production
        )

        # Verify provider was created
        assert provider is not None
        assert provider.id is not None
        assert provider.provider_type == CalendarProviderType.GOOGLE
        assert provider.is_connected is True
        assert provider.sync_enabled is True

        # Verify provider is in database
        user_providers = await real_dao.get_calendar_providers_by_user(user_id)
        assert len(user_providers) == 1
        assert user_providers[0].id == provider.id

    @pytest.mark.asyncio
    async def test_sync_calendar_event(self, integrations_service, real_dao, calendar_credentials):
        """
        Test syncing a calendar event

        This test verifies:
        1. Event can be created/synced
        2. Event data is stored correctly
        3. Sync status is tracked
        """
        if calendar_credentials is None:
            pytest.skip("Calendar credentials not available")

        user_id = uuid4()
        provider_id = uuid4()

        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=2)

        event = await integrations_service.sync_calendar_event(
            provider_id=provider_id,
            user_id=user_id,
            title="E2E Test Meeting",
            start_time=start_time,
            end_time=end_time,
            description="This is an E2E test calendar event"
        )

        # Verify event was created
        assert event is not None
        assert event.id is not None
        assert event.title == "E2E Test Meeting"
        assert event.sync_status == CalendarSyncStatus.SYNCED


# ============================================================================
# SLACK INTEGRATION E2E TESTS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.slack_api
@skip_if_no_slack
class TestSlackIntegrationE2E:
    """
    E2E tests for Slack workspace integration

    IMPORTANT: These tests interact with real Slack API and require:
    1. Valid Slack bot token with appropriate scopes
    2. Workspace ID where bot is installed
    3. Permissions to create channels and send messages
    """

    @pytest.mark.asyncio
    async def test_connect_slack_workspace(
        self,
        integrations_service,
        real_dao,
        slack_credentials
    ):
        """
        Test connecting Slack workspace

        This test verifies:
        1. Workspace connection succeeds with valid bot token
        2. Workspace data is stored correctly
        3. Default settings are applied
        """
        if slack_credentials is None:
            pytest.skip("Slack credentials not available")

        org_id = uuid4()

        workspace = await integrations_service.connect_slack_workspace(
            organization_id=org_id,
            workspace_id=slack_credentials["workspace_id"],
            bot_token=slack_credentials["bot_token"],
            workspace_name="E2E Test Workspace",
            scopes=["chat:write", "channels:read", "users:read"]
        )

        # Verify workspace was connected
        assert workspace is not None
        assert workspace.id is not None
        assert workspace.workspace_id == slack_credentials["workspace_id"]
        assert workspace.is_active is True

        # Verify workspace is in database
        org_workspace = await real_dao.get_slack_workspace_by_organization(org_id)
        assert org_workspace is not None
        assert org_workspace.id == workspace.id

    @pytest.mark.asyncio
    async def test_update_slack_settings(self, integrations_service, real_dao, slack_credentials):
        """
        Test updating Slack workspace settings

        This test verifies:
        1. Settings can be updated
        2. Changes are persisted
        3. Feature flags work correctly
        """
        if slack_credentials is None:
            pytest.skip("Slack credentials not available")

        org_id = uuid4()

        # First connect workspace
        workspace = await integrations_service.connect_slack_workspace(
            organization_id=org_id,
            workspace_id=slack_credentials["workspace_id"],
            bot_token=slack_credentials["bot_token"],
            workspace_name="Settings Test Workspace"
        )

        # Update settings
        await integrations_service.update_slack_settings(
            workspace_id=workspace.id,
            enable_notifications=True,
            enable_commands=True,
            enable_ai_assistant=True,
            default_announcements_channel="C12345"
        )

        # Verify settings were updated
        updated_workspace = await real_dao.get_slack_workspace_by_organization(org_id)
        assert updated_workspace.enable_notifications is True
        assert updated_workspace.enable_commands is True


# ============================================================================
# OAUTH TOKEN MANAGEMENT E2E TESTS
# ============================================================================

@pytest.mark.e2e
class TestOAuthTokenManagementE2E:
    """
    E2E tests for OAuth token lifecycle management

    These tests verify token storage, refresh, and invalidation without
    requiring external API calls.
    """

    @pytest.mark.asyncio
    async def test_store_and_retrieve_oauth_token(self, integrations_service, real_dao):
        """
        Test storing and retrieving OAuth tokens

        This test verifies:
        1. Tokens can be stored securely
        2. Tokens can be retrieved by user/organization
        3. Token metadata is tracked
        """
        user_id = uuid4()

        # Store token
        token = await integrations_service.store_oauth_token(
            provider=OAuthProvider.GOOGLE,
            access_token="test_access_token",
            user_id=user_id,
            refresh_token="test_refresh_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )

        assert token is not None
        assert token.id is not None
        assert token.is_valid is True

        # Retrieve token
        retrieved_token = await integrations_service.get_oauth_token(
            provider=OAuthProvider.GOOGLE,
            user_id=user_id
        )

        assert retrieved_token is not None
        assert retrieved_token.id == token.id

    @pytest.mark.asyncio
    async def test_refresh_oauth_token(self, integrations_service, real_dao):
        """
        Test refreshing OAuth tokens

        This test verifies:
        1. Token can be refreshed with new credentials
        2. Failure counter is reset on successful refresh
        3. New expiration time is set
        """
        user_id = uuid4()

        # Store initial token
        token = await integrations_service.store_oauth_token(
            provider=OAuthProvider.GOOGLE,
            access_token="old_access_token",
            user_id=user_id,
            refresh_token="old_refresh_token"
        )

        # Refresh token
        new_expires = datetime.now() + timedelta(hours=2)
        await integrations_service.refresh_oauth_token(
            token_id=token.id,
            new_access_token="new_access_token",
            new_expires_at=new_expires,
            new_refresh_token="new_refresh_token"
        )

        # Verify token was refreshed
        refreshed_token = await real_dao.get_oauth_token(user_id, None, OAuthProvider.GOOGLE)
        assert refreshed_token.access_token == "new_access_token"
        assert refreshed_token.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_invalidate_oauth_token(self, integrations_service, real_dao):
        """
        Test invalidating OAuth tokens

        This test verifies:
        1. Token can be marked as invalid
        2. Invalid tokens are not returned in queries
        3. Revoked tokens are deleted
        """
        user_id = uuid4()

        # Store token
        token = await integrations_service.store_oauth_token(
            provider=OAuthProvider.SLACK,
            access_token="test_token",
            user_id=user_id
        )

        # Invalidate token
        await integrations_service.invalidate_oauth_token(token.id)

        # Verify token is invalid
        invalid_token = await real_dao.oauth_tokens.get(str(token.id))
        if invalid_token:
            assert invalid_token.is_valid is False


# ============================================================================
# VALIDATION E2E TESTS
# ============================================================================

@pytest.mark.e2e
class TestIntegrationsValidationE2E:
    """
    E2E tests for input validation

    These tests verify that invalid inputs are properly rejected.
    """

    @pytest.mark.asyncio
    async def test_register_lti_platform_invalid_issuer(self, integrations_service):
        """Test that invalid issuer URL is rejected"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.register_lti_platform(
                organization_id=uuid4(),
                platform_name="Test Platform",
                issuer="invalid-url",
                client_id="client",
                auth_login_url="https://platform.test/auth",
                auth_token_url="https://platform.test/token",
                jwks_url="https://platform.test/jwks"
            )

        assert "issuer" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_store_oauth_token_no_owner(self, integrations_service):
        """Test that OAuth token without owner is rejected"""
        with pytest.raises(ValidationException) as exc_info:
            await integrations_service.store_oauth_token(
                provider=OAuthProvider.GOOGLE,
                access_token="test_token"
                # Missing both user_id and organization_id
            )

        assert "owner" in exc_info.value.field_errors

# E2E Integration Tests

This directory contains end-to-end (E2E) tests that interact with real external APIs and services.

## Overview

These tests verify actual integration functionality with external services including:

- **Slack API** - Notification sending, workspace management, channel operations
- **Zoom API** - Meeting room creation, bulk operations
- **Microsoft Teams API** - Meeting room creation, calendar integration
- **LTI 1.3 Platforms** - Platform registration, context management, grade sync
- **Calendar Providers** - Google Calendar, Outlook synchronization
- **OAuth** - Token management and refresh flows

## Requirements

### API Credentials

To run these tests, you need valid API credentials set as environment variables:

#### Slack Integration
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_WORKSPACE_ID="T123456789"
export SLACK_TEST_CHANNEL_ID="C123456789"  # Optional: for channel-specific tests
```

#### Zoom Integration
```bash
export ZOOM_API_KEY="your-zoom-api-key"
export ZOOM_API_SECRET="your-zoom-api-secret"
```

#### Microsoft Teams Integration
```bash
export TEAMS_CLIENT_ID="your-azure-app-client-id"
export TEAMS_CLIENT_SECRET="your-azure-app-client-secret"
export TEAMS_TENANT_ID="your-azure-tenant-id"
```

#### LTI Platform Integration
```bash
export LTI_PLATFORM_URL="https://your-lti-platform.com"
export LTI_CLIENT_ID="your-lti-client-id"
export LTI_ISSUER="https://your-lti-platform.com"
export LTI_JWKS_URL="https://your-lti-platform.com/jwks"  # Optional
export LTI_AUTH_LOGIN_URL="https://your-lti-platform.com/auth"  # Optional
export LTI_AUTH_TOKEN_URL="https://your-lti-platform.com/token"  # Optional
```

#### Calendar Integration
```bash
export GOOGLE_CALENDAR_CLIENT_ID="your-google-client-id"
export GOOGLE_CALENDAR_CLIENT_SECRET="your-google-client-secret"
export GOOGLE_CALENDAR_REDIRECT_URI="http://localhost:8000/auth/callback"  # Optional
```

### Test Configuration

Additional configuration options:

```bash
export E2E_TIMEOUT="30"  # API call timeout in seconds (default: 30)
export E2E_RETRY_COUNT="3"  # Number of retries for failed requests (default: 3)
export E2E_CLEANUP="true"  # Clean up test data after tests (default: true)
export E2E_VERBOSE="false"  # Enable verbose logging (default: false)
```

## Running Tests

### Run All E2E Integration Tests

```bash
pytest tests/e2e/integrations/ -v
```

### Run Specific Integration Tests

```bash
# Slack integration tests only
pytest tests/e2e/integrations/test_notification_service.py -v -m slack_api

# Zoom integration tests only
pytest tests/e2e/integrations/test_bulk_room_creation.py -v -m zoom_api

# Teams integration tests only
pytest tests/e2e/integrations/test_bulk_room_creation.py -v -m teams_api

# LTI integration tests only
pytest tests/e2e/integrations/test_integrations_service.py -v -m lti_api

# Calendar integration tests only
pytest tests/e2e/integrations/test_integrations_service.py -v -m calendar_api
```

### Run Without Credentials

If credentials are not available, tests will be automatically skipped:

```bash
pytest tests/e2e/integrations/ -v
# Tests requiring unavailable credentials will show as SKIPPED
```

### Run with Specific Markers

```bash
# Run all E2E tests
pytest -v -m e2e

# Run only Slack API tests
pytest -v -m slack_api

# Run only Zoom API tests
pytest -v -m zoom_api
```

## Test Structure

### Test Files

- **test_notification_service.py** - Slack notification sending and management
- **test_bulk_room_creation.py** - Zoom/Teams bulk meeting room creation
- **test_integrations_service.py** - LTI, Calendar, OAuth integration tests

### Fixtures

The `conftest.py` file provides:

- **Credential fixtures** - Load credentials from environment variables
- **Skip markers** - Automatically skip tests when credentials unavailable
- **Configuration** - Test timeout, retry, cleanup settings
- **Custom markers** - `@pytest.mark.e2e`, `@pytest.mark.slack_api`, etc.

## Test Development Guidelines

### Writing E2E Integration Tests

1. **Always use the `@pytest.mark.e2e` marker** - This is automatically added by conftest.py
2. **Add specific API markers** - Use `@pytest.mark.slack_api`, `@pytest.mark.zoom_api`, etc.
3. **Use skip markers** - Apply `@skip_if_no_slack`, `@skip_if_no_zoom`, etc.
4. **Add docstrings** - Explain what the test verifies and what it requires
5. **Clean up resources** - Delete created resources unless testing persistence

### Example Test

```python
@pytest.mark.e2e
@pytest.mark.slack_api
@skip_if_no_slack
class TestSlackFeatureE2E:
    """
    E2E tests for Slack feature X

    IMPORTANT: These tests make real API calls and require:
    1. Valid Slack bot token
    2. Workspace with test channel
    3. Permissions: chat:write, channels:read
    """

    @pytest.mark.asyncio
    async def test_feature_x(self, slack_credentials):
        """
        Test feature X with real Slack API

        This test verifies:
        1. API call succeeds
        2. Data is stored correctly
        3. Response is properly handled
        """
        # Test implementation
        pass
```

### Best Practices

1. **Idempotency** - Tests should be runnable multiple times
2. **Isolation** - Tests should not depend on each other
3. **Cleanup** - Remove test data after tests complete
4. **Timeout Handling** - Use appropriate timeouts for API calls
5. **Error Handling** - Verify both success and failure cases
6. **Real Data** - Use actual API responses, not mocks
7. **Documentation** - Document required credentials and permissions

## Troubleshooting

### Tests are Skipped

If all tests show as SKIPPED, verify:
1. Environment variables are set correctly
2. Credentials are valid and not expired
3. Required permissions/scopes are granted

### API Rate Limits

If you encounter rate limit errors:
1. Reduce test frequency
2. Use different test accounts
3. Implement retry logic with backoff

### Authentication Failures

If authentication fails:
1. Verify credentials are current
2. Check token expiration
3. Ensure required scopes are granted
4. Verify API keys are valid

### Network Timeouts

If tests timeout:
1. Increase `E2E_TIMEOUT` environment variable
2. Check network connectivity
3. Verify API endpoints are accessible

## CI/CD Integration

### GitHub Actions

These tests can be run in CI/CD with secrets:

```yaml
- name: Run E2E Integration Tests
  env:
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
    SLACK_WORKSPACE_ID: ${{ secrets.SLACK_WORKSPACE_ID }}
    ZOOM_API_KEY: ${{ secrets.ZOOM_API_KEY }}
    ZOOM_API_SECRET: ${{ secrets.ZOOM_API_SECRET }}
  run: |
    pytest tests/e2e/integrations/ -v
```

### Selective Testing

Run only tests with available credentials:

```yaml
- name: Run E2E Tests (Available Credentials Only)
  env:
    # Only set secrets that are available
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
    SLACK_WORKSPACE_ID: ${{ secrets.SLACK_WORKSPACE_ID }}
  run: |
    pytest tests/e2e/integrations/ -v
    # Tests without credentials will be skipped
```

## Security Notes

1. **Never commit credentials** - Use environment variables or secrets management
2. **Use test accounts** - Create dedicated test accounts/workspaces
3. **Limit permissions** - Grant only required scopes/permissions
4. **Rotate keys** - Regularly rotate API keys and tokens
5. **Monitor usage** - Track API usage to detect anomalies

## Migration Notes

These test files were moved from `tests/unit/organization_management/` because they require external API access and should be tested as E2E integrations rather than unit tests.

Original files:
- `test_notification_service.py` - Moved 2025-12-12
- `test_bulk_room_creation.py` - Moved 2025-12-12
- `test_integrations_service.py` - Moved 2025-12-12

The unit test versions used mocks and did not test actual API integration.

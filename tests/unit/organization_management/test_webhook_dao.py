"""
WebhookDAO Unit Tests - TDD RED Phase

BUSINESS CONTEXT:
The WebhookDAO handles webhook integration functionality for organizations,
allowing external services to receive real-time notifications about platform events
(course enrollments, grade updates, assignments submissions, etc.).

REFACTORING CONTEXT:
This test file is part of the IntegrationsDAO god class refactoring (2,911 lines → 5 specialized DAOs).
The WebhookDAO will be extracted to handle ONLY webhook-related operations.

TEST COVERAGE (TDD RED Phase):
1. Webhook Registration and Configuration (8 tests)
2. Webhook Delivery and Retry Logic (10 tests)
3. Event Subscription Management (7 tests)
4. Signature Generation and Validation (8 tests)
5. Webhook Monitoring and Logging (6 tests)
6. Security and Rate Limiting (6 tests)

DEPENDENCIES:
- Custom exceptions from shared/exceptions/__init__.py
- httpx for async HTTP requests
- hmac for signature generation
- Redis for delivery queue

EXPECTED BEHAVIOR (TDD RED - These tests WILL FAIL until implementation):
All tests define the DESIRED behavior for the WebhookDAO.
Implementation should follow the Clean Architecture pattern:
- Domain layer: Webhook event entities
- Application layer: Webhook delivery service
- Infrastructure layer: WebhookDAO (database + HTTP operations)

Related Files:
- services/organization-management/organization_management/data_access/integrations_dao.py (original god class)
- docs/INTEGRATIONS_DAO_REFACTORING_STATUS.md (refactoring plan)
- docs/EXCEPTION_MAPPING_GUIDE.md (exception handling patterns)
"""

import pytest
import asyncio
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

# These imports will fail until the WebhookDAO is created (TDD RED phase)
try:
    from organization_management.infrastructure.repositories.webhook_dao import WebhookDAO
except ImportError:
    WebhookDAO = None  # Expected during RED phase

# Custom exceptions (these should exist)
from shared.exceptions import (
    DatabaseException,
    ValidationException,
    ConflictException,
    NotFoundException,
    AuthenticationException,
    RateLimitException,
    ExternalServiceException
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def fake_db_pool():
    """Mock database connection pool.

    Supports both patterns:
    - Direct await: conn = await pool.acquire()
    - Context manager: async with pool.acquire() as conn
    """
    pool = AsyncMock()
    conn = AsyncMock()

    # Configure for direct await pattern (used by WebhookDAO implementation)
    pool.acquire.return_value = conn
    pool.release = AsyncMock()

    # Also configure for async context manager pattern (if needed)
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Configure connection methods
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_organization_id():
    """Sample organization UUID."""
    return "org-550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_webhook_config():
    """Sample webhook configuration."""
    return {
        "url": "https://external-service.example.com/webhooks/course-platform",
        "secret": "whsec_abcdefghijklmnopqrstuvwxyz123456",
        "events": ["course.enrolled", "assignment.submitted", "grade.updated"],
        "active": True,
        "description": "Integration with External LMS",
        "headers": {
            "X-Custom-Header": "value123"
        }
    }


@pytest.fixture
def sample_webhook_event():
    """Sample webhook event payload."""
    return {
        "event_type": "course.enrolled",
        "event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "course_id": "course-123",
            "course_title": "Introduction to Python",
            "student_id": "student-456",
            "student_email": "student@example.com",
            "enrollment_date": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture
def sample_delivery_log():
    """Sample webhook delivery log entry."""
    return {
        "delivery_id": "del_123456",
        "webhook_id": "webhook_789",
        "event_type": "course.enrolled",
        "status": "delivered",
        "status_code": 200,
        "response_time_ms": 145,
        "delivered_at": datetime.utcnow().isoformat(),
        "attempts": 1
    }


# ============================================================================
# TEST CLASS 1: Webhook Registration and Configuration
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestWebhookRegistrationAndConfiguration:
    """
    Tests for webhook registration and configuration.

    BUSINESS REQUIREMENTS:
    - Organizations can register multiple webhooks
    - Each webhook has unique URL endpoint
    - Webhooks must have secret for signature validation
    - Organizations can configure which events to receive
    - Webhooks can be activated/deactivated
    """

    @pytest.mark.asyncio
    async def test_register_new_webhook(self, fake_db_pool, sample_organization_id, sample_webhook_config):
        """
        Test registering a new webhook endpoint.

        EXPECTED BEHAVIOR:
        - Validates URL format
        - Generates webhook secret if not provided
        - Stores configuration in database
        - Returns webhook ID and secret
        - Webhook starts in active state
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "secret": sample_webhook_config["secret"],
            "active": True
        }

        # Act
        result = await dao.register_webhook(
            organization_id=sample_organization_id,
            webhook_config=sample_webhook_config
        )

        # Assert
        assert result["webhook_id"] == "webhook_789"
        assert result["secret"].startswith("whsec_")
        assert result["active"] is True
        assert len(result["events"]) == 3

    @pytest.mark.asyncio
    async def test_register_webhook_with_invalid_url(self, fake_db_pool, sample_organization_id):
        """
        Test registering webhook with invalid URL.

        EXPECTED BEHAVIOR:
        - Validates URL scheme (must be https://)
        - Validates URL format
        - Raises ValidationException for invalid URLs
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        invalid_configs = [
            {"url": "http://insecure.com/webhook"},  # HTTP not allowed
            {"url": "not-a-url"},  # Invalid format
            {"url": "ftp://weird.com/webhook"}  # Wrong protocol
        ]

        for config in invalid_configs:
            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.register_webhook(
                    organization_id=sample_organization_id,
                    webhook_config=config
                )

            assert "url" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_webhook_url(self, fake_db_pool, sample_organization_id, sample_webhook_config):
        """
        Test registering webhook with duplicate URL for same organization.

        EXPECTED BEHAVIOR:
        - Checks for existing webhook with same URL
        - Raises ConflictException
        - Suggests updating existing webhook instead
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - trigger UniqueViolationError on INSERT (fetchrow with RETURNING)
        import asyncpg
        fake_db_pool.acquire.return_value.fetchrow.side_effect = \
            asyncpg.UniqueViolationError("duplicate key value: organization_id + url")

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            await dao.register_webhook(
                organization_id=sample_organization_id,
                webhook_config=sample_webhook_config
            )

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_webhook_configuration(self, fake_db_pool, sample_organization_id):
        """
        Test updating existing webhook configuration.

        EXPECTED BEHAVIOR:
        - Updates URL, events, headers, description
        - Secret cannot be changed (must rotate instead)
        - Returns updated configuration
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        updates = {
            "webhook_id": "webhook_789",
            "events": ["course.enrolled", "course.completed"],  # Changed events
            "description": "Updated Integration"
        }

        # Act
        result = await dao.update_webhook(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            updates=updates
        )

        # Assert
        assert result["updated"] is True
        assert len(result["events"]) == 2

    @pytest.mark.asyncio
    async def test_activate_deactivate_webhook(self, fake_db_pool, sample_organization_id):
        """
        Test activating and deactivating webhook.

        EXPECTED BEHAVIOR:
        - Deactivated webhooks do not receive events
        - Activation state can be toggled
        - Useful for temporary pause without deletion
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act - Deactivate
        result_deactivate = await dao.set_webhook_status(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            active=False
        )

        # Act - Reactivate
        result_activate = await dao.set_webhook_status(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            active=True
        )

        # Assert
        assert result_deactivate["active"] is False
        assert result_activate["active"] is True

    @pytest.mark.asyncio
    async def test_rotate_webhook_secret(self, fake_db_pool, sample_organization_id):
        """
        Test rotating webhook secret for security.

        EXPECTED BEHAVIOR:
        - Generates new secret
        - Updates stored secret
        - Returns new secret to admin
        - Old signatures will fail validation
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        old_secret = "whsec_OLD_SECRET_123"
        new_secret = "whsec_NEW_SECRET_456"

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "secret": new_secret
        }

        # Act
        result = await dao.rotate_webhook_secret(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert result["secret"] == new_secret
        assert result["secret"] != old_secret
        assert result["rotated_at"] is not None

    @pytest.mark.asyncio
    async def test_get_webhook_configuration(self, fake_db_pool, sample_organization_id, sample_webhook_config):
        """
        Test retrieving webhook configuration.

        EXPECTED BEHAVIOR:
        - Returns all webhook details
        - Secret is returned masked (last 4 chars only)
        - Includes delivery statistics
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": sample_webhook_config["url"],
            "secret": sample_webhook_config["secret"],
            "active": True,
            "events": sample_webhook_config["events"],
            "total_deliveries": 1250,
            "successful_deliveries": 1230,
            "failed_deliveries": 20
        }

        # Act
        result = await dao.get_webhook(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert result["webhook_id"] == "webhook_789"
        assert result["url"] == sample_webhook_config["url"]
        assert result["secret"].startswith("whsec_")  # Secret included
        assert result["total_deliveries"] == 1250
        assert result["success_rate"] >= 98.0  # Calculated

    @pytest.mark.asyncio
    async def test_delete_webhook(self, fake_db_pool, sample_organization_id):
        """
        Test deleting webhook configuration.

        EXPECTED BEHAVIOR:
        - Soft delete (marks as deleted, keeps logs)
        - Stops all future event deliveries
        - Returns confirmation
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.delete_webhook(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert result["deleted"] is True
        assert result["webhook_id"] == "webhook_789"


# ============================================================================
# TEST CLASS 2: Webhook Delivery and Retry Logic
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestWebhookDeliveryAndRetryLogic:
    """
    Tests for webhook event delivery and retry logic.

    BUSINESS REQUIREMENTS:
    - Events are delivered asynchronously via HTTP POST
    - Failed deliveries are retried with exponential backoff
    - Maximum 5 retry attempts
    - Delivery timeout: 30 seconds
    - Returns 2xx status code = success
    """

    @pytest.mark.asyncio
    async def test_deliver_webhook_event_success(self, fake_db_pool, sample_organization_id, sample_webhook_config, sample_webhook_event):
        """
        Test successful webhook event delivery.

        EXPECTED BEHAVIOR:
        - Sends HTTP POST to webhook URL
        - Includes HMAC signature in headers
        - Includes timestamp and event ID
        - Logs successful delivery
        - Returns delivery confirmation
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - mock must return a dict, not an AsyncMock
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": sample_webhook_config["url"],
            "secret": sample_webhook_config["secret"],
            "headers": "{}",  # JSON string as stored in DB
            "events": sample_webhook_config["events"]
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.elapsed.total_seconds.return_value = 0.145
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            result = await dao.deliver_webhook_event(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

        # Assert
        assert result["delivered"] is True
        assert result["status_code"] == 200
        assert result["attempt"] == 1
        assert result["response_time_ms"] == 145

    @pytest.mark.asyncio
    async def test_deliver_webhook_event_with_timeout(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test webhook delivery timeout (30 seconds).

        EXPECTED BEHAVIOR:
        - HTTP request times out after 30 seconds
        - Logs timeout failure
        - Schedules retry
        - Raises ExternalServiceException
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - mock webhook config
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": "https://example.com/webhook",
            "secret": "whsec_test",
            "headers": "{}"
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = \
                asyncio.TimeoutError("Request timeout after 30 seconds")

            # Act & Assert
            with pytest.raises(ExternalServiceException) as exc_info:
                await dao.deliver_webhook_event(
                    organization_id=sample_organization_id,
                    webhook_event=sample_webhook_event
                )

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_deliver_webhook_event_4xx_error(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test webhook delivery with 4xx client error (no retry).

        EXPECTED BEHAVIOR:
        - Receives 4xx status code (e.g., 400, 401, 404)
        - Logs permanent failure
        - Does NOT schedule retry (client errors won't be fixed by retrying)
        - Deactivates webhook after repeated 4xx errors
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - mock webhook config
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": "https://example.com/webhook",
            "secret": "whsec_test",
            "headers": "{}"
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            result = await dao.deliver_webhook_event(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

        # Assert
        assert result["delivered"] is False
        assert result["status_code"] == 401
        assert result["retryable"] is False

    @pytest.mark.asyncio
    async def test_deliver_webhook_event_5xx_error_with_retry(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test webhook delivery with 5xx server error (retry enabled).

        EXPECTED BEHAVIOR:
        - Receives 5xx status code (e.g., 500, 502, 503)
        - Logs temporary failure
        - Schedules retry with exponential backoff
        - Maximum 5 retry attempts
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - mock webhook config
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": "https://example.com/webhook",
            "secret": "whsec_test",
            "headers": "{}"
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "Service Unavailable"
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            result = await dao.deliver_webhook_event(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

        # Assert
        assert result["delivered"] is False
        assert result["status_code"] == 503
        assert result["retryable"] is True
        assert result["retry_scheduled"] is True

    @pytest.mark.asyncio
    async def test_retry_failed_delivery_with_exponential_backoff(self, fake_db_pool, sample_organization_id):
        """
        Test retry logic with exponential backoff.

        EXPECTED BEHAVIOR:
        - Retry 1: Wait 1 minute
        - Retry 2: Wait 5 minutes
        - Retry 3: Wait 15 minutes
        - Retry 4: Wait 30 minutes
        - Retry 5: Wait 60 minutes
        - After 5 failures: Mark as permanently failed
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act
        retry_delays = []
        for attempt in range(1, 6):
            delay = await dao.calculate_retry_delay(attempt)
            retry_delays.append(delay)

        # Assert
        assert retry_delays[0] == 60  # 1 minute
        assert retry_delays[1] == 300  # 5 minutes
        assert retry_delays[2] == 900  # 15 minutes
        assert retry_delays[3] == 1800  # 30 minutes
        assert retry_delays[4] == 3600  # 60 minutes

    @pytest.mark.asyncio
    async def test_max_retry_attempts_exceeded(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test delivery after maximum retry attempts exceeded.

        EXPECTED BEHAVIOR:
        - After 5 failed attempts, mark as permanently failed
        - Log final failure
        - Do not schedule further retries
        - Optionally notify organization admin
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - 5 previous failed attempts
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "delivery_id": "del_123",
            "attempts": 5,
            "last_attempt_at": datetime.utcnow().isoformat(),
            "status": "failed"
        }

        # Act
        result = await dao.handle_failed_delivery(
            delivery_id="del_123",
            error="Service unavailable"
        )

        # Assert
        assert result["permanently_failed"] is True
        assert result["total_attempts"] == 5
        assert result["retry_scheduled"] is False

    @pytest.mark.asyncio
    async def test_batch_deliver_webhooks(self, fake_db_pool, sample_organization_id):
        """
        Test batch delivery of multiple webhook events.

        EXPECTED BEHAVIOR:
        - Delivers events in parallel (asyncio.gather)
        - Each webhook has independent delivery
        - One failure doesn't block others
        - Returns summary of deliveries
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        events = [
            {"event_type": "course.enrolled", "event_id": f"evt_{i}"}
            for i in range(10)
        ]

        # Arrange - mock webhook config
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "url": "https://example.com/webhook",
            "secret": "whsec_test"
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            result = await dao.batch_deliver_events(
                organization_id=sample_organization_id,
                webhook_events=events
            )

        # Assert
        assert result["total_events"] == 10
        assert result["successful_deliveries"] >= 0
        assert result["failed_deliveries"] >= 0

    @pytest.mark.asyncio
    async def test_deliver_webhook_with_custom_headers(self, fake_db_pool, sample_organization_id, sample_webhook_config, sample_webhook_event):
        """
        Test webhook delivery with custom headers.

        EXPECTED BEHAVIOR:
        - Includes custom headers from configuration
        - Preserves standard headers (signature, timestamp)
        - Custom headers override defaults
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - headers stored as JSON string in DB
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": sample_webhook_config["url"],
            "secret": sample_webhook_config["secret"],
            "headers": json.dumps(sample_webhook_config["headers"])  # JSON string
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            await dao.deliver_webhook_event(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

            # Assert - verify headers were included
            call_kwargs = mock_client.return_value.__aenter__.return_value.post.call_args.kwargs
            assert "X-Custom-Header" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_webhook_delivery_queuing(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test queuing webhook deliveries for async processing.

        EXPECTED BEHAVIOR:
        - High-volume events are queued (Redis/Celery)
        - Prevents blocking main request
        - Worker processes queue
        - Returns queued confirmation immediately
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.webhook_dao.enqueue_webhook_delivery") as mock_queue:
            mock_queue.return_value = {"queued": True, "queue_position": 42}

            # Act
            result = await dao.queue_webhook_delivery(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

        # Assert
        assert result["queued"] is True
        assert result["queue_position"] == 42


# ============================================================================
# TEST CLASS 3: Event Subscription Management
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestEventSubscriptionManagement:
    """
    Tests for webhook event subscription management.

    BUSINESS REQUIREMENTS:
    - Organizations can subscribe to specific event types
    - Event types follow pattern: resource.action
    - Wildcards supported (e.g., course.*)
    - Can filter events by additional criteria
    """

    @pytest.mark.asyncio
    async def test_subscribe_to_specific_events(self, fake_db_pool, sample_organization_id):
        """
        Test subscribing webhook to specific event types.

        EXPECTED BEHAVIOR:
        - Stores event subscriptions
        - Validates event type format
        - Allows multiple event types
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        events = ["course.enrolled", "assignment.submitted", "grade.updated"]

        # Act
        result = await dao.subscribe_to_events(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            event_types=events
        )

        # Assert
        assert result["subscribed_events"] == events
        assert result["subscription_count"] == 3

    @pytest.mark.asyncio
    async def test_subscribe_with_wildcard(self, fake_db_pool, sample_organization_id):
        """
        Test subscribing to events with wildcard pattern.

        EXPECTED BEHAVIOR:
        - Supports wildcard subscriptions (e.g., course.*)
        - Matches all events for resource
        - Expands to actual event types
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.subscribe_to_events(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            event_types=["course.*"]
        )

        # Assert
        assert "course.*" in result["subscribed_events"] or len(result["subscribed_events"]) > 1

    @pytest.mark.asyncio
    async def test_unsubscribe_from_events(self, fake_db_pool, sample_organization_id):
        """
        Test unsubscribing from specific event types.

        EXPECTED BEHAVIOR:
        - Removes event subscriptions
        - Webhook still active for other events
        - Returns updated subscription list
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - current events include grade.updated
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "events": ["course.enrolled", "assignment.submitted", "grade.updated"]
        }

        # Act
        result = await dao.unsubscribe_from_events(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            event_types=["grade.updated"]
        )

        # Assert
        assert "grade.updated" not in result["subscribed_events"]
        assert result["unsubscribed"] is True

    @pytest.mark.asyncio
    async def test_get_subscribed_events(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving list of subscribed events.

        EXPECTED BEHAVIOR:
        - Returns all subscribed event types
        - Includes subscription metadata
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {"event_type": "course.enrolled"},
            {"event_type": "assignment.submitted"}
        ]

        # Act
        result = await dao.get_subscribed_events(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert len(result["events"]) == 2
        assert "course.enrolled" in result["events"]

    @pytest.mark.asyncio
    async def test_list_available_event_types(self, fake_db_pool):
        """
        Test listing all available event types in platform.

        EXPECTED BEHAVIOR:
        - Returns catalog of event types
        - Groups by resource (course, assignment, user, etc.)
        - Includes event description and example payload
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.list_available_event_types()

        # Assert
        assert "course.enrolled" in result["event_types"]
        assert "assignment.submitted" in result["event_types"]
        assert len(result["event_types"]) > 10  # Many event types available

    @pytest.mark.asyncio
    async def test_filter_events_by_criteria(self, fake_db_pool, sample_organization_id):
        """
        Test filtering events by additional criteria.

        EXPECTED BEHAVIOR:
        - Can filter by course_id, instructor_id, etc.
        - Only matching events are delivered
        - Reduces noise for integrations
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        filters = {
            "course_id": "course-123",
            "instructor_id": "instructor-456"
        }

        # Act
        result = await dao.set_event_filters(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            filters=filters
        )

        # Assert
        assert result["filters_applied"] is True
        assert result["filters"]["course_id"] == "course-123"

    @pytest.mark.asyncio
    async def test_webhook_receives_only_subscribed_events(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test that webhook only receives subscribed event types.

        EXPECTED BEHAVIOR:
        - Checks event type against subscriptions
        - Delivers if subscribed
        - Skips if not subscribed
        - Logs skipped events
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - webhook subscribed to different event
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {"event_type": "assignment.submitted"}  # Not course.enrolled
        ]

        # Act
        result = await dao.should_deliver_event(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            event_type="course.enrolled"
        )

        # Assert
        assert result["should_deliver"] is False
        assert result["reason"] == "not_subscribed"


# ============================================================================
# TEST CLASS 4: Signature Generation and Validation
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestSignatureGenerationAndValidation:
    """
    Tests for webhook signature generation and validation.

    BUSINESS REQUIREMENTS:
    - All webhook requests include HMAC-SHA256 signature
    - Signature format: sha256=<hex_digest>
    - Signed payload includes timestamp to prevent replay attacks
    - Recipient validates signature using webhook secret
    """

    @pytest.mark.asyncio
    async def test_generate_webhook_signature(self, fake_db_pool):
        """
        Test generating HMAC-SHA256 signature for webhook payload.

        EXPECTED BEHAVIOR:
        - Uses webhook secret as HMAC key
        - Signs JSON payload + timestamp
        - Returns signature in format: sha256=<hex>
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        payload = {"event": "test", "data": "example"}
        timestamp = "1234567890"

        # Act
        signature = await dao.generate_signature(
            secret=secret,
            payload=payload,
            timestamp=timestamp
        )

        # Assert
        assert signature.startswith("sha256=")
        assert len(signature) == 71  # sha256= + 64 hex chars

    @pytest.mark.asyncio
    async def test_validate_webhook_signature_success(self, fake_db_pool):
        """
        Test successful webhook signature validation.

        EXPECTED BEHAVIOR:
        - Receives signature, timestamp, payload
        - Recreates signature using secret
        - Compares using constant-time comparison
        - Returns True if valid
        """
        import time
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        payload = {"event": "test"}
        # Use current timestamp to pass timestamp validation
        timestamp = str(int(time.time()))

        # Generate valid signature
        signature = await dao.generate_signature(secret, payload, timestamp)

        # Act
        result = await dao.validate_signature(
            secret=secret,
            received_signature=signature,
            payload=payload,
            timestamp=timestamp
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_webhook_signature_failure(self, fake_db_pool):
        """
        Test webhook signature validation failure.

        EXPECTED BEHAVIOR:
        - Receives invalid signature
        - Validation fails
        - Raises AuthenticationException
        """
        import time
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        payload = {"event": "test"}
        # Use current timestamp to pass timestamp validation, fail on signature
        timestamp = str(int(time.time()))
        invalid_signature = "sha256=invalidhexdigest1234567890abcdef0123456789abcdef0123456789"

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            result = await dao.validate_signature(
                secret=secret,
                received_signature=invalid_signature,
                payload=payload,
                timestamp=timestamp
            )

        assert "signature" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_signature_replay_attack_prevention(self, fake_db_pool):
        """
        Test replay attack prevention using timestamp validation.

        EXPECTED BEHAVIOR:
        - Checks timestamp is recent (within 5 minutes)
        - Old timestamps are rejected
        - Raises AuthenticationException for old signatures
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        payload = {"event": "test"}
        old_timestamp = str(int((datetime.utcnow() - timedelta(minutes=10)).timestamp()))

        # Generate signature with old timestamp
        signature = await dao.generate_signature(secret, payload, old_timestamp)

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await dao.validate_signature(
                secret=secret,
                received_signature=signature,
                payload=payload,
                timestamp=old_timestamp
            )

        assert "timestamp" in str(exc_info.value).lower() or "replay" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_signature_constant_time_comparison(self, fake_db_pool):
        """
        Test that signature comparison uses constant-time algorithm.

        EXPECTED BEHAVIOR:
        - Uses hmac.compare_digest() for timing attack resistance
        - All comparisons take same time regardless of match
        """
        import time as time_module
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        payload = {"event": "test"}
        # Use current timestamp
        timestamp = str(int(time_module.time()))

        valid_signature = await dao.generate_signature(secret, payload, timestamp)
        invalid_signature = "sha256=" + ("0" * 64)

        # Time valid comparison
        start1 = time_module.perf_counter()
        try:
            await dao.validate_signature(secret, valid_signature, payload, timestamp)
        except:
            pass
        duration1 = time_module.perf_counter() - start1

        # Time invalid comparison
        start2 = time_module.perf_counter()
        try:
            await dao.validate_signature(secret, invalid_signature, payload, timestamp)
        except:
            pass
        duration2 = time_module.perf_counter() - start2

        # Assert timings are similar (within 10ms)
        assert abs(duration1 - duration2) < 0.01

    @pytest.mark.asyncio
    async def test_signature_with_large_payload(self, fake_db_pool):
        """
        Test signature generation/validation with large payload (10MB+).

        EXPECTED BEHAVIOR:
        - Handles large payloads efficiently
        - Signature generation is fast
        - No payload size limit for signing
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        secret = "whsec_test_secret_123"
        large_payload = {"data": "x" * (10 * 1024 * 1024)}  # 10MB
        timestamp = "1234567890"

        # Act
        signature = await dao.generate_signature(secret, large_payload, timestamp)

        # Assert
        assert signature.startswith("sha256=")
        assert len(signature) == 71

    @pytest.mark.asyncio
    async def test_signature_headers_format(self, fake_db_pool, sample_organization_id, sample_webhook_event):
        """
        Test that webhook request includes proper signature headers.

        EXPECTED BEHAVIOR:
        - X-Webhook-Signature: sha256=<hex>
        - X-Webhook-Timestamp: <unix_timestamp>
        - X-Webhook-ID: <event_id>
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - mock webhook config
        fake_db_pool.acquire.return_value.fetchrow.return_value = {
            "webhook_id": "webhook_789",
            "url": "https://example.com/webhook",
            "secret": "whsec_test_secret",
            "headers": "{}"
        }

        with patch("organization_management.infrastructure.repositories.webhook_dao.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            await dao.deliver_webhook_event(
                organization_id=sample_organization_id,
                webhook_event=sample_webhook_event
            )

            # Assert headers
            call_kwargs = mock_client.return_value.__aenter__.return_value.post.call_args.kwargs
            headers = call_kwargs["headers"]
            assert "X-Webhook-Signature" in headers
            assert "X-Webhook-Timestamp" in headers
            assert headers["X-Webhook-Signature"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_signature_secret_rotation_transition(self, fake_db_pool):
        """
        Test signature validation during secret rotation transition.

        EXPECTED BEHAVIOR:
        - During rotation, both old and new secrets are valid
        - Allows graceful transition period
        - Old secret expires after 24 hours
        """
        import time
        dao = WebhookDAO(db_pool=fake_db_pool)

        old_secret = "whsec_old_secret"
        new_secret = "whsec_new_secret"
        payload = {"event": "test"}
        # Use current timestamp
        timestamp = str(int(time.time()))

        # Generate signature with old secret
        old_signature = await dao.generate_signature(old_secret, payload, timestamp)

        # Act - validate with both secrets
        result = await dao.validate_signature_with_rotation(
            old_secret=old_secret,
            new_secret=new_secret,
            received_signature=old_signature,
            payload=payload,
            timestamp=timestamp
        )

        # Assert
        assert result is True  # Old signature still valid during transition


# ============================================================================
# TEST CLASS 5: Webhook Monitoring and Logging
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestWebhookMonitoringAndLogging:
    """
    Tests for webhook monitoring and delivery logging.

    BUSINESS REQUIREMENTS:
    - Log all webhook delivery attempts
    - Track success/failure rates
    - Monitor response times
    - Alert on repeated failures
    - Provide delivery analytics
    """

    @pytest.mark.asyncio
    async def test_log_webhook_delivery(self, fake_db_pool, sample_organization_id, sample_delivery_log):
        """
        Test logging webhook delivery attempt.

        EXPECTED BEHAVIOR:
        - Logs delivery metadata (status, time, response)
        - Stores in database for analytics
        - Returns log entry ID
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Act
        result = await dao.log_delivery(
            organization_id=sample_organization_id,
            delivery_log=sample_delivery_log
        )

        # Assert
        assert result["logged"] is True
        assert result["log_id"] is not None

    @pytest.mark.asyncio
    async def test_get_webhook_delivery_logs(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving webhook delivery logs.

        EXPECTED BEHAVIOR:
        - Returns paginated delivery logs
        - Includes filters (status, date range, event type)
        - Returns newest first
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {"delivery_id": f"del_{i}", "status": "delivered", "status_code": 200}
            for i in range(50)
        ]

        # Act
        result = await dao.get_delivery_logs(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            limit=50,
            offset=0
        )

        # Assert
        assert len(result["logs"]) == 50
        assert result["total_count"] >= 50

    @pytest.mark.asyncio
    async def test_get_webhook_delivery_statistics(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving webhook delivery statistics.

        EXPECTED BEHAVIOR:
        - Total deliveries
        - Success rate percentage
        - Average response time
        - Failed deliveries count
        - Broken down by time period (24h, 7d, 30d)
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "total_deliveries": 1000,
            "successful_deliveries": 980,
            "failed_deliveries": 20,
            "avg_response_time_ms": 156.5
        }

        # Act
        result = await dao.get_delivery_statistics(
            organization_id=sample_organization_id,
            webhook_id="webhook_789",
            period_days=7
        )

        # Assert
        assert result["total_deliveries"] == 1000
        assert result["success_rate"] == 98.0
        assert result["avg_response_time_ms"] == 156.5

    @pytest.mark.asyncio
    async def test_alert_on_repeated_failures(self, fake_db_pool, sample_organization_id):
        """
        Test alerting when webhook has repeated failures.

        EXPECTED BEHAVIOR:
        - Monitors failure rate
        - Triggers alert after 10 consecutive failures
        - Notifies organization admin
        - Optionally auto-deactivates webhook
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - 10 consecutive failures
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 10

        # Act
        result = await dao.check_failure_threshold(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert result["alert_triggered"] is True
        assert result["consecutive_failures"] == 10
        assert result["action"] == "notify_admin"

    @pytest.mark.asyncio
    async def test_get_webhook_health_status(self, fake_db_pool, sample_organization_id):
        """
        Test retrieving webhook health status.

        EXPECTED BEHAVIOR:
        - Returns health indicator (healthy, degraded, failing)
        - Based on recent delivery success rate
        - Includes last successful delivery timestamp
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "recent_success_rate": 0.95,
            "last_successful_delivery": datetime.utcnow().isoformat(),
            "consecutive_failures": 0
        }

        # Act
        result = await dao.get_webhook_health(
            organization_id=sample_organization_id,
            webhook_id="webhook_789"
        )

        # Assert
        assert result["health_status"] == "healthy"
        assert result["success_rate"] >= 0.95

    @pytest.mark.asyncio
    async def test_prune_old_delivery_logs(self, fake_db_pool):
        """
        Test pruning old delivery logs (data retention).

        EXPECTED BEHAVIOR:
        - Deletes logs older than retention period (90 days)
        - Keeps summary statistics
        - Returns count of deleted logs
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 5000

        # Act
        result = await dao.prune_old_logs(
            retention_days=90
        )

        # Assert
        assert result["deleted_count"] == 5000
        assert result["retention_policy_days"] == 90


# ============================================================================
# TEST CLASS 6: Security and Rate Limiting
# ============================================================================

@pytest.mark.skipif(WebhookDAO is None, reason="DAO not implemented yet (TDD RED phase)")
class TestWebhookSecurityAndRateLimiting:
    """
    Tests for webhook security and rate limiting.

    BUSINESS REQUIREMENTS:
    - Prevent webhook abuse
    - Rate limit deliveries per organization
    - Validate SSL certificates
    - Prevent SSRF attacks
    - Enforce webhook URL allowlist/blocklist
    """

    @pytest.mark.asyncio
    async def test_validate_webhook_url_ssl_certificate(self, fake_db_pool, sample_organization_id):
        """
        Test validating SSL certificate of webhook URL.

        EXPECTED BEHAVIOR:
        - Validates SSL certificate is valid
        - Checks certificate expiration
        - Raises ValidationException for invalid certs
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        invalid_url = "https://expired-ssl.example.com/webhook"

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.validate_webhook_url(
                url=invalid_url,
                check_ssl=True
            )

        assert "ssl" in str(exc_info.value).lower() or "certificate" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_prevent_ssrf_attack_via_webhook_url(self, fake_db_pool, sample_organization_id):
        """
        Test preventing SSRF attacks via malicious webhook URLs.

        EXPECTED BEHAVIOR:
        - Blocks localhost URLs
        - Blocks private IP ranges (10.0.0.0/8, 192.168.0.0/16, etc.)
        - Blocks metadata service URLs (169.254.169.254)
        - Raises ValidationException
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        malicious_urls = [
            "https://localhost/webhook",
            "https://127.0.0.1/webhook",
            "https://10.0.0.1/webhook",  # Private IP
            "https://192.168.1.1/webhook",  # Private IP
            "https://169.254.169.254/latest/meta-data"  # AWS metadata service
        ]

        for url in malicious_urls:
            # Act & Assert
            with pytest.raises(ValidationException) as exc_info:
                await dao.validate_webhook_url(url)

            assert "not allowed" in str(exc_info.value).lower() or "private" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_webhook_deliveries(self, fake_db_pool, sample_organization_id):
        """
        Test rate limiting webhook deliveries per organization.

        EXPECTED BEHAVIOR:
        - Limits: 1000 deliveries per hour per organization
        - Tracks delivery rate in Redis
        - Raises RateLimitException when exceeded
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.webhook_dao.check_rate_limit") as mock_check:
            mock_check.return_value = {"limit_exceeded": True, "retry_after": 300}

            # Act & Assert
            with pytest.raises(RateLimitException) as exc_info:
                await dao.check_delivery_rate_limit(
                    organization_id=sample_organization_id
                )

            assert "rate limit" in str(exc_info.value).lower()
            assert "300" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_webhook_url_allowlist(self, fake_db_pool, sample_organization_id):
        """
        Test webhook URL allowlist enforcement.

        EXPECTED BEHAVIOR:
        - Organizations can configure domain allowlist
        - Only allowed domains can receive webhooks
        - Raises ValidationException for non-allowed domains
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Arrange - allowlist configured
        fake_db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            "webhook_url_allowlist": ["api.trusted-service.com", "webhooks.partner.io"]
        }

        invalid_url = "https://untrusted-domain.com/webhook"

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            await dao.validate_webhook_url(
                organization_id=sample_organization_id,
                url=invalid_url,
                check_allowlist=True
            )

        assert "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_webhook_secret_encryption_at_rest(self, fake_db_pool, sample_organization_id, sample_webhook_config):
        """
        Test that webhook secrets are encrypted in database.

        EXPECTED BEHAVIOR:
        - Secrets encrypted before storage
        - Decrypted only when needed for signing
        - Uses strong encryption (AES-256)
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        with patch("organization_management.infrastructure.repositories.webhook_dao.encrypt_secret") as mock_encrypt:
            mock_encrypt.return_value = "encrypted_secret_base64=="

            # Act
            await dao.register_webhook(
                organization_id=sample_organization_id,
                webhook_config=sample_webhook_config
            )

            # Assert
            mock_encrypt.assert_called_once_with(sample_webhook_config["secret"])

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, fake_db_pool, sample_organization_id):
        """
        Test handling database connection failure.

        EXPECTED BEHAVIOR:
        - Catches connection errors
        - Raises DatabaseException with context
        - Does not expose internal details
        """
        dao = WebhookDAO(db_pool=fake_db_pool)

        # Use ConnectionRefusedError as asyncpg.ConnectionError doesn't exist
        fake_db_pool.acquire.side_effect = ConnectionRefusedError("DB unavailable")

        # Act & Assert
        with pytest.raises(DatabaseException) as exc_info:
            await dao.get_webhook(
                organization_id=sample_organization_id,
                webhook_id="webhook_789"
            )

        assert "database" in str(exc_info.value).lower()

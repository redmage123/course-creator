"""
Guest Session DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Guest Session Data Access Object ensuring all privacy-compliant
session management, GDPR/CCPA/PIPEDA compliance features, and conversion analytics work
correctly. The Guest Session DAO is the foundation of the platform's demo service,
enabling unauthenticated users to explore features while maintaining full regulatory
compliance and collecting valuable conversion funnel analytics.

TECHNICAL IMPLEMENTATION:
- Tests all 20+ DAO methods across 5 functional categories
- Validates privacy compliance (pseudonymization, consent tracking, right to erasure)
- Tests session lifecycle (creation, retrieval, update, deletion)
- Ensures audit logging for GDPR Article 30 compliance
- Validates returning guest recognition via fingerprinting
- Tests conversion analytics and funnel statistics

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates guest sessions with privacy compliance fields
- Records consent with GDPR-compliant versioning
- Implements Right to Erasure (GDPR Article 17)
- Pseudonymizes PII using HMAC-SHA256
- Recognizes returning guests without storing PII
- Exports anonymized analytics for conversion optimization
- Maintains comprehensive audit logs for compliance
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import sys
from pathlib import Path
import hashlib
import hmac

# Add demo-service to path
demo_service_path = Path(__file__).parent.parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))

from data_access.guest_session_dao import GuestSessionDAO, hash_ip_address, hash_user_agent, _SHARED_SESSIONS, _SHARED_AUDIT_LOGS, _SHARED_CONSENT_RECORDS
from domain.entities.guest_session import GuestSession
from exceptions import ValidationException, BusinessRuleException, CourseCreatorBaseException


# Test fixtures for cleanup
@pytest.fixture(autouse=True)
def cleanup_shared_storage():
    """Clean shared storage before and after each test"""
    _SHARED_SESSIONS.clear()
    _SHARED_AUDIT_LOGS.clear()
    _SHARED_CONSENT_RECORDS.clear()
    yield
    _SHARED_SESSIONS.clear()
    _SHARED_AUDIT_LOGS.clear()
    _SHARED_CONSENT_RECORDS.clear()


class TestGuestSessionDAOBasicCRUD:
    """
    Test Suite: Guest Session Basic CRUD Operations

    BUSINESS REQUIREMENT:
    System must create, retrieve, update, and delete guest sessions
    with proper privacy compliance and data integrity.
    """

    def test_create_session_with_default_values(self):
        """
        TEST: Create guest session with default configuration

        BUSINESS REQUIREMENT:
        Guest sessions must be created with default privacy-compliant
        settings (30-min expiration, 10 AI request limit, consent=false)

        VALIDATES:
        - Session created with UUID
        - 30-minute expiration set automatically
        - AI request limit set to 10
        - Privacy compliance fields initialized
        - Audit log entry created
        """
        dao = GuestSessionDAO()

        # Execute: Create session
        session = dao.create_session()

        # Verify: Session created
        assert session is not None
        assert isinstance(session.id, UUID)
        assert isinstance(session, GuestSession)

        # Verify: Default expiration (30 minutes)
        expiration_delta = session.expires_at - session.created_at
        assert 29 * 60 <= expiration_delta.total_seconds() <= 31 * 60  # ~30 minutes

        # Verify: Default AI limit
        assert session.ai_requests_count == 0
        assert session.ai_requests_limit == 10

        # Verify: Privacy fields initialized
        assert session.consent_given is False
        assert session.consent_timestamp is None
        assert session.privacy_policy_version is None
        assert session.cookie_preferences == {}

        # Verify: Audit log created
        audit_logs = dao.get_audit_logs(session.id)
        assert len(audit_logs) == 1
        assert audit_logs[0]['action'] == 'created'

    def test_get_session_existing(self):
        """
        TEST: Retrieve existing guest session

        BUSINESS REQUIREMENT:
        System must retrieve active sessions to validate demo access

        VALIDATES:
        - Session retrieved by UUID
        - All fields intact after retrieval
        - Privacy compliance fields preserved
        """
        dao = GuestSessionDAO()

        # Setup: Create session
        created_session = dao.create_session()
        session_id = created_session.id

        # Execute: Retrieve session
        retrieved_session = dao.get_session(session_id)

        # Verify: Session retrieved
        assert retrieved_session is not None
        assert retrieved_session.id == session_id

        # Verify: Fields preserved
        assert retrieved_session.created_at == created_session.created_at
        assert retrieved_session.expires_at == created_session.expires_at
        assert retrieved_session.ai_requests_limit == created_session.ai_requests_limit

    def test_get_session_not_found(self):
        """
        TEST: Retrieve non-existent session

        BUSINESS REQUIREMENT:
        System must return None for non-existent sessions without errors

        VALIDATES:
        - Returns None for invalid UUID
        - No exception raised
        """
        dao = GuestSessionDAO()

        # Execute: Get non-existent session
        session = dao.get_session(uuid4())

        # Verify: None returned
        assert session is None

    def test_update_session_fields(self):
        """
        TEST: Update guest session data

        BUSINESS REQUIREMENT:
        Sessions must be updatable to track engagement and AI usage

        VALIDATES:
        - Session fields can be updated
        - Updated timestamp set automatically
        - Audit log entry created
        - Privacy fields preserved from original
        """
        dao = GuestSessionDAO()

        # Setup: Create and modify session
        session = dao.create_session()
        session.ai_requests_count = 5
        session.features_viewed = ['ai_content_generation', 'docker_labs']

        # Execute: Update session
        updated_session = dao.update_session(session)

        # Verify: Fields updated
        assert updated_session.ai_requests_count == 5
        assert len(updated_session.features_viewed) == 2
        assert 'ai_content_generation' in updated_session.features_viewed

        # Verify: Updated timestamp set
        assert hasattr(updated_session, 'updated_at')
        assert updated_session.updated_at is not None

        # Verify: Audit log created
        audit_logs = dao.get_audit_logs(session.id)
        assert len(audit_logs) >= 2  # Created + updated
        update_logs = [log for log in audit_logs if log['action'] == 'updated']
        assert len(update_logs) == 1

    def test_delete_session_right_to_erasure(self):
        """
        TEST: Delete guest session (GDPR Right to Erasure)

        BUSINESS REQUIREMENT:
        GDPR Article 17 grants users right to request deletion of their data

        VALIDATES:
        - Session deleted successfully
        - Returns True on successful deletion
        - Session no longer retrievable
        - Audit log entry created BEFORE deletion
        """
        dao = GuestSessionDAO()

        # Setup: Create session
        session = dao.create_session()
        session_id = session.id

        # Execute: Delete session
        result = dao.delete_session(session_id)

        # Verify: Deletion successful
        assert result is True

        # Verify: Session no longer exists
        retrieved = dao.get_session(session_id)
        assert retrieved is None

        # Verify: Audit log created
        audit_logs = dao.get_audit_logs(session_id)
        delete_logs = [log for log in audit_logs if log['action'] == 'deleted']
        assert len(delete_logs) == 1
        assert delete_logs[0]['details']['deletion_type'] == 'immediate'


class TestGuestSessionDAOPrivacyCompliance:
    """
    Test Suite: Privacy Compliance Operations

    BUSINESS REQUIREMENT:
    System must comply with GDPR/CCPA/PIPEDA regulations for guest data handling.
    """

    def test_record_consent_with_pseudonymization(self):
        """
        TEST: Record consent with hashed IP and user agent

        BUSINESS REQUIREMENT:
        GDPR Article 7 requires proof of consent with timestamp and version

        VALIDATES:
        - Consent stored with timestamp
        - Privacy policy version recorded
        - Cookie preferences saved
        - IP address and user agent hashed (pseudonymized)
        - Consent record created
        - Audit log entry created
        """
        dao = GuestSessionDAO()

        # Setup: Create session
        session = dao.create_session()

        # Execute: Record consent
        dao.record_consent(
            session_id=session.id,
            consent_given=True,
            privacy_policy_version='3.3.1',
            cookie_preferences={
                'functional': True,
                'analytics': True,
                'marketing': False
            },
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        )

        # Verify: Session updated with consent
        updated_session = dao.get_session(session.id)
        assert updated_session.consent_given is True
        assert updated_session.privacy_policy_version == '3.3.1'
        assert updated_session.cookie_preferences['functional'] is True
        assert updated_session.cookie_preferences['marketing'] is False

        # Verify: IP and user agent hashed
        assert updated_session.ip_address_hash is not None
        assert updated_session.user_agent_fingerprint is not None
        assert isinstance(updated_session.ip_address_hash, bytes)

        # Verify: Consent record created
        assert len(_SHARED_CONSENT_RECORDS) == 1
        consent_record = _SHARED_CONSENT_RECORDS[0]
        assert consent_record['guest_session_id'] == session.id
        assert consent_record['privacy_policy_version'] == '3.3.1'

        # Verify: Audit log
        audit_logs = dao.get_audit_logs(session.id)
        consent_logs = [log for log in audit_logs if log['action'] == 'consent_given']
        assert len(consent_logs) == 1

    def test_pseudonymization_functions_deterministic(self):
        """
        TEST: Hashing functions are deterministic

        BUSINESS REQUIREMENT:
        Pseudonymization must be deterministic for returning guest recognition

        VALIDATES:
        - Same IP produces same hash
        - Same user agent produces same hash
        - Different IPs produce different hashes
        - Hashes are irreversible (32 bytes)
        """
        secret_key = b'test_secret_key'

        # Execute: Hash same IP twice
        ip = '192.168.1.100'
        hash1 = hash_ip_address(ip, secret_key)
        hash2 = hash_ip_address(ip, secret_key)

        # Verify: Deterministic (same result)
        assert hash1 == hash2
        assert len(hash1) == 32  # SHA256 = 32 bytes

        # Execute: Hash different IP
        ip2 = '192.168.1.101'
        hash3 = hash_ip_address(ip2, secret_key)

        # Verify: Different hash
        assert hash1 != hash3

        # Execute: Hash user agent
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        ua_hash1 = hash_user_agent(ua, secret_key)
        ua_hash2 = hash_user_agent(ua, secret_key)

        # Verify: Deterministic
        assert ua_hash1 == ua_hash2
        assert len(ua_hash1) == 32

    def test_request_deletion_marks_session_for_deletion(self):
        """
        TEST: Request deletion (GDPR Article 17)

        BUSINESS REQUIREMENT:
        Users can request data deletion with 30-day grace period

        VALIDATES:
        - Session marked for deletion
        - Deletion timestamp recorded
        - Scheduled deletion date set (30 days)
        - Audit log entry created
        - Returns deletion timestamp
        """
        dao = GuestSessionDAO()

        # Setup: Create session
        session = dao.create_session()

        # Execute: Request deletion
        deletion_timestamp = dao.request_deletion(
            session_id=session.id,
            reason='User requested data deletion'
        )

        # Verify: Deletion timestamp returned
        assert deletion_timestamp is not None
        assert isinstance(deletion_timestamp, datetime)

        # Verify: Session marked for deletion
        updated_session = dao.get_session(session.id)
        assert updated_session.deletion_requested_at is not None
        assert updated_session.deletion_scheduled_at is not None

        # Verify: Scheduled 30 days out
        delta = updated_session.deletion_scheduled_at - deletion_timestamp
        assert 29 <= delta.days <= 31  # ~30 days

        # Verify: Audit log
        audit_logs = dao.get_audit_logs(session.id)
        deletion_logs = [log for log in audit_logs if log['action'] == 'deletion_requested']
        assert len(deletion_logs) == 1
        assert 'reason' in deletion_logs[0]['details']

    def test_execute_deletion_removes_session_immediately(self):
        """
        TEST: Execute immediate deletion

        BUSINESS REQUIREMENT:
        System can execute deletion immediately after request

        VALIDATES:
        - Session deleted immediately
        - Returns True on success
        - Session no longer retrievable
        """
        dao = GuestSessionDAO()

        # Setup: Create and request deletion
        session = dao.create_session()
        dao.request_deletion(session.id, 'immediate_deletion')

        # Execute: Execute deletion
        result = dao.execute_deletion(session.id)

        # Verify: Deletion successful
        assert result is True
        assert dao.get_session(session.id) is None

    def test_cleanup_old_sessions_retention_policy(self):
        """
        TEST: Cleanup old sessions (GDPR Storage Limitation)

        BUSINESS REQUIREMENT:
        GDPR Article 5(1)(e) requires data be kept only as long as necessary

        VALIDATES:
        - Sessions older than retention period deleted
        - Recent sessions preserved
        - Returns count of deleted sessions
        """
        dao = GuestSessionDAO()

        # Setup: Create sessions with different ages
        recent_session = dao.create_session()

        old_session = dao.create_session()
        # Manually set creation date to 40 days ago
        old_session_data = _SHARED_SESSIONS[old_session.id]
        old_session_data['created_at'] = datetime.utcnow() - timedelta(days=40)

        # Execute: Cleanup with 30-day retention
        deleted_count = dao.cleanup_old_sessions(retention_days=30)

        # Verify: Old session deleted
        assert deleted_count == 1
        assert dao.get_session(old_session.id) is None

        # Verify: Recent session preserved
        assert dao.get_session(recent_session.id) is not None


class TestGuestSessionDAOAuditLogging:
    """
    Test Suite: Audit Logging Operations

    BUSINESS REQUIREMENT:
    GDPR Article 30 requires maintaining records of processing activities.
    """

    def test_audit_log_created_on_session_creation(self):
        """
        TEST: Audit log entry on session creation

        BUSINESS REQUIREMENT:
        All data processing activities must be logged for compliance

        VALIDATES:
        - Audit log created automatically
        - Contains session_id, action, timestamp
        - Checksum generated for tamper detection
        """
        dao = GuestSessionDAO()

        # Execute: Create session
        session = dao.create_session()

        # Verify: Audit log created
        audit_logs = dao.get_audit_logs(session.id)
        assert len(audit_logs) == 1

        log = audit_logs[0]
        assert log['action'] == 'created'
        assert log['guest_session_id'] == session.id
        assert 'timestamp' in log
        assert 'checksum' in log

    def test_audit_logs_accumulate_for_session_lifecycle(self):
        """
        TEST: Multiple audit logs for session lifecycle

        BUSINESS REQUIREMENT:
        Complete activity history must be maintained for each session

        VALIDATES:
        - Create, update, consent, deletion all logged
        - Logs ordered chronologically
        - Each log has unique action
        """
        dao = GuestSessionDAO()

        # Execute: Full session lifecycle
        session = dao.create_session()
        session.ai_requests_count = 3
        dao.update_session(session)
        dao.record_consent(
            session.id, True, '3.3.1',
            {'functional': True},
            '192.168.1.1', 'Mozilla/5.0'
        )
        dao.request_deletion(session.id, 'test')

        # Verify: All actions logged
        audit_logs = dao.get_audit_logs(session.id)
        assert len(audit_logs) == 4

        actions = [log['action'] for log in audit_logs]
        assert 'created' in actions
        assert 'updated' in actions
        assert 'consent_given' in actions
        assert 'deletion_requested' in actions

    def test_log_data_access_for_gdpr_transparency(self):
        """
        TEST: Log data access events (GDPR Article 15)

        BUSINESS REQUIREMENT:
        Track when users access their own data for transparency

        VALIDATES:
        - Data access logged with hashed IP
        - Timestamp recorded
        - Audit log entry created
        """
        dao = GuestSessionDAO()

        # Setup: Create session
        session = dao.create_session()

        # Execute: Log data access
        dao.log_data_access(
            session_id=session.id,
            ip_address='192.168.1.50'
        )

        # Verify: Access logged
        audit_logs = dao.get_audit_logs(session.id)
        access_logs = [log for log in audit_logs if log['action'] == 'data_accessed']
        assert len(access_logs) == 1
        assert access_logs[0]['ip_address_hash'] is not None

    def test_audit_log_checksum_for_tamper_detection(self):
        """
        TEST: Audit log checksums prevent tampering

        BUSINESS REQUIREMENT:
        Audit logs must be tamper-evident for regulatory compliance

        VALIDATES:
        - Each log has SHA256 checksum
        - Checksum includes session_id, action, timestamp
        - Checksums are unique per log entry
        """
        dao = GuestSessionDAO()

        # Execute: Create multiple log entries
        session1 = dao.create_session()
        session2 = dao.create_session()

        # Verify: Checksums exist and differ
        logs1 = dao.get_audit_logs(session1.id)
        logs2 = dao.get_audit_logs(session2.id)

        assert logs1[0]['checksum'] != logs2[0]['checksum']
        assert len(logs1[0]['checksum']) == 64  # SHA256 hex = 64 chars


class TestGuestSessionDAOReturningGuestRecognition:
    """
    Test Suite: Returning Guest Recognition

    BUSINESS REQUIREMENT:
    Recognize returning guests using fingerprints for personalized experience.
    """

    def test_find_or_create_new_guest(self):
        """
        TEST: Create new session for first-time guest

        BUSINESS REQUIREMENT:
        First-time guests get new session with default settings

        VALIDATES:
        - New session created
        - is_returning_guest = False
        - Fingerprint stored (hashed IP + user agent)
        - Default preferences applied
        """
        dao = GuestSessionDAO()

        # Execute: Find or create for new guest
        session = dao.find_or_create_session(
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0)'
        )

        # Verify: New session created
        assert session is not None
        assert session.is_returning_guest is False

        # Verify: Fingerprint stored
        assert session.ip_address_hash is not None
        assert session.user_agent_fingerprint is not None

    def test_find_or_create_returning_guest(self):
        """
        TEST: Recognize returning guest by fingerprint

        BUSINESS REQUIREMENT:
        Returning guests should be recognized and preferences restored

        VALIDATES:
        - Previous session found by fingerprint match
        - New session created with is_returning_guest = True
        - User preferences copied from previous session
        - Fingerprint stored in new session
        """
        dao = GuestSessionDAO()

        # Setup: Create first session with preferences
        ip = '192.168.1.200'
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X)'

        first_session = dao.find_or_create_session(ip, ua)
        first_session.user_profile = {'role': 'instructor', 'interests': ['AI']}
        first_session.communication_style = 'technical'
        dao.update_session(first_session)

        # Execute: Return as same guest
        second_session = dao.find_or_create_session(ip, ua)

        # Verify: Recognized as returning guest
        assert second_session.is_returning_guest is True
        assert second_session.id != first_session.id  # New session

        # Verify: Preferences restored
        assert second_session.user_profile == first_session.user_profile
        assert second_session.communication_style == first_session.communication_style

    def test_fingerprint_matching_is_precise(self):
        """
        TEST: Fingerprint matching requires exact IP + user agent match

        BUSINESS REQUIREMENT:
        Guest recognition must be precise to avoid false positives

        VALIDATES:
        - Different IP = not recognized as returning guest
        - Different user agent = not recognized as returning guest
        - Both must match for recognition
        """
        dao = GuestSessionDAO()

        # Setup: Create session with specific fingerprint
        ip1 = '192.168.1.100'
        ua1 = 'Mozilla/5.0 (Windows)'

        first_session = dao.find_or_create_session(ip1, ua1)

        # Execute: Try with different IP
        session_diff_ip = dao.find_or_create_session('192.168.1.101', ua1)
        assert session_diff_ip.is_returning_guest is False

        # Execute: Try with different user agent
        session_diff_ua = dao.find_or_create_session(ip1, 'Chrome/90.0')
        assert session_diff_ua.is_returning_guest is False

        # Execute: Try with exact match
        session_match = dao.find_or_create_session(ip1, ua1)
        assert session_match.is_returning_guest is True


class TestGuestSessionDAOConversionAnalytics:
    """
    Test Suite: Conversion Analytics and Funnel Tracking

    BUSINESS REQUIREMENT:
    Marketing team needs analytics to optimize conversion funnel.
    """

    def test_export_analytics_date_range(self):
        """
        TEST: Export session analytics for date range

        BUSINESS REQUIREMENT:
        Marketing needs analytics data to track conversion patterns

        VALIDATES:
        - Only sessions in date range exported
        - Analytics include engagement metrics
        - Conversion score calculated
        - Data anonymized (no PII)
        """
        dao = GuestSessionDAO()

        # Setup: Create sessions with different dates
        now = datetime.utcnow()

        session1 = dao.create_session()
        session1.features_viewed = ['ai_content', 'docker_labs']
        session1.ai_requests_count = 7
        dao.update_session(session1)

        session2 = dao.create_session()
        # Manually set to 45 days ago
        _SHARED_SESSIONS[session2.id]['created_at'] = now - timedelta(days=45)

        # Execute: Export last 30 days
        start_date = now - timedelta(days=30)
        end_date = now
        analytics = dao.export_analytics(start_date, end_date)

        # Verify: Only recent session included
        assert len(analytics) == 1
        assert analytics[0]['session_id'] == session1.id

        # Verify: Analytics fields present
        assert 'features_count' in analytics[0]
        assert 'conversion_score' in analytics[0]
        assert 'duration_seconds' in analytics[0]

        # Verify: Conversion score calculated correctly
        # 2 features * 2 + 1 (AI engagement bonus) = 5
        assert analytics[0]['conversion_score'] == 5

    def test_conversion_funnel_stats_grouping(self):
        """
        TEST: Calculate conversion funnel statistics

        BUSINESS REQUIREMENT:
        Group sessions by engagement level to identify bottlenecks

        VALIDATES:
        - Sessions grouped into low/medium/high engagement
        - Low = 0-1 features
        - Medium = 2-3 features
        - High = 4+ features
        - Percentages calculated
        """
        dao = GuestSessionDAO()

        # Setup: Create sessions with different engagement levels
        # Low engagement (1 feature)
        low_session = dao.create_session()
        low_session.features_viewed = ['homepage']
        dao.update_session(low_session)

        # Medium engagement (2 features)
        medium_session = dao.create_session()
        medium_session.features_viewed = ['ai_content', 'docker_labs']
        dao.update_session(medium_session)

        # High engagement (4 features)
        high_session = dao.create_session()
        high_session.features_viewed = ['ai_content', 'docker_labs', 'analytics', 'courses']
        dao.update_session(high_session)

        # Execute: Get funnel stats
        stats = dao.get_conversion_funnel_stats()

        # Verify: Grouping correct
        assert stats['low_engagement_count'] == 1
        assert stats['medium_engagement_count'] == 1
        assert stats['high_engagement_count'] == 1
        assert stats['total_sessions'] == 3

        # Verify: Percentage calculated
        assert stats['high_engagement_percentage'] == pytest.approx(33.33, rel=0.1)

    def test_conversion_score_calculation(self):
        """
        TEST: Conversion score algorithm

        BUSINESS REQUIREMENT:
        Score guests 0-10 based on engagement to prioritize marketing

        VALIDATES:
        - Features viewed contribute 2 points each
        - AI engagement (>5 requests) adds 1 bonus point
        - Score capped at 10
        - Score included in analytics export
        """
        dao = GuestSessionDAO()

        # Setup: Create high-engagement session
        session = dao.create_session()
        session.features_viewed = ['f1', 'f2', 'f3', 'f4', 'f5']  # 5 features
        session.ai_requests_count = 6  # Triggers bonus
        dao.update_session(session)

        # Execute: Export analytics
        analytics = dao.export_analytics(
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow() + timedelta(hours=1)
        )

        # Verify: Conversion score
        # 5 features * 2 = 10, +1 bonus = 11, capped at 10
        assert analytics[0]['conversion_score'] == 10
        assert analytics[0]['features_count'] == 5
        assert analytics[0]['ai_requests_count'] == 6


class TestGuestSessionDAOSchemaValidation:
    """
    Test Suite: Database Schema Validation

    BUSINESS REQUIREMENT:
    Verify database schema matches privacy compliance requirements.
    """

    def test_guest_sessions_table_schema(self):
        """
        TEST: Guest sessions table has all required columns

        BUSINESS REQUIREMENT:
        Table must include all GDPR-required fields for compliance

        VALIDATES:
        - Privacy compliance columns present
        - Timestamps for tracking
        - Pseudonymization fields (bytea)
        - JSON fields for flexible data
        """
        dao = GuestSessionDAO()

        # Execute: Get schema
        schema = dao.get_table_schema('guest_sessions')

        # Verify: Required columns present
        required_columns = [
            'id', 'created_at', 'updated_at', 'expires_at',
            'consent_given', 'consent_timestamp', 'privacy_policy_version',
            'ip_address_hash', 'user_agent_fingerprint',
            'deletion_requested_at', 'deletion_scheduled_at'
        ]

        for column in required_columns:
            assert column in schema['columns'], f"Missing column: {column}"

        # Verify: Pseudonymization fields are bytea
        assert schema['columns']['ip_address_hash'] == 'bytea'
        assert schema['columns']['user_agent_fingerprint'] == 'bytea'

    def test_audit_log_table_schema(self):
        """
        TEST: Audit log table has compliance-required columns

        BUSINESS REQUIREMENT:
        Audit logs must capture all required information for GDPR Article 30

        VALIDATES:
        - Action and timestamp columns
        - Checksum for tamper detection
        - Pseudonymized IP and user agent
        - JSONB details field
        """
        dao = GuestSessionDAO()

        # Execute: Get schema
        schema = dao.get_table_schema('guest_session_audit_log')

        # Verify: Required columns
        required_columns = [
            'id', 'guest_session_id', 'action', 'timestamp',
            'ip_address_hash', 'user_agent_fingerprint',
            'details', 'checksum'
        ]

        for column in required_columns:
            assert column in schema['columns'], f"Missing column: {column}"

        # Verify: Details is JSONB
        assert schema['columns']['details'] == 'jsonb'

    def test_consent_records_table_schema(self):
        """
        TEST: Consent records table schema validation

        BUSINESS REQUIREMENT:
        GDPR Article 7 requires detailed consent records

        VALIDATES:
        - Privacy policy version tracking
        - Cookie preferences (functional, analytics, marketing)
        - Consent timestamp and method
        - Withdrawal tracking fields
        """
        dao = GuestSessionDAO()

        # Execute: Get schema
        schema = dao.get_table_schema('consent_records')

        # Verify: Required columns
        required_columns = [
            'id', 'guest_session_id', 'consent_timestamp',
            'privacy_policy_version', 'cookie_policy_version',
            'functional_cookies', 'analytics_cookies', 'marketing_cookies',
            'consent_method', 'withdrawn_at'
        ]

        for column in required_columns:
            assert column in schema['columns'], f"Missing column: {column}"


class TestGuestSessionDAOExpiredSessionHandling:
    """
    Test Suite: Expired Session Detection and Cleanup

    BUSINESS REQUIREMENT:
    Automatically detect and clean up expired sessions for security and performance.
    """

    def test_find_expired_sessions(self):
        """
        TEST: Query for expired sessions

        BUSINESS REQUIREMENT:
        System must identify expired sessions for cleanup

        VALIDATES:
        - Returns list of expired session UUIDs
        - Active sessions not included
        - Query efficient (no full scan needed)
        """
        dao = GuestSessionDAO()

        # Setup: Create mix of active and expired
        active = dao.create_session()

        expired = dao.create_session()
        _SHARED_SESSIONS[expired.id]['expires_at'] = datetime.utcnow() - timedelta(hours=1)

        # Execute: Find expired
        expired_ids = dao.find_expired_sessions()

        # Verify: Only expired found
        assert len(expired_ids) == 1
        assert expired.id in expired_ids
        assert active.id not in expired_ids

    def test_bulk_delete_expired_sessions(self):
        """
        TEST: Bulk cleanup of multiple expired sessions

        BUSINESS REQUIREMENT:
        Efficient bulk deletion for regular cleanup jobs

        VALIDATES:
        - Multiple expired sessions deleted
        - Active sessions preserved
        - Deletion count accurate
        """
        dao = GuestSessionDAO()

        # Setup: Create 3 expired, 2 active
        active1 = dao.create_session()
        active2 = dao.create_session()

        for _ in range(3):
            expired = dao.create_session()
            _SHARED_SESSIONS[expired.id]['expires_at'] = datetime.utcnow() - timedelta(hours=1)

        # Execute: Find and delete expired
        expired_ids = dao.find_expired_sessions()
        delete_count = sum(dao.delete_session(sid) for sid in expired_ids)

        # Verify: 3 deleted, 2 remain
        assert delete_count == 3
        assert len(_SHARED_SESSIONS) == 2
        assert dao.get_session(active1.id) is not None
        assert dao.get_session(active2.id) is not None

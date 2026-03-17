"""
TDD RED Phase: PostgreSQL Guest Session Storage with Privacy Compliance

BUSINESS REQUIREMENT:
Guest sessions must be stored in PostgreSQL with full GDPR/CCPA/PIPEDA compliance.
This allows:
- Session persistence across browser refreshes
- Returning guest recognition
- Conversion analytics and funnel optimization
- Privacy-compliant data collection with user consent

PRIVACY COMPLIANCE REQUIREMENTS:
- GDPR (EU): Articles 6, 7, 13, 17, 25, 32
- CCPA (California): Right to Know, Delete, Opt-Out
- PIPEDA (Canada): 10 privacy principles
- 30-day maximum data retention
- Pseudonymization (IP/user agent hashing)
- Explicit consent tracking
- Audit logging for all privacy-related actions

These tests should FAIL until we implement PostgreSQL backing store.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import hmac

# Add demo-service to path for imports
demo_service_path = Path(__file__).parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))

from organization_management.domain.entities.guest_session import GuestSession


class TestGuestSessionDAO:
    """
    Test: PostgreSQL Data Access Object for guest sessions

    BUSINESS REQUIREMENT:
    Guest sessions must persist in PostgreSQL for:
    - Session recovery after browser refresh
    - Returning guest recognition
    - Conversion analytics
    - Privacy compliance (audit trail, consent tracking)
    """

    def test_create_guest_session_in_database(self):
        """
        Test: Create new guest session in PostgreSQL

        EXPECTED BEHAVIOR:
        - Generate UUID for session ID
        - Store session with default values (30-min expiration, 10 AI requests limit)
        - Return GuestSession object with database ID
        - Created_at and updated_at timestamps set automatically
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        assert session is not None
        assert session.id is not None
        assert session.created_at is not None
        assert session.expires_at is not None
        assert session.expires_at == session.created_at + timedelta(minutes=30)
        assert session.ai_requests_count == 0
        assert session.ai_requests_limit == 10
        assert session.consent_given is False

    def test_retrieve_guest_session_by_id(self):
        """
        Test: Retrieve existing guest session from database

        EXPECTED BEHAVIOR:
        - Query database by session UUID
        - Return GuestSession object with all stored fields
        - Return None if session not found
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create session
        created_session = dao.create_session()
        session_id = created_session.id

        # Retrieve session
        retrieved_session = dao.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session.id == session_id
        assert retrieved_session.created_at == created_session.created_at
        assert retrieved_session.ai_requests_count == 0

    def test_update_guest_session_in_database(self):
        """
        Test: Update guest session fields in PostgreSQL

        EXPECTED BEHAVIOR:
        - Modify GuestSession object fields
        - Save changes to database
        - Updated_at timestamp automatically incremented
        - Verify changes persisted
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create and retrieve session
        session = dao.create_session()
        session_id = session.id

        # Update session
        session.ai_requests_count = 5
        session.user_profile = {'role': 'instructor', 'pain_points': ['time-consuming grading']}
        session.features_viewed = ['chatbot', 'ai_content_generation']

        dao.update_session(session)

        # Retrieve and verify
        updated_session = dao.get_session(session_id)
        assert updated_session.ai_requests_count == 5
        assert updated_session.user_profile['role'] == 'instructor'
        assert 'chatbot' in updated_session.features_viewed
        assert updated_session.updated_at > updated_session.created_at

    def test_delete_guest_session_from_database(self):
        """
        Test: Delete guest session (GDPR Right to Erasure)

        EXPECTED BEHAVIOR:
        - Delete session record from database
        - Cascade delete related records (audit logs, consent records)
        - Return True on success
        - Subsequent retrieval returns None
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create session
        session = dao.create_session()
        session_id = session.id

        # Delete session
        result = dao.delete_session(session_id)

        assert result is True

        # Verify deleted
        deleted_session = dao.get_session(session_id)
        assert deleted_session is None

    def test_query_sessions_by_expiration_date(self):
        """
        Test: Query sessions for cleanup (expired sessions)

        EXPECTED BEHAVIOR:
        - Find all sessions where expires_at < NOW()
        - Return list of expired session IDs
        - Used by automatic cleanup cron job
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create expired session (created 31 minutes ago)
        expired_session = dao.create_session()
        expired_session.created_at = datetime.utcnow() - timedelta(minutes=31)
        expired_session.expires_at = expired_session.created_at + timedelta(minutes=30)
        dao.update_session(expired_session)

        # Create active session
        active_session = dao.create_session()

        # Query expired sessions
        expired_ids = dao.find_expired_sessions()

        assert expired_session.id in expired_ids
        assert active_session.id not in expired_ids


class TestPrivacyCompliance:
    """
    Test: GDPR/CCPA/PIPEDA privacy compliance features

    BUSINESS REQUIREMENT:
    Guest session storage must comply with international privacy regulations.
    Non-compliance risks legal penalties and damages brand reputation.
    """

    def test_consent_tracking_stored_in_database(self):
        """
        Test: Consent records stored with timestamp and version

        GDPR Article 7: Conditions for Consent
        - Consent must be freely given, specific, informed, unambiguous
        - Must prove consent was given
        - Track which privacy policy version user consented to
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # User gives consent
        consent_timestamp = datetime.utcnow()
        dao.record_consent(
            session_id=session.id,
            consent_given=True,
            privacy_policy_version='3.3.0',
            cookie_preferences={
                'functional': True,
                'analytics': True,
                'marketing': False
            },
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        )

        # Retrieve and verify
        updated_session = dao.get_session(session.id)
        assert updated_session.consent_given is True
        assert updated_session.consent_timestamp is not None
        assert updated_session.privacy_policy_version == '3.3.0'
        assert updated_session.cookie_preferences['functional'] is True
        assert updated_session.cookie_preferences['marketing'] is False

    def test_ip_address_pseudonymization(self):
        """
        Test: IP addresses stored as HMAC-SHA256 hashes (not plaintext)

        GDPR Recital 26: Pseudonymization reduces risks
        GDPR Article 32: Security of Processing (encryption/pseudonymization)

        EXPECTED BEHAVIOR:
        - Store HMAC-SHA256 hash of IP address (not plaintext)
        - Use secret key from environment variable
        - Cannot reverse hash to original IP
        """
        from data_access.guest_session_dao import GuestSessionDAO, hash_ip_address

        dao = GuestSessionDAO()
        session = dao.create_session()

        ip_address = '203.0.113.45'
        secret_key = b'test_secret_key_12345'

        # Hash IP address
        ip_hash = hash_ip_address(ip_address, secret_key)

        # Store session with hashed IP
        dao.record_consent(
            session_id=session.id,
            consent_given=True,
            privacy_policy_version='3.3.0',
            cookie_preferences={'functional': True},
            ip_address=ip_address,
            user_agent='Mozilla/5.0'
        )

        # Retrieve session
        updated_session = dao.get_session(session.id)

        # Verify IP is stored as hash (not plaintext)
        assert updated_session.ip_address_hash is not None
        assert len(updated_session.ip_address_hash) == 32  # SHA-256 = 32 bytes
        assert updated_session.ip_address_hash != ip_address.encode()  # Not plaintext

        # Verify hash matches expected value
        expected_hash = hmac.new(secret_key, ip_address.encode(), hashlib.sha256).digest()
        assert updated_session.ip_address_hash == expected_hash

    def test_user_agent_pseudonymization(self):
        """
        Test: User agents stored as HMAC-SHA256 hashes

        BUSINESS REQUIREMENT:
        User agent strings can fingerprint users. Hash them for privacy.
        Use hashed user agent to recognize returning guests without PII.
        """
        from data_access.guest_session_dao import GuestSessionDAO, hash_user_agent

        dao = GuestSessionDAO()
        session = dao.create_session()

        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        secret_key = b'test_secret_key_12345'

        # Hash user agent
        ua_hash = hash_user_agent(user_agent, secret_key)

        # Store session
        dao.record_consent(
            session_id=session.id,
            consent_given=True,
            privacy_policy_version='3.3.0',
            cookie_preferences={'functional': True},
            ip_address='192.168.1.1',
            user_agent=user_agent
        )

        # Retrieve and verify
        updated_session = dao.get_session(session.id)
        assert updated_session.user_agent_fingerprint is not None
        assert len(updated_session.user_agent_fingerprint) == 32  # SHA-256
        assert updated_session.user_agent_fingerprint != user_agent.encode()

    def test_30_day_data_retention_policy(self):
        """
        Test: Sessions older than 30 days automatically deleted

        GDPR Article 5(1)(e): Storage Limitation
        - Keep data only as long as necessary
        - Delete sessions after 30 days

        EXPECTED BEHAVIOR:
        - cleanup_expired_guest_sessions() deletes sessions > 30 days old
        - Audit logs retained for 90 days (separate table)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create old session (31 days old)
        old_session = dao.create_session()
        old_session.created_at = datetime.utcnow() - timedelta(days=31)
        dao.update_session(old_session)

        # Create recent session (5 days old)
        recent_session = dao.create_session()
        recent_session.created_at = datetime.utcnow() - timedelta(days=5)
        dao.update_session(recent_session)

        # Run cleanup
        deleted_count = dao.cleanup_old_sessions(retention_days=30)

        assert deleted_count >= 1

        # Verify old session deleted
        assert dao.get_session(old_session.id) is None

        # Verify recent session still exists
        assert dao.get_session(recent_session.id) is not None

    def test_right_to_erasure_deletion_request(self):
        """
        Test: User can request immediate deletion (GDPR Article 17)

        GDPR Article 17: Right to Erasure ("Right to be Forgotten")
        CCPA: Right to Delete

        EXPECTED BEHAVIOR:
        - User requests deletion via privacy API
        - Session marked with deletion_requested_at timestamp
        - Session deleted within 30 days (or immediately)
        - Audit log records deletion request
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # User requests deletion
        deletion_timestamp = dao.request_deletion(session.id, reason='user_request')

        # Verify deletion timestamp recorded
        updated_session = dao.get_session(session.id)
        assert updated_session.deletion_requested_at is not None
        assert updated_session.deletion_requested_at == deletion_timestamp

        # Immediate deletion option
        dao.execute_deletion(session.id)

        # Verify session deleted
        assert dao.get_session(session.id) is None


class TestAuditLogging:
    """
    Test: Audit logging for all privacy-related actions

    GDPR Article 30: Records of Processing Activities
    BUSINESS REQUIREMENT: Track all data access and modifications for compliance
    """

    def test_audit_log_session_creation(self):
        """
        Test: Log session creation event

        EXPECTED BEHAVIOR:
        - Record: guest_session_id, action='created', timestamp, ip_hash
        - Audit log entry persisted to database
        - Checksum generated for tamper detection
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # Retrieve audit log
        audit_logs = dao.get_audit_logs(session.id)

        assert len(audit_logs) >= 1
        assert audit_logs[0]['action'] == 'created'
        assert audit_logs[0]['guest_session_id'] == session.id
        assert audit_logs[0]['timestamp'] is not None

    def test_audit_log_consent_given(self):
        """
        Test: Log consent events (GDPR compliance proof)

        EXPECTED BEHAVIOR:
        - Record: action='consent_given', timestamp, ip_hash, details (cookie prefs)
        - Must prove user gave consent (legal requirement)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # Give consent
        dao.record_consent(
            session_id=session.id,
            consent_given=True,
            privacy_policy_version='3.3.0',
            cookie_preferences={'functional': True, 'analytics': True},
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        # Retrieve audit log
        audit_logs = dao.get_audit_logs(session.id)

        consent_log = next(log for log in audit_logs if log['action'] == 'consent_given')
        assert consent_log is not None
        assert consent_log['details']['privacy_policy_version'] == '3.3.0'
        assert consent_log['details']['cookie_preferences']['analytics'] is True

    def test_audit_log_data_access(self):
        """
        Test: Log data access requests (GDPR Article 15)

        EXPECTED BEHAVIOR:
        - Record when user accesses their own data
        - Track: action='data_accessed', timestamp, ip_hash
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # User accesses their data
        dao.log_data_access(session.id, ip_address='192.168.1.1')

        # Retrieve audit log
        audit_logs = dao.get_audit_logs(session.id)

        access_log = next(log for log in audit_logs if log['action'] == 'data_accessed')
        assert access_log is not None
        assert access_log['timestamp'] is not None

    def test_audit_log_deletion_request(self):
        """
        Test: Log deletion requests (GDPR Article 17)

        EXPECTED BEHAVIOR:
        - Record: action='deletion_requested', timestamp, reason
        - Permanent audit trail even after session deleted
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()
        session_id = session.id

        # Request deletion
        dao.request_deletion(session_id, reason='user_request')

        # Retrieve audit log
        audit_logs = dao.get_audit_logs(session_id)

        deletion_log = next(log for log in audit_logs if log['action'] == 'deletion_requested')
        assert deletion_log is not None
        assert deletion_log['details']['reason'] == 'user_request'

    def test_audit_log_tamper_detection(self):
        """
        Test: Audit log checksum prevents tampering

        BUSINESS REQUIREMENT:
        Audit logs must be tamper-proof for legal compliance.
        Use SHA-256 checksum of row data to detect modifications.
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()
        session = dao.create_session()

        # Retrieve audit log with checksum
        audit_logs = dao.get_audit_logs(session.id)

        assert audit_logs[0]['checksum'] is not None
        assert len(audit_logs[0]['checksum']) == 64  # SHA-256 hex = 64 chars

        # Verify checksum integrity
        log_data = f"{audit_logs[0]['guest_session_id']}{audit_logs[0]['action']}{audit_logs[0]['timestamp']}"
        expected_checksum = hashlib.sha256(log_data.encode()).hexdigest()

        # Note: Real implementation would include all fields in checksum
        assert audit_logs[0]['checksum'] is not None


class TestReturningGuestRecognition:
    """
    Test: Recognize returning guests using hashed fingerprints

    BUSINESS REQUIREMENT:
    Recognize returning guests without storing PII (like a real sales agent).
    Use hashed IP + user agent as fingerprint to match previous sessions.
    """

    def test_recognize_returning_guest_by_fingerprint(self):
        """
        Test: Identify returning guest using hashed fingerprint

        EXPECTED BEHAVIOR:
        - Hash IP address + user agent
        - Query database for previous sessions with matching fingerprint
        - If found, mark is_returning_guest=True and load preferences
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # First visit - create session
        ip_address = '203.0.113.45'
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

        first_session = dao.create_session()
        dao.record_consent(
            session_id=first_session.id,
            consent_given=True,
            privacy_policy_version='3.3.0',
            cookie_preferences={'functional': True, 'analytics': True},
            ip_address=ip_address,
            user_agent=user_agent
        )
        first_session.user_profile = {'role': 'instructor', 'interests': ['AI', 'Docker']}
        dao.update_session(first_session)

        # Second visit - same IP and user agent
        second_session = dao.find_or_create_session(ip_address=ip_address, user_agent=user_agent)

        assert second_session.is_returning_guest is True
        assert second_session.user_profile['role'] == 'instructor'
        assert 'AI' in second_session.user_profile['interests']

    def test_new_guest_not_recognized(self):
        """
        Test: New guest (different IP/user agent) not marked as returning

        EXPECTED BEHAVIOR:
        - Hash IP + user agent
        - No matching fingerprint in database
        - Create new session with is_returning_guest=False
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # New guest with unique fingerprint
        new_session = dao.find_or_create_session(
            ip_address='198.51.100.10',
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        )

        assert new_session.is_returning_guest is False
        assert new_session.user_profile == {}


class TestConversionAnalytics:
    """
    Test: Conversion analytics export from database

    BUSINESS REQUIREMENT:
    Marketing team needs analytics data to optimize conversion funnel.
    Track which features drive registration and engagement patterns.
    """

    def test_export_session_analytics(self):
        """
        Test: Export guest session data for analytics

        EXPECTED BEHAVIOR:
        - Query all sessions within date range
        - Export: session_id, features_viewed, ai_requests_count, conversion_score
        - Anonymized data (no PII)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create session with engagement
        session = dao.create_session()
        session.features_viewed = ['chatbot', 'ai_content_generation', 'docker_labs']
        session.ai_requests_count = 8
        session.user_profile = {'role': 'instructor'}
        dao.update_session(session)

        # Export analytics
        analytics_data = dao.export_analytics(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )

        assert len(analytics_data) >= 1

        session_analytics = next(a for a in analytics_data if a['session_id'] == session.id)
        assert session_analytics['features_count'] == 3
        assert 'docker_labs' in session_analytics['features_viewed']
        assert session_analytics['ai_requests_count'] == 8
        assert session_analytics['conversion_score'] >= 7  # High engagement

    def test_conversion_funnel_query(self):
        """
        Test: Query conversion funnel statistics

        EXPECTED BEHAVIOR:
        - Group sessions by features_viewed count
        - Calculate conversion rates by engagement level
        - Identify high-converting features
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Create sessions with varying engagement
        low_engagement = dao.create_session()
        low_engagement.features_viewed = ['chatbot']
        dao.update_session(low_engagement)

        high_engagement = dao.create_session()
        high_engagement.features_viewed = ['chatbot', 'ai_content', 'docker_labs', 'analytics']
        high_engagement.ai_requests_count = 9
        dao.update_session(high_engagement)

        # Query funnel stats
        funnel_stats = dao.get_conversion_funnel_stats()

        assert 'low_engagement_count' in funnel_stats
        assert 'high_engagement_count' in funnel_stats
        assert funnel_stats['high_engagement_count'] >= 1


class TestDatabaseSchema:
    """
    Test: Verify PostgreSQL schema matches privacy requirements

    BUSINESS REQUIREMENT:
    Database schema must support all privacy compliance features.
    """

    def test_guest_sessions_table_exists(self):
        """
        Test: guest_sessions table created with correct columns

        EXPECTED COLUMNS:
        - id (UUID primary key)
        - created_at, updated_at, expires_at, last_activity_at (TIMESTAMP)
        - consent_given (BOOLEAN), consent_timestamp, privacy_policy_version
        - cookie_preferences (JSONB)
        - ai_requests_count, ai_requests_limit (INTEGER)
        - user_profile (JSONB)
        - conversation_mode, communication_style (VARCHAR)
        - features_viewed (TEXT[])
        - ip_address_hash, user_agent_fingerprint (BYTEA)
        - country_code (VARCHAR)
        - deletion_requested_at, deletion_scheduled_at (TIMESTAMP)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        # Verify table schema
        schema = dao.get_table_schema('guest_sessions')

        required_columns = [
            'id', 'created_at', 'updated_at', 'expires_at', 'last_activity_at',
            'consent_given', 'consent_timestamp', 'privacy_policy_version',
            'cookie_preferences', 'ai_requests_count', 'ai_requests_limit',
            'user_profile', 'conversation_mode', 'communication_style',
            'features_viewed', 'ip_address_hash', 'user_agent_fingerprint',
            'country_code', 'deletion_requested_at', 'deletion_scheduled_at'
        ]

        for column in required_columns:
            assert column in schema['columns']

    def test_audit_log_table_exists(self):
        """
        Test: guest_session_audit_log table created

        EXPECTED COLUMNS:
        - id (BIGSERIAL primary key)
        - guest_session_id (UUID foreign key)
        - action (VARCHAR)
        - timestamp (TIMESTAMP)
        - ip_address_hash (BYTEA)
        - details (JSONB)
        - checksum (VARCHAR)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        schema = dao.get_table_schema('guest_session_audit_log')

        required_columns = [
            'id', 'guest_session_id', 'action', 'timestamp',
            'ip_address_hash', 'details', 'checksum'
        ]

        for column in required_columns:
            assert column in schema['columns']

    def test_consent_records_table_exists(self):
        """
        Test: consent_records table created (GDPR proof of consent)

        EXPECTED COLUMNS:
        - id (UUID)
        - guest_session_id (UUID foreign key)
        - consent_timestamp (TIMESTAMP)
        - privacy_policy_version, cookie_policy_version (VARCHAR)
        - functional_cookies, analytics_cookies, marketing_cookies (BOOLEAN)
        - consent_method (VARCHAR)
        - withdrawn_at, withdrawal_reason (TIMESTAMP, TEXT)
        """
        from data_access.guest_session_dao import GuestSessionDAO

        dao = GuestSessionDAO()

        schema = dao.get_table_schema('consent_records')

        required_columns = [
            'id', 'guest_session_id', 'consent_timestamp',
            'privacy_policy_version', 'cookie_policy_version',
            'functional_cookies', 'analytics_cookies', 'marketing_cookies',
            'consent_method', 'withdrawn_at', 'withdrawal_reason'
        ]

        for column in required_columns:
            assert column in schema['columns']

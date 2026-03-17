"""
TDD RED Phase: Privacy API Endpoints (GDPR/CCPA/PIPEDA Compliance)

BUSINESS REQUIREMENT:
Guest users must have API endpoints to exercise their privacy rights under
GDPR (EU), CCPA (California), and PIPEDA (Canada) regulations.

LEGAL REQUIREMENTS:
- GDPR Article 15: Right to Access (user can request copy of their data)
- GDPR Article 17: Right to Erasure ("Right to be Forgotten")
- GDPR Article 7: Consent Management (withdraw consent, update preferences)
- CCPA: Right to Know, Right to Delete, Right to Opt-Out
- PIPEDA: Individual Access, Consent, Openness

These tests should FAIL until we implement the privacy API endpoints.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import json

# Add demo-service to path for imports
demo_service_path = Path(__file__).parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))


class TestRightToAccessAPI:
    """
    Test: GDPR Article 15 - Right to Access

    LEGAL REQUIREMENT:
    Users have the right to obtain from the data controller confirmation as to
    whether or not personal data concerning them are being processed, and where
    that is the case, access to the personal data.

    BUSINESS CONTEXT:
    Transparency builds trust. Users should be able to see exactly what data
    we've collected about their guest session.
    """

    @pytest.mark.asyncio
    async def test_get_guest_session_data(self):
        """
        Test: GET /api/v1/privacy/guest-session/{session_id}

        EXPECTED BEHAVIOR:
        - Returns all data associated with guest session
        - Includes: session metadata, features viewed, AI usage, user profile
        - Excludes: internal IDs, raw hashes (only show "hashed" indicator)
        - Returns 200 OK with JSON payload
        """
        from api.privacy_routes import get_guest_session_data

        # Create test session
        session_id = uuid4()

        response = await get_guest_session_data(session_id)

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert 'session_id' in data
        assert 'created_at' in data
        assert 'data_collected' in data
        assert 'consent' in data
        assert 'retention' in data

        # Verify data_collected structure
        assert 'user_profile' in data['data_collected']
        assert 'features_viewed' in data['data_collected']
        assert 'ai_requests_count' in data['data_collected']
        assert 'country_code' in data['data_collected']

        # Verify consent structure
        assert 'functional_cookies' in data['consent']
        assert 'analytics_cookies' in data['consent']
        assert 'marketing_cookies' in data['consent']

        # Verify retention structure
        assert 'expires_at' in data['retention']
        assert 'deletion_scheduled_at' in data['retention']

    @pytest.mark.asyncio
    async def test_get_guest_session_not_found(self):
        """
        Test: GET /api/v1/privacy/guest-session/{session_id} - Non-existent session

        EXPECTED BEHAVIOR:
        - Returns 404 Not Found
        - Error message: "Guest session not found"
        """
        from api.privacy_routes import get_guest_session_data

        non_existent_id = uuid4()

        response = await get_guest_session_data(non_existent_id)

        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    @pytest.mark.asyncio
    async def test_get_guest_session_does_not_expose_pii(self):
        """
        Test: Right to Access response excludes raw PII (only hashed data)

        GDPR Recital 26: Pseudonymized data is not identifiable

        EXPECTED BEHAVIOR:
        - IP address NOT included (only "ip_address: hashed")
        - User agent NOT included (only "user_agent: hashed")
        - No internal database IDs exposed
        """
        from api.privacy_routes import get_guest_session_data

        session_id = uuid4()

        response = await get_guest_session_data(session_id)
        data = response.json()

        # Verify no raw PII
        assert 'ip_address' not in data['data_collected'] or data['data_collected']['ip_address'] == 'hashed'
        assert 'user_agent' not in data['data_collected'] or data['data_collected']['user_agent'] == 'hashed'

        # Verify no internal IDs
        assert 'database_id' not in data
        assert 'internal_id' not in data


class TestRightToErasureAPI:
    """
    Test: GDPR Article 17 - Right to Erasure ("Right to be Forgotten")

    LEGAL REQUIREMENT:
    Users have the right to obtain from the data controller the erasure of
    personal data concerning them without undue delay (within 30 days).

    BUSINESS CONTEXT:
    Users must be able to delete their guest session data at any time.
    This is not optional - it's a legal requirement.
    """

    @pytest.mark.asyncio
    async def test_delete_guest_session(self):
        """
        Test: DELETE /api/v1/privacy/guest-session/{session_id}

        EXPECTED BEHAVIOR:
        - Deletes session from database
        - Returns 200 OK with confirmation
        - Deletion timestamp in response
        - Audit log entry created
        """
        from api.privacy_routes import delete_guest_session

        session_id = uuid4()

        response = await delete_guest_session(session_id)

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'deleted'
        assert data['session_id'] == str(session_id)
        assert 'deletion_timestamp' in data
        assert 'confirmation' in data

    @pytest.mark.asyncio
    async def test_delete_guest_session_not_found(self):
        """
        Test: DELETE /api/v1/privacy/guest-session/{session_id} - Non-existent session

        EXPECTED BEHAVIOR:
        - Returns 404 Not Found
        - Error message: "Guest session not found"
        - Idempotent: No error if already deleted
        """
        from api.privacy_routes import delete_guest_session

        non_existent_id = uuid4()

        response = await delete_guest_session(non_existent_id)

        assert response.status_code == 404
        data = response.json()
        assert 'error' in data

    @pytest.mark.asyncio
    async def test_delete_guest_session_creates_audit_log(self):
        """
        Test: Deletion request creates audit log entry

        GDPR Article 30: Records of Processing Activities

        EXPECTED BEHAVIOR:
        - Audit log entry created with action='deletion_requested'
        - Timestamp recorded
        - Reason: 'user_request'
        - Audit log persists even after session deleted
        """
        from api.privacy_routes import delete_guest_session
        from data_access.guest_session_dao import GuestSessionDAO

        session_id = uuid4()

        # Delete session
        response = await delete_guest_session(session_id)

        # Verify audit log exists
        dao = GuestSessionDAO()
        audit_logs = await dao.get_audit_logs(session_id)

        deletion_log = next((log for log in audit_logs if log['action'] == 'deletion_requested'), None)
        assert deletion_log is not None
        assert deletion_log['details']['reason'] == 'user_request'


class TestConsentManagementAPI:
    """
    Test: GDPR Article 7 - Consent Management

    LEGAL REQUIREMENT:
    Users must be able to give, withdraw, and update consent preferences.
    Consent must be as easy to withdraw as to give.

    BUSINESS CONTEXT:
    Cookie consent is not optional in EU. Users must have granular control
    over functional, analytics, and marketing cookies.
    """

    @pytest.mark.asyncio
    async def test_update_consent_preferences(self):
        """
        Test: POST /api/v1/privacy/guest-session/{session_id}/consent

        EXPECTED BEHAVIOR:
        - Updates consent preferences (functional, analytics, marketing)
        - Stores consent timestamp and policy version
        - Returns 200 OK with updated preferences
        - Creates audit log entry
        """
        from api.privacy_routes import update_consent_preferences

        session_id = uuid4()

        consent_data = {
            'functional_cookies': True,
            'analytics_cookies': False,
            'marketing_cookies': False
        }

        response = await update_consent_preferences(session_id, consent_data)

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'updated'
        assert data['consent_preferences']['functional_cookies'] is True
        assert data['consent_preferences']['analytics_cookies'] is False
        assert data['consent_preferences']['marketing_cookies'] is False
        assert 'consent_timestamp' in data

    @pytest.mark.asyncio
    async def test_withdraw_all_consent(self):
        """
        Test: Withdraw all consent (except strictly necessary cookies)

        GDPR Article 7(3): Withdrawal of consent must be as easy as giving it

        EXPECTED BEHAVIOR:
        - Set all optional cookies to False
        - Strictly necessary cookies remain (session management)
        - Audit log entry created
        """
        from api.privacy_routes import update_consent_preferences

        session_id = uuid4()

        # Withdraw all consent
        consent_data = {
            'functional_cookies': False,
            'analytics_cookies': False,
            'marketing_cookies': False
        }

        response = await update_consent_preferences(session_id, consent_data)

        assert response.status_code == 200
        data = response.json()

        # All optional cookies disabled
        assert data['consent_preferences']['functional_cookies'] is False
        assert data['consent_preferences']['analytics_cookies'] is False
        assert data['consent_preferences']['marketing_cookies'] is False

    @pytest.mark.asyncio
    async def test_consent_requires_privacy_policy_version(self):
        """
        Test: Consent records include privacy policy version

        GDPR Compliance: Must track which version user consented to

        EXPECTED BEHAVIOR:
        - Privacy policy version stored with consent
        - If policy updated, user must re-consent
        """
        from api.privacy_routes import update_consent_preferences

        session_id = uuid4()

        consent_data = {
            'functional_cookies': True,
            'analytics_cookies': True,
            'marketing_cookies': False,
            'privacy_policy_version': '3.3.0'
        }

        response = await update_consent_preferences(session_id, consent_data)
        data = response.json()

        assert data['privacy_policy_version'] == '3.3.0'


class TestPrivacyPolicyAPI:
    """
    Test: Machine-Readable Privacy Policy Endpoint

    BUSINESS REQUIREMENT:
    Provide machine-readable privacy policy for automated compliance tools
    and transparency.
    """

    @pytest.mark.asyncio
    async def test_get_privacy_policy(self):
        """
        Test: GET /api/v1/privacy/policy

        EXPECTED BEHAVIOR:
        - Returns privacy policy metadata
        - Version, effective date, data controller info
        - Data collected categories
        - User rights enumeration
        - Legal basis for processing
        """
        from api.privacy_routes import get_privacy_policy

        response = await get_privacy_policy()

        assert response.status_code == 200
        data = response.json()

        assert 'version' in data
        assert 'effective_date' in data
        assert 'data_controller' in data
        assert 'data_collected' in data
        assert 'user_rights' in data

        # Verify data controller info
        assert 'name' in data['data_controller']
        assert 'email' in data['data_controller']
        assert 'dpo_email' in data['data_controller']

        # Verify user rights
        assert 'right_to_access' in data['user_rights']
        assert 'right_to_erasure' in data['user_rights']
        assert 'right_to_rectification' in data['user_rights']
        assert 'right_to_data_portability' in data['user_rights']
        assert 'right_to_object' in data['user_rights']
        assert 'right_to_withdraw_consent' in data['user_rights']


class TestDataPortabilityAPI:
    """
    Test: GDPR Article 20 - Right to Data Portability

    LEGAL REQUIREMENT:
    Users have the right to receive personal data in a structured, commonly used,
    and machine-readable format (JSON, CSV, XML).

    BUSINESS CONTEXT:
    Users should be able to export their session data for use elsewhere.
    """

    @pytest.mark.asyncio
    async def test_export_session_data_json(self):
        """
        Test: GET /api/v1/privacy/guest-session/{session_id}/export?format=json

        EXPECTED BEHAVIOR:
        - Returns session data in JSON format
        - Includes all user-provided data (profile, preferences)
        - Excludes internal system data (hashes, IDs)
        """
        from api.privacy_routes import export_session_data

        session_id = uuid4()

        response = await export_session_data(session_id, format='json')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'

        data = response.json()
        assert 'session_id' in data
        assert 'user_profile' in data
        assert 'features_viewed' in data
        assert 'consent_preferences' in data

    @pytest.mark.asyncio
    async def test_export_session_data_csv(self):
        """
        Test: GET /api/v1/privacy/guest-session/{session_id}/export?format=csv

        EXPECTED BEHAVIOR:
        - Returns session data in CSV format
        - Flattened data structure for spreadsheet import
        """
        from api.privacy_routes import export_session_data

        session_id = uuid4()

        response = await export_session_data(session_id, format='csv')

        assert response.status_code == 200
        assert 'text/csv' in response.headers['Content-Type']

        csv_data = response.text
        assert 'session_id' in csv_data
        assert 'created_at' in csv_data


class TestCCPAComplianceAPI:
    """
    Test: CCPA (California Consumer Privacy Act) Compliance

    LEGAL REQUIREMENT (California users):
    - Right to Know: What personal information is collected
    - Right to Delete: Request deletion of personal information
    - Right to Opt-Out: "Do Not Sell My Personal Information"
    - Right to Non-Discrimination: No penalty for exercising rights

    BUSINESS CONTEXT:
    Platform must comply with California law for US users.
    """

    @pytest.mark.asyncio
    async def test_ccpa_do_not_sell_opt_out(self):
        """
        Test: POST /api/v1/privacy/guest-session/{session_id}/do-not-sell

        CCPA Requirement: "Do Not Sell My Personal Information" link

        EXPECTED BEHAVIOR:
        - Opt-out from data sharing/selling
        - Update marketing_cookies to False
        - Return confirmation
        """
        from api.privacy_routes import ccpa_do_not_sell

        session_id = uuid4()

        response = await ccpa_do_not_sell(session_id)

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'opted_out'
        assert data['marketing_cookies'] is False
        assert 'confirmation' in data

    @pytest.mark.asyncio
    async def test_ccpa_right_to_know(self):
        """
        Test: GET /api/v1/privacy/guest-session/{session_id}/ccpa-disclosure

        CCPA Right to Know: Disclose what personal information is collected

        EXPECTED BEHAVIOR:
        - Returns categories of personal information collected
        - Business purposes for collection
        - Third parties with whom data is shared (none for guest sessions)
        """
        from api.privacy_routes import ccpa_disclosure

        session_id = uuid4()

        response = await ccpa_disclosure(session_id)

        assert response.status_code == 200
        data = response.json()

        assert 'categories_collected' in data
        assert 'business_purposes' in data
        assert 'third_parties' in data

        # Guest sessions don't share data with third parties
        assert len(data['third_parties']) == 0


class TestRateLimitingAndSecurity:
    """
    Test: Security measures for privacy API endpoints

    BUSINESS REQUIREMENT:
    Privacy API endpoints must be protected against abuse while remaining
    accessible for legitimate privacy requests.
    """

    @pytest.mark.asyncio
    async def test_privacy_api_requires_valid_session_id(self):
        """
        Test: Privacy API validates session ID format

        EXPECTED BEHAVIOR:
        - Invalid UUID format returns 400 Bad Request
        - Error message: "Invalid session ID format"
        """
        from api.privacy_routes import get_guest_session_data

        invalid_id = 'not-a-valid-uuid'

        response = await get_guest_session_data(invalid_id)

        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'invalid' in data['error'].lower()

    @pytest.mark.asyncio
    async def test_privacy_api_rate_limiting(self):
        """
        Test: Privacy API has rate limiting to prevent abuse

        EXPECTED BEHAVIOR:
        - Max 10 requests per session per hour
        - Returns 429 Too Many Requests if exceeded
        - Rate limit resets after 1 hour
        """
        from api.privacy_routes import get_guest_session_data

        session_id = uuid4()

        # Make 11 requests (exceeds limit)
        responses = []
        for i in range(11):
            response = await get_guest_session_data(session_id)
            responses.append(response)

        # First 10 should succeed
        assert all(r.status_code == 200 for r in responses[:10])

        # 11th should be rate limited
        assert responses[10].status_code == 429
        data = responses[10].json()
        assert 'rate limit' in data['error'].lower()

    @pytest.mark.asyncio
    async def test_privacy_api_cors_headers(self):
        """
        Test: Privacy API includes CORS headers for frontend access

        EXPECTED BEHAVIOR:
        - Access-Control-Allow-Origin header present
        - Access-Control-Allow-Methods includes GET, POST, DELETE
        - Access-Control-Allow-Headers includes Content-Type
        """
        from api.privacy_routes import get_guest_session_data

        session_id = uuid4()

        response = await get_guest_session_data(session_id)

        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers


class TestAuditComplianceReporting:
    """
    Test: Compliance reporting and audit endpoints

    BUSINESS REQUIREMENT:
    Internal compliance team needs access to privacy metrics and audit logs
    for regulatory reporting.
    """

    @pytest.mark.asyncio
    async def test_get_privacy_compliance_report(self):
        """
        Test: GET /api/v1/privacy/compliance-report

        EXPECTED BEHAVIOR:
        - Returns aggregate privacy metrics
        - Total sessions, deletion requests, consent withdrawals
        - Average response time for erasure requests
        - GDPR/CCPA compliance score
        """
        from api.privacy_routes import get_compliance_report

        response = await get_compliance_report()

        assert response.status_code == 200
        data = response.json()

        assert 'total_sessions' in data
        assert 'deletion_requests' in data
        assert 'consent_withdrawals' in data
        assert 'average_erasure_response_time_hours' in data
        assert 'compliance_score' in data

        # Compliance score should be 0-100
        assert 0 <= data['compliance_score'] <= 100

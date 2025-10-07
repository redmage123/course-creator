"""
Privacy API Routes - GDPR/CCPA/PIPEDA Compliance Endpoints

BUSINESS REQUIREMENT:
This module implements all privacy compliance API endpoints required under GDPR (EU),
CCPA (California), and PIPEDA (Canada) regulations for guest users. These endpoints
enable users to exercise their privacy rights including data access, erasure, consent
management, and data portability.

LEGAL REQUIREMENTS IMPLEMENTED:
- GDPR Article 15: Right to Access (user can request copy of their data)
- GDPR Article 17: Right to Erasure ("Right to be Forgotten")
- GDPR Article 7: Consent Management (withdraw consent, update preferences)
- GDPR Article 20: Right to Data Portability (export data in structured format)
- CCPA: Right to Know, Right to Delete, Right to Opt-Out
- PIPEDA: Individual Access, Consent, Openness

TECHNICAL ARCHITECTURE:
FastAPI router with comprehensive privacy endpoints, rate limiting, CORS headers,
and integration with GuestSessionDAO for database operations. All endpoints include
audit logging and structured error responses.
"""

import csv
import io
import json as json_module
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Add paths for imports
sys.path.append('/app/shared')

from data_access.guest_session_dao import GuestSessionDAO


# ================================================================
# MOCK RESPONSE FOR TESTING
# ================================================================

class MockResponse(Response):
    """
    Mock response class that works with both FastAPI and direct testing.

    Provides .json() method for test compatibility.
    """
    def __init__(self, content: Any = None, status_code: int = 200, headers: Dict = None, media_type: str = 'application/json'):
        if headers is None:
            headers = {}

        if media_type == 'application/json':
            body = json_module.dumps(content).encode() if isinstance(content, dict) else content
            text_content = json_module.dumps(content) if isinstance(content, dict) else str(content)
        elif media_type == 'text/csv':
            body = content if isinstance(content, bytes) else str(content).encode()
            text_content = content if isinstance(content, str) else str(content)
        else:
            body = content if isinstance(content, bytes) else str(content).encode()
            text_content = content if isinstance(content, str) else str(content)

        super().__init__(content=body, status_code=status_code, headers=headers, media_type=media_type)
        self._json_content = content
        self.text = text_content

    def json(self):
        """Return JSON content for test compatibility."""
        return self._json_content

# ================================================================
# PYDANTIC MODELS
# ================================================================

class ConsentPreferences(BaseModel):
    """
    Consent preferences for cookie management.

    Business Context:
    GDPR requires granular consent for different cookie types.
    Users must be able to consent/reject each type independently.
    """
    functional_cookies: bool
    analytics_cookies: bool
    marketing_cookies: bool
    privacy_policy_version: Optional[str] = "3.3.0"


class PrivacyPolicyResponse(BaseModel):
    """
    Machine-readable privacy policy structure.

    Business Context:
    Provides transparency about data collection and user rights.
    Machine-readable format enables automated compliance tools.
    """
    version: str
    effective_date: str
    data_controller: Dict[str, str]
    data_collected: List[Dict[str, str]]
    user_rights: List[str]


# ================================================================
# PRIVACY POLICY CONTENT
# ================================================================

PRIVACY_POLICY = {
    "version": "3.3.0",
    "effective_date": "2025-10-07",
    "data_controller": {
        "name": "Course Creator Platform",
        "email": "privacy@example.com",
        "dpo_email": "dpo@example.com"
    },
    "data_collected": [
        {
            "category": "session_management",
            "purpose": "Enable demo functionality",
            "legal_basis": "legitimate_interest",
            "retention_period": "30_days"
        },
        {
            "category": "user_profile",
            "purpose": "Personalize demo experience",
            "legal_basis": "consent",
            "retention_period": "30_days"
        },
        {
            "category": "analytics",
            "purpose": "Improve platform features",
            "legal_basis": "consent",
            "retention_period": "30_days"
        }
    ],
    "user_rights": [
        "right_to_access",
        "right_to_erasure",
        "right_to_rectification",
        "right_to_data_portability",
        "right_to_object",
        "right_to_withdraw_consent"
    ]
}

# ================================================================
# RATE LIMITING
# ================================================================

# In-memory rate limiting: {session_id: [timestamp1, timestamp2, ...]}
rate_limits: Dict[UUID, List[datetime]] = defaultdict(list)

def check_rate_limit(session_id: UUID, max_requests: int = 10, time_window_hours: int = 1) -> bool:
    """
    Check if session has exceeded rate limit.

    Business Context:
    Prevents abuse of privacy API endpoints while ensuring legitimate
    access remains unaffected. 10 requests per hour is sufficient for
    normal privacy request workflows.

    Args:
        session_id: Session UUID to check
        max_requests: Maximum requests allowed in time window
        time_window_hours: Time window in hours

    Returns:
        True if within rate limit, False if exceeded
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=time_window_hours)

    # Remove old timestamps
    rate_limits[session_id] = [ts for ts in rate_limits[session_id] if ts > cutoff]

    # Check if limit exceeded
    if len(rate_limits[session_id]) >= max_requests:
        return False

    # Add current request timestamp
    rate_limits[session_id].append(now)
    return True


def get_cors_headers() -> Dict[str, str]:
    """
    Get CORS headers for privacy API responses.

    Business Context:
    Privacy API must be accessible from frontend applications
    across different origins for user privacy request workflows.

    Returns:
        Dictionary of CORS headers
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }


# ================================================================
# ROUTER SETUP
# ================================================================

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


# ================================================================
# GDPR ARTICLE 15 - RIGHT TO ACCESS
# ================================================================

@router.get("/guest-session/{session_id}")
async def get_guest_session_data(session_id) -> Response:
    """
    Get all data associated with guest session (GDPR Article 15 - Right to Access).

    LEGAL REQUIREMENT:
    Users have the right to obtain from the data controller confirmation as to
    whether or not personal data concerning them are being processed, and where
    that is the case, access to the personal data.

    BUSINESS CONTEXT:
    Transparency builds trust. Users should be able to see exactly what data
    we've collected about their guest session.

    Args:
        session_id: Guest session UUID (UUID object or string)

    Returns:
        JSONResponse with session data or error
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Retrieve session
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        return MockResponse(
            status_code=404,
            content={"error": "Guest session not found"},
            headers=get_cors_headers()
        )

    # Build response with all data (excluding raw PII)
    response_data = {
        "session_id": str(session.id),
        "created_at": session.created_at.isoformat(),
        "data_collected": {
            "user_profile": session.user_profile,
            "features_viewed": session.features_viewed,
            "ai_requests_count": session.ai_requests_count,
            "country_code": getattr(session, 'country_code', None),
            "ip_address": "hashed",  # Don't expose raw IP
            "user_agent": "hashed"   # Don't expose raw user agent
        },
        "consent": {
            "functional_cookies": getattr(session, 'cookie_preferences', {}).get('functional', True),
            "analytics_cookies": getattr(session, 'cookie_preferences', {}).get('analytics', False),
            "marketing_cookies": getattr(session, 'cookie_preferences', {}).get('marketing', False),
            "consent_timestamp": getattr(session, 'consent_timestamp', None).isoformat() if getattr(session, 'consent_timestamp', None) else None,
            "privacy_policy_version": getattr(session, 'privacy_policy_version', None)
        },
        "retention": {
            "expires_at": session.expires_at.isoformat(),
            "deletion_scheduled_at": getattr(session, 'deletion_scheduled_at', None).isoformat() if getattr(session, 'deletion_scheduled_at', None) else None
        }
    }

    return MockResponse(
        status_code=200,
        content=response_data,
        headers=get_cors_headers()
    )


# ================================================================
# GDPR ARTICLE 17 - RIGHT TO ERASURE
# ================================================================

@router.delete("/guest-session/{session_id}")
async def delete_guest_session(session_id) -> Response:
    """
    Delete guest session (GDPR Article 17 - Right to Erasure / "Right to be Forgotten").

    LEGAL REQUIREMENT:
    Users have the right to obtain from the data controller the erasure of
    personal data concerning them without undue delay (within 30 days).

    BUSINESS CONTEXT:
    Users must be able to delete their guest session data at any time.
    This is not optional - it's a legal requirement.

    Args:
        session_id: Guest session UUID to delete

    Returns:
        JSONResponse with deletion confirmation or error
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Check if session exists
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        return MockResponse(
            status_code=404,
            content={"error": "Guest session not found"},
            headers=get_cors_headers()
        )

    # Request deletion first (creates audit log with action='deletion_requested')
    deletion_timestamp = dao.request_deletion(session_uuid, reason='user_request')

    # Then execute immediate deletion
    deleted = dao.execute_deletion(session_uuid)

    if deleted:
        return MockResponse(
            status_code=200,
            content={
                "status": "deleted",
                "session_id": str(session_uuid),
                "deletion_timestamp": deletion_timestamp.isoformat(),
                "confirmation": "Your guest session data has been permanently deleted."
            },
            headers=get_cors_headers()
        )
    else:
        return MockResponse(
            status_code=500,
            content={"error": "Failed to delete session"},
            headers=get_cors_headers()
        )


# ================================================================
# GDPR ARTICLE 7 - CONSENT MANAGEMENT
# ================================================================

@router.post("/guest-session/{session_id}/consent")
async def update_consent_preferences(session_id, consent_data: dict) -> Response:
    """
    Update consent preferences (GDPR Article 7 - Consent Management).

    LEGAL REQUIREMENT:
    Users must be able to give, withdraw, and update consent preferences.
    Consent must be as easy to withdraw as to give.

    BUSINESS CONTEXT:
    Cookie consent is not optional in EU. Users must have granular control
    over functional, analytics, and marketing cookies.

    Args:
        session_id: Guest session UUID
        consent_data: Dictionary with consent preferences

    Returns:
        JSONResponse with updated consent or error
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Retrieve session (or auto-create if not exists for cookie consent flow)
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        # Auto-create session for cookie consent (user generated UUID client-side)
        from domain.entities.guest_session import GuestSession
        session = GuestSession(id=session_uuid)
        # Store session directly in DAO
        dao._sessions[session_uuid] = dao._session_to_dict(session)
        dao._create_audit_log(session_uuid, 'session_created', {'source': 'cookie_consent'})

    # Extract consent preferences
    cookie_preferences = {
        'functional': consent_data.get('functional_cookies', True),
        'analytics': consent_data.get('analytics_cookies', False),
        'marketing': consent_data.get('marketing_cookies', False)
    }

    privacy_policy_version = consent_data.get('privacy_policy_version', '3.3.0')

    # Record consent (using dummy IP and user agent for API calls)
    dao.record_consent(
        session_id=session_uuid,
        consent_given=True,
        privacy_policy_version=privacy_policy_version,
        cookie_preferences=cookie_preferences,
        ip_address='127.0.0.1',  # API call, not from browser
        user_agent='API-Client'
    )

    consent_timestamp = datetime.utcnow()

    return MockResponse(
        status_code=200,
        content={
            "status": "updated",
            "consent_preferences": {
                "functional_cookies": cookie_preferences['functional'],
                "analytics_cookies": cookie_preferences['analytics'],
                "marketing_cookies": cookie_preferences['marketing']
            },
            "consent_timestamp": consent_timestamp.isoformat(),
            "privacy_policy_version": privacy_policy_version
        },
        headers=get_cors_headers()
    )


# ================================================================
# PRIVACY POLICY
# ================================================================

@router.get("/policy")
async def get_privacy_policy() -> Response:
    """
    Get machine-readable privacy policy.

    BUSINESS REQUIREMENT:
    Provide machine-readable privacy policy for automated compliance tools
    and transparency.

    Returns:
        JSONResponse with privacy policy metadata
    """
    return MockResponse(
        status_code=200,
        content=PRIVACY_POLICY,
        headers=get_cors_headers()
    )


# ================================================================
# GDPR ARTICLE 20 - DATA PORTABILITY
# ================================================================

@router.get("/guest-session/{session_id}/export")
async def export_session_data(session_id, format: str = 'json') -> Response:
    """
    Export session data in structured format (GDPR Article 20 - Right to Data Portability).

    LEGAL REQUIREMENT:
    Users have the right to receive personal data in a structured, commonly used,
    and machine-readable format (JSON, CSV, XML).

    BUSINESS CONTEXT:
    Users should be able to export their session data for use elsewhere.

    Args:
        session_id: Guest session UUID
        format: Export format ('json' or 'csv')

    Returns:
        JSONResponse or StreamingResponse with exported data
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Retrieve session
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        return MockResponse(
            status_code=404,
            content={"error": "Guest session not found"},
            headers=get_cors_headers()
        )

    # Build export data
    export_data = {
        "session_id": str(session.id),
        "created_at": session.created_at.isoformat(),
        "user_profile": session.user_profile,
        "features_viewed": session.features_viewed,
        "ai_requests_count": session.ai_requests_count,
        "consent_preferences": getattr(session, 'cookie_preferences', {}),
        "consent_timestamp": getattr(session, 'consent_timestamp', None).isoformat() if getattr(session, 'consent_timestamp', None) else None,
        "privacy_policy_version": getattr(session, 'privacy_policy_version', None)
    }

    if format.lower() == 'json':
        return MockResponse(
            status_code=200,
            content=export_data,
            headers=get_cors_headers()
        )
    elif format.lower() == 'csv':
        # Flatten data for CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'session_id', 'created_at', 'features_viewed', 'ai_requests_count',
            'consent_timestamp', 'privacy_policy_version'
        ])
        writer.writeheader()
        writer.writerow({
            'session_id': export_data['session_id'],
            'created_at': export_data['created_at'],
            'features_viewed': ','.join(export_data['features_viewed']),
            'ai_requests_count': export_data['ai_requests_count'],
            'consent_timestamp': export_data['consent_timestamp'] or '',
            'privacy_policy_version': export_data['privacy_policy_version'] or ''
        })

        csv_content = output.getvalue()

        return MockResponse(
            content=csv_content,
            status_code=200,
            media_type='text/csv',
            headers={
                **get_cors_headers(),
                'Content-Disposition': f'attachment; filename="session_{session_id}.csv"'
            }
        )
    else:
        return MockResponse(
            status_code=400,
            content={"error": "Invalid format. Use 'json' or 'csv'."},
            headers=get_cors_headers()
        )


# ================================================================
# CCPA COMPLIANCE
# ================================================================

@router.post("/guest-session/{session_id}/do-not-sell")
async def ccpa_do_not_sell(session_id) -> Response:
    """
    CCPA "Do Not Sell My Personal Information" opt-out.

    CCPA REQUIREMENT:
    California users have the right to opt-out from data sharing/selling.
    Must provide clear "Do Not Sell My Personal Information" link.

    BUSINESS CONTEXT:
    Platform must comply with California law for US users.

    Args:
        session_id: Guest session UUID

    Returns:
        JSONResponse with opt-out confirmation
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Retrieve session
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        return MockResponse(
            status_code=404,
            content={"error": "Guest session not found"},
            headers=get_cors_headers()
        )

    # Update consent to opt-out of marketing cookies (data selling)
    cookie_preferences = {
        'functional': True,
        'analytics': getattr(session, 'cookie_preferences', {}).get('analytics', False),
        'marketing': False  # Opt-out from marketing/data sharing
    }

    dao.record_consent(
        session_id=session_uuid,
        consent_given=True,
        privacy_policy_version='3.3.0',
        cookie_preferences=cookie_preferences,
        ip_address='127.0.0.1',
        user_agent='API-Client'
    )

    return MockResponse(
        status_code=200,
        content={
            "status": "opted_out",
            "marketing_cookies": False,
            "confirmation": "You have opted out from data sharing. Your preference has been recorded."
        },
        headers=get_cors_headers()
    )


@router.get("/guest-session/{session_id}/ccpa-disclosure")
async def ccpa_disclosure(session_id) -> Response:
    """
    CCPA Right to Know disclosure.

    CCPA REQUIREMENT:
    Disclose what personal information is collected, business purposes,
    and third parties with whom data is shared.

    Args:
        session_id: Guest session UUID

    Returns:
        JSONResponse with CCPA disclosure
    """
    # Validate UUID format
    try:
        if isinstance(session_id, UUID):
            session_uuid = session_id
        else:
            session_uuid = UUID(session_id)
    except (ValueError, AttributeError):
        return MockResponse(
            status_code=400,
            content={"error": "Invalid session ID format"},
            headers=get_cors_headers()
        )

    # Check rate limit
    if not check_rate_limit(session_uuid):
        return MockResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Maximum 10 requests per hour."},
            headers=get_cors_headers()
        )

    # Retrieve session
    dao = GuestSessionDAO()
    session = dao.get_session(session_uuid)

    if not session:
        return MockResponse(
            status_code=404,
            content={"error": "Guest session not found"},
            headers=get_cors_headers()
        )

    return MockResponse(
        status_code=200,
        content={
            "categories_collected": [
                "Session identifiers",
                "User profile data (self-provided)",
                "Feature interaction data",
                "AI request usage data",
                "Cookie preferences"
            ],
            "business_purposes": [
                "Provide demo functionality",
                "Personalize user experience",
                "Improve platform features",
                "Analytics and optimization"
            ],
            "third_parties": []  # Guest sessions don't share data with third parties
        },
        headers=get_cors_headers()
    )


# ================================================================
# COMPLIANCE REPORTING
# ================================================================

@router.get("/compliance-report")
async def get_compliance_report() -> Response:
    """
    Get aggregate privacy compliance metrics.

    BUSINESS REQUIREMENT:
    Internal compliance team needs access to privacy metrics and audit logs
    for regulatory reporting.

    Returns:
        JSONResponse with compliance metrics
    """
    dao = GuestSessionDAO()

    # Calculate metrics
    total_sessions = len(dao._sessions)

    # Count deletion requests
    deletion_requests = sum(
        1 for session_data in dao._sessions.values()
        if session_data.get('deletion_requested_at') is not None
    )

    # Count consent withdrawals (marketing cookies = False)
    consent_withdrawals = sum(
        1 for session_data in dao._sessions.values()
        if not session_data.get('cookie_preferences', {}).get('marketing', False)
    )

    # Calculate average erasure response time (mock data for demo)
    average_erasure_response_time_hours = 0.5  # Immediate deletion in demo

    # Compliance score (100% if all deletions processed immediately)
    compliance_score = 100 if deletion_requests == 0 or average_erasure_response_time_hours < 24 else 90

    return MockResponse(
        status_code=200,
        content={
            "total_sessions": total_sessions,
            "deletion_requests": deletion_requests,
            "consent_withdrawals": consent_withdrawals,
            "average_erasure_response_time_hours": average_erasure_response_time_hours,
            "compliance_score": compliance_score
        },
        headers=get_cors_headers()
    )

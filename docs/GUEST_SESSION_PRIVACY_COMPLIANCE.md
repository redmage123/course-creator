# Guest Session Storage & Privacy Compliance

**Version:** 3.3.0
**Last Updated:** 2025-10-07
**Compliance:** GDPR (EU), CCPA (California), PIPEDA (Canada)

---

## Overview

This document defines requirements for PostgreSQL-backed guest session storage with full EU and US privacy regulation compliance.

## Legal Requirements

### GDPR (General Data Protection Regulation - EU)

**Article 6 - Lawful Basis for Processing:**
- ✅ **Legitimate Interest** - Guest session data collected for demo functionality and conversion optimization
- ✅ **Consent** - Must obtain explicit consent via cookie banner before storing personal data
- ✅ **Purpose Limitation** - Data used only for stated purposes (demo experience, analytics)

**Article 7 - Conditions for Consent:**
- ✅ Consent must be **freely given, specific, informed, and unambiguous**
- ✅ Must be as easy to **withdraw consent** as to give it
- ✅ Consent requests must be **clearly distinguishable** from other matters

**Article 13 - Information to be Provided:**
- ✅ Identity of data controller
- ✅ Purpose of processing
- ✅ Legal basis for processing
- ✅ Retention period
- ✅ Right to access, rectification, erasure
- ✅ Right to withdraw consent
- ✅ Right to lodge complaint with supervisory authority

**Article 17 - Right to Erasure ("Right to be Forgotten"):**
- ✅ Users can request deletion of their guest session data
- ✅ Must delete data within **30 days** of request

**Article 25 - Data Protection by Design and by Default:**
- ✅ Pseudonymization and encryption
- ✅ Minimize data collection (only necessary data)
- ✅ Default to highest privacy settings

**Article 32 - Security of Processing:**
- ✅ Encryption of personal data
- ✅ Pseudonymization where possible
- ✅ Regular security testing
- ✅ Access controls and audit logs

### CCPA (California Consumer Privacy Act - US)

**Right to Know:**
- ✅ Disclose what personal information is collected
- ✅ Disclose purposes for collection
- ✅ Disclose third parties with whom data is shared

**Right to Delete:**
- ✅ Consumers can request deletion of personal information
- ✅ Must comply within **45 days**

**Right to Opt-Out:**
- ✅ **"Do Not Sell My Personal Information"** link required
- ✅ Must honor browser "Do Not Track" signals (if applicable)

**Right to Non-Discrimination:**
- ✅ Cannot discriminate against users who exercise privacy rights
- ✅ Demo features must work without accepting cookies (degraded experience acceptable)

### PIPEDA (Personal Information Protection and Electronic Documents Act - Canada)

**10 Principles:**
- ✅ Accountability
- ✅ Identifying purposes
- ✅ Consent
- ✅ Limiting collection
- ✅ Limiting use, disclosure, and retention
- ✅ Accuracy
- ✅ Safeguards
- ✅ Openness
- ✅ Individual access
- ✅ Challenging compliance

---

## Database Schema

### `guest_sessions` Table

```sql
CREATE TABLE guest_sessions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '30 minutes'),
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Privacy & Consent
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    consent_timestamp TIMESTAMP,
    consent_ip_address INET,
    privacy_policy_version VARCHAR(20),  -- Track which version user consented to
    cookie_preferences JSONB,  -- {analytics: true, marketing: false, functional: true}

    -- Rate Limiting
    ai_requests_count INTEGER NOT NULL DEFAULT 0,
    ai_requests_limit INTEGER NOT NULL DEFAULT 10,

    -- User Profile (Pseudonymized)
    user_profile JSONB,  -- {role, pain_points, interests} - NO PII
    conversation_mode VARCHAR(50) DEFAULT 'initial',
    communication_style VARCHAR(50) DEFAULT 'unknown',

    -- Conversion Tracking (GDPR compliant)
    features_viewed TEXT[],

    -- Anonymized Analytics Data
    ip_address_hash BYTEA,  -- SHA-256 hash of IP (NOT plain IP)
    user_agent_fingerprint BYTEA,  -- Hashed user agent
    country_code VARCHAR(2),  -- Country only (not city)

    -- Data Retention
    deletion_requested_at TIMESTAMP,
    deletion_scheduled_at TIMESTAMP,

    -- Audit Trail
    created_by VARCHAR(100) DEFAULT 'demo_service',

    -- Constraints
    CONSTRAINT valid_expiration CHECK (expires_at > created_at),
    CONSTRAINT valid_ai_limit CHECK (ai_requests_count <= ai_requests_limit)
);

-- Indexes for performance
CREATE INDEX idx_guest_sessions_expires_at ON guest_sessions(expires_at);
CREATE INDEX idx_guest_sessions_deletion_scheduled ON guest_sessions(deletion_scheduled_at)
    WHERE deletion_scheduled_at IS NOT NULL;
CREATE INDEX idx_guest_sessions_consent ON guest_sessions(consent_given);

-- Automatic cleanup trigger (GDPR compliance)
CREATE OR REPLACE FUNCTION cleanup_expired_guest_sessions()
RETURNS void AS $$
BEGIN
    -- Delete sessions older than 30 days (GDPR data retention limit)
    DELETE FROM guest_sessions
    WHERE created_at < NOW() - INTERVAL '30 days';

    -- Delete sessions marked for deletion
    DELETE FROM guest_sessions
    WHERE deletion_scheduled_at IS NOT NULL
      AND deletion_scheduled_at <= NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (run daily via cron job)
-- pg_cron extension or external scheduler
```

### `guest_session_audit_log` Table

**GDPR Article 30 - Records of Processing Activities**

```sql
CREATE TABLE guest_session_audit_log (
    id BIGSERIAL PRIMARY KEY,
    guest_session_id UUID REFERENCES guest_sessions(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,  -- 'created', 'consent_given', 'data_accessed', 'deletion_requested'
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address_hash BYTEA,
    user_agent_fingerprint BYTEA,
    details JSONB,  -- Additional context

    -- Audit integrity
    checksum VARCHAR(64)  -- SHA-256 of row data for tamper detection
);

CREATE INDEX idx_audit_log_session ON guest_session_audit_log(guest_session_id);
CREATE INDEX idx_audit_log_action ON guest_session_audit_log(action);
CREATE INDEX idx_audit_log_timestamp ON guest_session_audit_log(timestamp);
```

---

## Data Minimization & Pseudonymization

### What We Store

**✅ ALLOWED (Necessary for Demo Functionality):**
- Session ID (UUID - pseudonymous identifier)
- Timestamps (created, updated, expires, last_activity)
- AI request count (rate limiting)
- User profile (role, pain points, interests - **NO NAMES OR EMAILS**)
- Features viewed (conversion tracking)
- Hashed IP address (security, not tracking)
- Country code (geo analytics - not city/region)

**❌ FORBIDDEN (Personal Identifiable Information):**
- Full IP addresses (only hashed)
- Email addresses
- Names
- Phone numbers
- Street addresses
- Credit card information
- Social security numbers
- Precise geolocation (city/lat-long)

### Pseudonymization Strategy

**IP Address Hashing:**
```python
import hashlib
import hmac

def hash_ip_address(ip_address: str, secret_key: bytes) -> bytes:
    """
    Hash IP address with HMAC-SHA256 for GDPR compliance

    GDPR Recital 26: Pseudonymization reduces risks and helps meet data protection obligations
    """
    return hmac.new(secret_key, ip_address.encode(), hashlib.sha256).digest()
```

**User Agent Fingerprinting:**
```python
def hash_user_agent(user_agent: str, secret_key: bytes) -> bytes:
    """Hash user agent to detect returning guests without storing PII"""
    return hmac.new(secret_key, user_agent.encode(), hashlib.sha256).digest()
```

---

## Consent Management

### Cookie Banner (GDPR Compliant)

**Required Elements:**
- ✅ Clear explanation of cookies used
- ✅ Granular consent (functional, analytics, marketing separately)
- ✅ "Accept All" button
- ✅ "Reject All" button
- ✅ "Customize" button
- ✅ Link to Privacy Policy
- ✅ Link to Cookie Policy

**Cookie Categories:**

1. **Strictly Necessary (No Consent Required)**
   - Session management
   - Security (CSRF tokens)
   - Load balancing

2. **Functional (Consent Required)**
   - Guest session persistence
   - Language preferences
   - UI customization

3. **Analytics (Consent Required)**
   - Conversion tracking
   - Feature usage statistics
   - A/B testing

4. **Marketing (Consent Required)**
   - Not used in demo service (guests are not authenticated users)

### Consent Database Schema

```sql
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_session_id UUID REFERENCES guest_sessions(id) ON DELETE CASCADE,
    consent_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    privacy_policy_version VARCHAR(20) NOT NULL,
    cookie_policy_version VARCHAR(20) NOT NULL,

    -- Granular consent choices
    functional_cookies BOOLEAN NOT NULL,
    analytics_cookies BOOLEAN NOT NULL,
    marketing_cookies BOOLEAN NOT NULL,

    -- Consent metadata
    consent_method VARCHAR(50),  -- 'banner_accept_all', 'banner_customize', 'settings_page'
    ip_address_hash BYTEA,
    user_agent_fingerprint BYTEA,

    -- Withdrawal tracking
    withdrawn_at TIMESTAMP,
    withdrawal_reason TEXT
);
```

---

## Data Retention & Deletion

### Retention Policy

**Guest Sessions:**
- **Active Sessions:** Expire after 30 minutes of inactivity
- **Stored Sessions:** Deleted after **30 days** (GDPR compliance)
- **Audit Logs:** Retained for **90 days** (security requirement)

**Consent Records:**
- Retained for **3 years** (legal requirement for proof of consent)
- Deleted upon user request (Right to Erasure)

### Automatic Deletion

**Cron Job (Daily at 2:00 AM UTC):**
```bash
# /etc/cron.d/cleanup-guest-sessions
0 2 * * * postgres psql -d course_creator -c "SELECT cleanup_expired_guest_sessions();"
```

**Manual Deletion API:**
```python
from datetime import datetime
from uuid import UUID

def delete_guest_session(session_id: UUID, reason: str = 'user_request') -> bool:
    """
    Delete guest session immediately (GDPR Right to Erasure)

    COMPLIANCE:
    - GDPR Article 17 (Right to Erasure)
    - CCPA Right to Delete
    """
    # Log deletion request
    audit_log.insert({
        'guest_session_id': session_id,
        'action': 'deletion_requested',
        'timestamp': datetime.utcnow(),
        'details': {'reason': reason}
    })

    # Delete session data
    db.guest_sessions.delete(id=session_id)

    # Delete related consent records
    db.consent_records.delete(guest_session_id=session_id)

    return True
```

---

## Privacy API Endpoints

### Required Endpoints (GDPR Compliance)

#### 1. GET `/api/v1/privacy/guest-session/{session_id}`
**Purpose:** Right to Access (GDPR Article 15)

**Response:**
```json
{
  "session_id": "uuid",
  "created_at": "2025-10-07T10:00:00Z",
  "data_collected": {
    "user_profile": {"role": "instructor", "interests": ["AI"]},
    "features_viewed": ["chatbot", "ai_content_generation"],
    "ai_requests_count": 7,
    "country_code": "US"
  },
  "consent": {
    "functional_cookies": true,
    "analytics_cookies": true,
    "marketing_cookies": false
  },
  "retention": {
    "expires_at": "2025-10-07T10:30:00Z",
    "deletion_scheduled_at": null
  }
}
```

#### 2. DELETE `/api/v1/privacy/guest-session/{session_id}`
**Purpose:** Right to Erasure (GDPR Article 17)

**Response:**
```json
{
  "status": "deleted",
  "session_id": "uuid",
  "deletion_timestamp": "2025-10-07T10:15:00Z",
  "confirmation": "All data associated with this session has been permanently deleted."
}
```

#### 3. POST `/api/v1/privacy/guest-session/{session_id}/consent`
**Purpose:** Update consent preferences

**Request:**
```json
{
  "functional_cookies": true,
  "analytics_cookies": false,
  "marketing_cookies": false
}
```

#### 4. GET `/api/v1/privacy/policy`
**Purpose:** Privacy Policy (machine-readable)

**Response:**
```json
{
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
```

---

## Security Measures

### Encryption

**At Rest:**
- PostgreSQL Transparent Data Encryption (TDE)
- Column-level encryption for sensitive JSONB fields

**In Transit:**
- TLS 1.3 for all API communications
- HTTPS only (no HTTP)

### Access Controls

**Database:**
- Least privilege principle
- Service accounts with read-only/write-only separation
- No direct database access from frontend

**API:**
- Rate limiting (prevent abuse)
- CORS restrictions
- Session ID validation

### Audit Logging

**All Privacy-Related Actions Logged:**
- Session creation
- Consent given/withdrawn
- Data access (GDPR Article 15 requests)
- Deletion requests (GDPR Article 17)

---

## Privacy Policy Template

```markdown
# Privacy Policy - Guest Demo Sessions

**Last Updated:** October 7, 2025
**Version:** 3.3.0

## What Data We Collect

When you use our demo features without creating an account, we collect:

- **Session ID:** A random identifier to maintain your demo session
- **Usage Data:** Features you view, questions you ask the AI chatbot
- **Technical Data:** Country (not city), browser type (hashed)
- **User Profile:** Role and interests you share (no names or emails)

## Why We Collect This Data

- **Demo Functionality:** Provide personalized demo experience
- **Improvement:** Understand which features visitors find valuable
- **Security:** Prevent abuse and spam

## Your Rights

### Right to Access
Request a copy of your data: privacy@example.com

### Right to Delete ("Right to be Forgotten")
Delete your guest session data at any time via the cookie settings menu.

### Right to Object
You can object to analytics cookies via cookie settings.

## Data Retention

- **Active Sessions:** 30 minutes
- **Stored Data:** 30 days maximum
- **Audit Logs:** 90 days (security requirement)

## Contact

Data Protection Officer: dpo@example.com
Privacy Team: privacy@example.com
```

---

## Implementation Checklist

### Phase 1: Database Setup
- [ ] Create `guest_sessions` table with privacy fields
- [ ] Create `guest_session_audit_log` table
- [ ] Create `consent_records` table
- [ ] Implement cleanup_expired_guest_sessions() function
- [ ] Schedule daily cleanup cron job

### Phase 2: Data Access Layer
- [ ] Create GuestSessionDAO with PostgreSQL integration
- [ ] Implement IP address hashing
- [ ] Implement user agent fingerprinting
- [ ] Add audit logging to all database operations

### Phase 3: API Endpoints
- [ ] GET /api/v1/privacy/guest-session/{id} (Right to Access)
- [ ] DELETE /api/v1/privacy/guest-session/{id} (Right to Erasure)
- [ ] POST /api/v1/privacy/guest-session/{id}/consent
- [ ] GET /api/v1/privacy/policy

### Phase 4: Frontend Compliance
- [ ] Cookie consent banner (GDPR compliant)
- [ ] Privacy Policy page
- [ ] Cookie Policy page
- [ ] Privacy settings menu
- [ ] "Do Not Sell" link (CCPA)

### Phase 5: Testing & Documentation
- [ ] Privacy compliance testing
- [ ] Data deletion testing (Right to Erasure)
- [ ] Audit log verification
- [ ] Legal review
- [ ] User documentation

---

## Conclusion

This implementation ensures **full compliance** with:
- ✅ GDPR (EU)
- ✅ CCPA (California)
- ✅ PIPEDA (Canada)

**Key Principles:**
1. **Data Minimization** - Collect only necessary data
2. **Pseudonymization** - Hash PII (IP addresses, user agents)
3. **Transparency** - Clear privacy policy and cookie banner
4. **User Control** - Easy consent management and data deletion
5. **Security** - Encryption, access controls, audit logging
6. **Retention Limits** - 30-day maximum storage

**Next Steps:**
1. Implement PostgreSQL schema
2. Create privacy API endpoints
3. Add cookie consent banner
4. Legal review of privacy policy
5. Security audit

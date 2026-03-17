# Privacy API Documentation

**Version:** 3.3.0
**Last Updated:** 2025-10-07
**Service:** Demo Service (Port 8010)
**Base URL:** `https://localhost:8010/api/v1/privacy`

---

## Overview

The Privacy API provides GDPR, CCPA, and PIPEDA compliant endpoints for guest users to exercise their privacy rights. All endpoints support CORS and include rate limiting to prevent abuse.

**Compliance Standards:**
- ✅ GDPR (EU) - Articles 7, 15, 17, 20, 30
- ✅ CCPA (California) - Right to Know, Delete, Opt-Out
- ✅ PIPEDA (Canada) - 10 Privacy Principles

---

## Authentication & Security

### Rate Limiting
- **Limit:** 10 requests per session per hour
- **Response:** `429 Too Many Requests` when exceeded
- **Reset:** Automatically after 1 hour

### CORS Headers
All endpoints include:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Error Responses
```json
{
  "error": "Error message",
  "details": "Additional context"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid UUID format)
- `404` - Not Found (session doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

---

## Endpoints

### 1. GDPR Article 15 - Right to Access

#### Get Guest Session Data
Retrieve all personal data associated with a guest session.

**Endpoint:** `GET /api/v1/privacy/guest-session/{session_id}`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000"
```

**Response (200 OK):**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-10-07T10:00:00Z",
  "data_collected": {
    "user_profile": {
      "role": "instructor",
      "interests": ["AI", "Docker"],
      "pain_points": ["time-consuming grading"]
    },
    "features_viewed": ["chatbot", "ai_content_generation", "docker_labs"],
    "ai_requests_count": 7,
    "country_code": "US",
    "ip_address": "hashed",
    "user_agent": "hashed"
  },
  "consent": {
    "functional_cookies": true,
    "analytics_cookies": true,
    "marketing_cookies": false,
    "consent_timestamp": "2025-10-07T10:00:00Z",
    "privacy_policy_version": "3.3.0"
  },
  "retention": {
    "expires_at": "2025-10-07T10:30:00Z",
    "deletion_scheduled_at": null
  }
}
```

**Privacy Note:** IP addresses and user agents are shown as "hashed" - raw values are never exposed.

---

### 2. GDPR Article 17 - Right to Erasure

#### Delete Guest Session
Delete all personal data associated with a guest session.

**Endpoint:** `DELETE /api/v1/privacy/guest-session/{session_id}`

**Request:**
```bash
curl -X DELETE "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000"
```

**Response (200 OK):**
```json
{
  "status": "deleted",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "deletion_timestamp": "2025-10-07T10:15:00Z",
  "confirmation": "All data associated with this session has been permanently deleted."
}
```

**Audit Trail:** Deletion request is logged with action='deletion_requested' and reason='user_request'.

---

### 3. GDPR Article 7 - Consent Management

#### Update Consent Preferences
Update cookie consent preferences for a guest session.

**Endpoint:** `POST /api/v1/privacy/guest-session/{session_id}/consent`

**Request:**
```bash
curl -X POST "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000/consent" \
  -H "Content-Type: application/json" \
  -d '{
    "functional_cookies": true,
    "analytics_cookies": false,
    "marketing_cookies": false,
    "privacy_policy_version": "3.3.0"
  }'
```

**Response (200 OK):**
```json
{
  "status": "updated",
  "consent_preferences": {
    "functional_cookies": true,
    "analytics_cookies": false,
    "marketing_cookies": false
  },
  "consent_timestamp": "2025-10-07T10:20:00Z",
  "privacy_policy_version": "3.3.0"
}
```

**Cookie Categories:**
- **Strictly Necessary:** Cannot be disabled (session management, security)
- **Functional:** Guest session persistence, UI preferences
- **Analytics:** Conversion tracking, feature usage statistics
- **Marketing:** Data sharing with third parties (always opt-in)

---

### 4. Privacy Policy

#### Get Privacy Policy
Retrieve machine-readable privacy policy.

**Endpoint:** `GET /api/v1/privacy/policy`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/policy"
```

**Response (200 OK):**
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
    },
    {
      "category": "user_profile",
      "purpose": "Personalized demo experience",
      "legal_basis": "consent",
      "retention_period": "30_days"
    },
    {
      "category": "analytics",
      "purpose": "Conversion funnel optimization",
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
```

---

### 5. GDPR Article 20 - Data Portability

#### Export Session Data (JSON)
Export guest session data in JSON format.

**Endpoint:** `GET /api/v1/privacy/guest-session/{session_id}/export?format=json`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000/export?format=json"
```

**Response (200 OK):**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-10-07T10:00:00Z",
  "user_profile": {
    "role": "instructor",
    "interests": ["AI", "Docker"]
  },
  "features_viewed": ["chatbot", "ai_content_generation"],
  "consent_preferences": {
    "functional_cookies": true,
    "analytics_cookies": true,
    "marketing_cookies": false
  },
  "ai_requests_count": 7
}
```

#### Export Session Data (CSV)
Export guest session data in CSV format.

**Endpoint:** `GET /api/v1/privacy/guest-session/{session_id}/export?format=csv`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000/export?format=csv"
```

**Response (200 OK):**
```csv
session_id,created_at,features_viewed,ai_requests_count,user_profile
123e4567-e89b-12d3-a456-426614174000,2025-10-07T10:00:00Z,"chatbot,ai_content_generation",7,"{""role"": ""instructor""}"
```

**Content-Type:** `text/csv; charset=utf-8`

---

### 6. CCPA Compliance

#### Do Not Sell My Personal Information
Opt-out from data sharing/selling (CCPA requirement).

**Endpoint:** `POST /api/v1/privacy/guest-session/{session_id}/do-not-sell`

**Request:**
```bash
curl -X POST "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000/do-not-sell"
```

**Response (200 OK):**
```json
{
  "status": "opted_out",
  "marketing_cookies": false,
  "confirmation": "You have successfully opted out of data selling. Marketing cookies have been disabled."
}
```

#### CCPA Disclosure
Get CCPA-compliant disclosure of data collection practices.

**Endpoint:** `GET /api/v1/privacy/guest-session/{session_id}/ccpa-disclosure`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/guest-session/123e4567-e89b-12d3-a456-426614174000/ccpa-disclosure"
```

**Response (200 OK):**
```json
{
  "categories_collected": [
    "Identifiers (session ID)",
    "Internet activity (features viewed, AI requests)",
    "Geolocation data (country only)",
    "Inferences (user role, interests)"
  ],
  "business_purposes": [
    "Provide personalized demo experience",
    "Analyze conversion funnel",
    "Improve platform features",
    "Prevent fraud and abuse"
  ],
  "third_parties": []
}
```

**Note:** Guest sessions do NOT share data with third parties.

---

### 7. Compliance Reporting

#### Get Compliance Report
Retrieve aggregate privacy compliance metrics (internal use).

**Endpoint:** `GET /api/v1/privacy/compliance-report`

**Request:**
```bash
curl -X GET "https://localhost:8010/api/v1/privacy/compliance-report"
```

**Response (200 OK):**
```json
{
  "total_sessions": 1250,
  "deletion_requests": 45,
  "consent_withdrawals": 23,
  "average_erasure_response_time_hours": 0.5,
  "compliance_score": 98,
  "report_generated_at": "2025-10-07T10:00:00Z"
}
```

**Compliance Score:**
- 90-100: Excellent compliance
- 80-89: Good compliance
- 70-79: Needs improvement
- <70: Critical issues

---

## Data Retention

### Automatic Cleanup
- **Session Expiration:** 30 minutes of inactivity
- **Data Retention:** Maximum 30 days
- **Audit Logs:** Retained for 90 days (security requirement)

### Manual Deletion
Users can delete their data at any time via the Right to Erasure endpoint.

---

## Pseudonymization

All potentially identifiable information is pseudonymized:

**IP Addresses:**
- Stored as HMAC-SHA256 hash (not plaintext)
- Used for returning guest recognition only
- Cannot be reversed to original IP

**User Agents:**
- Stored as HMAC-SHA256 hash
- Used for fingerprinting returning guests
- No tracking across sites

**Hashing Algorithm:**
```python
import hashlib
import hmac

def hash_ip_address(ip_address: str, secret_key: bytes) -> bytes:
    return hmac.new(secret_key, ip_address.encode(), hashlib.sha256).digest()
```

---

## Audit Logging

All privacy-related actions are logged:

**Logged Actions:**
- `created` - Session creation
- `consent_given` - Consent preferences updated
- `data_accessed` - User accessed their data (Right to Access)
- `deletion_requested` - User requested deletion (Right to Erasure)

**Audit Log Entry:**
```json
{
  "id": 12345,
  "guest_session_id": "123e4567-e89b-12d3-a456-426614174000",
  "action": "deletion_requested",
  "timestamp": "2025-10-07T10:15:00Z",
  "ip_address_hash": "5f4dcc3b5aa765d61d8327deb882cf99...",
  "details": {
    "reason": "user_request"
  },
  "checksum": "9b74c9897bac770ffc029102a200c5de..."
}
```

**Tamper Detection:**
- SHA-256 checksum of all log fields
- Verifies audit log integrity
- Detects unauthorized modifications

---

## Integration Examples

### JavaScript Frontend
```javascript
// Right to Access
async function getMyData(sessionId) {
  const response = await fetch(`https://localhost:8010/api/v1/privacy/guest-session/${sessionId}`);
  const data = await response.json();
  console.log('My data:', data);
}

// Right to Erasure
async function deleteMyData(sessionId) {
  const response = await fetch(`https://localhost:8010/api/v1/privacy/guest-session/${sessionId}`, {
    method: 'DELETE'
  });
  const result = await response.json();
  console.log('Deletion status:', result);
}

// Update Consent
async function updateConsent(sessionId, preferences) {
  const response = await fetch(`https://localhost:8010/api/v1/privacy/guest-session/${sessionId}/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences)
  });
  const result = await response.json();
  console.log('Consent updated:', result);
}
```

### Python Client
```python
import requests
from uuid import UUID

BASE_URL = "https://localhost:8010/api/v1/privacy"

def get_session_data(session_id: UUID):
    response = requests.get(f"{BASE_URL}/guest-session/{session_id}")
    return response.json()

def delete_session(session_id: UUID):
    response = requests.delete(f"{BASE_URL}/guest-session/{session_id}")
    return response.json()

def update_consent(session_id: UUID, preferences: dict):
    response = requests.post(
        f"{BASE_URL}/guest-session/{session_id}/consent",
        json=preferences
    )
    return response.json()

def export_data(session_id: UUID, format='json'):
    response = requests.get(
        f"{BASE_URL}/guest-session/{session_id}/export",
        params={'format': format}
    )
    return response.text if format == 'csv' else response.json()
```

---

## Cookie Consent Banner Integration

### Recommended Flow
1. User visits platform → Session created
2. Cookie banner shown → User makes choices
3. POST to `/consent` endpoint → Preferences saved
4. User continues demo → Personalized experience

### Consent Banner Example
```html
<div id="cookie-banner">
  <h3>Cookie Preferences</h3>
  <label>
    <input type="checkbox" checked disabled> Strictly Necessary (required)
  </label>
  <label>
    <input type="checkbox" id="functional"> Functional Cookies
  </label>
  <label>
    <input type="checkbox" id="analytics"> Analytics Cookies
  </label>
  <label>
    <input type="checkbox" id="marketing"> Marketing Cookies
  </label>
  <button onclick="saveConsent()">Save Preferences</button>
  <a href="/privacy-policy">Privacy Policy</a>
</div>

<script>
async function saveConsent() {
  const sessionId = localStorage.getItem('guest_session_id');
  const preferences = {
    functional_cookies: document.getElementById('functional').checked,
    analytics_cookies: document.getElementById('analytics').checked,
    marketing_cookies: document.getElementById('marketing').checked,
    privacy_policy_version: '3.3.0'
  };

  await fetch(`https://localhost:8010/api/v1/privacy/guest-session/${sessionId}/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences)
  });

  document.getElementById('cookie-banner').style.display = 'none';
}
</script>
```

---

## Legal Compliance Checklist

### GDPR (EU) ✅
- ✅ Article 6 - Lawful basis for processing (legitimate interest + consent)
- ✅ Article 7 - Conditions for consent (freely given, specific, informed, unambiguous)
- ✅ Article 13 - Information to be provided (privacy policy, rights, retention)
- ✅ Article 15 - Right to access (GET endpoint)
- ✅ Article 17 - Right to erasure (DELETE endpoint)
- ✅ Article 20 - Right to data portability (export endpoints)
- ✅ Article 25 - Data protection by design and by default (pseudonymization)
- ✅ Article 30 - Records of processing activities (audit logs)
- ✅ Article 32 - Security of processing (encryption, hashing, access controls)

### CCPA (California) ✅
- ✅ Right to Know (CCPA disclosure endpoint)
- ✅ Right to Delete (DELETE endpoint)
- ✅ Right to Opt-Out (Do Not Sell endpoint)
- ✅ Right to Non-Discrimination (demo works without cookies)

### PIPEDA (Canada) ✅
- ✅ Accountability (DPO contact provided)
- ✅ Identifying purposes (privacy policy)
- ✅ Consent (consent management endpoint)
- ✅ Limiting collection (data minimization)
- ✅ Limiting use, disclosure, retention (30-day limit, no third parties)
- ✅ Accuracy (user can update preferences)
- ✅ Safeguards (encryption, hashing, rate limiting)
- ✅ Openness (machine-readable privacy policy)
- ✅ Individual access (Right to Access endpoint)
- ✅ Challenging compliance (DPO contact, complaint process)

---

## Support & Contact

**Data Protection Officer (DPO):** dpo@example.com
**Privacy Team:** privacy@example.com
**API Issues:** support@example.com

**Documentation Version:** 3.3.0
**Last Updated:** October 7, 2025

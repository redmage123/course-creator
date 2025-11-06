# JWT Token Refresh System

## Overview

The JWT Token Refresh System implements activity-based token renewal to support multi-hour user sessions while maintaining security. This addresses the requirement that instructors and students may be logged in for multiple hours per day without experiencing unexpected logouts.

## Problem Solved

**Before**: JWT tokens expired after 30 minutes regardless of user activity, causing unexpected logouts for active users.

**After**: Tokens automatically refresh every 20 minutes for active users, enabling multi-hour sessions while maintaining security through activity-based validation.

## Architecture

### Backend Component

**Service**: `user-management` (port 8000)
**Endpoint**: `POST /auth/refresh`
**Location**: `/home/bbrelin/course-creator/services/user-management/routes.py` (line 504)

#### Endpoint Features

- **Authentication Required**: Requires valid JWT token via `Depends(get_current_user)`
- **Token Generation**: Issues new JWT token with fresh 30-minute expiration
- **User Validation**: Re-fetches user data from database to ensure current state
- **Organization Membership**: Refreshes organization_id for organization admins
- **Security**: Cannot refresh expired tokens (returns 401)

#### Request Format

```bash
POST /auth/refresh
Authorization: Bearer <current_token>
Content-Type: application/json
```

#### Response Format

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "username": "instructor1",
    "email": "instructor@example.com",
    "role": "instructor",
    "organization_id": "org-uuid"  // Only for org admins
  }
}
```

### Frontend Component

**Service**: `frontend`
**Module**: `auth.js`
**Location**: `/home/bbrelin/course-creator/frontend/js/modules/auth.js`

#### Key Methods

1. **`refreshToken()` (line 552)**
   - Calls `/auth/refresh` endpoint with current token
   - Checks user activity within last 30 minutes
   - Updates localStorage with new token
   - Handles token expiration (triggers logout)

2. **`startTokenRefresh()` (line 618)**
   - Starts automatic token refresh interval (20 minutes)
   - Called on login and page reload
   - Clears any existing interval before starting

3. **`stopTokenRefresh()` (line 628)**
   - Stops automatic token refresh interval
   - Called on logout, session expiry, and inactivity timeout

#### Refresh Strategy

```javascript
// Refresh every 20 minutes (before 30-minute expiration)
const REFRESH_INTERVAL = 20 * 60 * 1000; // 20 minutes

// Only refresh if user has activity within last 30 minutes
const ACTIVITY_THRESHOLD = 30 * 60 * 1000; // 30 minutes
```

## Lifecycle Management

### Token Refresh Lifecycle

```
User Login
    ↓
Start Token Refresh (every 20 min)
    ↓
Check Activity < 30 min?
    ├── YES → Call /auth/refresh → Update Token → Continue
    └── NO → Skip Refresh
    ↓
Token Expired (401 response)?
    ├── YES → Stop Refresh → Logout → Redirect to Home
    └── NO → Continue
    ↓
User Logout / Session Expire
    ↓
Stop Token Refresh
```

### Integration Points

**Token Refresh Starts**:
- Line 300: After successful login
- Line 215: On page reload with existing session

**Token Refresh Stops**:
- Line 702: On explicit logout
- Line 835: On session expiration
- Line 857: On inactivity timeout
- Line 1085: On session cleanup

## Security Features

### Activity-Based Validation

- Frontend checks `lastActivity` timestamp before refreshing
- Only refreshes if activity within last 30 minutes
- Prevents indefinite sessions without user interaction

### Token Expiration Handling

- Expired tokens cannot be refreshed (401 response)
- 401 triggers automatic logout and redirect
- Ensures no state where expired token keeps user logged in

### User State Re-validation

- Backend re-fetches user data from database on each refresh
- Organization membership re-validated for org admins
- Ensures user permissions are always current

## Configuration

### Backend Configuration

**File**: `/home/bbrelin/course-creator/services/user-management/conf/config.yaml`

```yaml
security:
  jwt_secret_key: '${oc.env:JWT_SECRET_KEY}'
  jwt_algorithm: 'HS256'
  access_token_expire_minutes: 30  # Token lifespan
```

### Frontend Configuration

**File**: `/home/bbrelin/course-creator/frontend/js/modules/auth.js`

```javascript
const REFRESH_INTERVAL = 20 * 60 * 1000;      // 20 minutes - refresh frequency
const ACTIVITY_THRESHOLD = 30 * 60 * 1000;    // 30 minutes - activity check
const MAX_SESSION_TIME = 8 * 60 * 60 * 1000;  // 8 hours - absolute session limit
const IDLE_TIMEOUT = 2 * 60 * 60 * 1000;      // 2 hours - inactivity timeout
```

## Usage Patterns

### Multi-Hour Instructor Session

```
Instructor logs in at 9:00 AM
    ↓
Token expires at 9:30 AM (30 min)
    BUT
Token refreshed at 9:20 AM (20 min interval)
    ↓
New token expires at 9:50 AM
    BUT
Token refreshed at 9:40 AM
    ↓
... continues as long as instructor is active ...
    ↓
Instructor inactive for 30+ minutes
    ↓
Next refresh skipped (no recent activity)
    ↓
Token expires → Auto logout → Redirect to home
```

### Student Multi-Hour Learning Session

```
Student logs in at 2:00 PM
    ↓
Watches lectures, takes notes, completes quizzes
    ↓
Token refreshes at: 2:20, 2:40, 3:00, 3:20, 3:40, 4:00...
    ↓
Student takes break (no activity for 30+ min)
    ↓
Token expires → Auto logout → Redirect to home
```

## Testing

### Manual Testing Steps

1. **Test Successful Refresh**:
   ```bash
   # Login and get token
   TOKEN=$(curl -X POST https://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"instructor1","password":"password"}' \
     -k | jq -r '.access_token')

   # Wait 1 minute (simulate activity)
   sleep 60

   # Refresh token
   curl -X POST https://localhost:8000/auth/refresh \
     -H "Authorization: Bearer $TOKEN" \
     -k | jq
   ```

2. **Test Activity Threshold**:
   - Login to platform
   - Open browser console
   - Monitor token refresh logs: `⏰ Auto token refresh triggered`
   - Leave browser idle for 30+ minutes
   - Verify refresh is skipped: `⏭️ No recent activity, skipping token refresh`

3. **Test Token Expiration**:
   - Login to platform
   - Wait for token to expire (30 minutes)
   - Verify automatic logout and redirect to home page

### Automated Testing

Create E2E test at: `tests/e2e/test_token_refresh_workflow.py`

```python
def test_token_refresh_keeps_session_active():
    """Verify token refresh prevents logout for active users"""
    # Login
    # Wait 25 minutes (before first refresh)
    # Verify still logged in
    # Wait 25 more minutes (token would have expired without refresh)
    # Verify still logged in (token was refreshed)
    pass

def test_inactive_users_auto_logout():
    """Verify inactive users are logged out after token expiry"""
    # Login
    # Disable activity tracking
    # Wait 30+ minutes
    # Verify auto logout and redirect
    pass
```

## Monitoring

### Backend Logs

```bash
# Monitor token refresh requests
docker logs course-creator_user-management_1 -f | grep "Token refresh"

# Expected log output
# 🔄 Token refresh requested for user: instructor1
# ✅ Token refreshed successfully for user: instructor1
```

### Frontend Console Logs

```javascript
// Token refresh triggered
"⏰ Auto token refresh triggered"

// Successful refresh
"✅ Token refreshed successfully"

// Skipped refresh (no activity)
"⏭️ No recent activity, skipping token refresh"

// Token expired
"❌ Token refresh failed: Token expired"
```

## Troubleshooting

### Issue: Users Being Logged Out Despite Activity

**Symptoms**: Active users experience unexpected logouts

**Possible Causes**:
1. Activity tracking not working (check localStorage 'lastActivity')
2. Token refresh interval stopped (check browser console for errors)
3. Backend refresh endpoint failing (check user-management logs)

**Debug Steps**:
```javascript
// Check if token refresh is running
console.log(window.authManager.tokenRefreshInterval); // Should not be null

// Check last activity timestamp
console.log(localStorage.getItem('lastActivity'));

// Check time since last activity
const lastActivity = parseInt(localStorage.getItem('lastActivity'));
const timeSinceActivity = Date.now() - lastActivity;
console.log(`Minutes since activity: ${timeSinceActivity / 60000}`);
```

### Issue: Token Refresh Endpoint Returns 401

**Symptoms**: Token refresh fails with 401 Unauthorized

**Possible Causes**:
1. Token already expired (refresh called too late)
2. Token invalid or tampered with
3. User deleted or disabled in database

**Debug Steps**:
```bash
# Check token expiration
python3 << EOF
from jose import jwt
token = "YOUR_TOKEN_HERE"
payload = jwt.decode(token, options={"verify_signature": False})
import datetime
exp = datetime.datetime.fromtimestamp(payload['exp'])
print(f"Token expires at: {exp}")
print(f"Current time: {datetime.datetime.utcnow()}")
EOF
```

### Issue: Token Refresh Not Starting

**Symptoms**: No refresh logs in browser console

**Possible Causes**:
1. `startTokenRefresh()` not called after login
2. Interval cleared unexpectedly
3. JavaScript error preventing method execution

**Debug Steps**:
```javascript
// Force start token refresh
window.authManager.startTokenRefresh();

// Verify interval is set
console.log(window.authManager.tokenRefreshInterval); // Should be a number (interval ID)

// Check for JavaScript errors
// Open browser console and look for errors
```

## Security Considerations

### Token Refresh vs Token Renewal

This implementation uses **token refresh** (issuing new tokens to authenticated users) rather than **token renewal** (issuing tokens without re-authentication).

**Why Token Refresh**:
- Requires valid existing token (user must already be authenticated)
- User state re-validated from database on each refresh
- Activity-based validation prevents indefinite sessions
- Balances security with user experience

**NOT Implemented** (for security reasons):
- Refresh tokens (long-lived tokens for getting new access tokens)
- Silent renewal without activity check
- Indefinite token refresh without time limits

### Session Limits

Even with token refresh, sessions have absolute limits:

- **Maximum Session Time**: 8 hours (enforced by frontend)
- **Inactivity Timeout**: 2 hours (enforced by frontend)
- **Activity Threshold**: 30 minutes (enforced by token refresh)

This ensures a balance between usability and security.

## Implementation Date

**Implemented**: October 19, 2025
**Version**: 3.3.1
**Related Issue**: JWT token expiration causing unexpected logouts for active users

## Files Modified

### Backend
- `/home/bbrelin/course-creator/services/user-management/routes.py` (lines 504-576)
  - Added `POST /auth/refresh` endpoint

### Frontend
- `/home/bbrelin/course-creator/frontend/js/modules/auth.js`
  - Line 110: Added `tokenRefreshInterval` property
  - Lines 552-595: Added `refreshToken()` method
  - Lines 618-622: Added `startTokenRefresh()` method
  - Lines 628-634: Added `stopTokenRefresh()` method
  - Line 215: Start refresh on page reload
  - Line 300: Start refresh on login
  - Line 702: Stop refresh on logout
  - Line 835: Stop refresh on session expiry
  - Line 857: Stop refresh on inactivity timeout
  - Line 1085: Stop refresh on session cleanup

## Future Enhancements

### Potential Improvements

1. **Adaptive Refresh Interval**
   - Adjust refresh frequency based on user activity patterns
   - More frequent refresh for highly active users
   - Less frequent refresh for occasional interactions

2. **Token Refresh History**
   - Track token refresh history in database
   - Detect suspicious refresh patterns
   - Alert on unusual refresh activity

3. **Graceful Degradation**
   - If refresh fails due to network issues, retry with exponential backoff
   - Show user-friendly notification before session expiry
   - Allow user to manually refresh token

4. **Performance Optimization**
   - Batch refresh requests for multiple tabs (shared service worker)
   - Use browser visibility API to skip refresh when tab is hidden
   - Predictive refresh based on user activity patterns

## References

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Token Refresh](https://tools.ietf.org/html/rfc6749#section-6)
- [Frontend Session Management Patterns](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

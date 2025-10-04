# Audit Log Fixes Summary

## Issues Found

### 1. Incorrect API URLs ✅ FIXED
**Problem**: Audit log endpoints were calling the wrong URL
- Was calling: `:3000/api/v1/rbac/audit-log` (frontend port)
- Should call: `:8008/api/v1/rbac/audit-log` (backend organization-management service)

**Root Cause**: Missing `${this.API_BASE}` prefix in fetch calls

**Fix Applied**:
```javascript
// Before
await fetch('/api/v1/rbac/audit-log', {...})

// After
await fetch(`${this.API_BASE}/api/v1/rbac/audit-log`, {...})
```

**Files Changed**:
- `frontend/js/site-admin-dashboard.js` (3 locations)
  - Line ~1890: `loadAuditLog()`
  - Line ~2050: `filterAuditLog()`
  - Line ~2105: `exportAuditLog()`

### 2. Authentication Errors (401 Unauthorized) ⚠️ NEEDS ATTENTION
**Problem**: All dashboard endpoints returning 401 errors:
- `/api/v1/site-admin/stats` → 401
- `/api/v1/site-admin/organizations` → 401
- `/api/v1/site-admin/platform/health` → 401
- `/api/v1/rbac/audit-log` → Will also get 401 with invalid token

**Root Cause**: Invalid or expired authentication token

**Why This Happens**:
1. Token expired (tokens have TTL)
2. Token not valid for site_admin role
3. Token validation failing in backend
4. Session storage corrupted

## How to Fix Authentication Issues

### Option 1: Re-login (Recommended)
1. Log out of the site admin dashboard
2. Log back in with valid site admin credentials
3. Token will be refreshed

### Option 2: Check Token in Browser Console
```javascript
// In browser console
console.log(localStorage.getItem('authToken'));
console.log(localStorage.getItem('currentUser'));

// Check token expiry
const token = localStorage.getItem('authToken');
if (token) {
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log('Token expires:', new Date(payload.exp * 1000));
}
```

### Option 3: Manually Set Valid Token (Development Only)
```javascript
// Get a fresh token from login endpoint first
const response = await fetch('https://localhost:8000/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'admin@example.com',
        password: 'your-password'
    })
});
const data = await response.json();
localStorage.setItem('authToken', data.token);
```

## Service Restart Required

The organization-management service was restarted to pick up the audit log endpoints. This may have invalidated existing sessions.

**What Happened**:
1. We added audit log endpoints to `services/organization-management/api/rbac_endpoints.py`
2. Fixed syntax error in the code
3. Restarted the service: `docker restart course-creator-organization-management-1`
4. **All existing auth tokens became invalid** (if service uses in-memory session storage)

**Solution**: Re-authenticate to get a fresh token

## Current Status

✅ **Fixed**:
- Audit log API URLs now point to correct backend (port 8008)
- Service is running with audit log endpoints
- No syntax errors in code

⚠️ **Needs User Action**:
- Re-login to get valid authentication token
- Or check if token is expired/invalid

## Testing the Fix

### Step 1: Verify Service is Running
```bash
docker ps | grep organization-management
# Should show: Up X minutes (healthy)
```

### Step 2: Test Endpoint Without Auth
```bash
curl -k https://localhost:8008/api/v1/rbac/audit-log
# Should return: 401 or 403 (not 404)
```

### Step 3: Test With Mock Token (Will Fail Auth)
```bash
curl -k -H "Authorization: Bearer test-token" \
  https://localhost:8008/api/v1/rbac/audit-log
# Should return: 401 Unauthorized (expected - token is invalid)
```

### Step 4: Re-Login in Browser
1. Go to site admin dashboard
2. If logged out, log in with site admin credentials
3. If still logged in, refresh the page
4. Check browser console for errors

### Step 5: Verify Audit Log Loads
1. Navigate to Audit tab
2. Should see audit log entries (or empty state if no data)
3. No 404 errors in console

## Expected Behavior After Fix

### Before Fix:
```
❌ :3000/api/v1/rbac/audit-log → 404 Not Found (wrong port)
❌ Failed to load audit log
```

### After Fix (with valid token):
```
✅ :8008/api/v1/rbac/audit-log → 200 OK (correct port)
✅ Audit log entries displayed
```

### After Fix (with invalid token):
```
⚠️ :8008/api/v1/rbac/audit-log → 401 Unauthorized (needs re-login)
⚠️ Failed to load audit log: Unauthorized
```

## Next Steps

1. **Re-login** to get a fresh authentication token
2. **Clear browser cache** if issues persist:
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   // Then re-login
   ```
3. **Check service logs** if still getting errors:
   ```bash
   docker logs course-creator-organization-management-1 --tail 50
   ```

## Files Changed in This Fix

1. `frontend/js/site-admin-dashboard.js`
   - Fixed `loadAuditLog()` - line ~1890
   - Fixed `filterAuditLog()` - line ~2050
   - Fixed `exportAuditLog()` - line ~2105

2. `services/organization-management/api/rbac_endpoints.py`
   - Fixed syntax error in CSV filename generation - line 720

3. `services/organization-management/conf/config.yaml`
   - Added Hydra output configuration

## Summary

**The audit log 404 error is now fixed**. The endpoints are calling the correct backend URL (port 8008).

**The 401 authentication errors require re-login** to get a fresh token, as the service was restarted.

**Action Required**: Log out and log back in to the site admin dashboard to get a new authentication token.

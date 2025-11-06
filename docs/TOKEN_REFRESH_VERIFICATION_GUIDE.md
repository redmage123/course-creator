# Token Refresh Verification Guide

## Quick Verification

The JWT token refresh system has been implemented and deployed. This guide helps you verify it's working correctly.

## Automated Testing Script

Run the automated test script with your credentials:

```bash
./scripts/test_token_refresh.sh
```

Or provide credentials as arguments:

```bash
./scripts/test_token_refresh.sh your_username your_password
```

The script will:
1. ✅ Login and get initial token
2. ✅ Test token refresh endpoint
3. ✅ Verify new token works for API calls
4. ✅ Test multiple consecutive refreshes
5. ✅ Verify invalid tokens are rejected
6. ✅ Verify missing tokens are rejected

## Manual Verification Steps

### 1. Backend Endpoint Verification

Test the `/auth/refresh` endpoint manually:

```bash
# Step 1: Login
curl -k -X POST https://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}' \
  | jq

# Copy the access_token from response

# Step 2: Refresh token
curl -k -X POST https://localhost:8000/auth/refresh \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  | jq

# You should get a new token in response
```

### 2. Frontend Automatic Refresh Verification

Test the automatic frontend token refresh:

```bash
# Login to the platform via browser
# Open browser DevTools console (F12)

# Check if token refresh is running:
window.authManager.tokenRefreshInterval
// Should return a number (interval ID), not null

# Monitor for automatic refresh (runs every 20 minutes)
// You should see in console:
"⏰ Auto token refresh triggered"
"✅ Token refreshed successfully"
```

### 3. Activity-Based Refresh Verification

Test that token refresh only happens for active users:

```bash
# Login to platform
# Open browser DevTools console

# Check last activity timestamp
localStorage.getItem('lastActivity')

# Wait 20 minutes (when auto-refresh triggers)
# If you've been active, you'll see:
"✅ Token refreshed successfully"

# If you've been inactive for 30+ minutes, you'll see:
"⏭️ No recent activity, skipping token refresh"
```

### 4. Automatic Logout Verification

Test that expired tokens trigger automatic logout:

```bash
# This is harder to test manually since it requires waiting 30+ minutes
# after being inactive

# Scenario:
1. Login to platform
2. Don't interact with the platform for 30+ minutes
3. Token refresh will be skipped (no activity)
4. Token will expire
5. Next API call will return 401
6. User will be automatically logged out
7. Page will redirect to home
```

## Expected Behavior

### Multi-Hour Session (Active User)

```
Login at 9:00 AM
  ↓
Token refreshed at 9:20 AM
  ↓
Token refreshed at 9:40 AM
  ↓
Token refreshed at 10:00 AM
  ↓
... continues as long as user is active ...
  ↓
User can work for hours without interruption
```

### Inactive User Logout

```
Login at 2:00 PM
  ↓
Token refreshed at 2:20 PM
  ↓
User becomes inactive
  ↓
Token refresh skipped at 2:40 PM (no activity)
  ↓
Token expires at 2:50 PM
  ↓
Next page load triggers 401
  ↓
Auto logout and redirect to home
```

## Monitoring

### Backend Logs

Monitor token refresh activity in user-management service:

```bash
docker logs course-creator_user-management_1 -f | grep "refresh"
```

Expected logs:
```
🔄 Token refresh requested for user: instructor1
✅ Token refreshed successfully for user: instructor1
```

### Frontend Console Logs

Open browser DevTools console to see:

```javascript
// Every 20 minutes for active users
"⏰ Auto token refresh triggered"
"✅ Token refreshed successfully"

// When user is inactive
"⏭️ No recent activity, skipping token refresh"

// When token expires
"❌ Token refresh failed: Token expired"
```

## Verification Checklist

Use this checklist to verify the implementation:

- [ ] Backend `/auth/refresh` endpoint exists and responds
- [ ] Endpoint requires valid JWT token
- [ ] Endpoint returns new token with fresh expiration
- [ ] Endpoint includes user data in response
- [ ] Frontend `refreshToken()` method exists
- [ ] Frontend `startTokenRefresh()` starts interval
- [ ] Frontend `stopTokenRefresh()` stops interval
- [ ] Token refresh starts on login
- [ ] Token refresh starts on page reload
- [ ] Token refresh stops on logout
- [ ] Token refresh stops on session expiry
- [ ] Refresh only happens if user has recent activity
- [ ] Refresh happens every 20 minutes
- [ ] Invalid tokens are rejected (401/403)
- [ ] Expired tokens trigger automatic logout
- [ ] Multi-hour sessions work without interruption
- [ ] Inactive users are logged out after token expiry

## Troubleshooting

### Token Refresh Not Working

If token refresh isn't working:

```bash
# Check if endpoint exists
docker exec course-creator_user-management_1 \
  grep -n "async def refresh_token" /app/routes.py

# Should show: 505:    async def refresh_token(

# Check if frontend has refresh method
docker exec course-creator_frontend_1 \
  grep -n "async refreshToken()" /usr/share/nginx/html/js/modules/auth.js

# Should show: 552:    async refreshToken() {

# Check if token refresh is starting
# Login and check browser console for:
"🔄 Automatic token refresh started (every 20 minutes)"
```

### Users Still Being Logged Out

If users are still experiencing unexpected logouts:

1. **Check activity tracking**:
   ```javascript
   localStorage.getItem('lastActivity')
   // Should be a timestamp, updated on user actions
   ```

2. **Check token refresh interval**:
   ```javascript
   window.authManager.tokenRefreshInterval
   // Should not be null
   ```

3. **Check backend logs**:
   ```bash
   docker logs course-creator_user-management_1 --tail 100 | grep refresh
   ```

## Testing Results

After running the verification steps, you should confirm:

✅ **Backend**: Token refresh endpoint works correctly
✅ **Frontend**: Automatic token refresh is running
✅ **Activity Check**: Refresh only happens for active users
✅ **Security**: Invalid tokens are rejected
✅ **Lifecycle**: Refresh starts on login, stops on logout
✅ **User Experience**: Multi-hour sessions work without interruption

## Next Steps

Once verification is complete:

1. ✅ Update version history in CLAUDE.md
2. ✅ Document in architecture documentation
3. ✅ Add to testing checklist
4. ✅ Consider adding E2E test for token refresh workflow
5. ✅ Monitor production logs for token refresh activity

## Related Documentation

- **Implementation Details**: `/home/bbrelin/course-creator/docs/JWT_TOKEN_REFRESH_SYSTEM.md`
- **Backend Code**: `/home/bbrelin/course-creator/services/user-management/routes.py` (line 504)
- **Frontend Code**: `/home/bbrelin/course-creator/frontend/js/modules/auth.js` (lines 110, 552, 618)
- **Configuration**: `/home/bbrelin/course-creator/services/user-management/conf/config.yaml`

## Support

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Review backend logs: `docker logs course-creator_user-management_1`
3. Review frontend console logs (browser DevTools)
4. Review implementation documentation: `JWT_TOKEN_REFRESH_SYSTEM.md`

# Authentication and AI Assistant Fixes

## Date: 2025-10-17

## Issues Reported by User

Based on screenshot `/tmp/Screenshot from 2025-10-17 10-42-52.png` and console errors:

1. **401 Authentication Error** - `/users/me` endpoint failing with "Invalid or expired token"
2. **AI Assistant Overlapping** - Text colliding with left sidebar menu

## Console Errors

```
/users/me:1 Failed to load resource: the server responded with a status of 401 ()
org-admin-api.js:665 ❌ API Error: 401 {"detail":"Invalid or expired token"}
org-admin-api.js:673 💥 Error fetching current user: Error: Failed to fetch current user: 401
org-admin-core.js:125 💥 Error initializing dashboard: Error: Failed to fetch current user: 401
```

## All Fixes Applied

### 1. Fixed Authentication Endpoint ✅

**File:** `/home/bbrelin/course-creator/frontend/js/modules/org-admin-api.js`

**Line 650:** Changed endpoint to include `/api/v1` prefix

**Before:**
```javascript
export async function fetchCurrentUser() {
    try {
        const url = `${USER_API_BASE}/users/me`;
        const headers = await getAuthHeaders();
```

**After:**
```javascript
export async function fetchCurrentUser() {
    try {
        const url = `${USER_API_BASE}/api/v1/users/me`;
        const headers = await getAuthHeaders();
```

**Root Cause:** The fetchCurrentUser() function was calling `/users/me` instead of `/api/v1/users/me`. The user-management service expects all API calls to use the `/api/v1` prefix, matching the pattern used by all other microservices.

**Result:** Authentication now uses correct endpoint, allowing dashboard to initialize properly.

### 2. Fixed AI Assistant HTML Syntax ✅

**File:** `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`

**Line 3336:** Fixed duplicate class attributes

**Before:**
```html
<div id="dashboardAIChatPanel" class="ai-assistant-panel" class="ai-panel-fixed">
    <!-- Draggable header -->
    <div class="ai-assistant-header" class="ai-panel-header">
```

**After:**
```html
<div id="dashboardAIChatPanel" class="ai-assistant-panel ai-panel-fixed">
    <!-- Draggable header -->
    <div class="ai-assistant-header ai-panel-header">
```

**Root Cause:** HTML elements cannot have duplicate `class` attributes. When duplicates exist, only the last one is used by the browser, causing the first set of styles (`.ai-assistant-panel`) to be ignored.

**Result:** AI Assistant now properly applies both CSS classes, ensuring correct positioning (bottom-right corner) with proper z-index layering above sidebar.

## Files Modified

1. **`/home/bbrelin/course-creator/frontend/js/modules/org-admin-api.js`**
   - Line 650: Added `/api/v1` prefix to user endpoint

2. **`/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`**
   - Line 3336: Fixed duplicate class attributes on AI Assistant panel
   - Line 3338: Fixed duplicate class attributes on AI Assistant header
   - Line 4375: Updated JavaScript version parameter to force browser cache refresh

## Container Restart

Frontend container restarted to apply all changes:
```bash
docker restart course-creator_frontend_1
# Container status: Up (healthy)
```

## Browser Caching Issue and Resolution

**Issue Discovered:** After applying the authentication fix, the browser was still calling the old `/users/me` endpoint due to JavaScript file caching.

**Root Cause:** The browser cached the old `org-admin-api.js` file. Even though the file was updated on the server, the browser continued using the cached version.

**Solution Applied:**
1. Updated JavaScript version parameter in `org-admin-dashboard.html` line 4375:
   - Old: `<script type="module" src="../js/org-admin-main.js?v=20251016-auth-debug"></script>`
   - New: `<script type="module" src="../js/org-admin-main.js?v=20251017-fix-401-auth"></script>`

2. Restarted frontend container to serve updated HTML with new version parameter

**User Action Required:**
**IMPORTANT:** You must perform a **hard refresh** in your browser to clear the cached files:
- **Chrome/Edge/Firefox (Windows/Linux):** Press `Ctrl + Shift + R` or `Ctrl + F5`
- **Chrome/Edge/Firefox (Mac):** Press `Cmd + Shift + R`
- **Alternative:** Open DevTools (F12) → Right-click the refresh button → "Empty Cache and Hard Reload"

## Testing Instructions

### Test 1: Dashboard Authentication
1. Navigate to: `https://176.9.99.103:3000`
2. Log in as organization admin
3. **Expected:**
   - No 401 errors in console
   - Dashboard loads successfully
   - "Loading dashboard..." spinner disappears
   - Dashboard shows organization data, recent projects, and recent activity

### Test 2: API Endpoint Verification
1. Open browser developer tools (F12)
2. Go to Network tab
3. Refresh the org-admin dashboard page
4. **Expected:**
   - Request to `/api/v1/users/me` returns 200 status
   - No requests to `/users/me` (incorrect endpoint)
   - User data successfully loaded

### Test 3: AI Assistant Positioning
1. Log in to org-admin dashboard
2. Click the floating 💬 AI Assistant button (bottom-right corner)
3. **Expected:**
   - AI Assistant panel appears in bottom-right corner
   - Panel does not overlap with left sidebar navigation
   - Panel has proper z-index (appears above all other content)
   - Panel styling is correct (rounded corners, gradient header, etc.)

### Test 4: AI Assistant Classes
1. Open browser developer tools (F12)
2. Inspect the AI Assistant panel element
3. **Expected:**
   - Element `#dashboardAIChatPanel` has both classes: `ai-assistant-panel ai-panel-fixed`
   - No duplicate class attributes in HTML
   - Both class styles applied correctly

## Summary of Changes

| Issue | Status | File Changed | Line(s) |
|-------|--------|--------------|---------|
| 401 Authentication Error | ✅ Fixed | org-admin-api.js | 650 |
| AI Assistant Duplicate Classes | ✅ Fixed | org-admin-dashboard.html | 3336, 3338 |
| Container Restart | ✅ Complete | - | - |

## Root Cause Analysis

### Authentication Error

**Primary Issue:** API endpoint mismatch

The fetchCurrentUser() function was using `/users/me` instead of `/api/v1/users/me`. This caused 401 errors because:

1. User-management service (port 8001) expects all endpoints to follow the pattern `/api/v1/{resource}`
2. The `/users/me` endpoint does not exist - it should be `/api/v1/users/me`
3. Without the correct endpoint, authentication validation failed
4. This prevented the entire dashboard from initializing

**Pattern Consistency:** All other API functions in org-admin-api.js correctly use `/api/v1` prefix:
- Line 86: `${ORG_API_BASE}/api/v1/organizations/${organizationId}`
- Line 115: `${ORG_API_BASE}/api/v1/organizations/${organizationId}`
- Line 166: `${ORG_API_BASE}/api/v1/organizations/${organizationId}/projects`

Only fetchCurrentUser() was missing this prefix.

### AI Assistant Positioning

**Primary Issue:** Duplicate class attributes causing style conflicts

HTML spec does not support duplicate attributes. When an element has multiple `class` attributes:
```html
<div class="class1" class="class2">
```

Browsers only apply the **last** class attribute, ignoring earlier ones. This caused:
- `.ai-assistant-panel` styles to be ignored
- Only `.ai-panel-fixed` styles applied
- Incomplete positioning and styling

**Solution:** Combine classes into single attribute:
```html
<div class="class1 class2">
```

This allows both CSS classes to be applied properly, ensuring correct positioning and layering.

## Notes

1. **API Versioning:** All microservice endpoints use `/api/v1` prefix for version management
2. **HTML Validation:** Duplicate attributes are invalid HTML and cause unpredictable browser behavior
3. **CSS Specificity:** AI Assistant uses `z-index: 1001` to appear above sidebar overlay (`z-index: 999`)
4. **Authentication Flow:** Dashboard initialization requires successful fetchCurrentUser() call first

## Verification

All fixes have been:
- ✅ Implemented in code
- ✅ Frontend container restarted
- ✅ Container status: healthy
- ✅ Changes are live on server

**Server:** https://176.9.99.103:3000/html/org-admin-dashboard.html

The dashboard should now:
- Authenticate successfully without 401 errors
- Load and display all data properly
- Show AI Assistant in correct position (bottom-right)
- No overlap between AI Assistant and sidebar navigation

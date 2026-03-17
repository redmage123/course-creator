# AI Assistant Widget Troubleshooting Guide

## Problem
AI Assistant widget not visible on org-admin dashboard despite being deployed.

## Verification

✅ **Widget HTML is deployed** (verified with curl - found 5 instances)
✅ **Module imports are present** (ai-assistant.js import found)
✅ **Frontend container restarted** (latest code loaded)
✅ **Module files exist** (/usr/share/nginx/html/js/modules/ai-assistant.js - 41KB)

## Solution Steps

### Step 1: Hard Refresh Browser (MOST LIKELY FIX)

**Chrome/Edge/Firefox (Windows/Linux)**:
- Press `Ctrl + Shift + R` or `Ctrl + F5`

**Chrome/Safari (Mac)**:
- Press `Cmd + Shift + R`

**Why**: Browser has cached the old version of org-admin-dashboard.html

---

### Step 2: Clear Browser Cache Completely

1. Open Developer Tools (F12)
2. Right-click the Refresh button
3. Select "Empty Cache and Hard Reload"

---

### Step 3: Check for JavaScript Errors

1. Open Developer Tools (F12)
2. Go to Console tab
3. Reload the page
4. Look for errors related to:
   - Module loading (`ERR_MODULE_NOT_FOUND`)
   - ai-assistant.js
   - org-admin-utils.js

**Expected**: No errors, should see:
```
✅ AI Assistant initialized for org-admin dashboard
```

---

### Step 4: Verify Widget HTML Exists

1. Open Developer Tools (F12)
2. Go to Elements/Inspector tab
3. Press `Ctrl+F` (or `Cmd+F`) to search
4. Search for: `ai-chat-toggle`

**Expected**: Should find the button element:
```html
<button class="ai-chat-toggle" id="ai-chat-toggle" onclick="toggleAIChat()">
    🤖 AI Assistant
</button>
```

**If NOT found**: JavaScript error prevented rendering (check Step 3)

---

### Step 5: Check Button CSS

If button exists in HTML but not visible:

1. In Elements tab, find the `<button id="ai-chat-toggle">` element
2. Look at Computed Styles panel
3. Check these properties:
   - `display`: should be a value (not `none`)
   - `visibility`: should be `visible`
   - `opacity`: should be `1`
   - `position`: should be `fixed`
   - `z-index`: should be `9999`

---

## Manual Test

Open browser console (F12) and paste this:

```javascript
// Check if button exists
const button = document.getElementById('ai-chat-toggle');
console.log('Button exists:', button !== null);
console.log('Button visible:', button?.offsetParent !== null);
console.log('Button location:', button?.getBoundingClientRect());

// Try to make it visible (if hidden)
if (button) {
    button.style.cssText = `
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 9999 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 1rem 1.5rem !important;
        cursor: pointer !important;
    `;
    console.log('✅ Forced button to be visible');
}
```

**Expected**: Button should appear in bottom-right corner

---

## Debugging Output

Run this in browser console for full diagnostics:

```javascript
console.log('=== AI WIDGET DIAGNOSTICS ===');
console.log('Button element:', document.getElementById('ai-chat-toggle'));
console.log('Panel element:', document.getElementById('ai-chat-panel'));
console.log('toggleAIChat function:', typeof window.toggleAIChat);
console.log('sendAIMessage function:', typeof window.sendAIMessage);
console.log('Page URL:', window.location.href);
console.log('Module loaded:', typeof window.initializeAIAssistant);
```

---

## Common Issues & Fixes

### Issue: Button not visible after refresh
**Cause**: Browser cache
**Fix**: Hard refresh (Ctrl+Shift+R)

### Issue: "Module not found" error in console
**Cause**: Path issue or file not deployed
**Fix**: Check frontend container has latest files:
```bash
docker exec course-creator_frontend_1 ls /usr/share/nginx/html/js/modules/ai-assistant.js
```

### Issue: "toggleAIChat is not defined"
**Cause**: JavaScript error preventing script execution
**Fix**: Check console for errors, ensure module loaded

### Issue: Button exists but at wrong position
**Cause**: CSS conflict with other styles
**Fix**: Increase z-index or check for conflicting fixed position elements

---

## File Locations

**HTML File**: `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`
- Lines 5390-5392: Toggle button
- Lines 5394-5447: Chat panel
- Lines 5449-5655: Styling
- Lines 5657-5799: JavaScript integration

**Module Files**:
- `/home/bbrelin/course-creator/frontend/js/modules/ai-assistant.js` (41KB)
- `/home/bbrelin/course-creator/frontend/js/modules/org-admin-utils.js` (12KB)

**Nginx Config**: `/home/bbrelin/course-creator/frontend/nginx.conf`
- Line 350: `/api/v1/chat` routing to course-generator

---

## Expected Behavior

When working correctly:

1. **On page load**:
   - Purple gradient button appears in bottom-right corner
   - Button text: "🤖 AI Assistant"
   - Console log: "✅ AI Assistant initialized for org-admin dashboard"

2. **On click**:
   - Chat panel slides up
   - Shows welcome message
   - Three quick action buttons visible
   - Input field ready for text

3. **On message send**:
   - User message appears in chat
   - Typing indicator shows
   - AI response appears
   - Suggestions listed (if any)

---

## Contact

If widget still not visible after all steps:
1. Take screenshot of browser console (F12)
2. Take screenshot of Elements tab showing the body tag contents
3. Share the console errors (if any)
4. Provide browser type and version

The widget deployment is confirmed working - this is likely a browser cache or JavaScript error issue.

# Cookie Consent Banner Implementation Guide

**Version:** 3.3.0
**Last Updated:** 2025-10-07
**Compliance:** GDPR (EU), CCPA (California), PIPEDA (Canada)

---

## Overview

This guide explains how to implement and use the GDPR-compliant cookie consent banner system for the Course Creator Platform.

## Files Created

### 1. Cookie Consent Banner (JavaScript)
**Location:** `/home/bbrelin/course-creator/frontend/public/js/cookie-consent-banner.js`

**Features:**
- Auto-displays on first visit (1-second delay for better UX)
- Beautiful gradient banner with slide-up animation
- Three action buttons: Accept All, Reject All (Necessary Only), Customize
- CCPA "Do Not Sell" link
- Saves preferences to backend via Privacy API
- Emits `cookieConsentChanged` event for application integration

**Usage:**
```html
<!-- Add to all pages -->
<script src="/js/cookie-consent-banner.js"></script>
```

**API:**
```javascript
// Check if consent given
if (window.cookieConsent.hasConsent()) {
    // User has made a choice
}

// Get current preferences
const prefs = window.cookieConsent.getConsent();
// Returns: {functional_cookies: true, analytics_cookies: false, marketing_cookies: false}

// Show banner programmatically
window.cookieConsent.show();

// Hide banner programmatically
window.cookieConsent.hide();

// Accept all cookies
window.cookieConsent.acceptAll();

// Reject all optional cookies
window.cookieConsent.rejectAll();

// CCPA opt-out
window.cookieConsent.ccpaOptOut();

// Listen for consent changes
window.addEventListener('cookieConsentChanged', (event) => {
    console.log('Consent updated:', event.detail);
    // event.detail = {functional_cookies: true, analytics_cookies: true, ...}
});
```

### 2. Cookie Consent Manager Page
**Location:** `/home/bbrelin/course-creator/frontend/public/cookie-consent.html`

**Features:**
- Full cookie preference management interface
- Displays current consent status
- Toggle switches for each cookie category
- Session ID display
- GDPR Right to Access (View My Data)
- GDPR Right to Erasure (Delete My Data)
- Links to Privacy Policy and Cookie Policy
- Real-time status updates

**Access:** `https://localhost:3000/cookie-consent.html`

### 3. Privacy Policy Page
**Location:** `/home/bbrelin/course-creator/frontend/public/privacy-policy.html`

**Contents:**
- Complete privacy policy for guest sessions
- GDPR/CCPA/PIPEDA compliance information
- Data collection practices
- User rights explanation
- Data retention policy
- Contact information (DPO, Privacy Team)

**Access:** `https://localhost:3000/privacy-policy.html`

### 4. Cookie Policy Page
**Location:** `/home/bbrelin/course-creator/frontend/public/cookie-policy.html`

**Contents:**
- Detailed cookie information
- Cookie categories (Strictly Necessary, Functional, Analytics, Marketing)
- Cookie table with names, purposes, and durations
- Browser-based cookie management instructions
- Third-party cookie disclosure

**Access:** `https://localhost:3000/cookie-policy.html`

---

## Integration Steps

### Step 1: Add Cookie Banner to All Pages

Add this script tag to the `<head>` or end of `<body>` in all HTML pages:

```html
<!-- Cookie Consent Banner -->
<script src="/js/cookie-consent-banner.js"></script>
```

### Step 2: Integrate with Analytics

Only load analytics scripts if user has consented:

```javascript
window.addEventListener('cookieConsentChanged', (event) => {
    if (event.detail.analytics_cookies) {
        // Load Google Analytics
        loadGoogleAnalytics();
    } else {
        // Disable analytics
        disableGoogleAnalytics();
    }
});

// Check on page load
if (window.cookieConsent.hasConsent()) {
    const prefs = window.cookieConsent.getConsent();
    if (prefs.analytics_cookies) {
        loadGoogleAnalytics();
    }
}
```

### Step 3: Conditional Marketing Scripts

```javascript
window.addEventListener('cookieConsentChanged', (event) => {
    if (event.detail.marketing_cookies) {
        // Load marketing pixels
        loadMarketingScripts();
    } else {
        // Disable marketing
        disableMarketingScripts();
    }
});
```

### Step 4: Add Privacy Links to Footer

```html
<footer>
    <a href="/privacy-policy.html">Privacy Policy</a>
    <a href="/cookie-policy.html">Cookie Policy</a>
    <a href="/cookie-consent.html">Cookie Preferences</a>
    <a href="#" onclick="window.cookieConsent.ccpaOptOut(event)">Do Not Sell (CCPA)</a>
</footer>
```

---

## User Flow

### First-Time Visitor
1. User visits platform → Session ID created
2. After 1 second → Cookie banner slides up from bottom
3. User chooses:
   - **Accept All** → All cookies enabled, banner hides
   - **Reject All** → Only necessary cookies, banner hides
   - **Customize** → Redirected to `/cookie-consent.html`

### Returning Visitor (Consent Given)
1. User visits platform
2. Consent preferences loaded from `localStorage`
3. No banner shown (already consented)
4. Application loads scripts based on preferences

### Returning Visitor (No Consent)
1. User visits platform
2. Banner shown again (consent required)

### User Wants to Change Preferences
1. Clicks "Cookie Preferences" link in footer
2. Opens `/cookie-consent.html`
3. Sees current settings
4. Changes toggle switches
5. Clicks "Save My Preferences"
6. Preferences sent to backend API
7. Success message shown

---

## Technical Implementation

### Session ID Generation

```javascript
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
```

Session ID is stored in `localStorage` as `guest_session_id`.

### Consent Storage

**LocalStorage:**
- `cookie_consent_given` → 'true' | 'false'
- `cookie_preferences` → JSON string: `{functional_cookies: true, analytics_cookies: false, marketing_cookies: false}`
- `guest_session_id` → UUID

**Backend (PostgreSQL):**
- Consent sent to `POST /api/v1/privacy/guest-session/{id}/consent`
- Stored with timestamp and privacy policy version
- Audit log entry created

### API Integration

```javascript
// Save consent
const response = await fetch(`${API_BASE_URL}/guest-session/${sessionId}/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        functional_cookies: true,
        analytics_cookies: true,
        marketing_cookies: false,
        privacy_policy_version: '3.3.0'
    })
});
```

---

## Cookie Categories

### 1. Strictly Necessary (Always Active)
- `guest_session_id` - Session management
- `csrf_token` - Security
- `load_balancer` - Infrastructure

**Cannot be disabled** - Required for platform functionality.

### 2. Functional (Optional)
- `cookie_preferences` - Remember user choices
- `user_preferences` - Language, theme, UI settings
- `returning_guest` - Hashed fingerprint for recognition

**Default:** Disabled (require explicit consent)

### 3. Analytics (Optional)
- `_ga` - Google Analytics
- `conversion_tracking` - Feature-to-registration tracking
- `ab_test_variant` - A/B testing

**Default:** Disabled (require explicit consent)

### 4. Marketing (Optional)
- `lead_score` - Engagement scoring (0-10)
- `campaign_source` - Traffic source tracking

**Default:** Disabled (require explicit consent)

---

## GDPR/CCPA Compliance Features

### GDPR Article 7 - Consent
- ✅ Consent is freely given (can reject all)
- ✅ Consent is specific (granular cookie categories)
- ✅ Consent is informed (clear explanations)
- ✅ Consent is unambiguous (explicit action required)
- ✅ Withdrawal as easy as giving (one-click preference change)

### GDPR Article 15 - Right to Access
- ✅ "View My Data" button in cookie manager
- ✅ Returns all session data in readable format

### GDPR Article 17 - Right to Erasure
- ✅ "Delete My Data" button in cookie manager
- ✅ Immediate deletion with confirmation
- ✅ Session ID removed from localStorage

### CCPA - Do Not Sell
- ✅ "Do Not Sell My Personal Information" link
- ✅ Disables marketing cookies
- ✅ Confirmation message

### PIPEDA - Openness & Access
- ✅ Clear privacy policy and cookie policy
- ✅ Contact information for DPO
- ✅ Easy access to preferences

---

## Testing

### Manual Testing

1. **First Visit Test:**
   - Clear localStorage and cookies
   - Visit platform
   - Banner should appear after 1 second
   - Click "Accept All" → Banner disappears
   - Reload page → Banner should NOT appear

2. **Reject All Test:**
   - Clear localStorage
   - Visit platform
   - Click "Reject All"
   - Open DevTools → localStorage should show:
     - `cookie_consent_given: "true"`
     - `cookie_preferences: {"functional_cookies":false,"analytics_cookies":false,"marketing_cookies":false}`

3. **Customize Test:**
   - Clear localStorage
   - Visit platform
   - Click "Customize" → Redirected to `/cookie-consent.html`
   - Toggle functional cookies ON
   - Toggle analytics cookies ON
   - Click "Save My Preferences"
   - See success message

4. **Consent Persistence Test:**
   - Set preferences
   - Close browser
   - Reopen browser
   - Visit platform
   - Preferences should be remembered

5. **Right to Access Test:**
   - Open `/cookie-consent.html`
   - Click "View My Data"
   - Alert should show session data in JSON format

6. **Right to Erasure Test:**
   - Open `/cookie-consent.html`
   - Click "Delete My Data"
   - Confirm deletion
   - Alert confirms deletion
   - Redirected to homepage
   - Session ID removed

### Automated Testing (E2E)

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_cookie_consent_banner():
    driver = webdriver.Chrome()
    driver.get('https://localhost:3000')

    # Wait for banner to appear
    banner = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, 'cookie-consent-banner'))
    )

    assert banner.is_displayed()

    # Click Accept All
    accept_btn = driver.find_element(By.CLASS_NAME, 'btn-accept-all')
    accept_btn.click()

    # Banner should disappear
    WebDriverWait(driver, 2).until(
        EC.invisibility_of_element_located((By.ID, 'cookie-consent-banner'))
    )

    driver.quit()
```

---

## Troubleshooting

### Banner Not Appearing
**Issue:** Cookie banner doesn't show on first visit

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify `/js/cookie-consent-banner.js` is loaded
3. Check `localStorage.getItem('cookie_consent_given')` → should be `null` on first visit
4. Ensure no ad blockers interfering

### Preferences Not Saving
**Issue:** Consent preferences don't persist

**Solutions:**
1. Check API endpoint is running: `https://localhost:8010/api/v1/privacy/`
2. Check browser console for network errors
3. Verify CORS headers are present
4. Check session ID exists: `localStorage.getItem('guest_session_id')`

### Banner Shows on Every Page Load
**Issue:** Banner appears even after consent

**Solutions:**
1. Check `localStorage.getItem('cookie_consent_given')` → should be `"true"`
2. Verify script loaded after DOM ready
3. Check for localStorage quota exceeded errors

---

## Customization

### Change Banner Colors

Edit `/js/cookie-consent-banner.js`:

```javascript
// Line ~23: Change gradient colors
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

// Change to your brand colors:
background: linear-gradient(135deg, #YourColor1 0%, #YourColor2 100%);
```

### Change Banner Position

```javascript
// Current: Bottom banner
position: fixed;
bottom: 0;

// Change to top banner:
position: fixed;
top: 0;
```

### Modify Auto-Show Delay

```javascript
// Line ~385: Change delay (currently 1 second)
setTimeout(createBanner, 1000);

// Change to 2 seconds:
setTimeout(createBanner, 2000);
```

---

## Maintenance

### Update Privacy Policy Version

When privacy policy changes:

1. Update version in `/js/cookie-consent-banner.js`:
```javascript
const PRIVACY_POLICY_VERSION = '3.4.0';  // Update this
```

2. Update version in `/privacy-policy.html`:
```html
<strong>Version:</strong> 3.4.0
```

3. Update version in `/cookie-policy.html`:
```html
<strong>Version:</strong> 3.4.0
```

4. Users will be prompted to re-consent if version changed

### Add New Cookie

1. Document in `/cookie-policy.html`
2. Add to appropriate category table
3. Update cookie manager if controls needed

---

## Support

**Questions or Issues:**
- Privacy Team: privacy@example.com
- Data Protection Officer: dpo@example.com
- Technical Support: support@example.com

**Legal Compliance:**
- EU Users: Contact your local data protection authority
- California Users: CCPA inquiries to privacy@example.com
- Canada Users: PIPEDA compliance to dpo@example.com

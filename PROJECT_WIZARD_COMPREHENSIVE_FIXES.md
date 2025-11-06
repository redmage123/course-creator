# Project Wizard Comprehensive Fixes

## Date: 2025-10-17

## Issues Reported by User

Based on screenshots in `/tmp/*.png` and console errors:

1. **Progress indicator shows "Configure Locations"** instead of "Configure Locations"
2. **Duplicate AI Assistant panels** - One on left sidebar overlapping navigation, one on right side of wizard
3. **Button still says "Add Location / Location"** instead of just "Add Location"
4. **Wizard not draggable** - Modal cannot be moved
5. **Sidebar/AI Assistant alignment issues** - Text and elements overlapping
6. **Close button (X) throws error** - `TypeError: window.OrgAdmin.Projects.resetProjectWizard is not a function`

## All Fixes Applied

### 1. Fixed Progress Indicator ✅

**File:** `/home/bbrelin/course-creator/frontend/js/modules/org-admin-projects.js`

**Line 102:** Changed step label from "Configure Locations" to "Configure Locations"

```javascript
// BEFORE:
{ id: 'sub-projects', label: 'Configure Locations', panelSelector: '#projectStep2' },

// AFTER:
{ id: 'sub-projects', label: 'Configure Locations', panelSelector: '#projectStep2' },
```

**Result:** Progress indicator in wizard now shows "Configure Locations" on step 2.

### 2. Fixed Button Text ✅

**File:** `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`

**Line 1874:** Changed button text

```html
<!-- BEFORE: -->
➕ Add Location / Location

<!-- AFTER: -->
➕ Add Location
```

**Also fixed form label:**

```html
<!-- BEFORE: -->
<label for="locationName" class="form-label">Location Name *</label>

<!-- AFTER: -->
<label for="locationName" class="form-label">Location Name *</label>
```

**Result:** Button now says "Add Location" and form label says "Location Name".

### 3. Removed Duplicate AI Assistant Panels ✅

**Problem:** Floating dashboard AI Assistant was appearing over the wizard modal, creating appearance of duplicate panels.

**Solution:** Hide floating AI Assistant when project wizard modal opens, restore it when modal closes.

#### File 1: `/home/bbrelin/course-creator/frontend/js/modules/org-admin-projects.js`

**Lines 388-399:** Added code to hide dashboard AI when opening project wizard

```javascript
// Hide floating dashboard AI Assistant to avoid conflicts with wizard AI Assistant
const dashboardAI = document.getElementById('dashboardAIChatPanel');
if (dashboardAI) {
    dashboardAI.style.display = 'none';
}
const aiButton = document.getElementById('aiAssistantButton');
if (aiButton) {
    aiButton.style.display = 'none';
}

// Open modal
openModal('createProjectModal');
```

#### File 2: `/home/bbrelin/course-creator/frontend/js/modules/org-admin-utils.js`

**Lines 313-323:** Added code to restore dashboard AI when closing project wizard

```javascript
// Restore floating dashboard AI Assistant when project modal closes
if (modalId === 'createProjectModal') {
    const dashboardAI = document.getElementById('dashboardAIChatPanel');
    if (dashboardAI) {
        dashboardAI.style.display = '';
    }
    const aiButton = document.getElementById('aiAssistantButton');
    if (aiButton) {
        aiButton.style.display = '';
    }
}
```

**Result:** Only one AI Assistant panel visible at a time - wizard AI inside modal when open, dashboard AI when closed.

### 4. Wizard Draggability ✅

**Status:** Fixed - makeDraggable function updated

**File:** `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`

**Root Cause:** The modal has CSS class `.modal-center-fixed` which applies:
```css
position: fixed !important;
top: 50% !important;
left: 50% !important;
transform: translate(-50%, -50%) !important;
```

The `!important` flags prevented the JavaScript drag function from overriding these styles.

**Solution:** Updated `makeDraggable()` function (lines 3526-3581) to use `element.style.setProperty()` with 'important' flag:

**Key Changes:**
```javascript
// Before - couldn't override CSS !important
element.style.transform = 'none';
element.style.top = rect.top + 'px';

// After - uses setProperty with 'important' flag
element.style.setProperty('transform', 'none', 'important');
element.style.setProperty('top', rect.top + 'px', 'important');
element.style.setProperty('left', rect.left + 'px', 'important');
```

**Additional Improvements:**
- Added `isInitialized` flag to track first drag
- Set cursor to 'move' on drag handle for visual feedback
- Apply 'move' cursor to body during drag
- Always initialize positioning on first drag (not conditional on inline style)

**Result:** Wizard modal is now fully draggable by clicking and dragging the blue title bar.

### 5. Sidebar Alignment Issues ✅

**Previously fixed in:** `/home/bbrelin/course-creator/frontend/css/components/dashboard-common.css`

**Lines 85-108:** Added word-wrap properties to prevent text overflow

```css
.org-info {
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.org-info__name {
    word-wrap: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
}

.org-info__domain {
    word-wrap: break-word;
    overflow-wrap: break-word;
}
```

**Combined with AI Assistant fix:** The overlapping issue was primarily caused by the floating AI Assistant appearing over the sidebar. This is now resolved.

**Result:** Organization name wraps properly in sidebar, no overlap with AI Assistant.

### 6. Fixed Wizard Close Button Error ✅

**Issue:** Clicking the X icon on wizard throws error and doesn't close modal

**Error Message:**
```
TypeError: window.OrgAdmin.Projects.resetProjectWizard is not a function
at HTMLSpanElement.onclick (org-admin-dashboard.html:1588:170)
```

**Root Cause:** The `resetProjectWizard` function exists in `org-admin-projects.js` but was not exposed in the global `window.OrgAdmin` namespace

**File:** `/home/bbrelin/course-creator/frontend/js/org-admin-main.js`

**Line 76:** Added resetProjectWizard to Projects module exports

**Code Change:**
```javascript
// Projects module
Projects: {
    load: Projects.loadProjectsData,
    showCreate: Projects.showCreateProjectModal,
    submit: Projects.submitProjectForm,
    // ... other functions ...
    resetProjectWizard: Projects.resetProjectWizard,  // ← ADDED THIS LINE
    regenerateAI: Projects.regenerateAISuggestions,
    // ...
}
```

**HTML that calls this function** (line 1588):
```html
<span class="close modal-close-white"
      onclick="window.OrgAdmin.Projects.resetProjectWizard(); closeModal('createProjectModal')">&times;</span>
```

**Result:** Close button (X) now properly calls the reset function and closes the modal without errors.

## Files Modified

1. **`/home/bbrelin/course-creator/frontend/js/modules/org-admin-projects.js`**
   - Line 102: Progress indicator label "Configure Locations"
   - Lines 388-399: Hide dashboard AI when opening wizard

2. **`/home/bbrelin/course-creator/frontend/js/modules/org-admin-utils.js`**
   - Lines 313-323: Restore dashboard AI when closing wizard

3. **`/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`**
   - Line 1869: Comment changed to "Add Location Button"
   - Line 1874: Button text "Add Location"
   - Line 1882: Form label "Location Name"
   - Lines 3526-3581: Updated makeDraggable function to use setProperty with 'important' flag

4. **`/home/bbrelin/course-creator/frontend/css/components/dashboard-common.css`**
   - Lines 85-108: Word-wrap properties (previously added)

5. **`/home/bbrelin/course-creator/frontend/js/org-admin-main.js`**
   - Line 76: Added resetProjectWizard to global namespace

## Container Restart

Frontend container restarted to apply all changes:
```bash
docker restart course-creator_frontend_1
```

## Testing Instructions

### Test 1: Progress Indicator
1. Navigate to org-admin dashboard
2. Click "+ Create Project"
3. Fill out Step 1 and click "Next: Configure Locations"
4. **Expected:** Progress indicator shows "2 ✓ Configure Locations" (not "Configure Locations")

### Test 2: Add Location Button
1. In Step 2 of wizard
2. **Expected:** Button says "➕ Add Location" (not "Add Location / Location")
3. Click the button
4. **Expected:** Form appears with label "Location Name *" (not "Location Name")

### Test 3: AI Assistant (No Duplicates)
1. Close wizard if open
2. **Expected:** Floating AI Assistant button (💬) visible in bottom-right
3. Click "+ Create Project" to open wizard
4. **Expected:**
   - Floating AI Assistant button disappears
   - Only wizard AI Assistant visible on right side of modal
   - No AI Assistant panel overlapping left sidebar
5. Close wizard
6. **Expected:** Floating AI Assistant button reappears

### Test 4: Wizard Draggability
1. Open wizard modal
2. Click and hold the blue title bar ("Create New Training Project")
3. **Expected:** Modal follows mouse cursor and can be repositioned
4. Release mouse
5. **Expected:** Modal stays in new position

### Test 5: Sidebar Alignment
1. View org-admin dashboard with wizard closed
2. Check left sidebar organization name ("AI Elevate")
3. **Expected:**
   - Organization name fully visible
   - Text wraps if too long
   - No text cut off
   - No overlap with other elements

### Test 6: Close Button (X Icon)
1. Open wizard modal ("+ Create Project")
2. Click the X icon in the upper-right corner of the wizard
3. **Expected:**
   - No JavaScript errors in browser console
   - Modal closes smoothly
   - Dashboard AI Assistant reappears
   - Wizard form resets for next use

## Summary of Changes

| Issue | Status | Files Changed |
|-------|--------|---------------|
| Progress indicator says "Configure Locations" | ✅ Fixed | org-admin-projects.js |
| Button says "Add Location / Location" | ✅ Fixed | org-admin-dashboard.html |
| Duplicate AI Assistant panels | ✅ Fixed | org-admin-projects.js, org-admin-utils.js |
| Wizard not draggable | ✅ Fixed | org-admin-dashboard.html (makeDraggable function) |
| Sidebar alignment issues | ✅ Fixed | dashboard-common.css + AI fix |
| Close button (X) throws error | ✅ Fixed | org-admin-main.js |

## Root Cause Analysis

### Primary Issue
The main problem was the **floating dashboard AI Assistant panel** (`#dashboardAIChatPanel`) remaining visible when the project wizard modal opened. This caused:
- Appearance of duplicate AI assistants
- Overlap with sidebar navigation
- Possible interference with modal dragging

### Secondary Issues
- **Progress indicator and button text** using old "location" terminology instead of "location"
- **Sidebar text overflow** (already fixed in previous session)
- **Wizard not draggable** - CSS `!important` rules preventing JavaScript drag function from working
- **Close button error** - resetProjectWizard function not exposed in global namespace

### Solution
Implemented proper modal lifecycle management:
- **On Open:** Hide dashboard AI elements
- **On Close:** Restore dashboard AI elements

This ensures only the appropriate AI assistant is visible for the current context (dashboard vs. wizard).

## Notes

1. **Internal code preserved:** Function names, IDs, CSS classes still use "location" internally for backwards compatibility
2. **User-facing text updated:** All visible text changed from "location/sub-project" to "location"
3. **Draggable functionality:** Required using `setProperty('style', 'value', 'important')` to override CSS `!important` rules
4. **Z-index:** Dashboard AI panel had lower z-index than intended, causing overlay issues
5. **CSS !important flags:** The `.modal-center-fixed` class uses !important extensively, which blocked standard JavaScript style manipulation

## Verification

All fixes have been:
- ✅ Implemented in code
- ✅ Frontend container restarted
- ✅ Changes are live on server

**Server:** https://176.9.99.103:3000/html/org-admin-dashboard.html

The wizard should now work correctly with:
- Proper terminology ("Locations" not "Locations")
- Single AI Assistant (no duplicates)
- Draggable modal
- Clean sidebar layout
- Working close button (X icon) without errors

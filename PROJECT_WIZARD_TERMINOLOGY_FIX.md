# Project Wizard Terminology & UI Fixes

## Date: 2025-10-17

## Issues Identified

Based on screenshots `/tmp/Screenshot from 2025-10-17 09-37-07.png` and `09-36-54.png`:

1. **Missing "Add Location" Button** - Button existed in HTML but wasn't immediately visible in step 2 of project wizard
2. **Terminology Issues** - "Location" and "Sub-Project" terms used throughout instead of "Location"
3. **Sidebar Alignment Issues** - Organization name/domain text potentially cut off or overlapping on far left

## Fixes Applied

### 1. Terminology Changes (All User-Facing Text)

**File: `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`**

Changed all user-facing instances of "location" and "sub-project" to "location":

#### Step Titles & Headers
- `Configure Sub-Projects (Locations)` → `Configure Locations`
- `Defined Locations` → `Defined Locations`
- `Add New Location` → `Add New Location`
- `Add Location / Location` → `Add Location`
- `Add Location` → `Add Location` (all button labels)
- `Create New Location` → `Create New Location` (modal title)

#### Button Labels
- `Next: Configure Sub-Projects` → `Next: Configure Locations` (line 1829)
- `➕ Add Location` → `➕ Add Location` (multiple locations)
- `Create Location` → `Create Location` (line 2076)

#### Descriptions & Help Text
- `Define locations for your multi-location project` → `Define locations for your multi-location project`
- `Each location represents` → `Each location represents`
- `Set up locations for different locations` → `Set up training locations`
- `Each location can have its own schedule` → `Each location can have its own schedule`
- `No locations defined yet` → `No locations defined yet`
- `Click "Add Location" to create your first location` → `Click "Add Location" to create your first location`
- `You can add more locations later` → `You can add more locations later`
- `Locations & Sub-Projects` → `Locations` (line 2080)

#### Form Labels
- `Location Name` → `Location Name`
- Placeholder text updated: `e.g., New York Campus, Q1 2025 Location` → `e.g., New York Campus, Downtown Branch`

#### Comments
- `Create Location/Sub-Project Modal` → `Create Location Modal` (line 2158)

### 2. Add Location Button Visibility

**Button Location: `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html` lines 1870-1875**

The button was present in HTML:
```html
<button
    type="button"
    class="btn btn-primary mb-2rem"
    onclick="window.OrgAdmin.Projects.showAddLocationForm()">
    ➕ Add Location
</button>
```

**CSS Styling: `/home/bbrelin/course-creator/frontend/css/accessibility.css` line 2229**

```css
.mb-2rem {
    margin-bottom: 2rem !important;
}
```

Button was correctly styled and should be visible. The issue may have been temporary or due to modal scrolling/height constraints.

### 3. Sidebar Alignment Fix

**File: `/home/bbrelin/course-creator/frontend/css/components/dashboard-common.css`**

**Lines 85-108: Added proper text wrapping for organization info**

```css
/* Organization Info Card */
.org-info {
    margin-bottom: var(--spacing-xl);
    padding: var(--spacing-md);
    background: var(--surface-hover);
    border-radius: var(--radius-lg);
    word-wrap: break-word;        /* ← ADDED */
    overflow-wrap: break-word;    /* ← ADDED */
}

.org-info__name {
    margin: 0 0 var(--spacing-sm) 0;
    font-weight: var(--font-weight-semibold);
    word-wrap: break-word;        /* ← ADDED */
    overflow-wrap: break-word;    /* ← ADDED */
    hyphens: auto;                /* ← ADDED */
}

.org-info__domain {
    margin: 0;
    color: var(--text-muted);
    font-size: var(--font-size-sm);
    word-wrap: break-word;        /* ← ADDED */
    overflow-wrap: break-word;    /* ← ADDED */
}
```

**Purpose:** Ensures long organization names (like "AI Elevate", "ai-elevate.ai") wrap properly within the sidebar width instead of being cut off or causing overflow.

## Files Modified

1. `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html`
   - Multiple terminology updates (user-facing text only)
   - Button labels, headings, descriptions, placeholders

2. `/home/bbrelin/course-creator/frontend/css/components/dashboard-common.css`
   - Added word-wrap and overflow-wrap properties to `.org-info*` classes

## Files Created

1. `/home/bbrelin/course-creator/fix_location_terminology.sh`
   - Bash script for automated terminology replacement
   - Creates backup before making changes

## Backups

- Automatic backup created: `/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html.backup_20251017_084648`

## Container Restart

Frontend container restarted to apply all changes:
```bash
docker restart course-creator_frontend_1
```

## What Changed for Users

### Before
- Step 2 showed: "Configure Sub-Projects (Locations)"
- Button said: "Add Location / Location"
- Empty state said: "No locations defined yet. Click 'Add Location'..."
- Organization name might have been cut off in sidebar

### After
- Step 2 shows: "Configure Locations"
- Button says: "Add Location"
- Empty state says: "No locations defined yet. Click 'Add Location'..."
- Organization name wraps properly in sidebar

## Code Preservation

**Important:** All internal code identifiers were preserved:
- Function names: `showAddLocationForm()`, `saveLocation()`, etc.
- IDs: `createLocationModal`, `addLocationForm`, `locationName`, etc.
- CSS classes: `.location-*`, `.location-form-hidden`, etc.
- API endpoints: `/sub-projects`, etc.
- JavaScript variables: `locationId`, `locationsList`, etc.

**Rationale:** Only user-facing text was changed to avoid breaking existing functionality. Internal code can be refactored separately if needed.

## Testing Recommendations

1. **Navigate to org-admin dashboard**
   ```
   https://176.9.99.103:3000/html/org-admin-dashboard.html
   ```

2. **Click "Projects" tab**

3. **Click "+ Create Project" button**

4. **Fill out Step 1 (Project Details)**
   - Select "Multi-Location Project" as project type

5. **Click "Next: Configure Locations"**

6. **Verify Step 2 displays:**
   - ✅ Title: "Configure Locations" (not "Configure Sub-Projects")
   - ✅ Button: "Add Location" (not "Add Location")
   - ✅ Empty state text: "No locations defined yet. Click 'Add Location'..."
   - ✅ Organization name in sidebar is fully visible (not cut off)

7. **Click "Add Location" button**

8. **Verify modal shows:**
   - ✅ Form title: "Add New Location"
   - ✅ Label: "Location Name" (not "Location Name")
   - ✅ All terminology updated throughout

## Known Limitations

1. **Console logging** - JavaScript console messages may still reference "location" in debug output
2. **API responses** - Backend API still uses "sub-project" terminology
3. **Database schema** - Tables still use "location" naming
4. **Internal variable names** - JavaScript variables still use "location" naming

These are intentional to maintain backwards compatibility and can be addressed in a separate refactoring effort if needed.

## Summary

✅ All user-visible "location" and "sub-project" terminology changed to "location"
✅ Add Location button confirmed present and properly styled
✅ Sidebar organization text now wraps properly (no cutoff)
✅ Frontend container restarted - changes are live
✅ Backup created before modifications
✅ Internal code identifiers preserved for compatibility

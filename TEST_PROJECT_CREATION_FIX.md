# Manual Test Instructions for Project Creation Fix

## Overview
Test that the 422 API error fix allows successful project creation through the UI.

---

## Test Setup

**Prerequisites**:
- Browser open with Developer Tools (F12)
- Logged in as organization admin
- Console tab visible in Developer Tools

**Test Organization**:
- ID: `259da6df-c148-40c2-bcd9-dc6889e7e9fb`

---

## Test Procedure

### Step 1: Open Project Creation Wizard

1. Navigate to: `https://localhost:3000` (or `http://localhost:3001`)
2. Log in as organization admin
3. Click "Projects" tab
4. Click "Create New Project" button

**Expected**: Wizard modal opens to Step 1

---

### Step 2: Fill Project Details (Step 1)

Fill in the following **exactly** (to match test data):

- **Project Name**: `Test Project - API Fix Verification`
- **URL Slug**: `test-project-api-fix-2024`
- **Description**: `This is a test project to verify the 422 API error fix is working correctly. The description must be at least 10 characters.`
- **Target Roles**: Select 2-3 roles (e.g., "Junior Developer", "Senior Developer")
- **Duration (weeks)**: `12`
- **Max Participants**: `30`
- **Start Date**: `2024-11-01`
- **End Date**: `2025-01-31`
- **Project Type**: Single location (or multi-location if you want to test that)

**Click**: "Next" button

**Expected**:
- No errors
- Advances to Step 2

---

### Step 3: Configure Locations (Step 2)

If **single location**: Just click "Next"

If **multi-location**: Add one or more locations, then click "Next"

**Expected**:
- Advances to Step 3

---

### Step 4: Configure Training Tracks (Step 3)

**What to verify**:
1. ✅ Auto-generated tracks appear immediately
2. ✅ Tracks display for each target role selected in Step 1
3. ✅ Summary box has **blue gradient** styling (not flat colors)
4. ✅ "Add Custom Track" button visible

**Click**: "Next: Review & Create"

**Expected**:
- Advances to Step 4

---

### Step 5: Review & Confirm (Step 4)

**Review** the project details

**Open Browser Console** (F12 → Console tab)

**Click**: "Create Project & Tracks" button

---

### Step 6: Monitor Console Output

## ✅ SUCCESS INDICATORS

**Watch for these console messages in order**:

```
📋 Project data prepared for API: {name: "Test Project - API Fix Verification", ...}
📤 Sending project creation request: {name: "Test Project - API Fix Verification", ...}
```

**Check the payload**:
- ✅ Should have: `name`, `slug`, `description`, `target_roles`, `duration_weeks`, `max_participants`, `start_date`, `end_date`, `selected_track_templates`
- ❌ Should NOT have: `objectives`, `has_sub_projects`, `locations`, `tracks`

```
✅ Project created successfully: {id: "...", name: "...", ...}
📋 Creating N tracks for project...
✅ Project creation completed successfully!
```

**UI Response**:
- ✅ Success notification appears
- ✅ Modal closes
- ✅ Project appears in project list
- ✅ No error messages

---

## ❌ FAILURE INDICATORS

If you see these, the fix **did not work**:

### 422 Validation Error (Old Problem)

**Console shows**:
```
❌ API Error Response: {detail: [{loc: [...], msg: "..."}]}
📋 Validation Details:
Validation Error:
  • body.objectives: extra fields not permitted
  • body.locations: extra fields not permitted
  • body.tracks: extra fields not permitted
```

**This means**: The invalid fields are still being sent

**Action**: Report this error with the full console output

---

### Other Errors

**400 Bad Request**: Invalid data format
**401 Unauthorized**: Authentication issue
**403 Forbidden**: Permission issue
**500 Internal Server Error**: Backend crash

**Action**: Report the error with console output and network tab details

---

## Verification Checklist

After testing, verify:

- [ ] Project created successfully (visible in project list)
- [ ] No 422 error in console
- [ ] Console shows corrected payload (without invalid fields)
- [ ] Tracks created and associated with project
- [ ] Success notification appeared
- [ ] Modal closed automatically

---

## Expected Console Output (Success)

```javascript
// Step 1: Data preparation
📋 Project data prepared for API: {
  name: "Test Project - API Fix Verification",
  slug: "test-project-api-fix-2024",
  description: "This is a test project to verify...",
  target_roles: ["junior_developer", "senior_developer"],
  duration_weeks: 12,
  max_participants: 30,
  start_date: "2024-11-01",
  end_date: "2025-01-31",
  selected_track_templates: []
}

// Step 2: Sending request
📤 Sending project creation request: {...}

// Step 3: Success response
✅ Project created successfully: {
  id: "uuid-here",
  name: "Test Project - API Fix Verification",
  slug: "test-project-api-fix-2024",
  ...
}

// Step 4: Track creation
📋 Creating 2 tracks for project...
✅ Track created: Junior Developer Learning Path
✅ Track created: Senior Developer Learning Path

// Step 5: Completion
✅ Project creation completed successfully!
```

---

## Alternative: Quick Test via Browser Console

If you want to test just the API call directly:

1. Open browser to `https://localhost:3000`
2. Log in as org admin
3. Open Console (F12 → Console)
4. Paste this code:

```javascript
// Test project creation with corrected payload
const testProjectCreation = async () => {
    const orgId = '259da6df-c148-40c2-bcd9-dc6889e7e9fb';
    const payload = {
        name: "Test Project - Console Test",
        slug: "test-console-" + Date.now(),
        description: "Testing from browser console - this description is long enough to meet the 10 character minimum.",
        target_roles: ["junior_developer"],
        duration_weeks: 8,
        max_participants: 20,
        start_date: "2024-11-15",
        end_date: "2025-01-15",
        selected_track_templates: []
    };

    console.log('📤 Testing project creation...');
    console.log('Payload:', payload);

    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`https://localhost:8008/api/v1/organizations/${orgId}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        console.log('Status:', response.status);
        const data = await response.json();
        console.log('Response:', data);

        if (response.ok) {
            console.log('✅ SUCCESS: Project created!');
        } else {
            console.log('❌ ERROR:', data);
        }
    } catch (error) {
        console.error('❌ Request failed:', error);
    }
};

// Run the test
testProjectCreation();
```

**Expected output**:
```
📤 Testing project creation...
Payload: {name: "...", slug: "..."}
Status: 200
Response: {id: "...", name: "...", ...}
✅ SUCCESS: Project created!
```

---

## Reporting Results

Please report back with:

1. ✅ **Success** or ❌ **Failure**
2. Screenshot of browser console output
3. Any error messages (full text)
4. Network tab response (if error occurred)

---

## Troubleshooting

### "Organization not found"
- Check you're logged in as admin of org `259da6df-c148-40c2-bcd9-dc6889e7e9fb`
- Or use your actual organization ID

### "Slug already exists"
- Change the slug to something unique: `test-project-api-fix-` + current timestamp
- e.g., `test-project-api-fix-20241019-1430`

### "Description too short"
- Ensure description is at least 10 characters
- Current test description is 96 characters (valid)

### Network timeout
- Check all Docker services are running: `docker-compose ps`
- Ensure organization-management service is healthy
- Check browser network tab for actual error

---

## Summary

This test verifies that:
1. Frontend sends correct payload (no extra fields)
2. API accepts the payload (no 422 error)
3. Project creates successfully
4. Tracks associate correctly
5. Error logging shows helpful details (if error occurs)

The fix is working if you get a **200 OK** response and see the project in your project list!

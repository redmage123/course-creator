# Bug Catalog - Regression Test Documentation

## Overview

This catalog documents all bugs that have been fixed in the Course Creator Platform and are covered by regression tests. Each entry provides complete information about the bug, its fix, and the test that prevents it from recurring.

**Last Updated**: 2025-11-05
**Total Bugs Documented**: 15
**Total Regression Tests**: 15
**Critical Bugs**: 7
**High Priority Bugs**: 5
**Medium Priority Bugs**: 3

---

## Critical Bugs (Severity: Critical)

### BUG-001: Org Admin Login Redirect Delay (10-12 seconds)
- **Severity**: Critical
- **Date Discovered**: 2025-10-07
- **Date Fixed**: 2025-10-08
- **Version Introduced**: v3.3.0
- **Version Fixed**: v3.3.1
- **Services Affected**: user-management, frontend
- **Git Commit**: dc9c18e242b0fa8ddc49d842a165591dcdbdf04a
- **Test File**: `tests/regression/python/test_auth_bugs.py::test_bug_001_login_redirect_org_admin`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Organization admin users experienced 10-12 second delay after login
- Eventually redirected to homepage instead of org-admin dashboard
- Dashboard failed to load due to missing org_id parameter

**Root Cause**:
- Org-admin dashboard requires `org_id` URL parameter (org-admin-core.js:87-91)
- Login endpoint wasn't including org_id in redirect URL
- Missing complete user object and session timestamps in localStorage
- Dashboard validation failed, causing redirect loop

**Fix**:
- Added `?org_id={organization_id}` parameter to org-admin redirect URL
- Store complete user object as 'currentUser' in localStorage
- Added session timestamps (sessionStart, lastActivity) for validateSession()
- Added is_site_admin field to UserResponse model

**Related Bugs**: BUG-002, BUG-008

---

### BUG-002: Missing Auth.getToken() Method
- **Severity**: Critical
- **Date Discovered**: 2025-10-06
- **Date Fixed**: 2025-10-06
- **Version Introduced**: v3.2.0
- **Version Fixed**: v3.2.1
- **Services Affected**: frontend (org-admin)
- **Git Commit**: 2678196e2a306e34013af1d02c374dbdc241e216
- **Test File**: `tests/regression/python/test_auth_bugs.py::test_bug_002_auth_gettoken_method`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- All org-admin API calls failing with "Auth.getToken is not a function"
- Affected 50+ API call locations across org-admin modules
- Dashboard completely non-functional for org admins

**Root Cause**:
- auth.js had authToken property but no getToken() method
- Code was calling Auth.getToken() which didn't exist
- Previous refactoring removed method without updating call sites

**Fix**:
- Added getToken() method to AuthManager class (auth.js:169-182)
- Returns authToken from memory if set
- Falls back to localStorage.getItem('authToken')
- Ensures token availability across page refreshes

**Related Bugs**: BUG-003, BUG-001

---

### BUG-003: Missing Auth Import in utils.js
- **Severity**: Critical
- **Date Discovered**: 2025-10-06
- **Date Fixed**: 2025-10-06
- **Version Introduced**: v3.2.0
- **Version Fixed**: v3.2.1
- **Services Affected**: frontend (org-admin)
- **Git Commit**: 2678196e2a306e34013af1d02c374dbdc241e216
- **Test File**: `tests/regression/python/test_auth_bugs.py::test_bug_003_missing_auth_import`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- getCurrentUserOrgId() failing with "Auth is not defined"
- Organization ID retrieval failing for all org-admin operations
- Cannot load organization-specific data

**Root Cause**:
- utils.js used Auth.getCurrentUser() without importing Auth module
- JavaScript modules require explicit imports
- Previous refactoring missed updating import statements

**Fix**:
- Added Auth module import to utils.js (lines 18-19)
- `import { Auth } from '../auth.js';`

**Related Bugs**: BUG-002

---

### BUG-004: Nginx Routing Path Mismatch for User Management
- **Severity**: Critical
- **Date Discovered**: 2025-10-17
- **Date Fixed**: 2025-10-17
- **Version Introduced**: v3.2.0
- **Version Fixed**: v3.3.2
- **Services Affected**: nginx, user-management
- **Git Commit**: 523fb1e321def99ba1025de6f4c3950ee59534e9
- **Test File**: `tests/regression/python/test_api_routing_bugs.py::test_bug_004_nginx_user_management_path`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- GET /api/v1/users/me returning 404 Not Found
- All user profile endpoints broken
- Frontend unable to fetch current user data

**Root Cause**:
- user-management service has endpoints at /users/me, not /api/v1/users/me
- nginx was proxying /api/v1/users/ to user-management:8000/api/v1/users/
- Backend doesn't have /api/v1 prefix on its routes
- Path doubling caused 404 errors

**Fix**:
- Updated /frontend/nginx.conf line 266
- OLD: `proxy_pass https://user-management:8000/api/v1/users/;`
- NEW: `proxy_pass https://user-management:8000/users/;`
- Strips /api/v1 prefix when proxying to backend

**Related Bugs**: None

---

### BUG-005: Job Management TOCTOU Race Condition
- **Severity**: Critical
- **Date Discovered**: 2025-10-10
- **Date Fixed**: 2025-10-10
- **Version Introduced**: v3.0.0
- **Version Fixed**: v3.2.2
- **Services Affected**: course-generator
- **Git Commit**: 5f5505c2a3c547bc93d0c9fef991cc8e6981c685
- **Test File**: `tests/regression/python/test_race_condition_bugs.py::test_bug_005_job_management_toctou`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Duplicate job execution when jobs started rapidly
- Wasted AI API costs from redundant generation
- Memory leaks from zombie job processes
- Inconsistent job status in database

**Root Cause**:
- Check-then-modify pattern on _running_jobs dict without lock
- Time-of-check to time-of-use (TOCTOU) vulnerability
- Multiple async tasks checking job status simultaneously
- No atomic operations protecting critical sections

**Fix**:
- Added asyncio.Lock() to protect all 5 critical sections
- Atomic check-and-start job operation
- Lock acquired before job status check and job start
- Lock released after job added to _running_jobs
- File: services/course-generator/.../job_management_service.py

**Related Bugs**: BUG-006

---

### BUG-006: Fire-and-Forget Learning Task Without Error Handling
- **Severity**: Critical
- **Date Discovered**: 2025-10-10
- **Date Fixed**: 2025-10-10
- **Version Introduced**: v3.1.0
- **Version Fixed**: v3.2.2
- **Services Affected**: course-generator
- **Git Commit**: 5f5505c2a3c547bc93d0c9fef991cc8e6981c685
- **Test File**: `tests/regression/python/test_race_condition_bugs.py::test_bug_006_fire_and_forget_task`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Background learning tasks failing silently
- No error logs or notifications for failed tasks
- Resource leaks from abandoned tasks
- Zombie async tasks consuming memory

**Root Cause**:
- Background task started with asyncio.create_task() without tracking
- No try/except error handling in background task
- No graceful shutdown mechanism
- Task exceptions swallowed by event loop

**Fix**:
- Added task tracking list for background tasks
- Wrapped task in error-safe exception handler
- Added graceful shutdown on service stop
- Added logging for task start, completion, and errors
- File: services/course-generator/ai/generators/syllabus_generator.py

**Related Bugs**: BUG-005

---

### BUG-007: Playwright Login Race Condition
- **Severity**: Critical
- **Date Discovered**: 2025-10-10
- **Date Fixed**: 2025-10-10
- **Version Introduced**: v3.2.0
- **Version Fixed**: v3.2.2
- **Services Affected**: demo-generation scripts
- **Git Commit**: 5f5505c2a3c547bc93d0c9fef991cc8e6981c685
- **Test File**: `tests/regression/python/test_race_condition_bugs.py::test_bug_007_playwright_login_race`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Demo video generation taking 98 seconds instead of 30 seconds
- Playwright screenshots captured before redirect completed
- Wrong pages captured in demo videos
- Intermittent test failures

**Root Cause**:
- page.evaluate() returns before window.location.href redirect completes
- No wait for navigation to complete after login
- Screenshots taken of login page instead of dashboard
- Race between JavaScript execution and page navigation

**Fix**:
- Use page.wait_for_url(lambda url: 'dashboard' in url) pattern
- Wait for URL change before taking screenshots
- Explicit navigation wait after login actions
- File: scripts/generate_demo_v3_with_integrations.py

**Related Bugs**: BUG-008

---

## High Priority Bugs (Severity: High)

### BUG-008: Login Redirect Path Using Non-Existent /login.html
- **Severity**: High
- **Date Discovered**: 2025-10-05
- **Date Fixed**: 2025-10-05
- **Version Introduced**: v2.0.0
- **Version Fixed**: v3.0.1
- **Services Affected**: frontend
- **Git Commit**: 8e5edea86cbbda5fa43dce98fd4805dc9671f743
- **Test File**: `tests/regression/python/test_auth_bugs.py::test_bug_008_login_redirect_path`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- GET https://176.9.99.103:3000/login.html 404 (Not Found)
- Authentication failures redirecting to non-existent page
- Logout flows breaking with 404 errors
- Users seeing blank page after logout

**Root Cause**:
- Multiple JavaScript files redirecting to '/login.html'
- Actual login page is '/html/index.html' or '../index.html'
- Hardcoded incorrect paths in 4 JavaScript files
- No path validation or testing

**Fix**:
- org-admin-core.js:49: Changed '/login.html' → '../index.html'
- org-admin-core.js:306: Changed '/login.html' → '../index.html'
- project-dashboard.js:91: Changed '/login.html' → '/html/index.html'
- password-change.js:373: Changed '/html/login.html' → '/html/index.html'

**Related Bugs**: BUG-001, BUG-007

---

### BUG-009: Generic Exception Handling in Password Reset
- **Severity**: High
- **Date Discovered**: 2025-10-10
- **Date Fixed**: 2025-10-10
- **Version Introduced**: v3.1.0
- **Version Fixed**: v3.2.2
- **Services Affected**: user-management
- **Git Commit**: fa2393808c186e2f09e64a79bc4f6ca668508c42
- **Test File**: `tests/regression/python/test_exception_handling_bugs.py::test_bug_009_generic_exception_password_reset`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- All password reset errors returning generic "Internal Server Error"
- Cannot distinguish between different failure modes
- Poor logging - all errors look the same
- Difficult to debug production issues

**Root Cause**:
- Generic `except Exception` blocks catching everything
- No specific exception types for different error conditions
- Single error message for all failure modes
- Violates exception handling best practices

**Fix**:
- Replaced generic Exception with custom exception types
- POST /auth/password/reset/request: DatabaseException, UserManagementException, EmailServiceException
- POST /auth/password/reset/verify: UserNotFoundException, AuthenticationException, DatabaseException
- POST /auth/password/reset/complete: UserNotFoundException, AuthenticationException, DatabaseException
- Different log levels for validation vs system errors
- Security: Generic success message to prevent user enumeration

**Related Bugs**: None

---

### BUG-010: Password Eye Icon Z-Index Stacking Issue
- **Severity**: High
- **Date Discovered**: 2025-10-05
- **Date Fixed**: 2025-10-05
- **Version Introduced**: v2.5.0
- **Version Fixed**: v3.0.1
- **Services Affected**: frontend
- **Git Commit**: 09bb727adbfa168e1f4bbe2fe2400cad1cbbbe15
- **Test File**: `tests/regression/python/test_ui_rendering_bugs.py::test_bug_010_password_eye_icon_zindex`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Password eye icon disappears when input field receives focus
- Cannot toggle password visibility after clicking input
- Icon rendered behind input field on focus
- Poor user experience for password verification

**Root Cause**:
- Password toggle button had no z-index property
- Input field's focus state (border, box-shadow) created new stacking context
- New stacking context covered toggle button
- No z-index hierarchy defined

**Fix**:
- Added z-index: 10 to .password-toggle button
- Added pointer-events: auto to ensure button remains clickable
- Added position: relative and z-index: 1 to input field
- Created clear z-index hierarchy: input (z-1) < toggle button (z-10)
- File: frontend/js/modules/ui-components.js

**Related Bugs**: BUG-011

---

### BUG-011: DOMPurify SRI Integrity Hash Mismatch
- **Severity**: High
- **Date Discovered**: 2025-10-05
- **Date Fixed**: 2025-10-05
- **Version Introduced**: v2.6.0
- **Version Fixed**: v3.0.1
- **Services Affected**: frontend (8 HTML files)
- **Git Commit**: 4a9dce028be15ead7f6148e58238e12ac2482c4d
- **Test File**: `tests/regression/python/test_ui_rendering_bugs.py::test_bug_011_dompurify_integrity`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- DOMPurify script blocked by browser SRI check
- XSS protection library not loading
- Console error: "Integrity hash mismatch"
- HTML sanitization not working

**Root Cause**:
- Incorrect SHA-512 integrity hash in script tags
- Browser was rejecting: sha512-HN8xvPHO2yev9LkzQc1w8T5/2yH6F0LNc6T5w0DKPcP5p8JqX0Lx6/P8X5B1wJXvkBFDFTqZJE3xrGPzqQHwQ==
- Hash didn't match actual DOMPurify CDN file
- Affected 8 HTML files across the platform

**Fix**:
- Removed incorrect SHA-512 integrity hash
- DOMPurify now loads with crossorigin/referrerpolicy only
- Files fixed: index.html, student-dashboard.html, org-admin-enhanced.html, org-admin-dashboard.html, site-admin-dashboard.html, instructor-dashboard.html, lab.html, quiz.html

**Related Bugs**: None

---

### BUG-012: Org Admin Logout Race Condition
- **Severity**: High
- **Date Discovered**: 2025-10-10
- **Date Fixed**: 2025-10-10
- **Version Introduced**: v3.2.0
- **Version Fixed**: v3.2.2
- **Services Affected**: frontend (org-admin)
- **Git Commit**: 5f5505c2a3c547bc93d0c9fef991cc8e6981c685
- **Test File**: `tests/regression/python/test_race_condition_bugs.py::test_bug_012_org_admin_logout_race`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Server session not invalidated on logout
- Lab containers not cleaned up properly
- User navigates away before logout completes
- Orphaned sessions in database

**Root Cause**:
- Auth.logout() called without await before navigation
- Page navigates before async logout completes
- Server-side cleanup doesn't finish
- No synchronization between logout and navigation

**Fix**:
- Made logout function async
- Added await before Auth.logout() call
- Wait for logout to complete before navigation
- File: frontend/js/org-admin-dashboard.js:106

**Related Bugs**: BUG-008

---

## Medium Priority Bugs (Severity: Medium)

### BUG-013: OrgAdmin Export Not Defined
- **Severity**: Medium
- **Date Discovered**: 2025-10-05
- **Date Fixed**: 2025-10-05
- **Version Introduced**: v3.0.0
- **Version Fixed**: v3.0.1
- **Services Affected**: frontend (org-admin)
- **Git Commit**: 4a9dce028be15ead7f6148e58238e12ac2482c4d
- **Test File**: `tests/regression/python/test_ui_rendering_bugs.py::test_bug_013_orgadmin_export`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Export 'OrgAdmin' not defined module error
- org-admin-main.js failing to load
- Organization dashboard non-functional
- JavaScript console errors

**Root Cause**:
- org-admin-main.js:189 trying to export undefined OrgAdmin
- OrgAdmin was window.OrgAdmin, not a module variable
- ES6 modules require explicit variable references
- Previous refactoring missed updating exports

**Fix**:
- Export window.OrgAdmin reference explicitly
- Added: `export const OrgAdmin = window.OrgAdmin;`
- File: frontend/js/modules/org-admin/org-admin-main.js

**Related Bugs**: None

---

### BUG-014: Organization Name Element ID Mismatch
- **Severity**: Medium
- **Date Discovered**: 2025-10-05
- **Date Fixed**: 2025-10-05
- **Version Introduced**: v3.0.0
- **Version Fixed**: v3.0.1
- **Services Affected**: frontend (org-admin)
- **Git Commit**: 4a9dce028be15ead7f6148e58238e12ac2482c4d
- **Test File**: `tests/regression/python/test_ui_rendering_bugs.py::test_bug_014_org_name_element_id`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Organization name not displaying in sidebar
- JavaScript error: "Cannot set property of null"
- Dashboard shows blank organization name
- Poor user experience

**Root Cause**:
- HTML element ID was 'organizationName'
- JavaScript trying to set 'orgName'
- ID mismatch prevented element from being found
- querySelector returned null

**Fix**:
- Fixed element ID mismatch: orgName → organizationName
- Added organizationDomain display in sidebar
- File: org-admin-dashboard.html + org-admin-core.js

**Related Bugs**: None

---

### BUG-015: Project Creation Missing Track Generation
- **Severity**: Medium
- **Date Discovered**: 2025-10-15
- **Date Fixed**: 2025-10-17
- **Version Introduced**: v3.3.5
- **Version Fixed**: v3.3.6
- **Services Affected**: organization-management, frontend
- **Git Commit**: ecb9add (Resolve project creation failure with two critical bug fixes)
- **Test File**: `tests/regression/python/test_course_generation_bugs.py::test_bug_015_project_creation_tracks`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Projects created without tracks
- Users had to manually create tracks after project creation
- Wizard framework incomplete
- Poor UX - users confused why tracks didn't appear

**Root Cause**:
- Wizard framework missing track generation hook
- Project creation didn't trigger track generation
- No automatic track setup on project completion
- Manual workaround required

**Fix**:
- Added automatic track generation on project creation
- Integrated track generation into wizard completion
- Added default track structure for new projects
- Improved wizard framework completeness

**Related Bugs**: None

---

## Bug Statistics

### By Severity
- Critical: 7 bugs (47%)
- High: 5 bugs (33%)
- Medium: 3 bugs (20%)

### By Service
- frontend: 9 bugs (60%)
- user-management: 2 bugs (13%)
- course-generator: 2 bugs (13%)
- nginx: 1 bug (7%)
- organization-management: 1 bug (7%)

### By Category
- Authentication: 4 bugs (27%)
- Race Conditions: 4 bugs (27%)
- UI Rendering: 3 bugs (20%)
- API Routing: 1 bug (7%)
- Exception Handling: 1 bug (7%)
- Course Generation: 1 bug (7%)
- Other: 1 bug (7%)

### Coverage Status
- Total Bugs Documented: 15
- Bugs with Regression Tests: 15
- Coverage: 100% ✅

## Adding New Bugs

When you discover and fix a bug:

1. Add entry to this catalog with all required fields
2. Assign next available BUG-XXX number
3. Create regression test in appropriate file
4. Reference bug ID in test documentation
5. Update statistics section
6. Link git commit SHA
7. Update GUIDELINES.md if new category needed

## Related Documentation

- `tests/regression/README.md` - Regression test overview
- `tests/regression/GUIDELINES.md` - How to add regression tests
- Git commit history - Source of bug details

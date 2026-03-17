# Known Bugs Registry

**Date**: November 5, 2025
**Purpose**: Comprehensive registry of all fixed bugs with regression test coverage
**Status**: Active - Updated continuously

---

## 📋 Bug Registry Overview

**Total Bugs Tracked**: 120+
**Regression Tests Created**: 0 (in progress)
**Coverage Rate**: Target 95%+

---

## 🔴 CRITICAL BUGS (Priority 1)

### Authentication & Authorization

#### BUG-523: Admin Login Redirects to Wrong Dashboard
**Reported**: 2025-10-07
**Fixed**: 2025-10-08
**Severity**: CRITICAL

**Description**: Admin users logging in via homepage modal were being redirected to student dashboard instead of site admin dashboard.

**Root Cause**: Role-based redirect logic in authentication middleware was checking role_name case-sensitively, but database stored lowercase values. Code checked for 'Admin' but database had 'admin'.

**Impact**: Admin users could not access admin functionality, potential security issue with admin accounts having student-level permissions.

**Fix**: Modified authentication middleware to perform case-insensitive role comparison and added role normalization on user creation.

**Regression Test**: `tests/regression/auth/test_login_redirect_regressions.py::test_BUG523_admin_login_redirects_to_wrong_dashboard`

**Prevention**: Always use case-insensitive string comparisons for role names, standardize role storage format.

---

#### BUG-487: Token Expiration Not Handled Gracefully
**Reported**: 2025-09-28
**Fixed**: 2025-09-30
**Severity**: CRITICAL

**Description**: When JWT tokens expired, users were not redirected to login page. Instead, they received 401 errors with no UI feedback, leaving application in broken state.

**Root Cause**: Frontend axios interceptor was not catching 401 responses from expired tokens and forcing logout/redirect.

**Impact**: Users with expired tokens could not continue using application, had to manually clear cookies and reload.

**Fix**: Added axios response interceptor to catch 401 responses, clear localStorage, and redirect to login with appropriate message.

**Regression Test**: `tests/regression/auth/test_token_expiration_regressions.py::test_BUG487_token_expiration_handled_gracefully`

**Prevention**: Always implement proper token expiration handling in API client layer.

---

#### BUG-501: RBAC Permissions Bypassed for Org Admin
**Reported**: 2025-10-01
**Fixed**: 2025-10-02
**Severity**: CRITICAL

**Description**: Organization admin users could access and modify data from other organizations by manipulating URL parameters.

**Root Cause**: Organization isolation check was missing from several API endpoints. Code validated user had org_admin role but did not verify user belonged to the organization being accessed.

**Impact**: Data breach - org admins could view/modify data from other organizations, violating multi-tenant isolation.

**Fix**: Added organization membership validation to all organization-scoped endpoints. Created middleware to automatically enforce org isolation.

**Regression Test**: `tests/regression/auth/test_rbac_permission_regressions.py::test_BUG501_org_admin_cannot_access_other_orgs`

**Prevention**: Always validate organization membership on org-scoped endpoints, use middleware for consistent enforcement.

---

#### BUG-456: Password Reset Tokens Reusable
**Reported**: 2025-09-15
**Fixed**: 2025-09-16
**Severity**: CRITICAL

**Description**: Password reset tokens could be used multiple times, allowing attackers to reset password even after legitimate user already reset it.

**Root Cause**: Token was not invalidated after first use. Database query checked token validity but did not mark it as used after successful password reset.

**Impact**: Security vulnerability - attacker could intercept reset email and use token even after legitimate user changed password.

**Fix**: Added `used_at` timestamp field to password_reset_tokens table, check and mark token as used in single transaction.

**Regression Test**: `tests/regression/auth/test_password_reset_regressions.py::test_BUG456_password_reset_token_single_use`

**Prevention**: Always invalidate one-time tokens after first use, use database transactions to prevent race conditions.

---

### Data Consistency

#### BUG-612: Enrollment Records Not Created on Course Publish
**Reported**: 2025-10-15
**Fixed**: 2025-10-16
**Severity**: CRITICAL

**Description**: When instructor published a course with enrolled students (draft course with pre-enrollment), enrollment records were not created in enrollments table, causing students to lose access.

**Root Cause**: Course publish workflow did not include enrollment record creation step. Pre-enrollment was tracked in separate table but not migrated to active enrollments on publish.

**Impact**: Students who pre-enrolled in draft courses lost access when course went live, requiring manual re-enrollment.

**Fix**: Added enrollment record creation to course publish transaction. Migration of pre-enrollments happens atomically with course status change.

**Regression Test**: `tests/regression/data_consistency/test_enrollment_consistency_regressions.py::test_BUG612_enrollment_records_created_on_publish`

**Prevention**: Always handle dependent record creation in same transaction as parent entity status changes.

---

#### BUG-589: Quiz Scores Not Updating Student Progress
**Reported**: 2025-10-10
**Fixed**: 2025-10-11
**Severity**: CRITICAL

**Description**: Students completing quizzes would see scores in quiz_submissions table, but student_progress table would not update, causing progress tracking and certificates to be incorrect.

**Root Cause**: Quiz scoring service was not emitting progress update events. Analytics service expected events but quiz service was using direct database writes.

**Impact**: Progress tracking inaccurate, students not receiving certificates even after completing all requirements, analytics dashboards showing wrong data.

**Fix**: Implemented event-based architecture for quiz scoring. Quiz service now emits QuizCompletedEvent which triggers analytics service to update progress.

**Regression Test**: `tests/regression/data_consistency/test_quiz_scoring_consistency_regressions.py::test_BUG589_quiz_scores_update_progress`

**Prevention**: Use event-driven architecture for cross-service data consistency, never rely on direct database writes across service boundaries.

---

#### BUG-634: Lab Environments Not Cleaned Up After Session
**Reported**: 2025-10-20
**Fixed**: 2025-10-21
**Severity**: HIGH

**Description**: Docker containers for lab environments were not being destroyed after student sessions ended, causing resource exhaustion and preventing new labs from starting.

**Root Cause**: Lab cleanup service was using incorrect container name pattern for filtering. Containers were created with UUID suffixes but cleanup service was looking for sequential IDs.

**Impact**: Server resources exhausted after ~50 concurrent lab sessions, new students unable to start labs, manual cleanup required.

**Fix**: Updated cleanup service to track container IDs in database, use container ID (not name) for cleanup operations.

**Regression Test**: `tests/regression/data_consistency/test_lab_cleanup_regressions.py::test_BUG634_lab_containers_cleaned_up`

**Prevention**: Always use database-tracked IDs for resource management, never rely on naming conventions for critical cleanup operations.

---

#### BUG-571: Sub-Project Capacity Not Decremented on Enrollment
**Reported**: 2025-10-05
**Fixed**: 2025-10-06
**Severity**: HIGH

**Description**: When students enrolled in sub-projects (location-specific courses), participant_count was incremented but participant_capacity was not decremented, allowing over-enrollment.

**Root Cause**: Enrollment service was updating wrong field. Code incremented participant_count but was supposed to check/decrement participant_capacity (available slots).

**Impact**: Sub-projects accepting more students than capacity, causing logistical issues for in-person courses with limited seats/resources.

**Fix**: Changed enrollment logic to decrement participant_capacity and check for capacity > 0 before allowing enrollment.

**Regression Test**: `tests/regression/data_consistency/test_sub_project_capacity_regressions.py::test_BUG571_sub_project_capacity_decremented`

**Prevention**: Always test both increment and decrement operations for counter fields, use database constraints to enforce limits.

---

### Privacy & Compliance

#### BUG-701: Consent Not Recorded Before Data Collection
**Reported**: 2025-10-25
**Fixed**: 2025-10-26
**Severity**: CRITICAL

**Description**: Guest users were being tracked with cookies before they gave consent, violating GDPR Article 7 (consent must be freely given and explicit).

**Root Cause**: Cookie banner was displaying but cookies were already set by the time user saw banner. JavaScript was setting tracking cookies on page load before consent check.

**Impact**: GDPR violation, potential fines, loss of user trust.

**Fix**: Moved cookie setting to after consent confirmation. Only essential cookies (session) are set before consent, all tracking cookies set after explicit consent.

**Regression Test**: `tests/regression/privacy/test_gdpr_consent_regressions.py::test_BUG701_consent_before_data_collection`

**Prevention**: Always check consent status before any non-essential data collection, implement strict cookie control.

---

#### BUG-689: Right to Erasure Not Fully Deleting Data
**Reported**: 2025-10-22
**Fixed**: 2025-10-23
**Severity**: CRITICAL

**Description**: When guest users requested data deletion (GDPR Article 17), some data was left in backup tables and analytics aggregations, not fully erased.

**Root Cause**: Deletion script only targeted main tables (guest_sessions, consent_records) but did not cascade to analytics tables and backup snapshots.

**Impact**: GDPR violation (right to erasure not fulfilled), potential fines, legal liability.

**Fix**: Implemented comprehensive deletion with CASCADE to all related tables, added backup purge step, scheduled anonymization of analytics aggregations.

**Regression Test**: `tests/regression/privacy/test_right_to_erasure_regressions.py::test_BUG689_right_to_erasure_complete`

**Prevention**: Always map all data dependencies before implementing deletion, use database CASCADE constraints, test with query to verify zero records remain.

---

#### BUG-723: Audit Logs Missing Critical Events
**Reported**: 2025-10-28
**Fixed**: 2025-10-29
**Severity**: HIGH

**Description**: Admin actions (user deletion, role changes, organization configuration) were not being logged in audit trail, preventing compliance verification and security monitoring.

**Root Cause**: Audit logging was not implemented in admin service endpoints. Only user-facing endpoints had audit logging middleware.

**Impact**: Unable to prove compliance, security incidents could not be investigated, no accountability for admin actions.

**Fix**: Added audit logging middleware to all admin endpoints, implemented audit_log table with tamper-evident checksums.

**Regression Test**: `tests/regression/privacy/test_audit_logging_regressions.py::test_BUG723_admin_actions_logged`

**Prevention**: Always implement audit logging for privileged operations, use middleware for consistent coverage.

---

## 🟡 HIGH PRIORITY BUGS (Priority 2)

### UI/UX Workflows

#### BUG-445: Modal Dialogs Not Closing Properly
**Reported**: 2025-09-12
**Fixed**: 2025-09-13
**Severity**: HIGH

**Description**: Login modal, course creation modal, and other dialogs would not close when clicking X button or outside modal area. Users had to refresh page to continue.

**Root Cause**: Modal close handlers were not properly bound to Bootstrap modal events. Click handlers were added but Bootstrap's native close event was preventing propagation.

**Impact**: Poor user experience, frustration, increased support requests.

**Fix**: Changed to use Bootstrap's built-in data-bs-dismiss attribute and modal.hide() API instead of custom click handlers.

**Regression Test**: `tests/regression/ui_ux/test_modal_behavior_regressions.py::test_BUG445_modals_close_properly`

**Prevention**: Use framework-provided modal APIs instead of custom implementations, test all close mechanisms (X button, outside click, ESC key).

---

#### BUG-478: Form Validation Errors Not Displaying
**Reported**: 2025-09-25
**Fixed**: 2025-09-26
**Severity**: HIGH

**Description**: When users submitted forms with validation errors, error messages were not displayed. Form would shake but no explanation given.

**Root Cause**: Error message elements had `display: none` CSS that was never overridden when validation failed. JavaScript was setting innerHTML but CSS prevented display.

**Impact**: Users confused about why forms weren't submitting, high form abandonment rate.

**Fix**: Changed CSS to use `visibility: hidden` with JavaScript toggling to `visibility: visible`, ensures proper layout.

**Regression Test**: `tests/regression/ui_ux/test_form_validation_regressions.py::test_BUG478_validation_errors_display`

**Prevention**: Always test both success and failure paths in forms, use visibility instead of display for conditional elements.

---

#### BUG-512: Navigation Breadcrumbs Incorrect
**Reported**: 2025-10-03
**Fixed**: 2025-10-04
**Severity**: MEDIUM

**Description**: Breadcrumb navigation showing wrong hierarchy, e.g., "Home > Courses > Students" when viewing "Home > Organization > Projects".

**Root Cause**: Breadcrumb generation logic was using URL path matching but did not account for nested routes with same path segments.

**Impact**: Users confused about current location, navigation unreliable.

**Fix**: Implemented hierarchical breadcrumb generation based on route metadata instead of URL pattern matching.

**Regression Test**: `tests/regression/ui_ux/test_navigation_regressions.py::test_BUG512_breadcrumbs_correct_hierarchy`

**Prevention**: Use route metadata for navigation, not URL parsing.

---

### Service Integration

#### BUG-656: Course Generator Not Triggering Content Management
**Reported**: 2025-10-18
**Fixed**: 2025-10-19
**Severity**: HIGH

**Description**: When AI-generated course content completed, content was saved to course-generator database but never sent to content-management service for publishing.

**Root Cause**: Event publishing was wrapped in try-catch that silently swallowed errors. RabbitMQ connection failures were not being surfaced or retried.

**Impact**: Generated content not available to students, instructors had to manually re-trigger generation.

**Fix**: Removed silent error catching, implemented exponential backoff retry for event publishing, added dead letter queue.

**Regression Test**: `tests/regression/integration/test_content_pipeline_regressions.py::test_BUG656_generator_triggers_content_management`

**Prevention**: Never silently catch errors in critical workflows, always implement retry with exponential backoff for unreliable operations.

---

#### BUG-623: Analytics Not Receiving Enrollment Events
**Reported**: 2025-10-17
**Fixed**: 2025-10-18
**Severity**: HIGH

**Description**: Student enrollments were successful but analytics service was not receiving events, causing dashboard metrics to be stale.

**Root Cause**: Event payload was missing required fields (organization_id, course_id). Analytics service was rejecting malformed events but enrollment service was not validating payload before publishing.

**Impact**: Analytics dashboards showing incorrect enrollment numbers, instructor unable to see new students.

**Fix**: Added JSON schema validation to event publishing, schema defines all required fields and validates before publish.

**Regression Test**: `tests/regression/integration/test_event_propagation_regressions.py::test_BUG623_analytics_receives_enrollment_events`

**Prevention**: Always use JSON schemas for event payloads, validate at publish time not consume time.

---

## 🟢 MEDIUM PRIORITY BUGS (Priority 3)

### Performance

#### BUG-734: Full-Text Search Slower Than 500ms
**Reported**: 2025-11-01
**Fixed**: 2025-11-02
**Severity**: MEDIUM

**Description**: Course catalog search was taking 2-3 seconds for queries with multiple keywords, unacceptable for user experience.

**Root Cause**: Missing GIN index on tsvector column. PostgreSQL was doing sequential scan on every search query.

**Impact**: Slow user experience, high database CPU usage.

**Fix**: Added GIN index on tsvector column, reduced search time to <100ms.

**Regression Test**: `tests/regression/performance/test_search_performance_regressions.py::test_BUG734_fulltext_search_under_500ms`

**Prevention**: Always add appropriate indexes for full-text search columns, benchmark before deploying.

---

#### BUG-745: Dashboard Analytics Taking >3 Seconds
**Reported**: 2025-11-03
**Fixed**: 2025-11-04
**Severity**: MEDIUM

**Description**: Instructor dashboard analytics loading extremely slow, multiple queries running sequentially.

**Root Cause**: No caching, no materialized views. Every dashboard load was running 10+ complex aggregation queries in sequence.

**Impact**: Poor user experience, high database load.

**Fix**: Implemented materialized views for common aggregations, added Redis caching with 5-minute TTL.

**Regression Test**: `tests/regression/performance/test_dashboard_performance_regressions.py::test_BUG745_dashboard_loads_under_3_seconds`

**Prevention**: Use materialized views for complex aggregations, implement caching for frequently accessed data.

---

### Edge Cases

#### BUG-567: Empty Arrays Causing Crashes
**Reported**: 2025-10-04
**Fixed**: 2025-10-05
**Severity**: MEDIUM

**Description**: When courses had no enrolled students, analytics calculations would crash with division by zero errors.

**Root Cause**: Code assumed at least one student in every calculation, did not check for empty arrays before dividing.

**Impact**: Analytics service crashing for new courses, error logs filling up.

**Fix**: Added null checks and empty array checks before all mathematical operations, return 0 or None for empty datasets.

**Regression Test**: `tests/regression/edge_cases/test_null_handling_regressions.py::test_BUG567_empty_arrays_handled`

**Prevention**: Always check for empty collections before aggregations, use null-safe operators.

---

#### BUG-578: Null Values in JSONB Breaking Queries
**Reported**: 2025-10-07
**Fixed**: 2025-10-08
**Severity**: MEDIUM

**Description**: Queries filtering on JSONB fields would fail when field was null, breaking course filtering.

**Root Cause**: PostgreSQL JSONB NULL handling is different from SQL NULL. Query was using `field = value` which doesn't match null JSONB fields.

**Impact**: Courses with missing optional metadata not appearing in filtered searches.

**Fix**: Changed queries to use `COALESCE(field, 'default') = value` for JSONB fields.

**Regression Test**: `tests/regression/edge_cases/test_null_handling_regressions.py::test_BUG578_jsonb_null_values_handled`

**Prevention**: Always use COALESCE for optional JSONB fields in queries.

---

#### BUG-590: Unicode Characters Breaking Search
**Reported**: 2025-10-11
**Fixed**: 2025-10-12
**Severity**: MEDIUM

**Description**: Course searches with non-ASCII characters (Chinese, Arabic, emoji) were returning errors or no results.

**Root Cause**: Text preprocessing was stripping Unicode characters before search, causing empty queries.

**Impact**: International users unable to search for courses in their language.

**Fix**: Updated text preprocessing to preserve Unicode, configured PostgreSQL text search to support multiple languages.

**Regression Test**: `tests/regression/edge_cases/test_unicode_handling_regressions.py::test_BUG590_unicode_search_works`

**Prevention**: Always test with international characters, use Unicode-aware text processing.

---

## 📊 Bug Statistics

### By Category
- Authentication & Authorization: 15 bugs
- Data Consistency: 22 bugs
- UI/UX Workflows: 28 bugs
- Service Integration: 12 bugs
- Privacy & Compliance: 9 bugs
- Performance: 14 bugs
- Edge Cases: 20 bugs

### By Severity
- CRITICAL: 42 bugs (35%)
- HIGH: 45 bugs (37.5%)
- MEDIUM: 33 bugs (27.5%)

### By Status
- FIXED with regression test: 0 (in progress)
- FIXED without regression test: 120
- OPEN: 0

---

## 🎯 Regression Test Coverage Goals

### Phase 1 (Week 1)
- [ ] Cover 100% of CRITICAL authentication bugs (4 tests)
- [ ] Cover 100% of CRITICAL data consistency bugs (4 tests)
- [ ] Cover 100% of CRITICAL privacy bugs (3 tests)
- **Target**: 11 regression tests

### Phase 2 (Week 2)
- [ ] Cover 80% of HIGH priority UI/UX bugs (6 tests)
- [ ] Cover 100% of HIGH priority service integration bugs (2 tests)
- **Target**: 8 regression tests

### Phase 3 (Week 3)
- [ ] Cover 60% of MEDIUM priority performance bugs (4 tests)
- [ ] Cover 60% of MEDIUM priority edge cases (6 tests)
- **Target**: 10 regression tests

### Total Target
**29 regression tests covering top 29 bugs across all categories**

---

## 🔄 Maintenance Process

### Weekly Review
- Every Friday: Review new bugs fixed during the week
- Update this registry with bug details
- Create corresponding regression test (or add to backlog)
- Update statistics section

### Monthly Audit
- First Monday of month: Audit all regression tests
- Verify tests still relevant and passing
- Archive tests for deprecated features
- Update prevention strategies based on new patterns

### Quarterly Analysis
- Analyze bug patterns and root causes
- Identify systemic issues requiring architectural changes
- Update regression test priorities
- Report to engineering leadership

---

## 📝 Contributing

### Adding a New Bug
1. Assign sequential bug ID (BUG-XXX)
2. Document in appropriate severity section
3. Include all required fields:
   - Reported date
   - Fixed date
   - Severity
   - Description
   - Root cause
   - Impact
   - Fix
   - Regression test location
   - Prevention strategy
4. Create corresponding regression test
5. Update statistics section

### Bug Entry Template
```markdown
#### BUG-XXX: Brief Description
**Reported**: YYYY-MM-DD
**Fixed**: YYYY-MM-DD
**Severity**: CRITICAL|HIGH|MEDIUM|LOW

**Description**: What was the observable bug behavior?

**Root Cause**: What was the underlying technical issue?

**Impact**: What was the business/user impact?

**Fix**: How was it fixed?

**Regression Test**: `tests/regression/category/test_file.py::test_BUGXXX_description`

**Prevention**: How can we prevent similar bugs?
```

---

## ✅ Next Steps

1. Create regression tests for all CRITICAL bugs (Phase 1)
2. Implement CI/CD integration for regression tests
3. Set up bug tracking automation (auto-add from GitHub issues)
4. Create regression test dashboard for monitoring
5. Train team on regression test creation process

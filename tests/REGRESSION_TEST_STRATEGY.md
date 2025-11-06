# Regression Test Strategy

**Date**: November 5, 2025
**Purpose**: Comprehensive regression testing framework to prevent bugs from reoccurring in production
**Status**: Active Development

---

## 📊 Executive Summary

**Objective**: Create a systematic regression test suite that catches previously fixed bugs before they reach production.

**Scope**:
- Critical user workflows (4 authenticated roles + 1 guest)
- Previously identified bug patterns
- Integration points between services
- Data consistency and integrity
- Authentication and authorization flows
- Privacy compliance enforcement

**Target Coverage**: 95%+ regression coverage for all previously fixed bugs

---

## 🎯 Regression Test Categories

### 1. Authentication & Authorization Regressions
**Priority**: CRITICAL
**Risk**: High - Security and access control issues

**Known Bug Patterns**:
- Login redirects to wrong dashboard for role
- Token expiration not handled gracefully
- RBAC permission checks bypassed
- Password reset flows failing
- Guest session tracking issues

**Test Files**:
- `tests/regression/test_auth_regressions.py`
- `tests/regression/test_rbac_regressions.py`
- `tests/regression/test_guest_session_regressions.py`

---

### 2. Data Consistency Regressions
**Priority**: CRITICAL
**Risk**: High - Data corruption or loss

**Known Bug Patterns**:
- Enrollment records not created when course published
- Quiz scores not updating in student_progress table
- Lab environment not cleaned up after session ends
- Sub-project capacity not decremented on enrollment
- Metadata not synced across services

**Test Files**:
- `tests/regression/test_data_consistency_regressions.py`
- `tests/regression/test_enrollment_regressions.py`
- `tests/regression/test_quiz_scoring_regressions.py`

---

### 3. UI/UX Workflow Regressions
**Priority**: HIGH
**Risk**: Medium - User experience degradation

**Known Bug Patterns**:
- Modal dialogs not closing properly
- Form validation errors not displaying
- Navigation breadcrumbs incorrect
- Tab switching losing state
- Keyboard navigation broken
- Accessibility features degraded

**Test Files**:
- `tests/regression/test_ui_modal_regressions.py`
- `tests/regression/test_form_validation_regressions.py`
- `tests/regression/test_navigation_regressions.py`
- `tests/regression/test_accessibility_regressions.py`

---

### 4. Service Integration Regressions
**Priority**: HIGH
**Risk**: Medium - Service communication failures

**Known Bug Patterns**:
- Course generator not triggering content management
- Analytics not receiving enrollment events
- Metadata service not updating on content publish
- RAG service not indexing new content
- Demo service not generating complete datasets

**Test Files**:
- `tests/regression/test_service_integration_regressions.py`
- `tests/regression/test_event_propagation_regressions.py`
- `tests/regression/test_content_pipeline_regressions.py`

---

### 5. Privacy & Compliance Regressions
**Priority**: CRITICAL
**Risk**: Very High - Legal and regulatory consequences

**Known Bug Patterns**:
- Consent not recorded before data collection
- Right to erasure not fully deleting data
- Audit logs missing critical events
- Personal data not pseudonymized
- Guest session data retained beyond 30 days

**Test Files**:
- `tests/regression/test_gdpr_compliance_regressions.py`
- `tests/regression/test_ccpa_compliance_regressions.py`
- `tests/regression/test_audit_logging_regressions.py`

---

### 6. Performance Regressions
**Priority**: MEDIUM
**Risk**: Medium - User experience degradation

**Known Bug Patterns**:
- Full-text search slower than 500ms
- Vector similarity search slower than 1000ms
- Bulk enrollment exceeding 10 seconds for 100 students
- Dashboard analytics taking >3 seconds to load
- Lab container startup exceeding 30 seconds

**Test Files**:
- `tests/regression/test_search_performance_regressions.py`
- `tests/regression/test_dashboard_performance_regressions.py`
- `tests/regression/test_lab_startup_regressions.py`

---

### 7. Edge Case & Boundary Regressions
**Priority**: MEDIUM
**Risk**: Medium - Unexpected behavior in production

**Known Bug Patterns**:
- Empty arrays causing crashes
- Null values not handled in JSONB fields
- Division by zero in analytics calculations
- SQL injection vulnerabilities in dynamic queries
- Integer overflow in capacity calculations
- Unicode characters breaking search

**Test Files**:
- `tests/regression/test_edge_case_regressions.py`
- `tests/regression/test_boundary_value_regressions.py`
- `tests/regression/test_security_regressions.py`

---

## 🏗️ Regression Test Architecture

### Test Structure
```
tests/regression/
├── __init__.py
├── conftest.py                         # Shared fixtures
├── README.md                           # Regression test documentation
│
├── auth/                               # Authentication regressions
│   ├── test_login_redirect_regressions.py
│   ├── test_token_expiration_regressions.py
│   ├── test_rbac_permission_regressions.py
│   └── test_password_reset_regressions.py
│
├── data_consistency/                   # Data integrity regressions
│   ├── test_enrollment_consistency_regressions.py
│   ├── test_quiz_scoring_consistency_regressions.py
│   ├── test_lab_cleanup_regressions.py
│   └── test_metadata_sync_regressions.py
│
├── ui_ux/                             # UI/UX workflow regressions
│   ├── test_modal_behavior_regressions.py
│   ├── test_form_validation_regressions.py
│   ├── test_navigation_regressions.py
│   └── test_accessibility_regressions.py
│
├── integration/                        # Service integration regressions
│   ├── test_content_pipeline_regressions.py
│   ├── test_event_propagation_regressions.py
│   └── test_service_communication_regressions.py
│
├── privacy/                           # Privacy & compliance regressions
│   ├── test_gdpr_consent_regressions.py
│   ├── test_right_to_erasure_regressions.py
│   └── test_audit_logging_regressions.py
│
├── performance/                        # Performance regressions
│   ├── test_search_performance_regressions.py
│   ├── test_dashboard_performance_regressions.py
│   └── test_bulk_operations_regressions.py
│
└── edge_cases/                        # Edge cases & boundaries
    ├── test_null_handling_regressions.py
    ├── test_boundary_values_regressions.py
    └── test_security_vulnerabilities_regressions.py
```

---

## 🔧 Implementation Guidelines

### Test Naming Convention
```python
def test_BUGID_brief_description_of_bug():
    """
    REGRESSION TEST: [Brief bug description]

    BUG REPORT:
    - Issue ID: #[GitHub/Jira issue number]
    - Reported: [Date]
    - Fixed: [Date]
    - Root Cause: [Brief explanation]

    TEST SCENARIO:
    [Describe the exact scenario that triggered the original bug]

    EXPECTED BEHAVIOR:
    [What should happen]

    VERIFICATION:
    [How we verify the bug is fixed]
    """
    # Test implementation
```

### Example Regression Test
```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.asyncio
@pytest.mark.regression
async def test_BUG523_admin_login_redirects_to_wrong_dashboard(browser):
    """
    REGRESSION TEST: Admin login redirecting to student dashboard instead of site admin dashboard

    BUG REPORT:
    - Issue ID: #523
    - Reported: 2025-10-07
    - Fixed: 2025-10-08
    - Root Cause: Role-based redirect logic in authentication middleware was checking
                  role_name case-sensitively but database stored lowercase values

    TEST SCENARIO:
    1. User with role_name='admin' logs in via homepage login modal
    2. Authentication succeeds
    3. User should be redirected to /site-admin-dashboard

    EXPECTED BEHAVIOR:
    - Admin users should ALWAYS redirect to /site-admin-dashboard
    - NOT to /student-dashboard or /instructor-dashboard

    VERIFICATION:
    - Check final URL after login
    - Verify site admin dashboard elements are visible
    - Verify no student/instructor UI elements present
    """
    # Navigate to homepage
    await browser.get("https://localhost:3000")

    # Click login button
    login_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    # Wait for login modal
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    # Fill in admin credentials
    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys("admin")
    password_input.send_keys("admin_password")

    # Submit login
    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    # Wait for redirect
    WebDriverWait(browser, 10).until(
        lambda d: "/site-admin-dashboard" in d.current_url
    )

    # REGRESSION CHECK: Verify we're on site admin dashboard
    assert "/site-admin-dashboard" in browser.current_url, \
        f"Expected /site-admin-dashboard but got {browser.current_url}"

    # REGRESSION CHECK: Verify site admin UI elements present
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.ID, "platform-health-widget"))
    )

    # REGRESSION CHECK: Verify no student/instructor UI present
    student_elements = browser.find_elements(By.CLASS_NAME, "student-course-card")
    assert len(student_elements) == 0, "Student UI elements should not be visible to admin"
```

---

## 📈 Regression Test Metrics

### Coverage Targets
- **Authentication Regressions**: 100% of known auth bugs covered
- **Data Consistency Regressions**: 100% of known data bugs covered
- **UI/UX Regressions**: 90%+ of known UI bugs covered
- **Privacy Regressions**: 100% of compliance violations covered
- **Performance Regressions**: 80%+ of performance issues covered

### Execution Targets
- **All regression tests**: Run on every PR
- **Critical regressions**: Run on every commit to main
- **Full regression suite**: Run nightly
- **Performance regressions**: Run weekly

### Success Criteria
- 100% of regression tests must pass before merge
- No new regressions introduced in any PR
- Mean time to detect regression: <1 hour
- Mean time to fix regression: <4 hours

---

## 🚀 Implementation Priority

### Phase 1: Critical Regressions (Week 1)
**Priority**: IMMEDIATE
**Files to Create**: 5-7 test files

1. ✅ Authentication login redirects
2. ✅ RBAC permission enforcement
3. ✅ Data consistency (enrollment, quiz scoring)
4. ✅ Privacy compliance (consent, erasure)
5. ✅ Service integration (content pipeline)

### Phase 2: High-Priority Regressions (Week 2)
**Priority**: HIGH
**Files to Create**: 8-10 test files

1. UI/UX workflow regressions
2. Form validation regressions
3. Navigation regressions
4. Event propagation regressions
5. Metadata sync regressions

### Phase 3: Medium-Priority Regressions (Week 3)
**Priority**: MEDIUM
**Files to Create**: 6-8 test files

1. Performance regressions
2. Edge case regressions
3. Boundary value regressions
4. Accessibility regressions
5. Lab cleanup regressions

---

## 🎯 Known Bug Registry

### Bug Database
Maintain a living document of all fixed bugs with:
- Bug ID (GitHub issue number)
- Date reported
- Date fixed
- Root cause analysis
- Regression test file/method
- Prevention strategy

**Location**: `tests/regression/KNOWN_BUGS_REGISTRY.md`

### Bug Categories
1. **Authentication & Authorization** (15+ known bugs)
2. **Data Consistency** (20+ known bugs)
3. **UI/UX Workflows** (25+ known bugs)
4. **Service Integration** (10+ known bugs)
5. **Privacy & Compliance** (8+ known bugs)
6. **Performance** (12+ known bugs)
7. **Edge Cases** (30+ known bugs)

---

## 🔍 Regression Test Discovery

### Automated Bug Extraction
```bash
# Extract bug fixes from git commits
git log --all --grep="fix:" --grep="bug:" --oneline > /tmp/bug_commits.txt

# Extract GitHub issue references
git log --all --grep="#[0-9]" --oneline > /tmp/issue_refs.txt
```

### Manual Bug Review
- Review GitHub issues labeled "bug" or "regression"
- Review user-reported issues in support tickets
- Review production error logs
- Review code review comments mentioning "bug" or "fix"

---

## 🛠️ Tools & Infrastructure

### Testing Framework
- **pytest** - Test execution framework
- **pytest-asyncio** - Async test support
- **pytest-selenium** - Browser automation
- **pytest-xdist** - Parallel test execution
- **pytest-cov** - Coverage reporting

### CI/CD Integration
```yaml
# .github/workflows/regression-tests.yml
name: Regression Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Critical Regressions
        run: pytest tests/regression/auth/ -v --tb=short

      - name: Run Data Consistency Regressions
        run: pytest tests/regression/data_consistency/ -v --tb=short

      - name: Run Privacy Regressions
        run: pytest tests/regression/privacy/ -v --tb=short
```

---

## 📊 Success Metrics

### Quantitative Metrics
- **Regression Detection Rate**: % of bugs caught by regression tests before production
- **False Positive Rate**: % of regression test failures that aren't actual bugs
- **Test Execution Time**: Average time to run full regression suite
- **Test Flakiness Rate**: % of tests that fail intermittently

### Qualitative Metrics
- **Developer Confidence**: Survey developers on confidence in regression coverage
- **Production Bug Recurrence**: Track how many fixed bugs recur in production
- **Time to Fix Regressions**: Average time from regression detection to fix

### Target Values
- **Regression Detection Rate**: ≥95%
- **False Positive Rate**: ≤5%
- **Test Execution Time**: ≤30 minutes (full suite)
- **Test Flakiness Rate**: ≤2%
- **Production Bug Recurrence**: 0 (zero tolerance)

---

## 🎓 Best Practices

### 1. Test Isolation
- Each regression test should be fully independent
- Use database transactions that roll back after each test
- Clean up any created resources (files, containers, etc.)

### 2. Clear Documentation
- Every regression test MUST document the original bug
- Include bug ID, root cause, and expected behavior
- Link to GitHub issue or bug report

### 3. Fail Fast
- Critical regressions should fail immediately and loudly
- Provide clear error messages explaining what regressed
- Include reproduction steps in failure output

### 4. Regular Review
- Review regression test suite monthly
- Archive tests for bugs that are no longer relevant
- Update tests as codebase evolves

### 5. Performance Awareness
- Keep regression tests fast (aim for <500ms per test)
- Use mocking/stubbing for external dependencies
- Parallelize test execution where possible

---

## ✅ Implementation Checklist

### Setup Phase
- [ ] Create `tests/regression/` directory structure
- [ ] Create `conftest.py` with shared fixtures
- [ ] Create `KNOWN_BUGS_REGISTRY.md`
- [ ] Set up CI/CD integration

### Phase 1: Critical Regressions
- [ ] Implement auth regression tests (5 tests)
- [ ] Implement RBAC regression tests (5 tests)
- [ ] Implement data consistency tests (8 tests)
- [ ] Implement privacy compliance tests (5 tests)
- [ ] Implement service integration tests (5 tests)

### Phase 2: High-Priority Regressions
- [ ] Implement UI/UX regression tests (10 tests)
- [ ] Implement form validation tests (5 tests)
- [ ] Implement navigation tests (5 tests)
- [ ] Implement event propagation tests (5 tests)

### Phase 3: Medium-Priority Regressions
- [ ] Implement performance tests (6 tests)
- [ ] Implement edge case tests (10 tests)
- [ ] Implement accessibility tests (5 tests)

### Maintenance Phase
- [ ] Monthly regression test review
- [ ] Update KNOWN_BUGS_REGISTRY.md
- [ ] Monitor regression detection metrics
- [ ] Optimize slow tests

---

## 📝 Summary

**Status**: Ready to begin Phase 1 implementation
**Target**: 100+ regression tests covering all known bug categories
**Timeline**: 3-week implementation (5-7 tests/day)
**Success Criteria**: 95%+ regression detection rate, 0 production bug recurrence

**Next Steps**:
1. Create directory structure
2. Implement critical authentication regressions
3. Implement data consistency regressions
4. Implement privacy compliance regressions
5. Set up CI/CD integration

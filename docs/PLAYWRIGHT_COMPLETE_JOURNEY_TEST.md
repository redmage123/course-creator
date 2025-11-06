# Playwright Complete Platform Journey Test

## Overview

This document describes the comprehensive end-to-end test for the complete platform workflow using Playwright MCP browser automation.

**Test File**: `tests/e2e/playwright/test_complete_platform_journey.py`

---

## Test Coverage

The test covers the **complete platform journey** from user signup through analytics viewing:

### 16 Test Steps:

1. **User Signup & Organization Creation**
   - New user registration
   - Auto-redirect to organization registration
   - Organization creation with org admin role

2. **Project & Subproject Creation**
   - Create main project
   - Create 2 subprojects (Alpha, Beta)
   - Verify project hierarchy

3. **Track Creation**
   - Create 3 tracks (Python, Web Dev, Data Science)
   - Assign tracks to subprojects

4. **Instructor Enrollment & Track Assignment**
   - Enroll 3 instructors
   - Assign each instructor to specific track
   - Verify instructor dashboard access

5. **Course Material Creation (Multiple Slide Decks)**
   - **Track 1**: 3 slide decks (Python Basics, Control Flow, Functions) - 30 slides total
   - **Track 2**: 2 slide decks (HTML/CSS, JavaScript) - 35 slides total
   - **Track 3**: 3 slide decks (NumPy, Pandas, Visualization) - 37 slides total
   - **TOTAL**: 8 slide decks, 102 slides

6. **Lab Environment Testing**
   - Launch lab environment
   - Test terminal functionality
   - Test AI assistant integration
   - Execute code in terminal
   - Use AI-assisted coding

7. **Student Enrollment**
   - Enroll 4 students
   - Distribute across 3 tracks
   - Verify student dashboard access

8. **Students Read Material & Use Lab**
   - Access course material
   - Navigate through slide decks
   - Launch lab environment
   - Use AI assistant for help
   - Write and execute code
   - Track progress

9. **Instructor Creates Quiz**
   - Create quiz with multiple question types
   - Use AI-assisted question generation from slides
   - Add multiple choice questions (5)
   - Add coding questions (2)
   - Add essay question (1)
   - Set passing score and publish

10. **Students Take Quiz**
    - Access quiz from dashboard
    - Answer all questions
    - Submit quiz
    - View auto-graded score (MC + coding)
    - See essay pending instructor review

11. **Students View Own Metrics**
    - Access personal progress dashboard
    - View completion percentage
    - View quiz scores
    - View time spent
    - View lab usage statistics
    - View AI assistant usage

12. **Instructor Views Student Metrics**
    - Access instructor analytics
    - View individual student metrics
    - See detailed progress breakdown
    - Grade pending essay questions
    - Add feedback
    - Update final scores

13. **Instructor Views Track Metrics**
    - Access track-level analytics
    - View aggregate student performance
    - See module completion rates
    - View quiz score distributions
    - Identify at-risk students
    - Export track report

14. **Org Admin Views Subproject Metrics**
    - Access subproject analytics
    - View cross-track comparison
    - See aggregate performance
    - Compare instructor performance
    - View resource utilization

15. **Org Admin Views Organization-Wide Metrics**
    - Access organization dashboard
    - View platform-wide metrics
    - See usage trends
    - View top performers
    - Identify areas needing attention
    - Export executive report

16. **Complete Journey Summary**
    - Verify all steps completed
    - Summary of all activities
    - Confirmation of platform functionality

---

## Handling Self-Signed Certificates

Since the platform uses self-signed HTTPS certificates on `localhost:3000`, Playwright needs to be configured to ignore SSL certificate errors.

### Option 1: Using Playwright MCP Browser (Recommended)

The Playwright MCP browser should automatically handle certificate issues, but if needed, you can configure it:

```python
# The MCP browser tools handle this automatically
# Just use https://localhost:3000 in navigation
```

### Option 2: Using Playwright Directly with Python

If running Playwright tests directly (not through MCP):

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=['--ignore-certificate-errors']
    )
    context = browser.new_context(
        ignore_https_errors=True  # Ignore SSL errors
    )
    page = context.new_page()
    page.goto('https://localhost:3000')
```

### Option 3: Pytest Playwright Configuration

In `pytest.ini` or `pyproject.toml`:

```ini
[pytest]
playwright_browser_context_args = {
    "ignore_https_errors": True
}
```

---

## Running the Test

### Prerequisites

1. **Platform Running**: All Docker containers must be healthy
   ```bash
   ./scripts/app-control.sh status
   # Verify all services show ✅ Healthy
   ```

2. **Frontend Accessible**:
   ```bash
   curl -k https://localhost:3000/
   # Should return 200 OK
   ```

3. **Playwright MCP Available**: The MCP Playwright server must be running

### Execute Test

```bash
# Run complete journey test
pytest tests/e2e/playwright/test_complete_platform_journey.py -v --tb=short

# Run specific step
pytest tests/e2e/playwright/test_complete_platform_journey.py::TestCompletePlatformJourney::test_01_signup_and_organization_creation -v

# Run with detailed output
pytest tests/e2e/playwright/test_complete_platform_journey.py -v -s
```

---

## Test Data

The test generates unique test data for each run:

### Organization
- **Name**: `Test Org {unique_id}`
- **Domain**: `testorg{unique_id}.com`

### Project Structure
- **Main Project**: `Main Project {unique_id}`
- **Subproject 1**: `Subproject Alpha {unique_id}`
- **Subproject 2**: `Subproject Beta {unique_id}`

### Tracks
- **Track 1**: `Python Fundamentals {unique_id}` (Subproject Alpha)
- **Track 2**: `Web Development {unique_id}` (Subproject Alpha)
- **Track 3**: `Data Science {unique_id}` (Subproject Beta)

### Users
- **1 Org Admin**: `orgadmin_{unique_id}@testorg.com`
- **3 Instructors**: One per track
- **4 Students**: Distributed across tracks

---

## Implementation Status

### ✅ Completed
- Test framework structure (16 steps)
- Test data generation
- Comprehensive documentation
- Test placeholders for all steps

### 🔄 To Be Implemented
The test currently contains placeholders (`assert True`) for each step. To fully implement:

1. **Replace placeholders with Playwright MCP calls**:
   - `mcp__playwright__browser_navigate`
   - `mcp__playwright__browser_click`
   - `mcp__playwright__browser_type`
   - `mcp__playwright__browser_snapshot`
   - `mcp__playwright__browser_wait_for`

2. **Add element locators**:
   ```python
   # Example for signup
   await mcp__playwright__browser_click(
       element="Sign Up button",
       ref="button[data-testid='signup-btn']"
   )
   ```

3. **Add verification assertions**:
   ```python
   # Example verification
   snapshot = await mcp__playwright__browser_snapshot()
   assert "Dashboard" in snapshot
   ```

4. **Add proper waits**:
   ```python
   await mcp__playwright__browser_wait_for(text="Welcome")
   ```

---

## Expected Outcomes

### Success Criteria

After complete implementation and execution:

1. **Organization Created**: ✅
   - Org admin can log in
   - Organization appears in system

2. **Project Structure**: ✅
   - 1 project, 2 subprojects, 3 tracks visible
   - Hierarchy correctly displayed

3. **Users Enrolled**: ✅
   - 3 instructors assigned to tracks
   - 4 students enrolled in tracks

4. **Course Content**: ✅
   - 8 slide decks created
   - 102 slides generated
   - All slides accessible

5. **Lab Environment**: ✅
   - Terminal works
   - AI assistant responds
   - Code executes successfully

6. **Assessments**: ✅
   - 3 quizzes created
   - Students completed quizzes
   - Auto-grading works
   - Manual grading works

7. **Analytics**: ✅
   - Student metrics visible
   - Instructor analytics functional
   - Track metrics accurate
   - Subproject metrics correct
   - Organization dashboard complete

### Performance Targets

- **Test Duration**: ~30-45 minutes (full journey)
- **Success Rate**: 100% (all steps pass)
- **Data Integrity**: All data persisted correctly

---

## Troubleshooting

### Common Issues

1. **SSL Certificate Error**
   ```
   Error: net::ERR_CERT_AUTHORITY_INVALID
   ```
   **Solution**: Ensure Playwright is configured to ignore HTTPS errors (see above)

2. **Frontend Not Responding**
   ```
   Error: Navigation timeout
   ```
   **Solution**: Check frontend is running: `docker ps | grep frontend`

3. **Element Not Found**
   ```
   Error: selector not found
   ```
   **Solution**: Update element locators to match actual HTML

4. **Test Data Collision**
   ```
   Error: User already exists
   ```
   **Solution**: Each test run generates unique IDs, should not occur

5. **Lab Environment Timeout**
   ```
   Error: Lab container failed to start
   ```
   **Solution**: Check lab-manager service health

---

## Next Steps

### Phase 1: Basic Flow Implementation (Priority: HIGH)
Implement the core user journeys:
- Steps 1-3: Signup, organization, project, tracks
- Step 7: Student enrollment
- Step 11: Student metrics view

### Phase 2: Content & Learning (Priority: HIGH)
Implement content creation and consumption:
- Step 5: Course material creation
- Step 8: Students read material and use lab
- Step 6: Lab environment testing

### Phase 3: Assessments (Priority: MEDIUM)
Implement quiz workflow:
- Step 9: Quiz creation
- Step 10: Quiz taking
- Step 12: Instructor grading

### Phase 4: Analytics (Priority: MEDIUM)
Implement analytics views:
- Step 13: Track metrics
- Step 14: Subproject metrics
- Step 15: Organization metrics

### Phase 5: Instructor Management (Priority: LOW)
- Step 4: Instructor enrollment and assignment

---

## Related Documentation

- **Infrastructure Fixes**: `docs/E2E_INFRASTRUCTURE_FIXES.md`
- **Test-Specific Fixes**: `docs/E2E_TEST_FIXES_COMPLETE.md`
- **Selenium Tests**: `tests/e2e/` directory
- **Playwright MCP**: See Playwright MCP documentation

---

## Conclusion

This comprehensive test provides a framework for validating the entire platform workflow from end to end. Once fully implemented with actual Playwright MCP browser automation calls, it will serve as:

1. **Regression Test**: Ensure changes don't break core workflows
2. **Integration Test**: Verify all services work together
3. **User Journey Validation**: Confirm realistic user scenarios work
4. **Performance Benchmark**: Measure platform responsiveness
5. **Demo Script**: Show platform capabilities

The test framework is complete and ready for implementation.

---

**Document Created**: 2025-11-06
**Test Framework**: Complete (16 steps)
**Implementation**: Placeholders ready for Playwright MCP calls
**Status**: Ready for development

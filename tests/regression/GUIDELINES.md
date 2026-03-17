# Regression Test Guidelines

## Purpose

This document provides step-by-step instructions for creating regression tests when you discover and fix bugs in the Course Creator Platform.

## When to Create a Regression Test

Create a regression test when:

1. **You fix a bug** - Any bug that required a code change deserves a regression test
2. **The bug was non-trivial** - If it took time to debug, it's worth preventing
3. **The bug could recur** - If refactoring might break it again, test it
4. **The bug affected users** - Production bugs especially need tests
5. **The bug was subtle** - Hard-to-find bugs are prime candidates

## Step-by-Step Process

### Step 1: Document the Bug

Before writing code to fix the bug, document it:

```markdown
## Bug Description
- **What went wrong**: Clear description from user perspective
- **How to reproduce**: Step-by-step reproduction steps
- **Expected behavior**: What should have happened
- **Actual behavior**: What actually happened
- **Impact**: How many users affected, severity
```

### Step 2: Investigate Root Cause

Don't just fix symptoms - understand the root cause:

```markdown
## Root Cause Analysis
- **Why it happened**: Technical explanation
- **Code location**: File and line number
- **Contributing factors**: What conditions enabled the bug
- **Similar patterns**: Where else might this occur
```

### Step 3: Fix the Bug

Make the minimal change needed to fix the issue:

```python
# Before (buggy code):
if user_id not in self._cache:  # No lock - race condition
    self._cache[user_id] = fetch_user(user_id)

# After (fixed code):
async with self._lock:  # Lock prevents race condition
    if user_id not in self._cache:
        self._cache[user_id] = await fetch_user(user_id)
```

### Step 4: Create Regression Test

Now write the test that would have caught the bug.

#### Choose the Right Test File

```
tests/regression/python/
├── test_auth_bugs.py              # Authentication issues
├── test_api_routing_bugs.py       # API/nginx routing
├── test_exception_handling_bugs.py # Exception handling
├── test_race_condition_bugs.py    # Async/race conditions
├── test_enrollment_bugs.py        # Enrollment system
├── test_course_generation_bugs.py # Course generation
├── test_analytics_bugs.py         # Analytics service
└── test_rbac_bugs.py              # RBAC permissions
```

If none fit, create a new file following the naming pattern: `test_[category]_bugs.py`

#### Write the Test

Use this template:

```python
def test_bug_XXX_descriptive_name(self):
    """
    BUG #XXX: Short Title

    ORIGINAL ISSUE:
    Detailed description of what went wrong from user perspective.
    Include error messages, symptoms, and impact.

    SYMPTOMS:
    - List observable behaviors
    - Error messages users saw
    - What didn't work

    ROOT CAUSE:
    Technical explanation of why it happened.
    Include code snippets showing the problem.

    ```python
    # BUGGY CODE:
    def broken_function():
        # What was wrong
        pass
    ```

    FIX IMPLEMENTATION:
    File: path/to/file.py (line X)

    ```python
    # FIXED CODE:
    def fixed_function():
        # What changed
        pass
    ```

    Git Commit: abc123def456 (full SHA)

    REGRESSION PREVENTION:
    This test ensures the bug cannot recur by:
    - Explanation of test strategy
    - What conditions it verifies
    - How it would fail if bug recurs
    """
    # Arrange: Set up the exact conditions that caused the bug

    # Act: Perform the action that previously failed

    # Assert: Verify the fix works correctly
    pass
```

### Step 5: Update Bug Catalog

Add entry to `BUG_CATALOG.md`:

```markdown
### BUG-XXX: Short Title
- **Severity**: Critical/High/Medium/Low
- **Date Discovered**: YYYY-MM-DD
- **Date Fixed**: YYYY-MM-DD
- **Version Introduced**: vX.X.X
- **Version Fixed**: vX.X.X
- **Services Affected**: service-name
- **Git Commit**: full_sha_hash
- **Test File**: `tests/regression/python/test_category_bugs.py::test_bug_XXX`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- What users experienced

**Root Cause**:
- Technical explanation

**Fix**:
- What was changed

**Related Bugs**: BUG-YYY, BUG-ZZZ (if any)
```

### Step 6: Assign Bug ID

Bug IDs are sequential:

1. Check `BUG_CATALOG.md` for the highest existing BUG-XXX number
2. Use next number (e.g., if highest is BUG-015, use BUG-016)
3. Update test documentation with new bug ID
4. Update catalog with new entry
5. Update statistics in catalog

### Step 7: Write Test Documentation

Every test MUST have comprehensive documentation:

#### Required Sections:

1. **Bug Title**: Short, descriptive (< 60 chars)
2. **Original Issue**: What went wrong (user perspective)
3. **Symptoms**: Observable behaviors, errors
4. **Root Cause**: Technical explanation
5. **Fix Implementation**: Code changes with file/line refs
6. **Git Commit**: Full SHA-1 hash
7. **Regression Prevention**: Test strategy explanation

#### Documentation Best Practices:

- **Be Specific**: Include actual error messages, file paths, line numbers
- **Be Complete**: Someone unfamiliar should understand the bug
- **Be Accurate**: Test what you document, document what you test
- **Be Educational**: Explain why the bug happened and how it was fixed
- **Link Everything**: Git commits, related bugs, affected files

### Step 8: Test Your Test

Verify your regression test works:

#### Test the Test Fails with Bug:

```bash
# Temporarily revert your fix
git stash

# Run the regression test - should FAIL
pytest tests/regression/python/test_category_bugs.py::test_bug_XXX -v

# If test passes with bug present, test is ineffective!
# Revise test to actually detect the bug

# Restore your fix
git stash pop
```

#### Test the Test Passes with Fix:

```bash
# Run the regression test - should PASS
pytest tests/regression/python/test_category_bugs.py::test_bug_XXX -v

# If test fails with fix present, test is broken
# Debug and fix the test
```

### Step 9: Integration with Codebase

Add your test to the test suite:

1. **Local Testing**:
   ```bash
   # Run your specific test
   pytest tests/regression/python/test_category_bugs.py::test_bug_XXX -v

   # Run all regression tests
   pytest tests/regression/python/ -v

   # Run with coverage
   pytest tests/regression/python/ --cov=services --cov-report=html
   ```

2. **Update Test Documentation**:
   - Add test to README.md if new category
   - Update test count in BUG_CATALOG.md
   - Update statistics

3. **Commit with Proper Message**:
   ```bash
   git add tests/regression/python/test_category_bugs.py
   git add tests/regression/BUG_CATALOG.md
   git commit -m "test: Add regression test for BUG-XXX (short description)

   Documents and prevents recurrence of bug where [brief explanation].

   - Test File: tests/regression/python/test_category_bugs.py
   - Bug ID: BUG-XXX
   - Severity: [Critical/High/Medium/Low]
   - Services: [affected services]

   Related to commit abc123def456 which fixed the original bug."
   ```

## Test Writing Best Practices

### Do's:

1. ✅ **Test Exact Bug Conditions**: Reproduce the precise scenario that caused the bug
2. ✅ **Use Descriptive Names**: `test_bug_001_login_redirect_org_admin` not `test_bug_1`
3. ✅ **Document Everything**: Each test should read like a bug report
4. ✅ **Test Edge Cases**: If bug was an edge case, test similar edges
5. ✅ **Keep Tests Isolated**: Each test should be independent
6. ✅ **Mock External Dependencies**: Don't depend on running services for unit tests
7. ✅ **Assert Specifically**: Check the exact thing that was broken
8. ✅ **Include Both Versions**: Show buggy behavior AND fixed behavior

### Don'ts:

1. ❌ **Don't Test General Functionality**: Regression tests are for specific bugs
2. ❌ **Don't Skip Documentation**: Undocumented tests are useless long-term
3. ❌ **Don't Test Multiple Bugs**: One test per bug (unless truly related)
4. ❌ **Don't Use Generic Assertions**: `assert result` tells nothing
5. ❌ **Don't Ignore Root Cause**: Understanding why matters for prevention
6. ❌ **Don't Forget Git Commit**: Link to the fix for context
7. ❌ **Don't Make Tests Brittle**: Test behavior, not implementation details
8. ❌ **Don't Skip the "Why"**: Explain why the bug happened and why test prevents it

## Example: Complete Workflow

Let's walk through creating a regression test for a fictional bug:

### 1. Bug Report

```
User reports: "When I create a course, the title is truncated after 50 characters,
but I can enter 255 characters in the form."
```

### 2. Root Cause Investigation

```python
# File: services/course-management/data_access/course_dao.py:123

# BUGGY CODE:
async def create_course(self, title: str) -> Course:
    # Database column is VARCHAR(50) but form allows 255 chars
    await self.db.execute(
        "INSERT INTO courses (title) VALUES (?)", (title,)
    )
    # Silently truncates at 50 characters!
```

### 3. Fix

```python
# FIXED CODE:
async def create_course(self, title: str) -> Course:
    # Validate title length before database insert
    if len(title) > 50:
        raise ValidationException(
            f"Course title must be 50 characters or less, got {len(title)}"
        )

    await self.db.execute(
        "INSERT INTO courses (title) VALUES (?)", (title,)
    )
```

### 4. Regression Test

```python
# File: tests/regression/python/test_course_generation_bugs.py

def test_bug_025_course_title_truncation(self):
    """
    BUG #025: Course Title Silent Truncation

    ORIGINAL ISSUE:
    When users created courses with titles longer than 50 characters,
    the title was silently truncated in the database despite the form
    allowing 255 characters. Users didn't know their titles were cut off.

    SYMPTOMS:
    - Course titles truncated after 50 characters
    - No error message to user
    - Form validation allowed 255 characters
    - Database schema mismatch
    - Silent data loss

    ROOT CAUSE:
    Database column was VARCHAR(50) but UI form allowed 255 characters.
    No validation between form and database layer.

    File: services/course-management/data_access/course_dao.py:123

    FIX IMPLEMENTATION:
    Added validation to raise ValidationException for titles > 50 chars.
    Git Commit: def456abc789...

    REGRESSION PREVENTION:
    Test ensures:
    1. Titles <= 50 chars are accepted
    2. Titles > 50 chars raise ValidationException
    3. Error message includes actual length
    4. No silent truncation occurs
    """
    # Arrange
    class MockCourseDAO:
        MAX_TITLE_LENGTH = 50

        async def create_course(self, title: str):
            if len(title) > self.MAX_TITLE_LENGTH:
                raise ValidationException(
                    f"Course title must be {self.MAX_TITLE_LENGTH} "
                    f"characters or less, got {len(title)}"
                )
            return {"id": 1, "title": title}

    dao = MockCourseDAO()

    # Act & Assert: Test 1 - Valid title (50 chars) works
    valid_title = "A" * 50
    result = await dao.create_course(valid_title)
    assert result["title"] == valid_title

    # Test 2 - Title > 50 chars raises exception
    long_title = "A" * 51
    with pytest.raises(ValidationException) as exc_info:
        await dao.create_course(long_title)

    # Test 3 - Error message includes length
    assert "51" in str(exc_info.value)
    assert "50" in str(exc_info.value)

    # Test 4 - Much longer title also fails (not just edge case)
    very_long_title = "A" * 255
    with pytest.raises(ValidationException):
        await dao.create_course(very_long_title)
```

### 5. Bug Catalog Entry

```markdown
### BUG-025: Course Title Silent Truncation
- **Severity**: High
- **Date Discovered**: 2025-11-05
- **Date Fixed**: 2025-11-05
- **Version Introduced**: v3.0.0
- **Version Fixed**: v3.5.1
- **Services Affected**: course-management
- **Git Commit**: def456abc789...
- **Test File**: `tests/regression/python/test_course_generation_bugs.py::test_bug_025`
- **Status**: ✅ Covered by regression test

**Symptoms**:
- Course titles silently truncated at 50 characters
- No validation error shown to user
- Form allowed 255 characters but database only stored 50

**Root Cause**:
Database column VARCHAR(50) but form validation allowed 255 characters.
No validation layer between form and database.

**Fix**:
Added validation in course_dao.py to raise ValidationException for titles > 50 chars.
Provides clear error message with actual vs maximum length.

**Related Bugs**: None
```

### 6. Commit

```bash
git add tests/regression/python/test_course_generation_bugs.py
git add tests/regression/BUG_CATALOG.md
git commit -m "test: Add regression test for BUG-025 (course title truncation)

Documents and prevents recurrence of silent course title truncation bug.

- Test File: tests/regression/python/test_course_generation_bugs.py
- Bug ID: BUG-025
- Severity: High
- Services: course-management

Related to commit def456abc789 which fixed the original bug."
```

## React Frontend Tests

For frontend bugs, follow similar process but use React Testing Library or Vitest:

```typescript
// File: tests/regression/react/test_form_bugs.test.tsx

describe('BUG-030: Password Eye Icon Disappears on Focus', () => {
  /**
   * BUG #030: Password Eye Icon Disappears on Focus
   *
   * ORIGINAL ISSUE:
   * When user clicked password input, eye icon disappeared
   *
   * USER IMPACT:
   * Cannot toggle password visibility after clicking input
   *
   * ROOT CAUSE:
   * CSS z-index issue - input focus created stacking context
   * that covered toggle button
   *
   * FIX:
   * Added z-index: 10 to toggle button
   * File: frontend/js/modules/ui-components.js
   *
   * REGRESSION TEST:
   * Verifies toggle button remains visible when input focused
   */

  it('toggle button visible when input focused', () => {
    const { getByTestId } = render(<PasswordInput />);

    const input = getByTestId('password-input');
    const toggle = getByTestId('password-toggle');

    // Before focus
    expect(toggle).toBeVisible();

    // Focus input
    fireEvent.focus(input);

    // After focus - button still visible
    expect(toggle).toBeVisible();

    // Button is clickable
    fireEvent.click(toggle);
    expect(input).toHaveAttribute('type', 'text');
  });
});
```

## Finding Bugs to Test

### Sources of Bug Information:

1. **Git History**:
   ```bash
   git log --all --grep="fix:" --grep="bug:" --oneline
   ```

2. **GitHub Issues**: Look for closed issues labeled "bug"

3. **Code Comments**: Search for TODO, FIXME, XXX comments

4. **Defensive Code**: Lots of null checks often indicate past bugs

5. **Production Logs**: Errors that occurred in production

6. **User Reports**: Customer support tickets

### Bug Categories to Prioritize:

1. **Critical Bugs**: System crashes, data loss, security issues
2. **High-Frequency Bugs**: Issues that affect many users
3. **Subtle Bugs**: Hard-to-find bugs that took time to debug
4. **Regression-Prone**: Areas of code that break often during refactoring

## Maintenance

### Regular Review:

- **Monthly**: Review regression test coverage by service
- **Per Release**: Run full regression suite before deployment
- **Post-Incident**: Add tests for any production bugs

### Cleanup:

- **Remove Obsolete Tests**: If feature is removed, remove its regression tests
- **Update Documentation**: Keep bug catalog current
- **Refactor Tests**: Improve test quality over time

### Metrics to Track:

- Total bugs documented
- Test coverage per service
- Critical bugs with tests
- Regression test pass rate
- Time to add test after bug fix

## Questions?

If you're unsure about:
- Which test file to use → Start a new file if no category fits
- How to reproduce bug → Document what you know and ask for help
- Test is too complex → Break into smaller tests
- Bug not worth testing → When in doubt, test it

## Related Documentation

- `tests/regression/README.md` - Overview
- `tests/regression/BUG_CATALOG.md` - All documented bugs
- `/claude.md/08-testing-strategy.md` - Overall testing approach
- `/tests/COMPREHENSIVE_E2E_TEST_PLAN.md` - E2E testing

# TDD (Test-Driven Development) Workflow

**Purpose:** Standard TDD workflow for ALL code changes

**Usage:** MANDATORY for every feature, bug fix, or refactoring

---

## 🔴 Phase 1: RED (Write Failing Test)

### Step 1: Create Test File
```bash
# For Python
touch tests/test_<feature_name>.py

# For JavaScript
touch tests/<feature_name>.test.js
```

### Step 2: Write Failing Test
```python
# Python example
def test_feature_does_not_exist():
    """
    This test SHOULD fail initially - proving the feature doesn't exist yet.
    This is the RED phase of TDD.
    """
    # Arrange
    expected_result = <expected output>

    # Act
    actual_result = new_feature_function()

    # Assert
    assert actual_result == expected_result
```

```javascript
// JavaScript example
describe('New Feature', () => {
  it('should not exist yet (RED phase)', () => {
    // Arrange
    const expectedResult = <expected output>;

    // Act
    const actualResult = newFeatureFunction();

    // Assert
    expect(actualResult).toBe(expectedResult);
  });
});
```

### Step 3: Run Test (Confirm RED)
```bash
# Python
pytest tests/test_<feature_name>.py -v

# JavaScript
npm test tests/<feature_name>.test.js

# Expected Output: FAILED (feature not implemented)
```

**✅ Checkpoint:**
- [ ] Test file created
- [ ] Test written
- [ ] Test runs and FAILS
- [ ] Failure message is clear

---

## 🟢 Phase 2: GREEN (Minimal Implementation)

### Step 1: Implement Minimal Code
Write the MINIMUM code needed to pass the test. Don't over-engineer.

```python
# Python example
def new_feature_function():
    """Minimal implementation to pass test"""
    return <expected output>
```

```javascript
// JavaScript example
function newFeatureFunction() {
  // Minimal implementation to pass test
  return <expected output>;
}
```

### Step 2: Run Test (Confirm GREEN)
```bash
# Python
pytest tests/test_<feature_name>.py -v

# JavaScript
npm test tests/<feature_name>.test.js

# Expected Output: PASSED
```

**✅ Checkpoint:**
- [ ] Minimal code implemented
- [ ] Test runs and PASSES
- [ ] No over-engineering (just enough to pass)

---

## 🔵 Phase 3: REFACTOR (Improve Quality)

### Step 1: Refactor Code
Now improve code quality without changing behavior:
- Extract functions
- Improve naming
- Add documentation
- Optimize performance
- Follow SOLID principles

### Step 2: Run Full Test Suite
```bash
# Python
pytest tests/ -v

# JavaScript
npm test

# Expected Output: ALL TESTS PASSED
```

### Step 3: Verify No Regressions
```bash
# Check that refactoring didn't break anything
pytest tests/ -v --tb=short

# All tests should still pass
```

**✅ Checkpoint:**
- [ ] Code refactored for quality
- [ ] All tests still pass
- [ ] No regressions introduced
- [ ] Code documented

---

## 📊 Phase 4: VERIFY (Evidence Collection)

### Step 1: Run Complete Test Suite
```bash
# Python
pytest tests/ -v --cov --cov-report=term

# JavaScript
npm test -- --coverage
```

### Step 2: Collect Evidence
```markdown
## Test Results

### Feature Tests
- Test file: tests/test_<feature>.py
- Tests run: <number>
- Tests passed: <number>
- Tests failed: <number>

### Full Suite
- Total tests: <number>
- Passed: <number>
- Failed: <number>
- Coverage: <percentage>%

### Output
```
<paste actual test output>
```
```

**✅ Checkpoint:**
- [ ] All tests pass
- [ ] Evidence collected
- [ ] Coverage adequate
- [ ] Ready to commit

---

## 🔄 Phase 5: INTEGRATE (Memory & Commit)

### Step 1: Update Memory
```bash
# Add new facts discovered
python3 .claude/query_memory.py add "Feature <name> implemented with TDD - tests at tests/test_<name>.py" "testing" "medium"

python3 .claude/query_memory.py add "Bug fix: <description> - root cause: <cause>" "bugfix" "high"
```

### Step 2: Mark TodoWrite Complete
```javascript
TodoWrite([
  {"content": "Write failing test", "status": "completed"},
  {"content": "Implement feature", "status": "completed"},
  {"content": "Refactor", "status": "completed"},
  {"content": "Verify tests", "status": "completed"},
  {"content": "Update memory", "status": "completed"}
])
```

### Step 3: Commit with Evidence
```bash
git add <files>
git commit -m "feat: Add <feature> with TDD

Tests: <X> passed, <Y> total
Coverage: <Z>%
TDD approach: Red-Green-Refactor

Test file: tests/test_<feature>.py
..."
```

**✅ Checkpoint:**
- [ ] Memory updated
- [ ] TodoWrite marked complete
- [ ] Committed with evidence
- [ ] Tests included in commit

---

## 🎯 TDD Checklist (Use Every Time)

### Before Starting
- [ ] Did I search memory for existing facts?
- [ ] Did I create TodoWrite board?
- [ ] Is this task appropriate for TDD?

### During Development
- [ ] Did I write test FIRST (before code)?
- [ ] Did test fail initially (RED phase)?
- [ ] Did I implement minimal code (GREEN phase)?
- [ ] Did I refactor for quality?
- [ ] Did all tests pass after refactor?

### Before Claiming Complete
- [ ] Do ALL tests pass (not just new ones)?
- [ ] Is test output captured as evidence?
- [ ] Did I update memory with new facts?
- [ ] Did I mark TodoWrite tasks complete?
- [ ] Did I use tentative language (no false claims)?

---

## 🚨 Red Flags (Don't Proceed If)

- ❌ Writing code before tests
- ❌ Tests passing on first run (not a real test)
- ❌ Skipping refactor phase
- ❌ Not running full test suite
- ❌ Claiming success without evidence

---

## 📋 TDD Examples

### Example 1: New Feature

**Feature:** Add user email validation

**RED:**
```python
def test_email_validation_rejects_invalid_format():
    assert validate_email("not-an-email") == False
    # FAILS - function doesn't exist
```

**GREEN:**
```python
def validate_email(email):
    return "@" in email and "." in email
    # PASSES - minimal implementation
```

**REFACTOR:**
```python
import re

def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
    # PASSES - improved implementation
```

### Example 2: Bug Fix

**Bug:** API returns 500 instead of 404 for missing user

**RED:**
```python
def test_api_returns_404_for_missing_user():
    response = client.get("/api/users/nonexistent")
    assert response.status_code == 404
    # FAILS - currently returns 500
```

**GREEN:**
```python
@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
    # PASSES - returns 404 correctly
```

**REFACTOR:**
```python
@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Database = Depends(get_db)):
    """
    Get user by ID.

    Returns 404 if user not found.
    """
    try:
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        return user
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise
    # PASSES - improved error handling and documentation
```

---

## 💡 TDD Best Practices

1. **Write Small Tests**
   - One assertion per test
   - Test one behavior at a time
   - Clear test names

2. **Red-Green-Refactor Cycle**
   - Always see RED first (proves test works)
   - Implement GREEN (minimal code)
   - Then REFACTOR (improve quality)

3. **Test Behavior, Not Implementation**
   - Test what it does, not how it does it
   - Allows refactoring without breaking tests

4. **Keep Tests Fast**
   - Mock external dependencies
   - Use in-memory databases for tests
   - Aim for sub-second test runs

5. **Maintain Test Quality**
   - Tests are code too
   - Keep them clean and readable
   - Refactor tests when needed

---

**Last Updated:** 2025-10-05
**Status:** Active Template
**Usage:** MANDATORY for all code changes

# Lab Environment E2E Test Suite Report

**Author:** Claude Code  
**Date:** 2025-11-05  
**Test Suite:** Lab Timeout/Cleanup and Multi-IDE Support  
**Status:** COMPLETE - TDD RED PHASE

---

## Executive Summary

Successfully created comprehensive E2E Selenium test suite for lab timeout/cleanup and multi-IDE support with **20 total tests** across 2 test files.

### Quick Stats
- **Total Tests Created:** 20 tests
- **Total Lines of Code:** 1,792 lines
- **Test Files:** 2 files
- **Fixture Files:** 1 file (conftest.py)
- **Page Objects:** 3 classes
- **Test Classes:** 5 classes

---

## 1. Test Files Created

### File 1: `test_lab_timeout_cleanup.py`
**Purpose:** Test lab timeout mechanisms and automated cleanup workflows

**Statistics:**
- Lines of Code: 1,056 lines
- Number of Tests: 12 tests
- Page Objects: 3 (LabPage, StudentDashboardPage, LoginPage)
- Test Classes: 3

**Test Breakdown:**

#### Class 1: TestLabTimeoutMechanisms (5 tests)
1. `test_lab_timeout_warning_displayed` - Verifies warning appears 15 min before timeout
2. `test_lab_timeout_countdown_visible` - Verifies countdown timer updates in real-time
3. `test_lab_auto_stops_after_inactivity_timeout` - Verifies lab stops after 2 hours inactivity
4. `test_student_can_extend_timeout` - Verifies students can extend timeout
5. `test_lab_cannot_exceed_max_duration` - Verifies 8-hour max duration enforced

#### Class 2: TestLabCleanupWorkflows (4 tests)
6. `test_lab_cleanup_on_student_logout` - Verifies cleanup on logout
7. `test_lab_cleanup_on_course_completion` - Verifies cleanup on course completion
8. `test_lab_cleanup_on_enrollment_removal` - Verifies cleanup on unenrollment
9. `test_lab_cleanup_on_course_deletion` - Verifies cleanup on course deletion

#### Class 3: TestLabOrphanDetection (3 tests)
10. `test_detect_orphaned_containers` - Verifies orphan detection system
11. `test_cleanup_orphaned_containers_automatically` - Verifies automated orphan cleanup
12. `test_alert_admin_of_cleanup_failures` - Verifies admin alerts for failures

---

### File 2: `test_multi_ide_support.py`
**Purpose:** Test multiple IDE support in lab environments

**Statistics:**
- Lines of Code: 736 lines
- Number of Tests: 8 tests
- Page Objects: 2 (MultiIDELabPage, LoginPage)
- Test Classes: 2

**Test Breakdown:**

#### Class 1: TestIDETypes (4 tests)
1. `test_launch_lab_with_vscode_ide` - Launch and verify VS Code IDE
2. `test_launch_lab_with_jupyterlab_ide` - Launch and verify JupyterLab IDE
3. `test_launch_lab_with_terminal_only` - Launch and verify terminal-only environment
4. `test_switch_between_ides_within_same_lab` - Verify IDE switching without data loss

#### Class 2: TestIDEFeatures (4 tests)
5. `test_code_syntax_highlighting_working` - Verify syntax highlighting active
6. `test_file_explorer_navigation` - Verify file explorer functional
7. `test_terminal_emulator_functional` - Verify terminal emulator works
8. `test_extensions_plugins_loaded` - Verify IDE extensions loaded

---

### File 3: `conftest.py`
**Purpose:** Pytest fixtures for lab environment tests

**Statistics:**
- Lines of Code: 92 lines
- Fixtures Provided: 5

**Fixtures:**
1. `docker_client` - Docker API client for container verification
2. `db_connection` - PostgreSQL connection for lab_sessions queries
3. `cleanup_test_labs` - Cleanup test containers/sessions after tests
4. `test_student_credentials` - Student credentials for authentication
5. `accelerated_timeout_env` - Accelerated timeout environment variables

---

## 2. Timeout Testing Approach

### Accelerated Timeout Strategy

**Problem:** Real timeouts too long for testing
- Real inactivity timeout: 2 hours
- Real max duration: 8 hours
- Real warning time: 15 minutes

**Solution:** Use accelerated timeouts via environment variables

```python
@pytest.fixture
def accelerated_timeout_env(monkeypatch):
    monkeypatch.setenv('LAB_INACTIVITY_TIMEOUT_SECONDS', '5')      # 5s instead of 2h
    monkeypatch.setenv('LAB_MAX_DURATION_SECONDS', '30')            # 30s instead of 8h
    monkeypatch.setenv('LAB_TIMEOUT_WARNING_SECONDS', '3')          # 3s instead of 15m
```

**Benefits:**
- Tests complete in seconds instead of hours
- Same logic tested (timeout mechanisms)
- Environment variables easy to configure

**Verification Strategy:**
1. **UI Verification:** Check timeout warning displayed
2. **Docker Verification:** Verify container actually stopped via docker-py
3. **Database Verification:** Verify lab_sessions table updated
4. **Three-layer validation:** UI + Container + Database

### Timeout Test Pattern

```python
@pytest.mark.asyncio
async def test_lab_auto_stops_after_inactivity_timeout(
    accelerated_timeout_env,
    docker_client,
    db_connection,
    test_student_credentials
):
    # Start lab
    lab_page.start_lab()
    
    # Get container
    containers = docker_client.containers.list(filters={"name": "lab_*"})
    container_id = containers[0].id
    
    # Wait for timeout (5 seconds with accelerated timeout)
    time.sleep(6)
    
    # VERIFICATION 1: UI shows stopped
    lab_status = lab_page.get_lab_status()
    assert "Stopped" in lab_status
    
    # VERIFICATION 2: Container actually stopped
    container = docker_client.containers.get(container_id)
    assert container.status in ["exited", "stopped"]
    
    # VERIFICATION 3: Database updated
    cursor.execute("SELECT status, ended_at FROM lab_sessions WHERE container_id = %s", (container_id,))
    row = cursor.fetchone()
    assert row[0] == 'stopped'
    assert row[1] is not None
```

---

## 3. Multi-IDE Verification Strategy

### IDE Type Verification

**Challenge:** Verify correct Docker image launched for each IDE type

**Approach:** Use docker-py to inspect container image

```python
# Get container
containers = docker_client.containers.list(filters={"name": "lab_*"})
container = containers[0]

# Check image name
image_name = container.image.tags[0] if container.image.tags else ""

# Verify IDE-specific image
if ide_type == 'vscode':
    assert "vscode" in image_name.lower() or "code-server" in image_name.lower()
elif ide_type == 'jupyter':
    assert "jupyter" in image_name.lower() or "jupyterlab" in image_name.lower()
elif ide_type == 'terminal':
    assert any(term in image_name.lower() for term in ['alpine', 'debian', 'ubuntu', 'terminal'])
```

### IDE Feature Verification

**Challenge:** Verify IDE-specific features work (syntax highlighting, file explorer, terminal)

**Approach:** Switch to iframe and inspect IDE UI elements

```python
def is_ide_loaded(self, ide_type):
    # Switch to lab iframe
    iframe = self.wait_for_element_visible(self.LAB_IFRAME, timeout=30)
    self.driver.switch_to.frame(iframe)
    
    # Check IDE-specific elements
    if ide_type == 'vscode':
        editor = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "monaco-workbench"))
        )
        result = editor.is_displayed()
    elif ide_type == 'jupyter':
        notebook = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jp-Notebook"))
        )
        result = notebook.is_displayed()
    elif ide_type == 'terminal':
        terminal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "xterm"))
        )
        result = terminal.is_displayed()
    
    self.driver.switch_to.default_content()
    return result
```

**IDE-Specific Elements:**
- **VS Code:** `.monaco-workbench`, `.monaco-editor`, `.explorer-viewlet`
- **JupyterLab:** `.jp-Notebook`, `.jp-FileBrowser`, `.jp-TerminalPanel`
- **Terminal:** `.xterm`, `.terminal-outer-container`

### IDE Performance Testing

**Load Time Requirements:**
- VS Code: < 30 seconds
- JupyterLab: < 30 seconds
- Terminal: < 10 seconds (minimal UI)

**Implementation:**
```python
start_time = time.time()
lab_page.start_lab(ide_type='vscode')
assert lab_page.is_ide_loaded('vscode')
load_time = time.time() - start_time
assert load_time < 30, f"VS Code should load in < 30 seconds, took {load_time:.1f}s"
```

### IDE Switching Test

**Critical Requirement:** Switching IDEs must not restart container

**Verification:**
```python
# Get initial container ID
containers = docker_client.containers.list(filters={"name": "lab_*"})
initial_container_id = containers[0].id

# Switch IDE
lab_page.switch_ide('jupyter')

# Verify same container
containers = docker_client.containers.list(filters={"name": "lab_*"})
current_container_id = containers[0].id
assert current_container_id == initial_container_id, "Same container should be used"
```

---

## 4. Challenges with Accelerated Timeout Testing

### Challenge 1: Timing Precision

**Issue:** Accelerated timeouts require precise timing
- 5-second timeout means tests must wait exactly 6 seconds
- Too short → test fails (timeout not triggered)
- Too long → test takes longer than necessary

**Solution:** Add small buffer (0.5-1 second) to timeout wait

```python
# Wait for timeout (5 seconds) + 1 second buffer
time.sleep(6)
```

### Challenge 2: Race Conditions

**Issue:** Cleanup may not be instant
- Container stops asynchronously
- Database updates may lag
- UI updates may lag

**Solution:** Poll for expected state with timeout

```python
# Poll for stopped status (max 5 seconds)
for _ in range(10):
    container = docker_client.containers.get(container_id)
    if container.status in ["exited", "stopped"]:
        break
    time.sleep(0.5)
else:
    pytest.fail("Container should stop within 5 seconds")
```

### Challenge 3: Environment Variable Propagation

**Issue:** Environment variables must reach lab-manager service
- Tests set env vars in test process
- Lab-manager service may not see them

**Solution:** Document requirement for lab-manager to read env vars

```python
# In lab-manager service
INACTIVITY_TIMEOUT = int(os.getenv('LAB_INACTIVITY_TIMEOUT_SECONDS', '7200'))  # Default 2h
MAX_DURATION = int(os.getenv('LAB_MAX_DURATION_SECONDS', '28800'))             # Default 8h
TIMEOUT_WARNING = int(os.getenv('LAB_TIMEOUT_WARNING_SECONDS', '900'))         # Default 15m
```

### Challenge 4: Cleanup Side Effects

**Issue:** Test labs may interfere with other tests
- Orphaned containers from failed tests
- Database sessions not cleaned up

**Solution:** Use cleanup fixtures that run after each test

```python
@pytest.fixture
def cleanup_test_labs(docker_client, db_connection):
    yield
    
    # Cleanup containers
    containers = docker_client.containers.list(filters={"name": "lab_test_*"})
    for container in containers:
        container.stop(timeout=5)
        container.remove(force=True)
    
    # Cleanup database
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM lab_sessions WHERE container_name LIKE 'lab_test_%'")
    db_connection.commit()
```

### Challenge 5: Docker API Permissions

**Issue:** Tests require Docker API access
- May not work in all CI environments
- Requires docker socket access

**Solution:** Document Docker requirement and provide skip logic

```python
@pytest.fixture(scope="session")
def docker_client():
    try:
        client = docker.from_env()
        yield client
        client.close()
    except docker.errors.DockerException:
        pytest.skip("Docker not available")
```

---

## 5. Page Object Model (POM) Implementation

### Benefits of POM Pattern

1. **Maintainability:** UI changes only affect page objects, not tests
2. **Reusability:** Page objects shared across tests
3. **Readability:** Tests read like user stories
4. **Separation of Concerns:** Test logic separated from UI interaction

### Page Objects Created

#### 1. LabPage (Timeout Tests)
```python
class LabPage(BasePage):
    # Locators
    START_LAB_BUTTON = (By.ID, "start-lab-button")
    TIMEOUT_WARNING = (By.ID, "timeout-warning")
    EXTEND_TIMEOUT_BUTTON = (By.ID, "extend-timeout-button")
    
    # Methods
    def start_lab(self)
    def get_lab_status(self)
    def extend_timeout(self)
    def is_timeout_warning_visible(self)
```

#### 2. MultiIDELabPage (Multi-IDE Tests)
```python
class MultiIDELabPage(BasePage):
    # Locators
    IDE_TAB_VSCODE = (By.CSS_SELECTOR, "[data-ide='vscode']")
    IDE_TAB_JUPYTER = (By.CSS_SELECTOR, "[data-ide='jupyter']")
    LAB_IFRAME = (By.ID, "lab-iframe")
    
    # Methods
    def start_lab(self, ide_type='vscode')
    def switch_ide(self, ide_type)
    def is_ide_loaded(self, ide_type)
    def is_file_explorer_visible(self)
    def is_terminal_accessible(self)
```

#### 3. LoginPage (Both)
```python
class LoginPage(BasePage):
    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    
    # Methods
    def navigate(self)
    def login(self, email, password)
```

---

## 6. Test Execution Strategy

### Running Individual Test Files

```bash
# Run timeout/cleanup tests only
pytest tests/e2e/lab_environment/test_lab_timeout_cleanup.py -v

# Run multi-IDE tests only
pytest tests/e2e/lab_environment/test_multi_ide_support.py -v
```

### Running by Test Class

```bash
# Run only timeout mechanism tests
pytest tests/e2e/lab_environment/test_lab_timeout_cleanup.py::TestLabTimeoutMechanisms -v

# Run only IDE type tests
pytest tests/e2e/lab_environment/test_multi_ide_support.py::TestIDETypes -v
```

### Running by Priority

```bash
# Run only critical priority tests
pytest tests/e2e/lab_environment/ -m priority_critical -v

# Run high priority tests
pytest tests/e2e/lab_environment/ -m priority_high -v
```

### Running with Accelerated Timeouts

```bash
# Set environment variables for accelerated timeouts
export LAB_INACTIVITY_TIMEOUT_SECONDS=5
export LAB_MAX_DURATION_SECONDS=30
export LAB_TIMEOUT_WARNING_SECONDS=3

pytest tests/e2e/lab_environment/test_lab_timeout_cleanup.py -v
```

---

## 7. Expected Test Results (TDD RED Phase)

### All Tests Expected to FAIL Initially

This is **CORRECT** and follows TDD methodology:
1. **RED Phase:** Write failing tests (current phase)
2. **GREEN Phase:** Implement features to make tests pass
3. **REFACTOR Phase:** Optimize implementation

### Common Failure Reasons (Expected)

1. **UI Elements Not Found:**
   - `timeout-warning` element doesn't exist yet
   - `extend-timeout-button` doesn't exist yet
   - `ide-selector` doesn't exist yet

2. **API Endpoints Not Implemented:**
   - `/api/v1/courses/complete` returns 404
   - `/api/v1/enrollments/remove` returns 404
   - Cleanup jobs not scheduled

3. **Database Tables Missing:**
   - `cleanup_failures` table doesn't exist
   - `audit_log` table doesn't exist
   - `lab_sessions` may need additional columns

4. **Container Images Not Built:**
   - VS Code container image doesn't exist
   - JupyterLab container image doesn't exist
   - Terminal container image doesn't exist

### When Tests Should Pass

Tests will pass when:
1. Lab-manager service implements timeout logic
2. Cleanup jobs scheduled and working
3. Multi-IDE support implemented in frontend
4. Docker images built for each IDE type
5. Database schema updated
6. API endpoints implemented

---

## 8. Business Requirements Coverage

### Timeout Mechanisms ✓
- [x] Lab timeout warning (15 min before expiry)
- [x] Lab timeout countdown visible in UI
- [x] Lab auto-stops after inactivity timeout (2 hours)
- [x] Student can extend timeout before expiry
- [x] Lab cannot be extended beyond max duration (8 hours)

### Cleanup Workflows ✓
- [x] Lab cleanup on student logout
- [x] Lab cleanup on course completion
- [x] Lab cleanup on enrollment removal
- [x] Lab cleanup on course deletion

### Orphan Detection ✓
- [x] Detect orphaned containers (no associated session)
- [x] Cleanup orphaned containers automatically (daily job)
- [x] Alert admin of cleanup failures

### Multi-IDE Support ✓
- [x] Launch lab with VS Code IDE
- [x] Launch lab with JupyterLab IDE
- [x] Launch lab with terminal-only environment
- [x] Switch between IDEs within same lab

### IDE Features ✓
- [x] Code syntax highlighting working
- [x] File explorer navigation
- [x] Terminal emulator functional
- [x] Extensions/plugins loaded

---

## 9. Code Quality Metrics

### Documentation Coverage
- **Every test has:**
  - Comprehensive docstring
  - Business requirement explanation
  - Test scenario steps
  - Validation criteria
  - Technical notes (accelerated timeouts, etc.)

### Test Markers
- `@pytest.mark.e2e` - E2E test
- `@pytest.mark.lab_environment` - Lab environment category
- `@pytest.mark.timeout` - Timeout-related
- `@pytest.mark.cleanup` - Cleanup-related
- `@pytest.mark.multi_ide` - Multi-IDE related
- `@pytest.mark.priority_critical` - Critical priority
- `@pytest.mark.priority_high` - High priority
- `@pytest.mark.priority_medium` - Medium priority
- `@pytest.mark.asyncio` - Async test

### Error Handling
- All Docker operations wrapped in try/except
- All database operations use cursor cleanup
- All iframe switches have default_content fallback
- All tests have cleanup fixtures

---

## 10. Integration with Existing Test Infrastructure

### Selenium Base Classes
Tests use existing `selenium_base.py`:
- `BasePage` - Page object base class
- `BaseTest` - Test base class
- Provides wait utilities, screenshot capture, etc.

### Pytest Configuration
Tests integrate with existing `conftest.py`:
- Uses session-scoped fixtures
- Compatible with existing markers
- Follows existing patterns

### CI/CD Integration
Tests ready for GitHub Actions:
```yaml
- name: Run Lab E2E Tests
  run: |
    export LAB_INACTIVITY_TIMEOUT_SECONDS=5
    export LAB_MAX_DURATION_SECONDS=30
    pytest tests/e2e/lab_environment/ -v --tb=short
```

---

## 11. Next Steps (GREEN Phase)

### 1. Implement Timeout Logic in Lab-Manager
- Add inactivity tracking
- Implement timeout warnings
- Implement auto-stop mechanism
- Add timeout extension endpoint

### 2. Implement Cleanup Jobs
- Create cron job for orphan detection
- Create cleanup endpoints
- Add database triggers for cleanup events

### 3. Build Multi-IDE Docker Images
- Create VS Code Dockerfile
- Create JupyterLab Dockerfile
- Create Terminal Dockerfile
- Push images to registry

### 4. Implement Multi-IDE Frontend
- Add IDE selector UI
- Add IDE switching logic
- Add iframe management
- Add IDE-specific features

### 5. Run Tests and Fix Failures
```bash
pytest tests/e2e/lab_environment/ -v --tb=short
```

---

## 12. Maintenance Guidelines

### When UI Changes
Update page object locators only:
```python
class LabPage(BasePage):
    # Old locator
    # TIMEOUT_WARNING = (By.ID, "timeout-warning")
    
    # New locator
    TIMEOUT_WARNING = (By.CLASS_NAME, "lab-timeout-alert")
```

### When Business Rules Change
Update test assertions and documentation:
```python
# Old: 2 hour timeout
# monkeypatch.setenv('LAB_INACTIVITY_TIMEOUT_SECONDS', '7200')

# New: 1 hour timeout
monkeypatch.setenv('LAB_INACTIVITY_TIMEOUT_SECONDS', '3600')
```

### When Adding New IDE Types
1. Add locator to `MultiIDELabPage`
2. Add test in `TestIDETypes`
3. Update `is_ide_loaded()` method

---

## Conclusion

Successfully created comprehensive E2E test suite for lab timeout/cleanup and multi-IDE support:

- **20 tests** covering all business requirements
- **1,792 lines** of well-documented test code
- **Page Object Model** pattern for maintainability
- **Accelerated timeout** strategy for fast testing
- **Docker verification** for container state
- **Database verification** for data integrity
- **Ready for TDD GREEN phase** implementation

All tests follow CLAUDE.md requirements:
- ✓ HTTPS-only testing (https://localhost:3000)
- ✓ Comprehensive documentation
- ✓ Business context in docstrings
- ✓ Multiple verification layers
- ✓ Proper error handling
- ✓ Cleanup fixtures

**Status:** COMPLETE - Ready for implementation phase

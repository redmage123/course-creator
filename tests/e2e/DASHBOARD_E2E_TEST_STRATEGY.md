# Track and Sub-Project Dashboard E2E Test Strategy

## Purpose

This document defines a comprehensive E2E testing strategy for Track and Sub-Project dashboards that prevents the types of errors missed by previous testing approaches.

## Lessons Learned from Previous Testing Gaps

### Issues Missed by Previous Tests:
1. **URL Construction Errors** - Missing trailing slashes in API URLs
2. **Missing Element IDs** - Buttons without IDs preventing Selenium from locating them
3. **Invalid CSS Selectors** - Using jQuery-style `:contains()` not supported in standard CSS
4. **HTML Attribute Errors** - Duplicate `class` attributes, wrong button types
5. **Async Operation Timeouts** - Not waiting for async operations to complete

### Root Causes:
- Tests didn't validate HTML structure before attempting operations
- Tests didn't verify API endpoint routes work correctly
- Tests didn't check for HTML validation errors
- Tests made assumptions about element existence without verification

## New Testing Strategy

### Phase 1: Pre-Flight Validation (Before Running Workflow Tests)

#### 1.1 HTML Structure Validation
```python
def test_track_dashboard_html_elements_exist():
    """
    Verify all required HTML elements exist with correct IDs and attributes

    PREVENTS: Missing ID errors, invalid selector errors
    """
    # Check table exists
    assert driver.find_element(By.ID, "tracksTable")

    # Check action buttons exist
    assert driver.find_element(By.ID, "createTrackBtn")
    assert driver.find_element(By.ID, "trackSearchInput")
    assert driver.find_element(By.ID, "trackProjectFilter")

    # Check modal elements (should exist in DOM even if hidden)
    assert driver.find_element(By.ID, "createTrackModal")
    assert driver.find_element(By.ID, "editTrackModal")
    assert driver.find_element(By.ID, "deleteTrackModal")

    # Check form fields in create modal
    assert driver.find_element(By.ID, "trackName")
    assert driver.find_element(By.ID, "trackDescription")
    assert driver.find_element(By.ID, "trackDifficultyLevel")
    assert driver.find_element(By.ID, "trackDurationHours")

    # Check submit buttons
    create_btn = driver.find_element(By.ID, "submitCreateTrackBtn")
    assert create_btn.get_attribute("type") == "submit"
```

#### 1.2 API Endpoint Validation
```python
def test_track_api_endpoints_respond_correctly():
    """
    Verify all API endpoints return correct status codes

    PREVENTS: 404 errors, URL construction errors
    """
    base_url = "https://localhost:3000"
    headers = {"Authorization": f"Bearer {get_test_token()}"}

    # Test with trailing slash
    response = requests.get(f"{base_url}/api/v1/tracks/", headers=headers, verify=False)
    assert response.status_code == 200

    # Test without trailing slash (should redirect or work)
    response = requests.get(f"{base_url}/api/v1/tracks", headers=headers, verify=False)
    assert response.status_code in [200, 301, 308]

    # Test with query parameters (proper URL construction)
    response = requests.get(f"{base_url}/api/v1/tracks/?project_id=test", headers=headers, verify=False)
    assert response.status_code in [200, 400]  # 400 if test ID invalid
```

#### 1.3 CSS Selector Validation
```python
def test_css_selectors_are_valid():
    """
    Verify all CSS selectors used in tests are valid

    PREVENTS: Invalid selector errors
    """
    # Test each selector without executing
    selectors = [
        (By.ID, "createTrackBtn"),
        (By.ID, "submitCreateTrackBtn"),
        (By.CSS_SELECTOR, "button.btn-primary[type='submit']"),
        # Add all selectors used in tests
    ]

    for by, selector in selectors:
        try:
            driver.find_elements(by, selector)  # Should not throw
        except Exception as e:
            pytest.fail(f"Invalid selector: {selector} - {e}")
```

### Phase 2: Complete CRUD Workflow Tests

#### 2.1 Track Dashboard - Create Operation
```python
def test_track_dashboard_create_new_track():
    """
    Test complete track creation workflow

    WORKFLOW:
    1. Navigate to Tracks tab
    2. Click "Create Track" button
    3. Fill all form fields (including JSONB fields)
    4. Submit form
    5. Verify track appears in table
    6. Verify track exists in database
    7. Verify all attributes saved correctly
    """
    # Step 1: Navigate
    driver.get("https://localhost:3000/org-admin-dashboard.html")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tracksTab")))
    driver.find_element(By.ID, "tracksTab").click()

    # Step 2: Open modal
    create_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "createTrackBtn"))
    )
    create_btn.click()

    # Step 3: Fill form
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "createTrackModal")))

    track_data = {
        "name": "Test Track E2E",
        "description": "End-to-end test track",
        "difficulty_level": "intermediate",
        "estimated_duration_hours": 40,
        "prerequisites": '["Python basics", "Git fundamentals"]',
        "learning_objectives": '["Master Django", "Build REST APIs"]',
        "is_active": True
    }

    driver.find_element(By.ID, "trackName").send_keys(track_data["name"])
    driver.find_element(By.ID, "trackDescription").send_keys(track_data["description"])
    Select(driver.find_element(By.ID, "trackDifficultyLevel")).select_by_value(track_data["difficulty_level"])
    driver.find_element(By.ID, "trackDurationHours").send_keys(str(track_data["estimated_duration_hours"]))
    driver.find_element(By.ID, "trackPrerequisites").send_keys(track_data["prerequisites"])
    driver.find_element(By.ID, "trackLearningObjectives").send_keys(track_data["learning_objectives"])

    # Step 4: Submit
    submit_btn = driver.find_element(By.ID, "submitCreateTrackBtn")
    submit_btn.click()

    # Step 5: Wait for modal to close and table to update
    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "createTrackModal")))
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.ID, "tracksTable"), track_data["name"])
    )

    # Step 6: Verify in database
    track_id = get_latest_track_id_from_table()
    db_track = get_track_from_database(track_id)

    assert db_track["name"] == track_data["name"]
    assert db_track["description"] == track_data["description"]
    assert db_track["difficulty_level"] == track_data["difficulty_level"]
    assert db_track["estimated_duration_hours"] == track_data["estimated_duration_hours"]
    assert db_track["prerequisites"] == json.loads(track_data["prerequisites"])
    assert db_track["learning_objectives"] == json.loads(track_data["learning_objectives"])
```

#### 2.2 Track Dashboard - Read Operation
```python
def test_track_dashboard_display_all_tracks():
    """
    Test track listing and filtering

    WORKFLOW:
    1. Navigate to Tracks tab
    2. Verify tracks table populates
    3. Test search filter
    4. Test project filter
    5. Test difficulty filter
    """
    # Implementation...
```

#### 2.3 Track Dashboard - Update Operation
```python
def test_track_dashboard_edit_existing_track():
    """
    Test complete track editing workflow

    WORKFLOW:
    1. Navigate to Tracks tab
    2. Click edit button on existing track
    3. Modify all editable fields
    4. Submit changes
    5. Verify changes appear in table
    6. Verify changes persisted in database
    """
    # Implementation...
```

#### 2.4 Track Dashboard - Delete Operation
```python
def test_track_dashboard_delete_track():
    """
    Test track deletion workflow

    WORKFLOW:
    1. Navigate to Tracks tab
    2. Click delete button on track
    3. Confirm deletion in modal
    4. Verify track removed from table
    5. Verify track deleted from database (soft or hard delete)
    """
    # Implementation...
```

### Phase 3: Sub-Project Dashboard Tests

#### 3.1 Sub-Project Dashboard - All CRUD Operations
Similar structure to Track Dashboard tests, but for sub-projects with additional location fields.

```python
def test_subproject_dashboard_create_with_location():
    """
    Test complete sub-project creation with location data

    ADDITIONAL FIELDS:
    - location_country
    - location_region
    - location_city
    - location_address
    - timezone
    - start_date
    - end_date
    - max_participants
    """
    # Implementation...
```

### Phase 4: Integration Tests

#### 4.1 Cross-Dashboard Interactions
```python
def test_track_appears_in_subproject_track_selection():
    """
    Test that tracks created in Track Dashboard appear in Sub-Project track selection

    WORKFLOW:
    1. Create track in Track Dashboard
    2. Navigate to Sub-Project Dashboard
    3. Open create modal
    4. Verify track appears in track selection dropdown
    """
    # Implementation...
```

### Phase 5: Error Handling and Validation

#### 5.1 Validation Rules
```python
def test_track_validation_prevents_invalid_data():
    """
    Test that validation rules work correctly

    TEST CASES:
    - Empty required fields
    - Invalid duration (negative)
    - Invalid JSON in prerequisites
    - Duplicate track names
    """
    # Implementation...
```

#### 5.2 Network Error Handling
```python
def test_track_dashboard_handles_api_errors_gracefully():
    """
    Test error handling when API calls fail

    TEST CASES:
    - 500 server error
    - Network timeout
    - Authentication failure
    - Validation error (400)
    """
    # Implementation...
```

## Test Organization Structure

```
tests/e2e/
├── dashboards/
│   ├── test_track_dashboard_preflight.py        # Phase 1: Pre-flight validation
│   ├── test_track_dashboard_crud.py             # Phase 2: CRUD operations
│   ├── test_subproject_dashboard_preflight.py   # Phase 1: Sub-project validation
│   ├── test_subproject_dashboard_crud.py        # Phase 2: Sub-project CRUD
│   ├── test_dashboard_integration.py            # Phase 4: Cross-dashboard tests
│   └── test_dashboard_error_handling.py         # Phase 5: Error scenarios
└── fixtures/
    ├── dashboard_test_data.py                   # Test data generators
    └── dashboard_helpers.py                     # Shared helper functions
```

## Test Execution Order

1. **Run pre-flight tests first** - If these fail, don't run workflow tests
2. **Run CRUD tests** - Test each operation independently
3. **Run integration tests** - Test interactions between dashboards
4. **Run error handling tests** - Verify graceful degradation

## Success Criteria

- ✅ All pre-flight validation tests pass
- ✅ All CRUD operations work end-to-end
- ✅ All data persists correctly in database
- ✅ All validation rules enforced
- ✅ All error scenarios handled gracefully
- ✅ 90%+ code coverage of dashboard JavaScript
- ✅ Zero console errors during test execution
- ✅ Tests run consistently (no flaky tests)

## Database Verification Helpers

```python
def get_track_from_database(track_id: str) -> dict:
    """Fetch track from database for verification"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM course_creator.tracks WHERE id = %s",
        (track_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result

def get_subproject_from_database(subproject_id: str) -> dict:
    """Fetch sub-project from database for verification"""
    # Implementation...
```

## Continuous Improvement

After each test failure:
1. Analyze root cause
2. Add specific test to prevent recurrence
3. Update this strategy document
4. Run full suite to verify fix

---

**Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: 📋 Ready for Implementation

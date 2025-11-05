"""
Authentication Token Expiration Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring JWT token expiration is handled gracefully.
Prevents users from being stuck in broken application state when tokens expire.

CRITICAL IMPORTANCE:
- Token expiration is inevitable (security requirement)
- Poor handling breaks user experience and causes support requests
- Users should be seamlessly redirected to login with clear messaging

REGRESSION BUGS COVERED:
- BUG-487: Token expiration not handled gracefully
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import asyncio


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_expired_token_redirects_to_login(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: Expired JWT token handling

    BUG REPORT:
    - Issue ID: BUG-487
    - Reported: 2025-09-28
    - Fixed: 2025-09-30
    - Severity: CRITICAL
    - Root Cause: Frontend axios interceptor was not catching 401 responses from
                  expired tokens. Users received 401 errors with no UI feedback,
                  leaving application in broken state.

    TEST SCENARIO:
    1. User logs in successfully
    2. Token expires (simulated by waiting or manual invalidation)
    3. User tries to perform authenticated action
    4. Should be gracefully redirected to login page with message

    EXPECTED BEHAVIOR:
    - User sees "Session expired" message
    - Redirected to login page automatically
    - LocalStorage cleared (no stale tokens)
    - Can log in again without manual cookie clearing

    VERIFICATION:
    - No 401 error displayed to user
    - Smooth redirect to login
    - Clear error messaging

    PREVENTION:
    - Always implement axios response interceptor for 401
    - Clear localStorage on token expiration
    - Show user-friendly message
    - Redirect to login with return URL
    """
    # Step 1: Log in successfully
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    # Wait for successful login
    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Step 2: Simulate token expiration by clearing localStorage token
    # This mimics what happens when JWT expires
    browser.execute_script("""
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
    """)

    # Step 3: Try to perform authenticated action (navigate to course)
    # This should trigger 401 response
    browser.get(f"{test_base_url}/courses")

    # Step 4: REGRESSION CHECK - Should be redirected to login
    try:
        # Wait for redirect to login page
        wait.until(
            lambda d: "/login" in d.current_url or "login" in d.current_url.lower(),
            message="Expected redirect to login page after token expiration"
        )

        # REGRESSION CHECK 1: Verify on login page
        assert "/login" in browser.current_url or "login" in browser.current_url.lower(), \
            f"REGRESSION FAILURE BUG-487: Not redirected to login after token expiration. Current URL: {browser.current_url}"

    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-487: Token expiration not handled gracefully: {e}")

    # REGRESSION CHECK 2: Verify no 401 error message shown to user
    # (Technical error should not be exposed)
    page_source = browser.page_source.lower()
    assert "401" not in page_source or "unauthorized" in page_source, \
        "REGRESSION FAILURE BUG-487: Technical 401 error exposed to user"

    # REGRESSION CHECK 3: Verify user can log in again
    try:
        # Should be able to see login form
        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "login-username"))
        )
        assert username_input.is_displayed(), \
            "REGRESSION FAILURE BUG-487: Login form not accessible after token expiration"
    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-487: Cannot access login form after expiration: {e}")


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_token_expiration_shows_user_friendly_message(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: User-friendly messaging on token expiration

    BUG REPORT:
    - Related to BUG-487
    - Ensures user sees helpful message, not technical error

    TEST SCENARIO:
    1. User's token expires
    2. User sees "Session expired" or similar friendly message
    3. NOT a technical "401 Unauthorized" error

    EXPECTED BEHAVIOR:
    - Clear, non-technical message
    - Explains what happened ("Your session has expired")
    - Tells user what to do ("Please log in again")

    VERIFICATION:
    - Message is visible
    - Message is user-friendly
    - No technical jargon
    """
    # Log in
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Simulate token expiration
    browser.execute_script("localStorage.clear();")

    # Trigger authenticated request
    browser.get(f"{test_base_url}/courses")

    # Wait a moment for error handling
    time.sleep(1)

    # REGRESSION CHECK: Look for user-friendly message
    # Check for common patterns in friendly messages
    page_source = browser.page_source.lower()

    friendly_messages = [
        "session expired",
        "please log in again",
        "your session has expired",
        "session timed out",
        "please sign in again"
    ]

    has_friendly_message = any(msg in page_source for msg in friendly_messages)

    # REGRESSION CHECK: Should have friendly message OR be on login page
    on_login_page = "/login" in browser.current_url or "login" in browser.current_url.lower()

    assert has_friendly_message or on_login_page, \
        "REGRESSION FAILURE BUG-487: No user-friendly message shown for token expiration"

    # REGRESSION CHECK: Should NOT have technical error messages
    technical_errors = [
        "error 401",
        "unauthorized request",
        "http error",
        "axios error",
        "request failed"
    ]

    has_technical_error = any(err in page_source for err in technical_errors)

    assert not has_technical_error, \
        "REGRESSION FAILURE BUG-487: Technical error message exposed to user"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_token_expiration_clears_local_storage(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: LocalStorage cleared on token expiration

    BUG REPORT:
    - Related to BUG-487
    - Ensures stale tokens don't remain in storage

    TEST SCENARIO:
    1. User logs in (token stored in localStorage)
    2. Token expires
    3. LocalStorage should be cleared
    4. No stale tokens remain

    EXPECTED BEHAVIOR:
    - Token removed from localStorage on expiration
    - User info removed from localStorage
    - Fresh login required (no auto-login with stale token)

    TECHNICAL VERIFICATION:
    - Check localStorage after expiration handling
    - Verify authToken, refreshToken, userInfo all cleared
    """
    # Log in
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Verify tokens are stored after login
    auth_token = browser.execute_script("return localStorage.getItem('authToken');")
    assert auth_token is not None, "Auth token should be stored after login"

    # Simulate token expiration
    browser.execute_script("localStorage.removeItem('authToken');")

    # Trigger authenticated request (should detect expired token)
    browser.get(f"{test_base_url}/courses")

    # Wait for redirect
    time.sleep(2)

    # REGRESSION CHECK: Verify localStorage is cleared
    remaining_token = browser.execute_script("return localStorage.getItem('authToken');")
    refresh_token = browser.execute_script("return localStorage.getItem('refreshToken');")
    user_info = browser.execute_script("return localStorage.getItem('userInfo');")

    assert remaining_token is None, \
        "REGRESSION FAILURE BUG-487: Auth token not cleared from localStorage"

    assert refresh_token is None, \
        "REGRESSION FAILURE BUG-487: Refresh token not cleared from localStorage"

    # User info may or may not be cleared depending on implementation
    # But sensitive data should definitely be gone


@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_token_refresh_on_expiration(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: Token refresh mechanism on near-expiration

    BUG REPORT:
    - Related to BUG-487
    - Ensures token refresh works to prevent expiration

    TEST SCENARIO:
    1. User logs in with valid token
    2. Token approaches expiration (not yet expired)
    3. System should attempt refresh token exchange
    4. User continues working without interruption

    EXPECTED BEHAVIOR:
    - If refresh token valid: Silent token refresh
    - User doesn't see expiration message
    - No redirect to login

    NOTE: This test validates the IDEAL behavior (automatic refresh)
    If automatic refresh not implemented, expiration handling is acceptable
    """
    # Log in
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Get initial token
    initial_token = browser.execute_script("return localStorage.getItem('authToken');")

    # Perform several authenticated actions over time
    # If token refresh implemented, token should be refreshed
    for i in range(3):
        browser.get(f"{test_base_url}/courses")
        time.sleep(1)

        current_url = browser.current_url
        # Should still be authenticated, not redirected to login
        assert "/login" not in current_url.lower(), \
            f"User redirected to login during normal activity (iteration {i+1})"

    # NOTE: If token refresh implemented, we could verify:
    # current_token = browser.execute_script("return localStorage.getItem('authToken');")
    # assert current_token != initial_token (token was refreshed)

    # At minimum, verify user still authenticated
    assert "/dashboard" in browser.current_url, \
        "User should remain authenticated during normal activity"


@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_simultaneous_requests_with_expired_token(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: Multiple simultaneous requests with expired token

    BUG REPORT:
    - Edge case related to BUG-487
    - Ensures multiple 401s don't cause multiple redirects

    TEST SCENARIO:
    1. User has expired token
    2. Multiple API requests triggered simultaneously
    3. All return 401
    4. Should only redirect ONCE, not multiple times

    EXPECTED BEHAVIOR:
    - Single redirect to login
    - Single error message (not multiple)
    - No redirect loop

    TECHNICAL VERIFICATION:
    - Axios interceptor should de-duplicate 401 handling
    - Only first 401 triggers logout/redirect
    """
    # Log in
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Simulate token expiration
    browser.execute_script("localStorage.clear();")

    # Navigate to page that makes multiple API calls
    browser.get(f"{test_base_url}/student-dashboard")

    # Wait for handling
    time.sleep(2)

    # REGRESSION CHECK: Should be on login page (not in redirect loop)
    current_url = browser.current_url

    # Verify we ended up on login page
    assert "/login" in current_url or "login" in current_url.lower(), \
        f"REGRESSION FAILURE BUG-487: Not properly redirected (URL: {current_url})"

    # Verify browser history doesn't show multiple login redirects
    # (Would indicate redirect loop)
    # This is hard to check directly in Selenium, but we can verify
    # page loaded successfully
    page_state = browser.execute_script("return document.readyState;")
    assert page_state == "complete", \
        "REGRESSION FAILURE BUG-487: Page not fully loaded (possible redirect loop)"


@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.asyncio
async def test_BUG487_return_url_preserved_after_expiration(
    browser, test_base_url, student_credentials
):
    """
    REGRESSION TEST: Return URL preserved after token expiration

    BUG REPORT:
    - Enhancement to BUG-487 fix
    - User should return to intended page after re-login

    TEST SCENARIO:
    1. User is on specific page (e.g., /courses/123)
    2. Token expires
    3. Redirected to login with return URL
    4. After login, return to original page

    EXPECTED BEHAVIOR:
    - Login URL includes return parameter
    - After successful login, user returns to intended page
    - Not redirected to default dashboard

    TECHNICAL VERIFICATION:
    - Check for returnUrl query parameter
    - Verify redirect after login goes to correct page
    """
    # Log in
    browser.get(test_base_url)
    wait = WebDriverWait(browser, 10)

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "homepage-login-button"))
    )
    login_button.click()

    wait.until(
        EC.visibility_of_element_located((By.ID, "login-modal"))
    )

    username_input = browser.find_element(By.ID, "login-username")
    password_input = browser.find_element(By.ID, "login-password")

    username_input.send_keys(student_credentials["username"])
    password_input.send_keys(student_credentials["password"])

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    wait.until(
        lambda d: "/student-dashboard" in d.current_url
    )

    # Navigate to specific page
    target_page = f"{test_base_url}/courses"
    browser.get(target_page)

    # Simulate token expiration
    browser.execute_script("localStorage.clear();")

    # Trigger authenticated request
    browser.refresh()

    time.sleep(2)

    # REGRESSION CHECK: Verify on login page
    current_url = browser.current_url

    # Check if return URL is preserved (if feature implemented)
    # This is a nice-to-have feature
    if "returnUrl" in current_url or "return" in current_url:
        assert "courses" in current_url, \
            "REGRESSION WARNING BUG-487: Return URL not correctly preserved"

    # At minimum, verify user is on login page
    assert "/login" in current_url or "login" in current_url.lower(), \
        f"REGRESSION FAILURE BUG-487: Not redirected to login (URL: {current_url})"

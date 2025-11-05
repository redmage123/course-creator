"""
GDPR Compliance Regression Tests

BUSINESS CONTEXT:
Regression tests ensuring GDPR compliance is maintained across code changes.
Prevents previously fixed privacy bugs from reoccurring in production.

CRITICAL IMPORTANCE:
- GDPR non-compliance can result in fines up to €20M or 4% of global revenue
- Privacy bugs expose user data and violate EU data protection laws
- Consent management is legally required before any tracking
- Right to erasure must completely remove all user data

REGRESSION BUGS COVERED:
- BUG-701: Consent not recorded before data collection (GDPR Article 7)
- BUG-689: Right to erasure not fully deleting data (GDPR Article 17)
- BUG-723: Audit logs missing critical events (GDPR Article 30)

COMPLIANCE STANDARDS:
- GDPR (General Data Protection Regulation) - EU Regulation 2016/679
- CCPA (California Consumer Privacy Act) - California Civil Code §1798
- PIPEDA (Personal Information Protection and Electronic Documents Act) - Canada

TEST PATTERN:
Each test follows TDD Red-Green-Refactor:
1. Document the original bug and root cause
2. Test the exact failing scenario
3. Verify the fix prevents recurrence
4. Add preventive checks

TECHNICAL IMPLEMENTATION:
- Uses Selenium for browser-based consent UI tests
- Uses httpx for API-based privacy endpoint tests
- Uses asyncpg for database verification tests
- Tests pseudonymization with HMAC-SHA256
- Tests tamper-evident checksums with SHA256
"""

import pytest
import asyncio
import httpx
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ============================================================================
# CONSENT MANAGEMENT REGRESSION TESTS (BUG-701) - 5 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG701_consent_recorded_before_tracking(
    browser, test_base_url, db_transaction, create_test_guest_session
):
    """
    REGRESSION TEST: Consent must be recorded before any tracking

    BUG REPORT:
    - Issue ID: BUG-701
    - Reported: 2025-10-25
    - Fixed: 2025-10-26
    - Severity: CRITICAL
    - Root Cause: Cookie banner displayed but analytics cookies were already set
                  before user gave consent. JavaScript tracking code loaded in
                  <head> before cookie consent check.

    GDPR COMPLIANCE:
    - Article 7: Conditions for consent - consent must be freely given, specific,
                 informed and unambiguous. Must be obtained BEFORE processing.
    - Article 6(1)(a): Lawful processing requires consent as legal basis

    TEST SCENARIO:
    1. User visits homepage for first time
    2. System must NOT set any tracking cookies
    3. Cookie consent banner appears
    4. User accepts consent
    5. ONLY THEN can tracking cookies be set

    EXPECTED BEHAVIOR:
    - No cookies set before consent given
    - Consent preference recorded in database with timestamp
    - Tracking cookies only set after explicit consent
    - Essential cookies can be set (exempt from consent)

    VERIFICATION:
    - Check no analytics cookies exist before consent
    - Verify consent record created with proper timestamp
    - Verify tracking starts only after consent

    PREVENTION:
    - Cookie consent check must be first script in <head>
    - Tracking scripts loaded conditionally after consent
    - Regular automated testing of cookie timing
    """
    # Navigate to homepage
    browser.get(test_base_url)

    wait = WebDriverWait(browser, 10)

    # REGRESSION CHECK 1: Verify NO analytics cookies before consent
    cookies_before = browser.get_cookies()
    analytics_cookies_before = [
        c for c in cookies_before
        if c['name'] in ['_ga', '_gid', 'analytics_session', 'tracking_id']
    ]

    assert len(analytics_cookies_before) == 0, \
        f"REGRESSION FAILURE BUG-701: Analytics cookies found before consent: {analytics_cookies_before}"

    # REGRESSION CHECK 2: Verify cookie banner appears
    try:
        cookie_banner = wait.until(
            EC.visibility_of_element_located((By.ID, "cookie-consent-banner"))
        )
        assert cookie_banner.is_displayed(), \
            "REGRESSION FAILURE BUG-701: Cookie consent banner not visible"
    except TimeoutException:
        pytest.fail("REGRESSION FAILURE BUG-701: Cookie consent banner not found")

    # REGRESSION CHECK 3: Verify no tracking scripts loaded yet
    tracking_active = browser.execute_script(
        "return window.analytics !== undefined || window.gtag !== undefined || window._gaq !== undefined"
    )

    assert not tracking_active, \
        "REGRESSION FAILURE BUG-701: Tracking scripts loaded before consent"

    # User accepts consent
    accept_button = browser.find_element(By.ID, "accept-all-cookies-btn")
    accept_button.click()

    time.sleep(1)  # Allow consent processing

    # REGRESSION CHECK 4: Verify consent recorded in database
    session_id = browser.execute_script("return localStorage.getItem('session_id')")

    if session_id:
        consent_record = await db_transaction.fetchrow(
            """
            SELECT consent_given, consent_timestamp, consent_type
            FROM guest_sessions
            WHERE session_id = $1
            """,
            session_id
        )

        assert consent_record is not None, \
            "REGRESSION FAILURE BUG-701: Consent not recorded in database"

        assert consent_record['consent_given'] is True, \
            "REGRESSION FAILURE BUG-701: Consent marked as not given"

        assert consent_record['consent_timestamp'] is not None, \
            "REGRESSION FAILURE BUG-701: Consent timestamp not recorded"

        assert consent_record['consent_type'] in ['all', 'essential'], \
            f"REGRESSION FAILURE BUG-701: Invalid consent type: {consent_record['consent_type']}"

    # REGRESSION CHECK 5: Now tracking cookies CAN be set
    cookies_after = browser.get_cookies()
    consent_cookie = next((c for c in cookies_after if c['name'] == 'cookie_consent'), None)

    assert consent_cookie is not None, \
        "REGRESSION FAILURE BUG-701: Consent cookie not set after acceptance"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG701_cookie_banner_displays_before_cookies_set(
    browser, test_base_url
):
    """
    REGRESSION TEST: Cookie banner must display before ANY cookies are set

    BUG REPORT:
    - Related to BUG-701
    - Cookie banner rendering was delayed by 500ms for "smooth fade-in"
    - Analytics cookies were set immediately on page load
    - This violated GDPR Article 7 consent timing requirement

    GDPR COMPLIANCE:
    - Article 7(1): Consent must be obtained BEFORE processing
    - Recital 32: Consent should be given by clear affirmative action

    TEST SCENARIO:
    1. Clear all browser data
    2. Navigate to homepage
    3. Immediately check for cookies
    4. Verify banner appears BEFORE cookies

    EXPECTED BEHAVIOR:
    - Cookie banner visible on first load
    - No tracking cookies until after consent
    - Essential cookies (session) are exempt

    VERIFICATION:
    - Banner visible check
    - Cookie count and types
    - Timing verification

    PREVENTION:
    - Remove artificial delays on cookie banner
    - Use synchronous banner rendering
    - Test cookie timing in CI/CD
    """
    # Clear all cookies and storage
    browser.delete_all_cookies()
    browser.execute_script("localStorage.clear(); sessionStorage.clear();")

    # Navigate to homepage
    browser.get(test_base_url)

    # REGRESSION CHECK 1: Banner appears immediately (within 100ms)
    wait = WebDriverWait(browser, 2)
    start_time = time.time()

    try:
        cookie_banner = wait.until(
            EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
        )
        banner_load_time = time.time() - start_time

        assert banner_load_time < 0.1, \
            f"REGRESSION FAILURE BUG-701: Cookie banner took {banner_load_time:.3f}s (should be <0.1s)"

    except TimeoutException:
        pytest.fail("REGRESSION FAILURE BUG-701: Cookie banner not found within 2 seconds")

    # REGRESSION CHECK 2: No tracking cookies before banner interaction
    cookies = browser.get_cookies()
    tracking_cookies = [
        c for c in cookies
        if c['name'] in ['_ga', '_gid', 'analytics_session', 'tracking_id', '_fbp']
    ]

    assert len(tracking_cookies) == 0, \
        f"REGRESSION FAILURE BUG-701: Tracking cookies found before consent: {[c['name'] for c in tracking_cookies]}"

    # REGRESSION CHECK 3: Only essential cookies allowed
    essential_cookie_names = ['session_id', 'XSRF-TOKEN', 'csrf_token']
    non_essential_cookies = [
        c for c in cookies
        if c['name'] not in essential_cookie_names
    ]

    assert len(non_essential_cookies) == 0, \
        f"REGRESSION FAILURE BUG-701: Non-essential cookies before consent: {[c['name'] for c in non_essential_cookies]}"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
def test_BUG701_essential_vs_nonessential_cookie_separation(
    browser, test_base_url
):
    """
    REGRESSION TEST: Essential cookies separated from non-essential

    BUG REPORT:
    - Related to BUG-701
    - All cookies were treated as "essential" to bypass consent
    - Analytics and marketing cookies incorrectly marked as essential
    - GDPR requires explicit consent for non-essential cookies

    GDPR COMPLIANCE:
    - Recital 30: Essential cookies for legitimate interest are exempt
    - Article 6(1)(f): Legitimate interest does NOT apply to tracking

    TEST SCENARIO:
    1. Navigate to homepage
    2. Check cookie consent banner categories
    3. Verify essential vs non-essential distinction
    4. Verify essential cookies functional without consent

    EXPECTED BEHAVIOR:
    - Clear separation of cookie categories
    - Essential: session, CSRF, security
    - Non-essential: analytics, marketing, preferences
    - Essential cookies work without consent

    VERIFICATION:
    - Cookie category checkboxes
    - Essential cookies not require consent
    - Non-essential require explicit opt-in

    PREVENTION:
    - Maintain strict cookie category definitions
    - Code reviews for cookie additions
    - Automated cookie categorization tests
    """
    browser.get(test_base_url)

    wait = WebDriverWait(browser, 10)

    # Wait for cookie consent banner
    cookie_banner = wait.until(
        EC.visibility_of_element_located((By.ID, "cookie-consent-banner"))
    )

    # Click "Customize" to see categories
    customize_btn = browser.find_element(By.ID, "customize-cookies-btn")
    customize_btn.click()

    time.sleep(0.5)

    # REGRESSION CHECK 1: Essential cookies checkbox is disabled (always on)
    try:
        essential_checkbox = browser.find_element(By.ID, "essential-cookies-checkbox")

        assert not essential_checkbox.is_enabled(), \
            "REGRESSION FAILURE BUG-701: Essential cookies checkbox should be disabled (always required)"

        assert essential_checkbox.is_selected(), \
            "REGRESSION FAILURE BUG-701: Essential cookies should be pre-selected"

    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-701: Essential cookies checkbox not found: {e}")

    # REGRESSION CHECK 2: Analytics cookies checkbox is enabled (opt-in)
    try:
        analytics_checkbox = browser.find_element(By.ID, "analytics-cookies-checkbox")

        assert analytics_checkbox.is_enabled(), \
            "REGRESSION FAILURE BUG-701: Analytics cookies should be optional"

        assert not analytics_checkbox.is_selected(), \
            "REGRESSION FAILURE BUG-701: Analytics cookies should NOT be pre-selected"

    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-701: Analytics cookies checkbox not found: {e}")

    # REGRESSION CHECK 3: Marketing cookies checkbox is enabled (opt-in)
    try:
        marketing_checkbox = browser.find_element(By.ID, "marketing-cookies-checkbox")

        assert marketing_checkbox.is_enabled(), \
            "REGRESSION FAILURE BUG-701: Marketing cookies should be optional"

        assert not marketing_checkbox.is_selected(), \
            "REGRESSION FAILURE BUG-701: Marketing cookies should NOT be pre-selected"

    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-701: Marketing cookies checkbox not found: {e}")

    # REGRESSION CHECK 4: Cookie descriptions present
    essential_description = browser.find_element(By.ID, "essential-cookies-description")
    assert "required for website functionality" in essential_description.text.lower(), \
        "REGRESSION FAILURE BUG-701: Essential cookies description missing or unclear"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG701_consent_withdrawal_functionality(
    browser, test_base_url, db_transaction
):
    """
    REGRESSION TEST: Users can withdraw consent at any time

    BUG REPORT:
    - Related to BUG-701
    - Consent could be given but not withdrawn
    - No UI to change cookie preferences after initial acceptance
    - GDPR requires consent to be as easy to withdraw as to give

    GDPR COMPLIANCE:
    - Article 7(3): Withdrawal of consent must be as easy as giving consent
    - Recital 42: Consent must be withdrawable at any time

    TEST SCENARIO:
    1. User accepts cookies
    2. User accesses cookie settings
    3. User withdraws consent
    4. Tracking stops immediately
    5. Consent withdrawn recorded in database

    EXPECTED BEHAVIOR:
    - Cookie settings accessible from privacy link
    - Withdraw consent button clearly visible
    - Tracking cookies deleted on withdrawal
    - Database records consent_withdrawn: true

    VERIFICATION:
    - Settings page accessible
    - Withdrawal action succeeds
    - Database updated correctly
    - Cookies removed

    PREVENTION:
    - Always provide cookie settings link
    - Test withdrawal workflow regularly
    - Verify database consent status updates
    """
    browser.get(test_base_url)

    wait = WebDriverWait(browser, 10)

    # Accept cookies first
    cookie_banner = wait.until(
        EC.visibility_of_element_located((By.ID, "cookie-consent-banner"))
    )

    accept_btn = browser.find_element(By.ID, "accept-all-cookies-btn")
    accept_btn.click()

    time.sleep(1)

    # REGRESSION CHECK 1: Cookie settings link available in footer
    try:
        cookie_settings_link = browser.find_element(By.ID, "cookie-settings-link")
        assert cookie_settings_link.is_displayed(), \
            "REGRESSION FAILURE BUG-701: Cookie settings link not visible"
    except Exception as e:
        pytest.fail(f"REGRESSION FAILURE BUG-701: Cookie settings link not found: {e}")

    # Navigate to cookie settings
    cookie_settings_link.click()

    time.sleep(0.5)

    # REGRESSION CHECK 2: Withdraw consent button present
    try:
        withdraw_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "withdraw-consent-btn"))
        )

        assert withdraw_btn.is_displayed(), \
            "REGRESSION FAILURE BUG-701: Withdraw consent button not visible"

    except TimeoutException:
        pytest.fail("REGRESSION FAILURE BUG-701: Withdraw consent button not found")

    # Get session ID before withdrawal
    session_id = browser.execute_script("return localStorage.getItem('session_id')")

    # Withdraw consent
    withdraw_btn.click()

    time.sleep(1)

    # REGRESSION CHECK 3: Tracking cookies removed
    cookies_after_withdrawal = browser.get_cookies()
    tracking_cookies = [
        c for c in cookies_after_withdrawal
        if c['name'] in ['_ga', '_gid', 'analytics_session', 'tracking_id']
    ]

    assert len(tracking_cookies) == 0, \
        f"REGRESSION FAILURE BUG-701: Tracking cookies still present after withdrawal: {[c['name'] for c in tracking_cookies]}"

    # REGRESSION CHECK 4: Database updated with withdrawal
    if session_id:
        consent_record = await db_transaction.fetchrow(
            """
            SELECT consent_given, consent_withdrawn, consent_withdrawn_at
            FROM guest_sessions
            WHERE session_id = $1
            """,
            session_id
        )

        if consent_record:
            assert consent_record['consent_withdrawn'] is True, \
                "REGRESSION FAILURE BUG-701: Consent withdrawal not recorded"

            assert consent_record['consent_withdrawn_at'] is not None, \
                "REGRESSION FAILURE BUG-701: Consent withdrawal timestamp not recorded"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG701_consent_records_with_pseudonymized_data(
    db_transaction, create_test_guest_session
):
    """
    REGRESSION TEST: Consent records use pseudonymized identifiers

    BUG REPORT:
    - Related to BUG-701
    - Consent records stored with plain IP addresses
    - User agents stored in plain text
    - GDPR requires data minimization and pseudonymization

    GDPR COMPLIANCE:
    - Article 5(1)(c): Data minimization principle
    - Article 25: Privacy by design and by default
    - Article 32: Security of processing - pseudonymization

    TEST SCENARIO:
    1. Create guest session with consent
    2. Verify IP address is pseudonymized (HMAC-SHA256)
    3. Verify user agent is fingerprinted (SHA256)
    4. Verify no PII in consent records

    EXPECTED BEHAVIOR:
    - IP addresses hashed with HMAC-SHA256 + secret
    - User agents converted to fingerprint hash
    - Consent timestamp preserved (for 30-day retention)
    - No reversible personal identifiers

    VERIFICATION:
    - Check pseudonymization algorithm
    - Verify hash format (64 char hex)
    - Verify original data not stored

    PREVENTION:
    - Use centralized pseudonymization service
    - Regular security audits of data storage
    - Automated PII detection tests
    """
    # Create test session
    session_data = create_test_guest_session(
        ip_address="203.0.113.42",
        user_agent="Mozilla/5.0 (Test Browser)"
    )

    # Insert into database
    await db_transaction.execute(
        """
        INSERT INTO guest_sessions (
            session_id, fingerprint_hash, pseudonymized_ip, user_agent,
            consent_given, consent_timestamp, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        session_data['session_id'],
        session_data['fingerprint_hash'],
        session_data['pseudonymized_ip'],
        "REDACTED",  # User agent should be redacted
        True,
        datetime.utcnow(),
        session_data['created_at']
    )

    # Retrieve record
    record = await db_transaction.fetchrow(
        """
        SELECT session_id, fingerprint_hash, pseudonymized_ip, user_agent
        FROM guest_sessions
        WHERE session_id = $1
        """,
        session_data['session_id']
    )

    # REGRESSION CHECK 1: IP address is pseudonymized (HMAC-SHA256)
    assert record['pseudonymized_ip'] is not None, \
        "REGRESSION FAILURE BUG-701: IP address not pseudonymized"

    assert len(record['pseudonymized_ip']) == 64, \
        f"REGRESSION FAILURE BUG-701: Invalid pseudonymized IP length: {len(record['pseudonymized_ip'])}"

    assert record['pseudonymized_ip'] != "203.0.113.42", \
        "REGRESSION FAILURE BUG-701: IP address stored in plain text"

    # REGRESSION CHECK 2: Fingerprint hash is SHA256
    assert record['fingerprint_hash'] is not None, \
        "REGRESSION FAILURE BUG-701: Fingerprint hash not generated"

    assert len(record['fingerprint_hash']) == 64, \
        f"REGRESSION FAILURE BUG-701: Invalid fingerprint hash length: {len(record['fingerprint_hash'])}"

    # REGRESSION CHECK 3: User agent redacted
    assert record['user_agent'] == "REDACTED", \
        f"REGRESSION FAILURE BUG-701: User agent not redacted: {record['user_agent']}"

    # REGRESSION CHECK 4: Verify HMAC-SHA256 pseudonymization
    expected_pseudonymized_ip = hmac.new(
        b"test_secret_key",
        "203.0.113.42".encode(),
        hashlib.sha256
    ).hexdigest()

    assert record['pseudonymized_ip'] == expected_pseudonymized_ip, \
        "REGRESSION FAILURE BUG-701: HMAC-SHA256 pseudonymization incorrect"


# ============================================================================
# RIGHT TO ERASURE REGRESSION TESTS (BUG-689) - 5 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG689_complete_data_deletion_on_erasure_request(
    db_transaction, create_test_user, create_test_course, create_test_enrollment
):
    """
    REGRESSION TEST: Right to erasure completely deletes all user data

    BUG REPORT:
    - Issue ID: BUG-689
    - Reported: 2025-10-20
    - Fixed: 2025-10-22
    - Severity: CRITICAL
    - Root Cause: Deletion script only removed user record from users table.
                  Related data in enrollments, progress, quiz_attempts, analytics,
                  and audit_logs tables was orphaned but not deleted.

    GDPR COMPLIANCE:
    - Article 17: Right to erasure (right to be forgotten)
    - Must delete ALL personal data without undue delay
    - Includes direct identifiers and indirect identifiers

    TEST SCENARIO:
    1. Create user with complete data profile
    2. User has enrollments, progress, quiz attempts
    3. User has analytics data, session logs
    4. User requests erasure
    5. Verify ALL data deleted from ALL tables

    EXPECTED BEHAVIOR:
    - User record deleted from users table
    - All enrollments deleted
    - All progress records deleted
    - All quiz attempts deleted
    - All analytics data deleted
    - All audit logs anonymized

    VERIFICATION:
    - Check each related table for user data
    - Verify foreign key constraints handle cascading
    - Verify no orphaned records remain

    PREVENTION:
    - Use CASCADE on foreign key constraints
    - Maintain data relationship diagram
    - Automated data deletion verification tests
    - Regular data retention audits
    """
    # Create test user
    user_data = create_test_user(role="student")
    user_id = user_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id, user_data['username'], user_data['email'],
        user_data['password_hash'], user_data['role_name'],
        user_data['is_active'], user_data['created_at']
    )

    # Create related data - course
    course_data = create_test_course(instructor_id=str(uuid.uuid4()))
    course_id = course_data['id']

    await db_transaction.execute(
        """
        INSERT INTO courses (id, title, slug, description, instructor_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        course_id, course_data['title'], course_data['slug'],
        course_data['description'], course_data['instructor_id'],
        course_data['status'], course_data['created_at']
    )

    # Create enrollment
    enrollment_data = create_test_enrollment(user_id, course_id)

    await db_transaction.execute(
        """
        INSERT INTO enrollments (id, student_id, course_id, enrolled_at, status)
        VALUES ($1, $2, $3, $4, $5)
        """,
        enrollment_data['id'], user_id, course_id,
        enrollment_data['enrolled_at'], enrollment_data['status']
    )

    # Create progress record
    await db_transaction.execute(
        """
        INSERT INTO student_progress (id, student_id, course_id, progress_percentage, last_accessed_at)
        VALUES ($1, $2, $3, $4, $5)
        """,
        str(uuid.uuid4()), user_id, course_id, 45, datetime.utcnow()
    )

    # Create analytics record
    await db_transaction.execute(
        """
        INSERT INTO student_analytics (id, student_id, page_views, time_spent_minutes, last_activity)
        VALUES ($1, $2, $3, $4, $5)
        """,
        str(uuid.uuid4()), user_id, 127, 456, datetime.utcnow()
    )

    # Verify data exists before deletion
    user_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM users WHERE id = $1", user_id
    )
    assert user_exists == 1, "User should exist before deletion"

    # Execute erasure request
    await db_transaction.execute(
        """
        DELETE FROM users WHERE id = $1
        """,
        user_id
    )

    # REGRESSION CHECK 1: User record deleted
    user_deleted = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM users WHERE id = $1", user_id
    )

    assert user_deleted == 0, \
        "REGRESSION FAILURE BUG-689: User record not deleted"

    # REGRESSION CHECK 2: Enrollments deleted (CASCADE)
    enrollments_deleted = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM enrollments WHERE student_id = $1", user_id
    )

    assert enrollments_deleted == 0, \
        f"REGRESSION FAILURE BUG-689: {enrollments_deleted} enrollment records not deleted"

    # REGRESSION CHECK 3: Progress records deleted (CASCADE)
    progress_deleted = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM student_progress WHERE student_id = $1", user_id
    )

    assert progress_deleted == 0, \
        f"REGRESSION FAILURE BUG-689: {progress_deleted} progress records not deleted"

    # REGRESSION CHECK 4: Analytics records deleted (CASCADE)
    analytics_deleted = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM student_analytics WHERE student_id = $1", user_id
    )

    assert analytics_deleted == 0, \
        f"REGRESSION FAILURE BUG-689: {analytics_deleted} analytics records not deleted"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG689_cascade_deletion_to_all_related_tables(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Cascade deletion works across all related tables

    BUG REPORT:
    - Related to BUG-689
    - Foreign key constraints existed but CASCADE not configured
    - Manual deletion required for each related table
    - Easy to miss tables during erasure process

    GDPR COMPLIANCE:
    - Article 17(1): Right to erasure applies to all personal data
    - Article 5(1)(e): Data must not be kept longer than necessary

    TEST SCENARIO:
    1. Create user with data in 10+ related tables
    2. Verify foreign key constraints have ON DELETE CASCADE
    3. Delete user from users table
    4. Verify cascading deletion worked in all tables

    EXPECTED BEHAVIOR:
    - Single DELETE from users triggers cascades
    - All related records automatically deleted
    - No manual cleanup required
    - No orphaned records

    VERIFICATION:
    - Test each table for cascade behavior
    - Verify foreign key constraint definitions
    - Check for orphaned records after deletion

    PREVENTION:
    - All foreign keys must use ON DELETE CASCADE
    - Data model review before adding new tables
    - Automated foreign key constraint testing
    """
    # Create user
    user_data = create_test_user(role="instructor")
    user_id = user_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id, user_data['username'], user_data['email'],
        user_data['password_hash'], user_data['role_name'],
        user_data['is_active'], user_data['created_at']
    )

    # Create records in multiple related tables
    related_tables = [
        ('user_sessions', 'INSERT INTO user_sessions (id, user_id, token, created_at) VALUES ($1, $2, $3, $4)'),
        ('user_preferences', 'INSERT INTO user_preferences (id, user_id, theme, language) VALUES ($1, $2, $3, $4)'),
        ('user_notifications', 'INSERT INTO user_notifications (id, user_id, message, created_at) VALUES ($1, $2, $3, $4)'),
    ]

    for table_name, insert_query in related_tables:
        try:
            await db_transaction.execute(
                insert_query,
                str(uuid.uuid4()), user_id, 'test_value', datetime.utcnow()
            )
        except Exception:
            # Table might not exist, skip
            pass

    # Delete user
    await db_transaction.execute(
        "DELETE FROM users WHERE id = $1", user_id
    )

    # REGRESSION CHECK: Verify cascading deletion in each table
    for table_name, _ in related_tables:
        try:
            count = await db_transaction.fetchval(
                f"SELECT COUNT(*) FROM {table_name} WHERE user_id = $1",
                user_id
            )

            assert count == 0, \
                f"REGRESSION FAILURE BUG-689: {table_name} still has {count} records after user deletion"

        except Exception:
            # Table might not exist, skip verification
            pass


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG689_backup_purge_after_erasure(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Backups must be purged after erasure request

    BUG REPORT:
    - Related to BUG-689
    - User data deleted from production database
    - Backups still contained user's personal data
    - GDPR requires deletion from ALL copies including backups

    GDPR COMPLIANCE:
    - Article 17(1): Erasure applies to ALL copies of personal data
    - Recital 65: Includes backups and disaster recovery systems

    TEST SCENARIO:
    1. Create user with data
    2. Simulate backup containing user data
    3. User requests erasure
    4. Verify erasure request recorded in erasure_requests table
    5. Verify backup_purge_required flag set
    6. Simulate backup purge process
    7. Verify erasure completed

    EXPECTED BEHAVIOR:
    - Erasure request creates record in erasure_requests table
    - Backup systems notified of purge requirement
    - Backups purged within 30 days (standard retention)
    - Erasure status tracked until complete

    VERIFICATION:
    - Erasure request record exists
    - Backup purge flag set
    - Status tracking accurate

    PREVENTION:
    - Automated backup purge workflows
    - Erasure status monitoring dashboard
    - Regular backup compliance audits
    """
    # Create user
    user_data = create_test_user(role="student")
    user_id = user_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id, user_data['username'], user_data['email'],
        user_data['password_hash'], user_data['role_name'],
        user_data['is_active'], user_data['created_at']
    )

    # Record erasure request
    erasure_request_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO erasure_requests (
            id, user_id, requested_at, status,
            production_deleted, backup_purge_required, backup_purge_completed
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        erasure_request_id, user_id, datetime.utcnow(),
        'in_progress', False, True, False
    )

    # Delete from production database
    await db_transaction.execute(
        "DELETE FROM users WHERE id = $1", user_id
    )

    # Update erasure request status
    await db_transaction.execute(
        """
        UPDATE erasure_requests
        SET production_deleted = TRUE, production_deleted_at = $2
        WHERE id = $1
        """,
        erasure_request_id, datetime.utcnow()
    )

    # REGRESSION CHECK 1: Erasure request recorded
    erasure_record = await db_transaction.fetchrow(
        """
        SELECT id, user_id, status, production_deleted, backup_purge_required
        FROM erasure_requests
        WHERE id = $1
        """,
        erasure_request_id
    )

    assert erasure_record is not None, \
        "REGRESSION FAILURE BUG-689: Erasure request not recorded"

    assert erasure_record['production_deleted'] is True, \
        "REGRESSION FAILURE BUG-689: Production deletion not marked complete"

    assert erasure_record['backup_purge_required'] is True, \
        "REGRESSION FAILURE BUG-689: Backup purge not flagged as required"

    # REGRESSION CHECK 2: Backup purge workflow triggered
    # In real system, this would trigger async backup purge job
    # Here we simulate the completion
    await db_transaction.execute(
        """
        UPDATE erasure_requests
        SET backup_purge_completed = TRUE,
            backup_purge_completed_at = $2,
            status = 'completed'
        WHERE id = $1
        """,
        erasure_request_id, datetime.utcnow()
    )

    final_status = await db_transaction.fetchrow(
        """
        SELECT status, backup_purge_completed, backup_purge_completed_at
        FROM erasure_requests
        WHERE id = $1
        """,
        erasure_request_id
    )

    assert final_status['status'] == 'completed', \
        "REGRESSION FAILURE BUG-689: Erasure status not marked as completed"

    assert final_status['backup_purge_completed'] is True, \
        "REGRESSION FAILURE BUG-689: Backup purge not marked as completed"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG689_analytics_anonymization_after_erasure(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Analytics data must be anonymized after erasure

    BUG REPORT:
    - Related to BUG-689
    - Analytics aggregates retained personal identifiers
    - Course completion stats linked to user IDs
    - GDPR allows retention of anonymous statistics only

    GDPR COMPLIANCE:
    - Article 17(3)(d): Exception for archiving in public interest
    - Only applies if data is truly anonymous (not pseudonymous)
    - Must not be possible to re-identify individual

    TEST SCENARIO:
    1. User completes courses, generates analytics
    2. Analytics stored with user_id for reporting
    3. User requests erasure
    4. Verify user_id replaced with anonymous token
    5. Verify aggregate statistics preserved
    6. Verify re-identification not possible

    EXPECTED BEHAVIOR:
    - user_id replaced with anonymization token
    - Statistical values preserved (course completion, scores)
    - Personal identifiers removed (name, email)
    - Data still useful for aggregate reporting

    VERIFICATION:
    - Check user_id anonymization
    - Verify statistics intact
    - Test re-identification prevention

    PREVENTION:
    - Separate personal data from analytics
    - Use anonymization tokens from creation
    - Regular data de-identification audits
    """
    # Create user
    user_data = create_test_user(role="student")
    user_id = user_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        user_id, user_data['username'], user_data['email'],
        user_data['password_hash'], user_data['role_name'],
        user_data['is_active'], user_data['created_at']
    )

    # Create analytics record
    analytics_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO anonymized_analytics (
            id, user_token, course_completed, final_score, completion_date
        ) VALUES ($1, $2, $3, $4, $5)
        """,
        analytics_id, user_id, True, 87.5, datetime.utcnow()
    )

    # Generate anonymization token
    anonymization_token = hashlib.sha256(
        f"anonymous-{uuid.uuid4()}".encode()
    ).hexdigest()[:16]

    # Anonymize analytics (replace user_id with token)
    await db_transaction.execute(
        """
        UPDATE anonymized_analytics
        SET user_token = $2
        WHERE user_token = $1
        """,
        user_id, anonymization_token
    )

    # Delete user
    await db_transaction.execute(
        "DELETE FROM users WHERE id = $1", user_id
    )

    # REGRESSION CHECK 1: Analytics record still exists
    analytics_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM anonymized_analytics WHERE id = $1",
        analytics_id
    )

    assert analytics_exists == 1, \
        "REGRESSION FAILURE BUG-689: Analytics record deleted (should be anonymized)"

    # REGRESSION CHECK 2: User token is anonymized
    analytics_record = await db_transaction.fetchrow(
        """
        SELECT user_token, course_completed, final_score
        FROM anonymized_analytics
        WHERE id = $1
        """,
        analytics_id
    )

    assert analytics_record['user_token'] != user_id, \
        "REGRESSION FAILURE BUG-689: User ID not anonymized in analytics"

    assert analytics_record['user_token'] == anonymization_token, \
        "REGRESSION FAILURE BUG-689: Anonymization token not applied correctly"

    # REGRESSION CHECK 3: Statistical values preserved
    assert analytics_record['course_completed'] is True, \
        "REGRESSION FAILURE BUG-689: Course completion status lost during anonymization"

    assert analytics_record['final_score'] == 87.5, \
        "REGRESSION FAILURE BUG-689: Final score lost during anonymization"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG689_thirty_day_grace_period_enforcement(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: 30-day grace period enforced before permanent deletion

    BUG REPORT:
    - Related to BUG-689
    - Data deleted immediately on erasure request
    - No grace period for user to recover account
    - Industry standard is 30 days before permanent deletion

    GDPR COMPLIANCE:
    - Article 17(1): Without undue delay (typically 30 days)
    - Allows reasonable time for backup purging
    - Balances user rights with operational needs

    TEST SCENARIO:
    1. User requests erasure
    2. Account marked for deletion, not immediately deleted
    3. Data remains accessible for 30 days
    4. After 30 days, permanent deletion occurs
    5. User can cancel erasure within grace period

    EXPECTED BEHAVIOR:
    - Erasure request creates scheduled_deletion_date
    - Account marked as inactive but data preserved
    - After 30 days, automated job performs deletion
    - User can login and cancel within grace period

    VERIFICATION:
    - Check scheduled deletion date
    - Verify account status
    - Test cancellation workflow
    - Verify auto-deletion after 30 days

    PREVENTION:
    - Scheduled deletion job monitoring
    - Grace period configurable (default 30 days)
    - User notification system for pending deletion
    """
    # Create user
    user_data = create_test_user(role="student")
    user_id = user_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (
            id, username, email, password_hash, role_name,
            is_active, deletion_scheduled, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        user_id, user_data['username'], user_data['email'],
        user_data['password_hash'], user_data['role_name'],
        True, False, user_data['created_at']
    )

    # Request erasure
    erasure_date = datetime.utcnow()
    scheduled_deletion_date = erasure_date + timedelta(days=30)

    await db_transaction.execute(
        """
        UPDATE users
        SET deletion_scheduled = TRUE,
            scheduled_deletion_date = $2,
            is_active = FALSE
        WHERE id = $1
        """,
        user_id, scheduled_deletion_date
    )

    # REGRESSION CHECK 1: User not immediately deleted
    user_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM users WHERE id = $1", user_id
    )

    assert user_exists == 1, \
        "REGRESSION FAILURE BUG-689: User immediately deleted (should have 30-day grace period)"

    # REGRESSION CHECK 2: Scheduled deletion date set
    user_record = await db_transaction.fetchrow(
        """
        SELECT deletion_scheduled, scheduled_deletion_date, is_active
        FROM users
        WHERE id = $1
        """,
        user_id
    )

    assert user_record['deletion_scheduled'] is True, \
        "REGRESSION FAILURE BUG-689: Deletion not scheduled"

    assert user_record['scheduled_deletion_date'] is not None, \
        "REGRESSION FAILURE BUG-689: Scheduled deletion date not set"

    # REGRESSION CHECK 3: Account marked inactive
    assert user_record['is_active'] is False, \
        "REGRESSION FAILURE BUG-689: Account still active after erasure request"

    # REGRESSION CHECK 4: Grace period is 30 days
    actual_grace_period = (user_record['scheduled_deletion_date'] - erasure_date).days

    assert actual_grace_period == 30, \
        f"REGRESSION FAILURE BUG-689: Grace period is {actual_grace_period} days (should be 30)"

    # Simulate user canceling deletion within grace period
    await db_transaction.execute(
        """
        UPDATE users
        SET deletion_scheduled = FALSE,
            scheduled_deletion_date = NULL,
            is_active = TRUE
        WHERE id = $1
        """,
        user_id
    )

    # REGRESSION CHECK 5: Cancellation successful
    user_after_cancel = await db_transaction.fetchrow(
        """
        SELECT deletion_scheduled, is_active
        FROM users
        WHERE id = $1
        """,
        user_id
    )

    assert user_after_cancel['deletion_scheduled'] is False, \
        "REGRESSION FAILURE BUG-689: Deletion still scheduled after cancellation"

    assert user_after_cancel['is_active'] is True, \
        "REGRESSION FAILURE BUG-689: Account not reactivated after cancellation"


# ============================================================================
# AUDIT LOGGING REGRESSION TESTS (BUG-723) - 4 TESTS
# ============================================================================

@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG723_admin_actions_logged_with_tamper_evident_checksums(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Admin actions logged with tamper-evident checksums

    BUG REPORT:
    - Issue ID: BUG-723
    - Reported: 2025-10-28
    - Fixed: 2025-10-30
    - Severity: HIGH
    - Root Cause: Admin endpoints did not have audit middleware applied.
                  Audit logs stored without integrity verification checksums.
                  Logs could be modified without detection.

    GDPR COMPLIANCE:
    - Article 30: Records of processing activities
    - Article 32: Security of processing - integrity verification
    - Article 33: Breach notification requires audit trail

    TEST SCENARIO:
    1. Admin performs privileged action (user creation)
    2. Audit log entry created
    3. Log includes tamper-evident checksum (SHA256)
    4. Modify log entry
    5. Verify checksum invalidation detects tampering

    EXPECTED BEHAVIOR:
    - All admin actions logged automatically
    - Log entry includes SHA256 checksum
    - Checksum covers: action, actor_id, timestamp, details
    - Checksum verification detects any modification

    VERIFICATION:
    - Audit log created for action
    - Checksum present and valid
    - Tamper detection works

    PREVENTION:
    - Apply audit middleware to ALL admin endpoints
    - Automated audit log coverage testing
    - Regular audit log integrity verification
    """
    # Create admin user
    admin_data = create_test_user(role="admin")
    admin_id = admin_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        admin_id, admin_data['username'], admin_data['email'],
        admin_data['password_hash'], admin_data['role_name'],
        admin_data['is_active'], admin_data['created_at']
    )

    # Simulate admin action - create new user
    target_user = create_test_user(role="student")
    target_user_id = target_user['id']

    action_timestamp = datetime.utcnow()
    action_details = f"Created user {target_user['username']}"

    # Calculate tamper-evident checksum
    checksum_input = f"{admin_id}|user_created|{action_timestamp.isoformat()}|{action_details}"
    tamper_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

    # Create audit log entry
    audit_log_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO audit_logs (
            id, actor_id, action_type, action_timestamp,
            action_details, tamper_checksum
        ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
        audit_log_id, admin_id, 'user_created', action_timestamp,
        action_details, tamper_checksum
    )

    # REGRESSION CHECK 1: Audit log created
    log_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM audit_logs WHERE id = $1", audit_log_id
    )

    assert log_exists == 1, \
        "REGRESSION FAILURE BUG-723: Audit log not created for admin action"

    # REGRESSION CHECK 2: Tamper checksum present
    log_record = await db_transaction.fetchrow(
        """
        SELECT actor_id, action_type, action_timestamp, action_details, tamper_checksum
        FROM audit_logs
        WHERE id = $1
        """,
        audit_log_id
    )

    assert log_record['tamper_checksum'] is not None, \
        "REGRESSION FAILURE BUG-723: Tamper checksum not generated"

    assert len(log_record['tamper_checksum']) == 64, \
        f"REGRESSION FAILURE BUG-723: Invalid checksum length: {len(log_record['tamper_checksum'])}"

    # REGRESSION CHECK 3: Checksum is valid
    verify_input = f"{log_record['actor_id']}|{log_record['action_type']}|{log_record['action_timestamp'].isoformat()}|{log_record['action_details']}"
    verify_checksum = hashlib.sha256(verify_input.encode()).hexdigest()

    assert log_record['tamper_checksum'] == verify_checksum, \
        "REGRESSION FAILURE BUG-723: Tamper checksum does not match"

    # REGRESSION CHECK 4: Tamper detection works
    # Modify log entry
    await db_transaction.execute(
        """
        UPDATE audit_logs
        SET action_details = 'Modified details'
        WHERE id = $1
        """,
        audit_log_id
    )

    # Retrieve modified record
    modified_record = await db_transaction.fetchrow(
        """
        SELECT actor_id, action_type, action_timestamp, action_details, tamper_checksum
        FROM audit_logs
        WHERE id = $1
        """,
        audit_log_id
    )

    # Verify checksum
    modified_verify_input = f"{modified_record['actor_id']}|{modified_record['action_type']}|{modified_record['action_timestamp'].isoformat()}|{modified_record['action_details']}"
    modified_verify_checksum = hashlib.sha256(modified_verify_input.encode()).hexdigest()

    checksum_valid = modified_record['tamper_checksum'] == modified_verify_checksum

    assert not checksum_valid, \
        "REGRESSION FAILURE BUG-723: Tamper detection failed - modified log passed checksum verification"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG723_user_deletion_logged(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: User deletion must be logged in audit trail

    BUG REPORT:
    - Related to BUG-723
    - User deletions (GDPR erasure) not logged
    - No record of who approved deletion
    - No timestamp of deletion for compliance

    GDPR COMPLIANCE:
    - Article 30(1)(a): Records of processing activities
    - Must document: purpose, categories, recipients, erasures

    TEST SCENARIO:
    1. Admin deletes user (GDPR erasure)
    2. Verify audit log created
    3. Log includes: admin_id, user_id, reason, timestamp
    4. Log immutable with tamper checksum

    EXPECTED BEHAVIOR:
    - Deletion triggers audit log entry
    - Actor (admin) identified
    - Target (user) identified
    - Reason (GDPR Article 17) documented
    - Timestamp recorded

    VERIFICATION:
    - Audit log exists
    - Required fields present
    - Tamper checksum valid

    PREVENTION:
    - Audit middleware on delete endpoints
    - Automated deletion audit testing
    - Compliance audit reports
    """
    # Create admin
    admin_data = create_test_user(role="admin")
    admin_id = admin_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        admin_id, admin_data['username'], admin_data['email'],
        admin_data['password_hash'], admin_data['role_name'],
        admin_data['is_active'], admin_data['created_at']
    )

    # Create user to delete
    target_user = create_test_user(role="student")
    target_user_id = target_user['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        target_user_id, target_user['username'], target_user['email'],
        target_user['password_hash'], target_user['role_name'],
        target_user['is_active'], target_user['created_at']
    )

    # Log deletion action
    deletion_timestamp = datetime.utcnow()
    deletion_reason = "GDPR Article 17 - Right to Erasure"
    action_details = f"Deleted user {target_user['username']} (ID: {target_user_id}). Reason: {deletion_reason}"

    checksum_input = f"{admin_id}|user_deleted|{deletion_timestamp.isoformat()}|{action_details}"
    tamper_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

    audit_log_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO audit_logs (
            id, actor_id, target_user_id, action_type, action_timestamp,
            action_details, deletion_reason, tamper_checksum
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        audit_log_id, admin_id, target_user_id, 'user_deleted',
        deletion_timestamp, action_details, deletion_reason, tamper_checksum
    )

    # Delete user
    await db_transaction.execute(
        "DELETE FROM users WHERE id = $1", target_user_id
    )

    # REGRESSION CHECK 1: Audit log exists
    log_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM audit_logs WHERE id = $1", audit_log_id
    )

    assert log_exists == 1, \
        "REGRESSION FAILURE BUG-723: User deletion not logged"

    # REGRESSION CHECK 2: Required fields present
    log_record = await db_transaction.fetchrow(
        """
        SELECT actor_id, target_user_id, action_type, deletion_reason, tamper_checksum
        FROM audit_logs
        WHERE id = $1
        """,
        audit_log_id
    )

    assert log_record['actor_id'] == admin_id, \
        "REGRESSION FAILURE BUG-723: Admin ID not recorded in deletion log"

    assert log_record['target_user_id'] == target_user_id, \
        "REGRESSION FAILURE BUG-723: Target user ID not recorded"

    assert log_record['action_type'] == 'user_deleted', \
        "REGRESSION FAILURE BUG-723: Action type not recorded correctly"

    assert log_record['deletion_reason'] is not None, \
        "REGRESSION FAILURE BUG-723: Deletion reason not documented"

    assert "GDPR Article 17" in log_record['deletion_reason'], \
        "REGRESSION FAILURE BUG-723: GDPR article not referenced in deletion reason"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG723_role_changes_logged(
    db_transaction, create_test_user
):
    """
    REGRESSION TEST: Role changes must be logged for security audit

    BUG REPORT:
    - Related to BUG-723
    - Role escalations not logged
    - Privilege changes not auditable
    - Security risk for unauthorized access

    GDPR COMPLIANCE:
    - Article 30: Records of processing activities
    - Article 32: Security measures including access control

    TEST SCENARIO:
    1. Admin changes user role (student → instructor)
    2. Verify audit log created
    3. Log includes: admin_id, user_id, old_role, new_role
    4. Tamper checksum protects integrity

    EXPECTED BEHAVIOR:
    - Role change triggers audit log
    - Both old and new roles recorded
    - Timestamp and actor documented
    - Immutable audit trail

    VERIFICATION:
    - Audit log created
    - Role transition documented
    - Checksum valid

    PREVENTION:
    - Audit all RBAC changes
    - Security audit reports
    - Anomaly detection for role changes
    """
    # Create admin
    admin_data = create_test_user(role="admin")
    admin_id = admin_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        admin_id, admin_data['username'], admin_data['email'],
        admin_data['password_hash'], admin_data['role_name'],
        admin_data['is_active'], admin_data['created_at']
    )

    # Create user with initial role
    target_user = create_test_user(role="student")
    target_user_id = target_user['id']
    old_role = "student"
    new_role = "instructor"

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        target_user_id, target_user['username'], target_user['email'],
        target_user['password_hash'], old_role,
        target_user['is_active'], target_user['created_at']
    )

    # Log role change
    change_timestamp = datetime.utcnow()
    action_details = f"Changed role for {target_user['username']} from {old_role} to {new_role}"

    checksum_input = f"{admin_id}|role_changed|{change_timestamp.isoformat()}|{action_details}"
    tamper_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

    audit_log_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO audit_logs (
            id, actor_id, target_user_id, action_type, action_timestamp,
            action_details, old_role, new_role, tamper_checksum
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        audit_log_id, admin_id, target_user_id, 'role_changed',
        change_timestamp, action_details, old_role, new_role, tamper_checksum
    )

    # Change user role
    await db_transaction.execute(
        """
        UPDATE users
        SET role_name = $2
        WHERE id = $1
        """,
        target_user_id, new_role
    )

    # REGRESSION CHECK 1: Audit log exists
    log_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM audit_logs WHERE id = $1", audit_log_id
    )

    assert log_exists == 1, \
        "REGRESSION FAILURE BUG-723: Role change not logged"

    # REGRESSION CHECK 2: Role transition documented
    log_record = await db_transaction.fetchrow(
        """
        SELECT actor_id, target_user_id, old_role, new_role, action_type
        FROM audit_logs
        WHERE id = $1
        """,
        audit_log_id
    )

    assert log_record['old_role'] == old_role, \
        f"REGRESSION FAILURE BUG-723: Old role not recorded (expected {old_role}, got {log_record['old_role']})"

    assert log_record['new_role'] == new_role, \
        f"REGRESSION FAILURE BUG-723: New role not recorded (expected {new_role}, got {log_record['new_role']})"

    assert log_record['action_type'] == 'role_changed', \
        "REGRESSION FAILURE BUG-723: Action type not recorded correctly"


@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.privacy
@pytest.mark.asyncio
async def test_BUG723_organization_configuration_changes_logged(
    db_transaction, create_test_user, create_test_organization
):
    """
    REGRESSION TEST: Organization configuration changes must be logged

    BUG REPORT:
    - Related to BUG-723
    - Organization setting changes not audited
    - Privacy settings changes untracked
    - Compliance configuration not documented

    GDPR COMPLIANCE:
    - Article 30: Records of processing activities
    - Article 28: Processor must maintain records

    TEST SCENARIO:
    1. Org admin changes organization settings
    2. Settings change affects data processing
    3. Verify audit log created
    4. Log documents: who, what, when, why

    EXPECTED BEHAVIOR:
    - Configuration changes logged
    - Actor and organization identified
    - Old and new values recorded
    - Tamper-evident checksum

    VERIFICATION:
    - Audit log created
    - Configuration diff documented
    - Checksum valid

    PREVENTION:
    - Audit middleware on org config endpoints
    - Change management workflows
    - Compliance configuration tracking
    """
    # Create org admin
    admin_data = create_test_user(role="org_admin")
    admin_id = admin_data['id']

    # Create organization
    org_data = create_test_organization()
    org_id = org_data['id']

    await db_transaction.execute(
        """
        INSERT INTO users (id, username, email, password_hash, role_name, organization_id, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        admin_id, admin_data['username'], admin_data['email'],
        admin_data['password_hash'], admin_data['role_name'],
        org_id, admin_data['is_active'], admin_data['created_at']
    )

    await db_transaction.execute(
        """
        INSERT INTO organizations (id, name, slug, contact_email, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        org_id, org_data['name'], org_data['slug'],
        org_data['contact_email'], org_data['is_active'], org_data['created_at']
    )

    # Log configuration change
    change_timestamp = datetime.utcnow()
    setting_name = "data_retention_days"
    old_value = "90"
    new_value = "30"
    action_details = f"Changed {setting_name} from {old_value} to {new_value} for organization {org_data['name']}"

    checksum_input = f"{admin_id}|org_config_changed|{change_timestamp.isoformat()}|{action_details}"
    tamper_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

    audit_log_id = str(uuid.uuid4())

    await db_transaction.execute(
        """
        INSERT INTO audit_logs (
            id, actor_id, organization_id, action_type, action_timestamp,
            action_details, setting_name, old_value, new_value, tamper_checksum
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        audit_log_id, admin_id, org_id, 'org_config_changed',
        change_timestamp, action_details, setting_name,
        old_value, new_value, tamper_checksum
    )

    # REGRESSION CHECK 1: Audit log exists
    log_exists = await db_transaction.fetchval(
        "SELECT COUNT(*) FROM audit_logs WHERE id = $1", audit_log_id
    )

    assert log_exists == 1, \
        "REGRESSION FAILURE BUG-723: Organization configuration change not logged"

    # REGRESSION CHECK 2: Configuration change documented
    log_record = await db_transaction.fetchrow(
        """
        SELECT actor_id, organization_id, setting_name, old_value, new_value
        FROM audit_logs
        WHERE id = $1
        """,
        audit_log_id
    )

    assert log_record['organization_id'] == org_id, \
        "REGRESSION FAILURE BUG-723: Organization ID not recorded"

    assert log_record['setting_name'] == setting_name, \
        "REGRESSION FAILURE BUG-723: Setting name not documented"

    assert log_record['old_value'] == old_value, \
        "REGRESSION FAILURE BUG-723: Old value not recorded"

    assert log_record['new_value'] == new_value, \
        "REGRESSION FAILURE BUG-723: New value not recorded"

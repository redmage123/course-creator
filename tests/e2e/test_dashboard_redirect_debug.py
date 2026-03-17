"""
Debug Test for Dashboard Redirect Issue

BUSINESS CONTEXT:
Reproduces the exact user flow where user 'bbrelin' logs in, navigates to
org admin dashboard, and experiences a redirect back to home page after 9 seconds.

TECHNICAL IMPLEMENTATION:
- Uses Selenium to automate the exact user journey
- Captures console logs to see what's causing the redirect
- Monitors localStorage to track session data
- Records timing of redirect

TDD METHODOLOGY:
This test will help us understand WHY the redirect is happening by capturing
all browser state and logs during the redirect.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

class TestDashboardRedirectDebug:
    """
    Debug test to capture what causes the dashboard redirect
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """Setup Chrome with logging enabled and Grid support"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')

        # Enable browser logging
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        # Check for Selenium Grid configuration
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        if selenium_remote:
            driver = webdriver.Remote(
                command_executor=selenium_remote,
                options=chrome_options
            )
        else:
            driver = webdriver.Chrome(options=chrome_options)

        driver.set_page_load_timeout(45)  # Increased for Grid reliability
        yield driver
        driver.quit()

    def test_reproduce_dashboard_redirect(self, driver):
        """
        TEST: Reproduce the exact user flow and capture redirect behavior
        """
        BASE_URL = 'https://localhost:3000'

        print("\n" + "="*80)
        print("STARTING DASHBOARD REDIRECT DEBUG TEST")
        print("="*80)

        # Step 1: Navigate to home page
        print("\n[STEP 1] Navigating to home page...")
        driver.get(f'{BASE_URL}/html/index.html')
        time.sleep(2)

        # Step 2: Check if already logged in (look for "back to dashboard" link)
        print("\n[STEP 2] Checking if already logged in...")
        try:
            # Look for dashboard link or login form
            dashboard_link = driver.find_elements(By.PARTIAL_LINK_TEXT, 'dashboard')
            login_form = driver.find_elements(By.NAME, 'username')

            if dashboard_link:
                print("✓ User appears to be logged in (dashboard link found)")
            elif login_form:
                print("✓ User not logged in (login form found)")
                print("[STEP 2a] Logging in as 'bbrelin'...")

                # Login
                username_field = driver.find_element(By.NAME, 'username')
                password_field = driver.find_element(By.NAME, 'password')

                username_field.send_keys('bbrelin')
                password_field.send_keys('password123')  # You'll need to provide real password

                submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                submit_btn.click()

                print("   Waiting for login to complete...")
                time.sleep(3)
        except Exception as e:
            print(f"⚠ Could not determine login state: {e}")

        # Step 3: Capture localStorage after login
        print("\n[STEP 3] Capturing localStorage state...")
        local_storage = driver.execute_script("""
            return {
                authToken: localStorage.getItem('authToken'),
                currentUser: localStorage.getItem('currentUser'),
                sessionStart: localStorage.getItem('sessionStart'),
                lastActivity: localStorage.getItem('lastActivity'),
                userEmail: localStorage.getItem('userEmail')
            };
        """)

        print("   localStorage contents:")
        for key, value in local_storage.items():
            if value:
                display_value = value[:50] + '...' if len(str(value)) > 50 else value
                print(f"     {key}: {display_value}")
            else:
                print(f"     {key}: [NOT SET]")

        # Step 4: Navigate to org admin dashboard
        print("\n[STEP 4] Navigating to org admin dashboard...")
        current_url = driver.current_url
        print(f"   Current URL: {current_url}")

        # Try to find dashboard link or navigate directly
        try:
            # Look for any dashboard links
            dashboard_links = driver.find_elements(By.PARTIAL_LINK_TEXT, 'dashboard')
            if dashboard_links:
                print(f"   Found {len(dashboard_links)} dashboard link(s)")
                print(f"   Clicking first dashboard link...")
                dashboard_links[0].click()
            else:
                # Navigate directly - we need to get org_id from currentUser
                current_user_json = local_storage.get('currentUser')
                if current_user_json:
                    import json
                    current_user = json.loads(current_user_json)
                    org_id = current_user.get('organization_id')
                    if org_id:
                        print(f"   Navigating directly with org_id={org_id}")
                        driver.get(f'{BASE_URL}/html/org-admin-dashboard.html?org_id={org_id}')
                    else:
                        print("   ⚠ No organization_id found in currentUser")
                        driver.get(f'{BASE_URL}/html/org-admin-dashboard.html')
                else:
                    print("   ⚠ No currentUser in localStorage, navigating without org_id")
                    driver.get(f'{BASE_URL}/html/org-admin-dashboard.html')
        except Exception as e:
            print(f"   ⚠ Error navigating to dashboard: {e}")

        time.sleep(2)

        # Step 5: Verify we're on the dashboard
        print("\n[STEP 5] Verifying dashboard loaded...")
        dashboard_url = driver.current_url
        print(f"   Current URL: {dashboard_url}")

        if 'org-admin-dashboard' in dashboard_url:
            print("   ✓ Successfully loaded org admin dashboard")
        else:
            print("   ✗ Not on org admin dashboard!")
            return

        # Step 6: Monitor for redirect (wait up to 15 seconds)
        print("\n[STEP 6] Monitoring for redirect (waiting 15 seconds)...")
        print("   Time | URL")
        print("   " + "-"*70)

        start_time = time.time()
        last_url = dashboard_url
        redirect_detected = False
        redirect_time = None

        for i in range(15):
            time.sleep(1)
            current_url = driver.current_url
            elapsed = i + 1

            # Print status every second
            url_display = current_url if len(current_url) < 60 else current_url[:57] + '...'
            print(f"   {elapsed:02d}s  | {url_display}")

            # Check if redirect happened
            if current_url != last_url:
                redirect_detected = True
                redirect_time = elapsed
                print(f"\n   🔔 REDIRECT DETECTED at {elapsed} seconds!")
                print(f"      From: {last_url}")
                print(f"      To:   {current_url}")
                break

            last_url = current_url

        # Step 7: Capture browser console logs
        print("\n[STEP 7] Capturing browser console logs...")
        logs = driver.get_log('browser')

        if logs:
            print(f"   Found {len(logs)} console log entries:")
            print("   " + "-"*70)
            for log in logs:
                timestamp = log.get('timestamp', 'unknown')
                level = log.get('level', 'INFO')
                message = log.get('message', '')

                # Filter for relevant logs
                if any(keyword in message.lower() for keyword in ['session', 'redirect', 'auth', 'error', 'invalid']):
                    print(f"   [{level}] {message[:200]}")
        else:
            print("   No console logs captured")

        # Step 8: Capture final localStorage state
        print("\n[STEP 8] Capturing final localStorage state...")
        final_storage = driver.execute_script("""
            return {
                authToken: localStorage.getItem('authToken'),
                currentUser: localStorage.getItem('currentUser'),
                sessionStart: localStorage.getItem('sessionStart'),
                lastActivity: localStorage.getItem('lastActivity'),
                userEmail: localStorage.getItem('userEmail')
            };
        """)

        print("   Final localStorage contents:")
        for key, value in final_storage.items():
            if value:
                display_value = value[:50] + '...' if len(str(value)) > 50 else value
                print(f"     {key}: {display_value}")
            else:
                print(f"     {key}: [NOT SET]")

        # Step 9: Results summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        if redirect_detected:
            print(f"❌ REDIRECT OCCURRED after {redirect_time} seconds")
            print(f"   Initial URL: {dashboard_url}")
            print(f"   Final URL:   {driver.current_url}")
        else:
            print(f"✓ NO REDIRECT in 15 seconds")
            print(f"   Dashboard remained stable at: {driver.current_url}")

        print("\nLocalStorage Changes:")
        for key in local_storage.keys():
            initial = local_storage.get(key)
            final = final_storage.get(key)
            if initial != final:
                print(f"   {key}: CHANGED")
                print(f"     Before: {initial}")
                print(f"     After:  {final}")
            else:
                status = "SET" if initial else "NOT SET"
                print(f"   {key}: {status} (unchanged)")

        print("="*80)

        # Keep browser open for manual inspection
        print("\n⏸  Browser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)

if __name__ == "__main__":
    # Run the test directly
    test = TestDashboardRedirectDebug()
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    test_instance = test
    try:
        test_instance.test_reproduce_dashboard_redirect(driver)
    finally:
        driver.quit()

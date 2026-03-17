#!/usr/bin/env python3
"""
Debug script to check what's actually loading on the org admin dashboard
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Setup Chrome
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)

try:
    # Navigate to login page
    print("1. Navigating to login page...")
    driver.get("https://localhost/html/index.html")
    time.sleep(2)

    # Set up authentication
    print("2. Setting up authentication...")
    driver.execute_script("""
        localStorage.setItem('authToken', 'test-org-admin-token-12345');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 100,
            email: 'orgadmin@testorg.com',
            role: 'organization_admin',
            organization_id: 1,
            name: 'Test Org Admin'
        }));
        localStorage.setItem('userEmail', 'orgadmin@testorg.com');
        localStorage.setItem('sessionStart', Date.now().toString());
        localStorage.setItem('lastActivity', Date.now().toString());
    """)

    # Navigate to dashboard
    print("3. Navigating to org admin dashboard...")
    driver.get("https://localhost/html/org-admin-dashboard.html?org_id=1")
    time.sleep(5)

    # Save screenshot
    screenshot_path = "/home/bbrelin/course-creator/tests/reports/screenshots/debug_dashboard_load.png"
    driver.save_screenshot(screenshot_path)
    print(f"4. Screenshot saved to {screenshot_path}")

    # Check page title
    print(f"5. Page title: {driver.title}")

    # Check page source for projects tab
    page_source = driver.page_source
    if 'data-tab="projects"' in page_source:
        print("6. ✅ Found 'data-tab=\"projects\"' in page source")
    else:
        print("6. ❌ NOT FOUND: 'data-tab=\"projects\"' in page source")

    # Try to find any elements with data-tab attribute
    data_tab_elements = driver.find_elements(By.CSS_SELECTOR, '[data-tab]')
    print(f"7. Found {len(data_tab_elements)} elements with [data-tab] attribute:")
    for elem in data_tab_elements[:10]:  # Show first 10
        tab_name = elem.get_attribute('data-tab')
        visible = elem.is_displayed()
        print(f"   - data-tab=\"{tab_name}\" (visible: {visible})")

    # Check for JavaScript errors
    logs = driver.get_log('browser')
    if logs:
        print(f"8. Browser console logs ({len(logs)} entries):")
        for log in logs[:10]:  # Show first 10
            print(f"   {log['level']}: {log['message'][:100]}")
    else:
        print("8. No browser console logs")

    # Check if page loaded properly
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print(f"9. Page body text length: {len(body_text)} characters")
    if body_text:
        print(f"   First 200 chars: {body_text[:200]}")

finally:
    driver.quit()
    print("\n10. Driver closed")

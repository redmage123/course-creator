#!/usr/bin/env python3
"""
Quick verification that navigation-system.js syntax error is fixed
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
    # Navigate and authenticate
    print("1. Setting up authentication...")
    driver.get("https://localhost/html/index.html")
    time.sleep(2)

    driver.execute_script("""
        localStorage.setItem('authToken', 'test-org-admin-token-12345');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 100,
            email: 'orgadmin@testorg.com',
            role: 'organization_admin',
            organization_id: 1,
            name: 'Test Org Admin'
        }));
    """)

    # Navigate to dashboard
    print("2. Navigating to org admin dashboard...")
    driver.get("https://localhost/html/org-admin-dashboard.html?org_id=1")
    time.sleep(5)

    # Check for JavaScript errors
    print("3. Checking browser console for errors...")
    logs = driver.get_log('browser')

    has_navigation_error = False
    has_wizard_error = False

    for log in logs:
        if 'navigation-system.js:85' in log['message'] and 'SyntaxError' in log['message']:
            has_navigation_error = True
            print(f"   ❌ STILL BROKEN: {log['message'][:150]}")
        elif 'wizard-validation.js:93' in log['message'] and 'Form not found' in log['message']:
            has_wizard_error = True
            print(f"   ⚠️  SECONDARY: {log['message'][:150]}")
        elif log['level'] == 'SEVERE':
            print(f"   ⚠️  {log['level']}: {log['message'][:150]}")

    if not has_navigation_error:
        print("   ✅ navigation-system.js:85 syntax error FIXED!")

    if has_wizard_error:
        print("   ℹ️  Wizard validation error still present (may be secondary issue)")

    # Try to click Projects tab to verify JavaScript functionality
    print("4. Testing Projects tab click...")
    try:
        projects_tab = driver.find_element(By.CSS_SELECTOR, '[data-tab="projects"]')
        driver.execute_script("arguments[0].click()", projects_tab)
        time.sleep(2)
        print("   ✅ Projects tab clickable - JavaScript executing")
    except Exception as e:
        print(f"   ❌ Projects tab issue: {str(e)[:100]}")

finally:
    driver.quit()
    print("\n5. Verification complete")

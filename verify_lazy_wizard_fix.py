#!/usr/bin/env python3
"""
Verify that lazy wizard initialization prevents "Form not found" error
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

    # Check for errors BEFORE opening modal (should be none now)
    print("3. Checking errors BEFORE opening modal...")
    logs_before = driver.get_log('browser')
    wizard_errors_before = [log for log in logs_before if 'wizard-validation.js:92' in log['message'] and 'Form not found' in log['message']]

    if len(wizard_errors_before) > 0:
        print(f"   ❌ FAILED: {len(wizard_errors_before)} wizard validation errors BEFORE modal opened")
        for err in wizard_errors_before:
            print(f"      {err['message'][:150]}")
    else:
        print("   ✅ No wizard errors on dashboard load (lazy init working!)")

    # Click Projects tab
    print("4. Clicking Projects tab...")
    projects_tab = driver.find_element(By.CSS_SELECTOR, '[data-tab="projects"]')
    driver.execute_script("arguments[0].click()", projects_tab)
    time.sleep(3)

    # Open Create Project modal
    print("5. Opening Create Project modal...")
    create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Project')]")
    driver.execute_script("arguments[0].click()", create_btn)
    time.sleep(2)

    # Check for wizard initialization log
    print("6. Checking wizard initialization...")
    result = driver.execute_script("""
        return {
            wizardExists: typeof projectWizard !== 'undefined' && projectWizard !== null,
            wizardType: typeof projectWizard
        };
    """)

    if result['wizardExists']:
        print("   ✅ Wizard initialized successfully after modal opened")
    else:
        print(f"   ⚠️  Wizard status: {result['wizardType']}")

    # Check console logs after modal opened
    print("7. Checking errors AFTER opening modal...")
    logs_after = driver.get_log('browser')
    wizard_errors_after = [log for log in logs_after if 'wizard-validation.js:92' in log['message'] and 'Form not found' in log['message']]

    new_errors = len(wizard_errors_after) - len(wizard_errors_before)
    if new_errors > 0:
        print(f"   ❌ {new_errors} NEW wizard errors after opening modal")
    else:
        print("   ✅ No new wizard errors after opening modal")

finally:
    driver.quit()
    print("\n8. Verification complete")

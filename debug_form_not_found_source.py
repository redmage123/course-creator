#!/usr/bin/env python3
"""
Debug script to find the exact source of "Form not found: null" error
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

# Enable verbose console logging
options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})

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

    # Get ALL browser logs
    print("3. Analyzing browser console logs...\n")
    logs = driver.get_log('browser')

    # Find wizard validation errors
    wizard_errors = []
    for log in logs:
        msg = log['message']
        if 'wizard-validation.js' in msg and 'Form not found' in msg:
            wizard_errors.append(log)

    if len(wizard_errors) == 0:
        print("✅ NO 'Form not found' ERRORS - Fix successful!\n")
    else:
        print(f"❌ FOUND {len(wizard_errors)} 'Form not found' ERROR(S):\n")
        for i, err in enumerate(wizard_errors, 1):
            print(f"Error #{i}:")
            print(f"  Level: {err['level']}")
            print(f"  Source: {err['source']}")
            print(f"  Message: {err['message']}\n")

    # Check for any WizardFramework initialization logs
    print("4. Checking for WizardFramework initialization logs...")
    framework_logs = [log for log in logs if 'WizardFramework' in log['message'] or 'Initializing Wave 5' in log['message']]
    if framework_logs:
        print(f"Found {len(framework_logs)} framework logs:")
        for log in framework_logs:
            print(f"  - {log['message'][:200]}")
    else:
        print("  No WizardFramework initialization logs found")

finally:
    driver.quit()
    print("\n5. Debug complete")

#!/usr/bin/env python3
"""
Debug script to check which functions are actually exported
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

    # Click Projects tab
    print("3. Clicking Projects tab...")
    projects_tab = driver.find_element(By.CSS_SELECTOR, '[data-tab="projects"]')
    driver.execute_script("arguments[0].click()", projects_tab)
    time.sleep(3)

    # Check what functions are available
    print("4. Checking available functions...")
    result = driver.execute_script("""
        return {
            orgAdminExists: typeof window.OrgAdmin !== 'undefined',
            projectsExists: typeof window.OrgAdmin?.Projects !== 'undefined',
            allKeys: window.OrgAdmin?.Projects ? Object.keys(window.OrgAdmin.Projects) : [],
            nextProjectStep: typeof window.OrgAdmin?.Projects?.nextProjectStep,
            previousProjectStep: typeof window.OrgAdmin?.Projects?.previousProjectStep,
            resetProjectWizard: typeof window.OrgAdmin?.Projects?.resetProjectWizard,
            finalizeProjectCreation: typeof window.OrgAdmin?.Projects?.finalizeProjectCreation
        };
    """)

    print(f"   window.OrgAdmin exists: {result['orgAdminExists']}")
    print(f"   window.OrgAdmin.Projects exists: {result['projectsExists']}")
    print(f"   Total functions exported: {len(result['allKeys'])}")
    print(f"   All exported function names: {', '.join(result['allKeys'][:10])}...")
    print(f"\n   nextProjectStep type: {result['nextProjectStep']}")
    print(f"   previousProjectStep type: {result['previousProjectStep']}")
    print(f"   resetProjectWizard type: {result['resetProjectWizard']}")
    print(f"   finalizeProjectCreation type: {result['finalizeProjectCreation']}")

finally:
    driver.quit()
    print("\n5. Debug complete")

#!/usr/bin/env python3
"""
Debug script to investigate why Step 2 doesn't show 'active' class immediately
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

    # Open wizard
    print("4. Opening Create Project wizard...")
    create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Project')]")
    driver.execute_script("arguments[0].click()", create_btn)
    time.sleep(1)

    # Fill Step 1
    print("5. Filling Step 1 fields...")
    project_name = driver.find_element(By.ID, "projectName")
    project_name.send_keys("Debug Test Project")

    project_slug = driver.find_element(By.ID, "projectSlug")
    project_slug.send_keys("debug-test")
    time.sleep(0.5)

    # Check Step 1 class BEFORE navigation
    step1_before = driver.find_element(By.ID, "projectStep1")
    step2_before = driver.find_element(By.ID, "projectStep2")
    print(f"6. BEFORE navigation:")
    print(f"   Step 1 class: {step1_before.get_attribute('class')}")
    print(f"   Step 2 class: {step2_before.get_attribute('class')}")
    print(f"   Step 1 display: {step1_before.value_of_css_property('display')}")
    print(f"   Step 2 display: {step2_before.value_of_css_property('display')}")

    # Call nextProjectStep() and wait for promise
    print("7. Calling nextProjectStep()...")
    result = driver.execute_script("""
        return new Promise((resolve) => {
            window.OrgAdmin.Projects.nextProjectStep().then(success => {
                resolve(success);
            });
        });
    """)
    print(f"   Navigation result: {result}")

    # Check Step 2 class IMMEDIATELY AFTER navigation
    time.sleep(0.1)  # Tiny wait to ensure DOM update
    step1_after = driver.find_element(By.ID, "projectStep1")
    step2_after = driver.find_element(By.ID, "projectStep2")
    print(f"8. AFTER navigation (0.1s wait):")
    print(f"   Step 1 class: {step1_after.get_attribute('class')}")
    print(f"   Step 2 class: {step2_after.get_attribute('class')}")
    print(f"   Step 1 display: {step1_after.value_of_css_property('display')}")
    print(f"   Step 2 display: {step2_after.value_of_css_property('display')}")

    # Check again after 2 seconds
    time.sleep(2)
    step1_later = driver.find_element(By.ID, "projectStep1")
    step2_later = driver.find_element(By.ID, "projectStep2")
    print(f"9. AFTER navigation (2s wait):")
    print(f"   Step 1 class: {step1_later.get_attribute('class')}")
    print(f"   Step 2 class: {step2_later.get_attribute('class')}")
    print(f"   Step 1 display: {step1_later.value_of_css_property('display')}")
    print(f"   Step 2 display: {step2_later.value_of_css_property('display')}")

    # Check for console errors
    print("10. Checking browser console logs:")
    logs = driver.get_log('browser')
    for log in logs:
        if log['level'] in ['SEVERE', 'WARNING']:
            print(f"    {log['level']}: {log['message'][:200]}")

finally:
    driver.quit()
    print("\n11. Debug complete")

#!/usr/bin/env python3
"""
Regenerate Slide 2: Organization Dashboard
With privacy modal dismissal, mouse cursor movement, and form filling

BUSINESS CONTEXT:
Shows the organization registration workflow with clear visual demonstration
of each form field being filled, including mouse cursor movements.
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
SCREENSHOT_DIR = "/home/bbrelin/course-creator/frontend/static/demo/screenshots"

print("=" * 70)
print("SLIDE 2: ORGANIZATION REGISTRATION - VIDEO CAPTURE")
print("=" * 70)

# Setup Chrome
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")
# NOT headless - we want to see the cursor

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

def slow_type(element, text, delay=0.08):
    """Type text slowly with visible cursor movement"""
    # First click the element to focus and move cursor there
    actions.move_to_element(element).click().perform()
    time.sleep(0.3)

    # Type each character with delay
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def move_and_click(element):
    """Move cursor to element and click it"""
    actions.move_to_element(element).perform()
    time.sleep(0.5)
    element.click()
    time.sleep(0.3)

try:
    print("\n1. Navigating to homepage...")
    driver.get(f"{BASE_URL}/")
    time.sleep(3)

    print("2. Dismissing privacy modal...")
    try:
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            move_and_click(accept_btn)
            time.sleep(2)
            print("   ✓ Privacy modal dismissed")
    except Exception as e:
        print(f"   ⚠️  No privacy modal: {e}")

    print("3. Navigating to organization registration...")
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(3)

    # Scroll to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    print("4. Filling organization information...")

    # Organization Name
    print("   - Organization Name")
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning Institute")
    time.sleep(1)

    # Website URL
    print("   - Website URL")
    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "https://acmelearning.edu")
    time.sleep(1)

    # Description
    print("   - Description")
    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional development and technical training for modern enterprises.", delay=0.06)
    time.sleep(1)

    # Scroll to contact information
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(1)

    print("5. Filling contact information...")

    # Business Email
    print("   - Business Email")
    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu")
    time.sleep(1)

    # Street Address
    print("   - Street Address")
    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Drive")
    time.sleep(1)

    # City
    print("   - City")
    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco")
    time.sleep(1)

    # Postal Code
    print("   - Postal Code")
    org_postal = driver.find_element(By.ID, "orgPostalCode")
    slow_type(org_postal, "94105")
    time.sleep(1)

    # Scroll to administrator section
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(1.5)

    print("6. Filling administrator information...")

    # Admin Name
    print("   - Administrator Name")
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson")
    time.sleep(1)

    # Admin Username
    print("   - Username")
    admin_username = driver.find_element(By.ID, "adminUsername")
    slow_type(admin_username, "sjohnson")
    time.sleep(1)

    # Admin Email
    print("   - Administrator Email")
    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah.johnson@acmelearning.edu")
    time.sleep(1)

    # Admin Password
    print("   - Password")
    admin_password = driver.find_element(By.ID, "adminPassword")
    slow_type(admin_password, "SecurePass123!", delay=0.1)
    time.sleep(1)

    # Confirm Password
    print("   - Confirm Password")
    admin_confirm = driver.find_element(By.ID, "adminPasswordConfirm")
    slow_type(admin_confirm, "SecurePass123!", delay=0.1)
    time.sleep(1)

    # Scroll to privacy consents
    driver.execute_script("window.scrollTo(0, 1800);")
    time.sleep(1.5)

    print("7. Accepting privacy consents...")

    # Check the consent checkboxes
    try:
        consent_essential = driver.find_element(By.ID, "consentEssential")
        if not consent_essential.is_selected():
            move_and_click(consent_essential)
            time.sleep(0.5)

        consent_analytics = driver.find_element(By.ID, "consentAnalytics")
        if not consent_analytics.is_selected():
            move_and_click(consent_analytics)
            time.sleep(0.5)

        consent_marketing = driver.find_element(By.ID, "consentMarketing")
        if not consent_marketing.is_selected():
            move_and_click(consent_marketing)
            time.sleep(0.5)
    except Exception as e:
        print(f"   ⚠️  Some checkboxes not found: {e}")

    # Scroll to submit button
    driver.execute_script("window.scrollTo(0, 2200);")
    time.sleep(1.5)

    print("8. Hovering over submit button...")
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        actions.move_to_element(submit_btn).perform()
        time.sleep(2)
        print("   ✓ Mouse over submit button")
    except Exception as e:
        print(f"   ⚠️  Submit button interaction: {e}")

    # Scroll back to show filled form
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(2)

    print("\n9. Taking final screenshot...")
    screenshot_path = f"{SCREENSHOT_DIR}/slide_02_org_form_filled.png"
    driver.save_screenshot(screenshot_path)

    if os.path.exists(screenshot_path):
        file_size = os.path.getsize(screenshot_path)
        print(f"   ✓ Screenshot saved: {screenshot_path} ({file_size:,} bytes)")

    print("\n✅ Form demonstration complete!")
    print("   Total time: ~45 seconds (matches slide duration)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n10. Closing browser...")
    driver.quit()

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("1. Use screen recorder (OBS/SimpleScreenRecorder) to capture this workflow")
print("2. Or modify script to use ffmpeg screen recording")
print("3. Save as: slide_02_org_admin.mp4")
print("=" * 70)

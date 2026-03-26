#!/usr/bin/env python3
"""
Debug script to test Files tab loading
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.add_argument('--user-data-dir=/tmp/chrome-debug-profile')

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

try:
    # Navigate to homepage
    print("1. Navigating to homepage...")
    driver.get("https://localhost:3000/html/index.html")
    time.sleep(2)

    # Set up instructor session
    print("2. Setting up instructor session...")
    driver.execute_script("""
        localStorage.setItem('authToken', 'test-instructor-token-12345');
        localStorage.setItem('userRole', 'instructor');
        localStorage.setItem('userName', 'Test Instructor');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 200, email: 'instructor@example.com', role: 'instructor',
            organization_id: 1, name: 'Test Instructor'
        }));
        localStorage.setItem('userEmail', 'instructor@example.com');
    """)

    # Navigate to dashboard
    print("3. Navigating to instructor dashboard...")
    driver.get("https://localhost:3000/html/instructor-dashboard-modular.html")
    time.sleep(3)

    print("4. Current URL:", driver.current_url)
    print("5. Page title:", driver.title)

    # Check if files tab link exists
    print("6. Looking for files tab link...")
    try:
        files_link = driver.find_element(By.CSS_SELECTOR, "[data-tab='files']")
        print("   ✓ Files tab link found!")
        print("   Link text:", files_link.text)
        print("   Link visible:", files_link.is_displayed())
    except Exception as e:
        print("   ✗ Files tab link NOT found:", e)

    # Try to click it
    print("7. Clicking files tab...")
    try:
        files_link.click()
        time.sleep(2)
        print("   ✓ Clicked files tab!")
    except Exception as e:
        print("   ✗ Could not click:", e)

    # Check for container
    print("8. Looking for instructorFileExplorerContainer...")
    try:
        container = driver.find_element(By.ID, "instructorFileExplorerContainer")
        print("   ✓ Container found!")
        print("   Container visible:", container.is_displayed())
        print("   Container HTML:", container.get_attribute('outerHTML')[:200])
    except Exception as e:
        print("   ✗ Container NOT found:", e)

    # Check page source
    print("9. Checking page source for 'instructorFileExplorerContainer'...")
    if "instructorFileExplorerContainer" in driver.page_source:
        print("   ✓ Found in page source!")
    else:
        print("   ✗ NOT in page source!")

    # Check for any JavaScript errors
    print("10. Checking browser console logs...")
    logs = driver.get_log('browser')
    if logs:
        print("   Console logs:")
        for log in logs[-10:]:  # Last 10 logs
            print(f"     {log['level']}: {log['message']}")
    else:
        print("   No console logs")

    # Save screenshot
    driver.save_screenshot('/home/bbrelin/course-creator/debug_files_tab.png')
    print("11. Screenshot saved to debug_files_tab.png")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\nDebug complete!")

"""
Debug test for courses tab visibility
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def selenium_driver():
    """Selenium WebDriver fixture with Chrome"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)

    yield driver

    driver.quit()


def test_debug_courses_tab(selenium_driver):
    """Debug test to check courses tab behavior"""
    driver = selenium_driver

    # Navigate to home page
    driver.get("https://localhost:3000/html/index.html")
    time.sleep(2)

    # Set up auth
    driver.execute_script("""
        localStorage.setItem('authToken', 'test-org-admin-token-course-gen');
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
    driver.get("https://localhost:3000/html/org-admin-dashboard.html?org_id=1")
    time.sleep(3)

    # Check if courses tab exists
    courses_tab = driver.find_element(By.CSS_SELECTOR, "[data-tab='courses']")
    print(f"✓ Courses tab found: {courses_tab.text}")
    print(f"  Is displayed: {courses_tab.is_displayed()}")

    # Check if courses content exists
    courses_content = driver.find_element(By.ID, "courses")
    print(f"✓ Courses content found")
    print(f"  Display style before click: {courses_content.value_of_css_property('display')}")
    print(f"  Is displayed before click: {courses_content.is_displayed()}")
    print(f"  Classes before click: {courses_content.get_attribute('class')}")

    # Check if button exists
    try:
        button = driver.find_element(By.ID, "generateCourseBtn")
        print(f"✓ Generate button found")
        print(f"  Button text: '{button.text}'")
        print(f"  Button innerHTML: '{button.get_attribute('innerHTML')}'")
    except Exception as e:
        print(f"✗ Generate button NOT found: {e}")

    # Click the tab
    print("\nClicking courses tab...")
    courses_tab.click()
    time.sleep(1)

    # Check state after click
    print(f"  Display style after click: {courses_content.value_of_css_property('display')}")
    print(f"  Is displayed after click: {courses_content.is_displayed()}")
    print(f"  Classes after click: {courses_content.get_attribute('class')}")

    # Check if any JavaScript errors
    logs = driver.get_log('browser')
    if logs:
        print("\nBrowser console logs:")
        for log in logs:
            print(f"  [{log['level']}] {log['message']}")

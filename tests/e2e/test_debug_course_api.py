"""
Debug test for course generation API integration
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


def test_debug_course_generation_api(selenium_driver):
    """Debug test to check course generation with real API"""
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

    print("\n=== STEP 1: Dashboard loaded ===")

    # Click Courses tab
    courses_tab = driver.find_element(By.CSS_SELECTOR, "[data-tab='courses']")
    courses_tab.click()
    time.sleep(2)

    print("=== STEP 2: Courses tab clicked ===")

    # Click Generate Course button
    generate_btn = driver.find_element(By.ID, "generateCourseBtn")
    print(f"Generate button found: {generate_btn.text}")
    generate_btn.click()
    time.sleep(1)

    print("=== STEP 3: Generate modal opened ===")

    # Fill form
    title_input = driver.find_element(By.ID, "generateCourseTitle")
    title_input.send_keys("Test Course via API")

    desc_input = driver.find_element(By.ID, "generateCourseDescription")
    desc_input.send_keys("This is a test course to verify API integration")

    category_select = driver.find_element(By.ID, "generateCourseCategory")
    driver.execute_script("arguments[0].value = 'Programming';", category_select)

    difficulty_select = driver.find_element(By.ID, "generateCourseDifficulty")
    driver.execute_script("arguments[0].value = 'beginner';", difficulty_select)

    print("=== STEP 4: Form filled ===")

    # Submit form
    submit_btn = driver.find_element(By.ID, "submitGenerateCourse")
    submit_btn.click()

    print("=== STEP 5: Form submitted, waiting for response... ===")

    # Wait and check for success or error
    time.sleep(5)

    # Check browser console logs
    logs = driver.get_log('browser')
    print("\n=== BROWSER CONSOLE LOGS ===")
    for log in logs:
        if 'SEVERE' in log['level'] or 'course' in log['message'].lower():
            print(f"[{log['level']}] {log['message']}")

    # Check if success message appeared
    try:
        success_div = driver.find_element(By.ID, "generateCourseSuccess")
        print(f"\n=== SUCCESS DIV ===")
        print(f"Display: {success_div.value_of_css_property('display')}")
        print(f"Visible: {success_div.is_displayed()}")
        print(f"Text: {success_div.text}")
    except Exception as e:
        print(f"\n=== SUCCESS DIV NOT FOUND: {e} ===")

    # Check courses grid
    try:
        courses_grid = driver.find_element(By.ID, "coursesGrid")
        print(f"\n=== COURSES GRID ===")
        print(f"HTML length: {len(courses_grid.get_attribute('innerHTML'))}")
        print(f"First 500 chars: {courses_grid.get_attribute('innerHTML')[:500]}")
    except Exception as e:
        print(f"\n=== COURSES GRID ERROR: {e} ===")

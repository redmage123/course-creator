#!/usr/bin/env python3
"""
Debug script to check why header-actions (login/register buttons) are not visible
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--user-data-dir=/tmp/chrome-debug-header-' + str(time.time()))

driver = webdriver.Chrome(options=chrome_options)

try:
    print("=" * 80)
    print("DEBUG: Header Actions Visibility")
    print("=" * 80)

    # Load homepage
    print("\n1. Loading homepage...")
    driver.get('https://localhost:3000/html/index.html')
    time.sleep(2)

    # Check if header-actions exists
    print("\n2. Checking header-actions element...")
    try:
        header_actions = driver.find_element(By.CLASS_NAME, 'header-actions')
        print(f"   ✅ header-actions found")

        # Get computed styles
        display = driver.execute_script("return window.getComputedStyle(arguments[0]).display", header_actions)
        visibility = driver.execute_script("return window.getComputedStyle(arguments[0]).visibility", header_actions)
        opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity", header_actions)
        width = driver.execute_script("return window.getComputedStyle(arguments[0]).width", header_actions)
        height = driver.execute_script("return window.getComputedStyle(arguments[0]).height", header_actions)
        overflow = driver.execute_script("return window.getComputedStyle(arguments[0]).overflow", header_actions)

        print(f"   - display: {display}")
        print(f"   - visibility: {visibility}")
        print(f"   - opacity: {opacity}")
        print(f"   - width: {width}")
        print(f"   - height: {height}")
        print(f"   - overflow: {overflow}")

        # Check if it's actually visible
        is_displayed = header_actions.is_displayed()
        print(f"   - is_displayed(): {is_displayed}")

        # Get element position
        locations = header_actions.locations
        size = header_actions.size
        print(f"   - locations: {locations}")
        print(f"   - size: {size}")

    except Exception as e:
        print(f"   ❌ header-actions not found: {e}")

    # Check login button specifically
    print("\n3. Checking login button...")
    try:
        login_btn = driver.find_element(By.ID, 'loginBtn')
        print(f"   ✅ loginBtn found")

        # Get computed styles
        display = driver.execute_script("return window.getComputedStyle(arguments[0]).display", login_btn)
        visibility = driver.execute_script("return window.getComputedStyle(arguments[0]).visibility", login_btn)
        opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity", login_btn)

        print(f"   - display: {display}")
        print(f"   - visibility: {visibility}")
        print(f"   - opacity: {opacity}")

        is_displayed = login_btn.is_displayed()
        print(f"   - is_displayed(): {is_displayed}")

        # Get all classes
        classes = login_btn.get_attribute('class')
        print(f"   - classes: {classes}")

        # Get text content
        text = login_btn.text
        print(f"   - text: '{text}'")

    except Exception as e:
        print(f"   ❌ loginBtn not found: {e}")

    # Check register button
    print("\n4. Checking register button...")
    try:
        register_btn = driver.find_element(By.ID, 'registerBtn')
        print(f"   ✅ registerBtn found")

        display = driver.execute_script("return window.getComputedStyle(arguments[0]).display", register_btn)
        visibility = driver.execute_script("return window.getComputedStyle(arguments[0]).visibility", register_btn)
        is_displayed = register_btn.is_displayed()

        print(f"   - display: {display}")
        print(f"   - visibility: {visibility}")
        print(f"   - is_displayed(): {is_displayed}")

    except Exception as e:
        print(f"   ❌ registerBtn not found: {e}")

    # Check all CSS files loaded
    print("\n5. Checking CSS files loaded...")
    css_links = driver.find_elements(By.CSS_SELECTOR, 'link[rel="stylesheet"]')
    print(f"   Found {len(css_links)} stylesheets:")
    for link in css_links:
        href = link.get_attribute('href')
        print(f"   - {href}")

    # Take screenshot
    print("\n6. Taking screenshot...")
    screenshot_path = '/home/bbrelin/course-creator/debug_header_actions.png'
    driver.save_screenshot(screenshot_path)
    print(f"   ✅ Screenshot saved: {screenshot_path}")

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

finally:
    driver.quit()

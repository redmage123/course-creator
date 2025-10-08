#!/usr/bin/env python3
"""
Selenium script to inspect the login button on index.html
Takes a screenshot and extracts CSS properties to debug text cutoff issue
"""

import sys
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import random

# Setup Chrome options
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

driver = webdriver.Chrome(options=options)

try:
    # Load the page
    driver.get('https://localhost:3000/html/index.html')
    time.sleep(2)  # Wait for page to load

    # Find the login button
    login_button = driver.find_element(By.ID, 'loginBtn')

    # Get computed styles
    styles = {
        'width': driver.execute_script("return window.getComputedStyle(arguments[0]).width;", login_button),
        'padding': driver.execute_script("return window.getComputedStyle(arguments[0]).padding;", login_button),
        'padding-left': driver.execute_script("return window.getComputedStyle(arguments[0]).paddingLeft;", login_button),
        'padding-right': driver.execute_script("return window.getComputedStyle(arguments[0]).paddingRight;", login_button),
        'font-size': driver.execute_script("return window.getComputedStyle(arguments[0]).fontSize;", login_button),
        'border': driver.execute_script("return window.getComputedStyle(arguments[0]).border;", login_button),
        'box-sizing': driver.execute_script("return window.getComputedStyle(arguments[0]).boxSizing;", login_button),
        'white-space': driver.execute_script("return window.getComputedStyle(arguments[0]).whiteSpace;", login_button),
        'overflow': driver.execute_script("return window.getComputedStyle(arguments[0]).overflow;", login_button),
    }

    # Get button properties
    button_text = login_button.text
    button_rect = login_button.rect

    # Print button information
    print("=" * 60)
    print("LOGIN BUTTON INSPECTION")
    print("=" * 60)
    print(f"Button Text: '{button_text}'")
    print(f"Button Dimensions: {button_rect['width']}px x {button_rect['height']}px")
    print(f"Button Position: ({button_rect['x']}, {button_rect['y']})")
    print("\nComputed Styles:")
    print("-" * 60)
    for key, value in styles.items():
        print(f"  {key:20s}: {value}")

    # Highlight the button and take a screenshot
    driver.execute_script("arguments[0].style.border='3px solid red';", login_button)
    driver.execute_script("arguments[0].scrollIntoView();", login_button)
    time.sleep(0.5)

    # Save screenshot
    screenshot_path = '/home/bbrelin/course-creator/tests/reports/screenshots/login_button_inspection.png'
    driver.save_screenshot(screenshot_path)
    print(f"\nScreenshot saved to: {screenshot_path}")

    # Also take a screenshot of just the button
    login_button.screenshot('/home/bbrelin/course-creator/tests/reports/screenshots/login_button_only.png')
    print(f"Button-only screenshot saved to: /home/bbrelin/course-creator/tests/reports/screenshots/login_button_only.png")

    print("\n" + "=" * 60)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    driver.quit()

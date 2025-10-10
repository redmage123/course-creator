#!/usr/bin/env python3
"""
Simplest possible approach - no user data directory, just capture the page

BUSINESS CONTEXT:
Regenerate slide 1 video without cookie consent banner for clean demo presentation
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

print("Starting simple slide 1 regeneration...")

# Minimal Chrome options - no user data directory
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--headless")  # Run headless for automation

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

try:
    print("1. Navigating to homepage...")
    driver.get("https://localhost:3000/")
    time.sleep(3)

    print("2. Looking for cookie banner...")
    try:
        # Wait for privacy modal to be present
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))

        # Check if it's displayed
        if modal.is_displayed():
            print("   Privacy modal found, clicking Accept All...")
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(2)
            print("   ✓ Cookie banner dismissed!")
    except Exception as e:
        print(f"   ⚠️  Cookie banner not found or already dismissed: {e}")

    print("3. Taking clean screenshot...")
    screenshot_path = "/home/bbrelin/course-creator/frontend/static/demo/screenshots/slide_01_clean.png"
    driver.save_screenshot(screenshot_path)

    if os.path.exists(screenshot_path):
        file_size = os.path.getsize(screenshot_path)
        print(f"   ✓ Screenshot saved: {screenshot_path} ({file_size} bytes)")
    else:
        print(f"   ❌ Screenshot NOT saved!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("4. Closing browser...")
    driver.quit()

print("\n✅ Screenshot capture complete!")
print("Next: Regenerate video using generate_demo_videos.py")

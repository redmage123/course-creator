#!/usr/bin/env python3
"""Fix slide 1 - dismiss cookie banner and capture clean homepage"""

import time
import os
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Unique session ID
session_id = str(uuid.uuid4())[:8]
user_data_dir = f"/tmp/chrome_fix_slide1_{session_id}"

print(f"Using unique profile: {user_data_dir}")

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--remote-debugging-port=0")  # Use random port

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("Navigating to homepage...")
    driver.get("https://localhost:3000/")
    time.sleep(3)

    # Dismiss cookie banner
    print("Looking for cookie banner...")
    try:
        accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
        if accept_btn.is_displayed():
            accept_btn.click()
            time.sleep(2)
            print("✓ Cookie banner dismissed!")
        else:
            print("⚠️  Accept button not visible")
    except Exception as e:
        print(f"⚠️  Cookie banner not found: {e}")
        print("Proceeding anyway...")

    # Take clean screenshot
    screenshot_path = "/home/bbrelin/course-creator/frontend/static/demo/screenshots/slide_01_clean.png"
    driver.save_screenshot(screenshot_path)
    print(f"✓ Screenshot saved: {screenshot_path}")

    # Now record video using ffmpeg (15 seconds of homepage)
    print("\n⚠️  Manual step needed:")
    print("This browser window will stay open for 20 seconds.")
    print("Use a screen recorder to capture it, or take screenshots.")
    print("Starting countdown...")

    for i in range(20, 0, -1):
        print(f"  {i} seconds remaining...")
        time.sleep(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nClosing browser...")
    driver.quit()

    # Cleanup temp directory
    import shutil
    try:
        shutil.rmtree(user_data_dir)
        print(f"✓ Cleaned up {user_data_dir}")
    except:
        pass

print("\n✅ Done! Use the screenshot to regenerate the video.")

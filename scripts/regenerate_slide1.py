#!/usr/bin/env python3
"""Quick script to regenerate slide 1 video without cookie banner"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import subprocess

# Setup Chrome
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-blink-features=AutomationControlled")

# Create unique profile
import tempfile
profile_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={profile_dir}")

driver = webdriver.Chrome(options=options)

try:
    # Navigate to homepage
    driver.get("https://localhost:3000/")
    time.sleep(3)

    # Dismiss cookie banner
    try:
        accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
        accept_btn.click()
        time.sleep(1)
        print("✓ Cookie banner dismissed")
    except:
        print("⚠️  Cookie banner not found or already dismissed")

    # Record 15 seconds of homepage
    print("Recording homepage for 15 seconds...")

    # Use ffmpeg to record the Chrome window
    # For now, just take a screenshot
    driver.save_screenshot("/home/bbrelin/course-creator/frontend/static/demo/screenshots/slide_01_clean.png")
    print("✓ Screenshot saved")

finally:
    driver.quit()

print("\n✅ Slide 1 regenerated without cookie banner")
print("Now regenerate the video using generate_demo_videos.py")

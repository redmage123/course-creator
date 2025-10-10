#!/usr/bin/env python3
"""
Regenerate Slide 2 with FFmpeg screen recording
Records the organization registration workflow with visible cursor and form filling

BUSINESS CONTEXT:
Demonstrates organization setup with clear visual feedback of each step
"""

import time
import os
import subprocess
import signal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_02_org_admin.mp4"
DURATION = 45  # seconds

print("=" * 70)
print("SLIDE 2: ORGANIZATION REGISTRATION - VIDEO RECORDING")
print("=" * 70)

# Setup Chrome (NOT headless - need visible window for cursor)
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
driver.set_window_position(0, 0)
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

# Get window ID for ffmpeg
window_info = driver.execute_script("return {width: window.screen.width, height: window.screen.height};")
print(f"Screen: {window_info}")

def slow_type(element, text, delay=0.08):
    """Type text slowly with visible cursor"""
    actions.move_to_element(element).click().perform()
    time.sleep(0.2)
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def move_and_click(element):
    """Move cursor to element and click"""
    actions.move_to_element(element).perform()
    time.sleep(0.4)
    element.click()
    time.sleep(0.2)

# Start FFmpeg recording
print("\n1. Starting screen recording...")
ffmpeg_cmd = [
    'ffmpeg',
    '-video_size', '1920x1080',
    '-framerate', '30',
    '-f', 'x11grab',
    '-i', ':0.0',
    '-t', str(DURATION),
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-y',
    VIDEO_OUTPUT
]

ffmpeg_process = subprocess.Popen(
    ffmpeg_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("   ✓ Recording started")
time.sleep(2)  # Let ffmpeg initialize

try:
    print("\n2. Navigating to homepage...")
    driver.get(f"{BASE_URL}/")
    time.sleep(2)

    print("3. Dismissing privacy modal...")
    try:
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            move_and_click(accept_btn)
            time.sleep(1)
            print("   ✓ Privacy modal dismissed")
    except:
        print("   ⚠️  No privacy modal")

    print("4. Navigating to organization registration...")
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    print("5. Filling organization info (18s)...")

    # Organization Name (2s)
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning Institute", delay=0.07)
    time.sleep(0.5)

    # Website (1.5s)
    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "acmelearning.edu", delay=0.06)
    time.sleep(0.5)

    # Description (3s)
    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional technical training", delay=0.05)
    time.sleep(0.5)

    # Scroll to contact (1s)
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(1)

    # Business Email (2s)
    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu", delay=0.06)
    time.sleep(0.5)

    # Street Address (1.5s)
    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Dr", delay=0.06)
    time.sleep(0.5)

    # City (1s)
    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco", delay=0.06)
    time.sleep(0.5)

    # Postal (1s)
    org_postal = driver.find_element(By.ID, "orgPostalCode")
    slow_type(org_postal, "94105", delay=0.08)
    time.sleep(0.5)

    # Scroll to admin (1s)
    driver.execute_script("window.scrollTo(0, 1100);")
    time.sleep(1.5)

    print("6. Filling administrator info (15s)...")

    # Admin Name (1.5s)
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson", delay=0.07)
    time.sleep(0.5)

    # Username (1s)
    admin_username = driver.find_element(By.ID, "adminUsername")
    slow_type(admin_username, "sjohnson", delay=0.08)
    time.sleep(0.5)

    # Email (2s)
    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah@acmelearning.edu", delay=0.06)
    time.sleep(0.5)

    # Password (1.5s)
    admin_password = driver.find_element(By.ID, "adminPassword")
    slow_type(admin_password, "••••••••", delay=0.1)  # Visual representation
    time.sleep(0.5)

    # Confirm Password (1.5s)
    admin_confirm = driver.find_element(By.ID, "adminPasswordConfirm")
    slow_type(admin_confirm, "••••••••", delay=0.1)
    time.sleep(0.5)

    # Scroll to consents (1s)
    driver.execute_script("window.scrollTo(0, 1700);")
    time.sleep(1.5)

    print("7. Accepting privacy consents (4s)...")
    try:
        consent1 = driver.find_element(By.ID, "consentEssential")
        if not consent1.is_selected():
            move_and_click(consent1)
            time.sleep(0.6)

        consent2 = driver.find_element(By.ID, "consentAnalytics")
        if not consent2.is_selected():
            move_and_click(consent2)
            time.sleep(0.6)

        consent3 = driver.find_element(By.ID, "consentMarketing")
        if not consent3.is_selected():
            move_and_click(consent3)
            time.sleep(0.6)
    except:
        print("   ⚠️  Consent checkboxes not found")

    # Scroll to submit (1s)
    driver.execute_script("window.scrollTo(0, 2100);")
    time.sleep(1)

    print("8. Hovering submit button (2s)...")
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        actions.move_to_element(submit_btn).perform()
        time.sleep(2)
    except:
        time.sleep(2)

    # Show filled form overview (3s)
    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(3)

    print("\n✓ Workflow complete (~45s)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n9. Stopping recording...")
    # Send SIGINT to ffmpeg to finish gracefully
    ffmpeg_process.send_signal(signal.SIGINT)

    try:
        ffmpeg_process.wait(timeout=10)
        print("   ✓ Recording stopped")
    except subprocess.TimeoutExpired:
        ffmpeg_process.kill()
        print("   ⚠️  Recording force-stopped")

    driver.quit()

# Verify output
if os.path.exists(VIDEO_OUTPUT):
    file_size = os.path.getsize(VIDEO_OUTPUT)
    print(f"\n✅ Video saved: {VIDEO_OUTPUT} ({file_size:,} bytes)")
else:
    print(f"\n❌ Video not found: {VIDEO_OUTPUT}")

print("\n" + "=" * 70)
print("COMPLETE: Slide 2 video regenerated with:")
print("  - Privacy modal dismissed")
print("  - Visible mouse cursor movements")
print("  - Form fields filled with realistic typing")
print("  - 45-second duration")
print("=" * 70)

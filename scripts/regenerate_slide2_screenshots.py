#!/usr/bin/env python3
"""
Regenerate Slide 2 using screenshot sequences
Creates video from sequential screenshots showing form filling progression

BUSINESS CONTEXT:
Demonstrates organization setup process with clear visual progression
through each form field, suitable for headless environments.
"""

import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = "/tmp/slide2_sequence"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_02_org_admin.mp4"

# Create screenshots directory
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("SLIDE 2: ORGANIZATION REGISTRATION - SCREENSHOT SEQUENCE")
print("=" * 70)

# Setup Chrome (headless)
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)

screenshot_count = 0

def capture(name, duration_frames=30):
    """Capture screenshot and hold for N frames"""
    global screenshot_count
    screenshot_count += 1
    path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
    driver.save_screenshot(path)
    print(f"   {screenshot_count:2d}. {name}")

    # Duplicate frame for duration (30 fps)
    for i in range(1, duration_frames):
        screenshot_count += 1
        duplicate_path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
        subprocess.run(['cp', path, duplicate_path], check=True)

def slow_type(element, text):
    """Type text character by character"""
    for char in text:
        element.send_keys(char)
        time.sleep(0.05)

try:
    print("\n1. Navigating and dismissing privacy modal...")
    driver.get(f"{BASE_URL}/")
    time.sleep(2)

    # Dismiss privacy modal
    try:
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
            print("   ✓ Privacy modal dismissed")
    except:
        print("   ⚠️  No privacy modal found")

    print("\n2. Loading organization registration form...")
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    # Capture empty form (2 seconds = 60 frames)
    capture("Empty registration form", 60)

    print("\n3. Filling organization information...")

    # Organization Name
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning Institute")
    capture("Organization name filled", 45)

    # Website
    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "https://acmelearning.edu")
    capture("Website URL filled", 40)

    # Description
    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional development and technical training for modern enterprises")
    capture("Description filled", 40)

    # Scroll to contact section
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(0.5)
    capture("Scrolled to contact information", 35)

    print("\n4. Filling contact information...")

    # Business Email
    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu")
    capture("Business email filled", 40)

    # Street Address
    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Drive")
    capture("Street address filled", 35)

    # City
    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco")
    capture("City filled", 30)

    # Postal Code
    org_postal = driver.find_element(By.ID, "orgPostalCode")
    slow_type(org_postal, "94105")
    capture("Postal code filled", 30)

    # Scroll to administrator section
    driver.execute_script("window.scrollTo(0, 1100);")
    time.sleep(0.5)
    capture("Scrolled to administrator section", 45)

    print("\n5. Filling administrator information...")

    # Admin Name
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson")
    capture("Administrator name filled", 35)

    # Username
    admin_username = driver.find_element(By.ID, "adminUsername")
    slow_type(admin_username, "sjohnson")
    capture("Username filled", 30)

    # Email
    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah.johnson@acmelearning.edu")
    capture("Administrator email filled", 40)

    # Password
    admin_password = driver.find_element(By.ID, "adminPassword")
    admin_password.send_keys("SecurePass123!")
    capture("Password filled", 35)

    # Confirm Password
    admin_confirm = driver.find_element(By.ID, "adminPasswordConfirm")
    admin_confirm.send_keys("SecurePass123!")
    capture("Password confirmed", 35)

    # Scroll to privacy section
    driver.execute_script("window.scrollTo(0, 1700);")
    time.sleep(0.5)
    capture("Scrolled to privacy consents", 40)

    print("\n6. Accepting privacy consents...")

    # Check consents
    try:
        consent1 = driver.find_element(By.ID, "consentEssential")
        if not consent1.is_selected():
            consent1.click()
            capture("Essential consent accepted", 25)

        consent2 = driver.find_element(By.ID, "consentAnalytics")
        if not consent2.is_selected():
            consent2.click()
            capture("Analytics consent accepted", 25)

        consent3 = driver.find_element(By.ID, "consentMarketing")
        if not consent3.is_selected():
            consent3.click()
            capture("Marketing consent accepted", 25)
    except Exception as e:
        print(f"   ⚠️  Consent checkboxes: {e}")

    # Scroll to submit button
    driver.execute_script("window.scrollTo(0, 2100);")
    time.sleep(0.5)
    capture("Ready to submit", 50)

    # Show overview of filled form
    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(0.5)
    capture("Form completed - overview", 90)

    print(f"\n✅ Captured {screenshot_count} frames")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# Create video from screenshots using ffmpeg
print("\n7. Creating video from screenshots...")

ffmpeg_cmd = [
    'ffmpeg',
    '-framerate', '30',
    '-pattern_type', 'glob',
    '-i', f'{SCREENSHOTS_DIR}/frame_*.png',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-y',
    VIDEO_OUTPUT
]

try:
    result = subprocess.run(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        if os.path.exists(VIDEO_OUTPUT):
            file_size = os.path.getsize(VIDEO_OUTPUT)
            duration = screenshot_count / 30.0
            print(f"   ✓ Video created: {VIDEO_OUTPUT}")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Duration: {duration:.1f}s ({screenshot_count} frames @ 30fps)")
        else:
            print("   ❌ Video file not found after creation")
    else:
        print(f"   ❌ FFmpeg error: {result.stderr[:500]}")

except subprocess.TimeoutExpired:
    print("   ❌ FFmpeg timed out")
except Exception as e:
    print(f"   ❌ Error creating video: {e}")

# Cleanup
print("\n8. Cleaning up temporary files...")
subprocess.run(['rm', '-rf', SCREENSHOTS_DIR])
print(f"   ✓ Removed {SCREENSHOTS_DIR}")

print("\n" + "=" * 70)
print("✅ COMPLETE: Slide 2 video regenerated")
print("   - Privacy modal dismissed")
print("   - Form filling progression shown")
print("   - All fields populated with realistic data")
print(f"   - Output: {VIDEO_OUTPUT}")
print("=" * 70)

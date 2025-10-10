#!/usr/bin/env python3
"""
Regenerate Slide 2 - Final version with proper ffmpeg encoding
Uses concat demuxer for reliable video creation from screenshots
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
print("SLIDE 2: ORGANIZATION REGISTRATION")
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

    # Duplicate frame for duration
    for i in range(1, duration_frames):
        screenshot_count += 1
        duplicate_path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
        subprocess.run(['cp', path, duplicate_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def slow_type(element, text):
    """Type text character by character"""
    for char in text:
        element.send_keys(char)
        time.sleep(0.03)

try:
    print("\n1. Setup...")
    driver.get(f"{BASE_URL}/")
    time.sleep(2)

    # Dismiss privacy modal
    try:
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
    except:
        pass

    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    print("\n2. Capturing form progression...")

    # Empty form (3s)
    capture("Empty form", 90)

    # Organization info
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning Institute")
    capture("Org name", 75)

    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "https://acmelearning.edu")
    capture("Website", 70)

    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional technical training")
    capture("Description", 70)

    # Scroll and contact info
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(0.5)
    capture("Contact section", 60)

    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu")
    capture("Email", 70)

    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Drive")
    capture("Address", 60)

    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco")
    capture("City", 55)

    org_postal = driver.find_element(By.ID, "orgPostalCode")
    slow_type(org_postal, "94105")
    capture("Postal", 55)

    # Scroll to admin
    driver.execute_script("window.scrollTo(0, 1100);")
    time.sleep(0.5)
    capture("Admin section", 75)

    # Admin info
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson")
    capture("Admin name", 65)

    admin_username = driver.find_element(By.ID, "adminUsername")
    slow_type(admin_username, "sjohnson")
    capture("Username", 55)

    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah@acmelearning.edu")
    capture("Admin email", 70)

    admin_password = driver.find_element(By.ID, "adminPassword")
    admin_password.send_keys("SecurePass123!")
    capture("Password", 60)

    admin_confirm = driver.find_element(By.ID, "adminPasswordConfirm")
    admin_confirm.send_keys("SecurePass123!")
    capture("Confirm", 60)

    # Final view
    driver.execute_script("window.scrollTo(0, 1700);")
    time.sleep(0.5)
    capture("Privacy section", 80)

    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(0.5)
    capture("Form complete", 280)  # Hold final frame ~9 seconds total for 45s video

    print(f"\n✅ Captured {screenshot_count} frames")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# Create video using concat demuxer
print("\n3. Creating video...")

# Create file list for concat
file_list_path = f"{SCREENSHOTS_DIR}/files.txt"
with open(file_list_path, 'w') as f:
    for i in range(1, screenshot_count + 1):
        f.write(f"file 'frame_{i:04d}.png'\n")
        f.write(f"duration 0.033333\n")  # 30fps = 1/30 seconds per frame

print(f"   Created file list with {screenshot_count} frames")

# Use image2 and scale filter
ffmpeg_cmd = [
    'ffmpeg',
    '-r', '30',  # Input framerate
    '-i', f'{SCREENSHOTS_DIR}/frame_%04d.png',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-vf', 'scale=1920:1080',  # Ensure consistent size
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
        if os.path.exists(VIDEO_OUTPUT) and os.path.getsize(VIDEO_OUTPUT) > 0:
            file_size = os.path.getsize(VIDEO_OUTPUT)
            duration = screenshot_count / 30.0
            print(f"   ✓ Video created successfully")
            print(f"     File: {VIDEO_OUTPUT}")
            print(f"     Size: {file_size:,} bytes")
            print(f"     Duration: {duration:.1f}s")
        else:
            print(f"   ❌ Video file is empty or not found")
            print(f"   FFmpeg stderr: {result.stderr[-500:]}")
    else:
        print(f"   ❌ FFmpeg failed (exit code {result.returncode})")
        print(f"   Error: {result.stderr[-1000:]}")

except subprocess.TimeoutExpired:
    print("   ❌ FFmpeg timed out")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Cleanup
print("\n4. Cleaning up...")
subprocess.run(['rm', '-rf', SCREENSHOTS_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)

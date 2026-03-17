#!/usr/bin/env python3
"""
Regenerate Slide 2 - Complete Getting Started Workflow

Shows the complete registration workflow:
1. Home page with cursor
2. Mouse moves to Register button
3. Click Register button
4. Navigate to organization registration
5. Fill in the form

Duration: ~35 seconds to match audio
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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = "/tmp/slide2_homepage_sequence"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_02_org_admin.mp4"

# Create screenshots directory
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("SLIDE 2: GETTING STARTED - ORGANIZATION REGISTRATION")
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
    print(f"   {screenshot_count:2d}. {name} ({duration_frames} frames)")

    # Duplicate frame for duration
    for i in range(1, duration_frames):
        screenshot_count += 1
        duplicate_path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
        subprocess.run(['cp', path, duplicate_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def smooth_move_to_element(element, steps=20):
    """Move cursor smoothly to element"""
    actions = ActionChains(driver)
    # Move cursor to element with smooth motion
    for _ in range(steps):
        actions.move_to_element_with_offset(element, 0, 0)
        actions.perform()
        capture("Moving cursor", 2)
        time.sleep(0.05)

def slow_type(element, text):
    """Type text character by character"""
    for char in text:
        element.send_keys(char)
        time.sleep(0.03)

try:
    print("\n1. Load home page...")
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

    # Home page loaded (3 seconds = 90 frames) - "To get started..."
    capture("Home page", 90)

    print("\n2. Moving cursor to Register button...")
    # Find Register button
    register_btn = wait.until(EC.presence_of_element_located((By.ID, 'registerBtn')))

    # Smooth cursor movement (1.5 seconds = 45 frames total)
    smooth_move_to_element(register_btn, steps=20)

    # Hover on button (0.8 seconds) - "...simply click Register Organization"
    capture("Hover on Register", 24)

    print("\n3. Click Register button...")
    # Navigate to organization registration (instead of student registration)
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    # Registration page loaded (2 seconds) - "Now, let's fill in the details"
    capture("Registration page", 60)

    print("\n4. Filling organization details...")

    # Organization name - "Enter your organization name..."
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning")
    capture("Org name", 50)

    # Website - "...website..."
    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "acmelearning.edu")
    capture("Website", 45)

    # Description - "...and a brief description"
    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional training")
    capture("Description", 45)

    print("\n5. Contact information...")
    # Scroll to contact section
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(0.3)
    capture("Contact section", 35)

    # Email - "Add your contact information, including business email..."
    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu")
    capture("Email", 45)

    # Address - "...and address"
    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Dr")
    capture("Address", 40)

    # City
    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco")
    capture("City", 35)

    print("\n6. Administrator account...")
    # Scroll to admin section
    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(0.3)
    capture("Admin section", 45)

    # Admin name - "Finally, set up your administrator account..."
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson")
    capture("Admin name", 45)

    # Admin email - "...with credentials"
    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah@acmelearning.edu")
    capture("Admin email", 50)

    # Password
    admin_password = driver.find_element(By.ID, "adminPassword")
    admin_password.send_keys("SecurePass123!")
    capture("Password", 35)

    # Final view - form complete (8 seconds) - "In under a minute, you've created..."
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(0.3)
    capture("Form complete", 240)

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count/30:.1f} seconds)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# Create video using ffmpeg
print("\n7. Creating video...")

ffmpeg_cmd = [
    'ffmpeg',
    '-r', '30',  # Input framerate
    '-i', f'{SCREENSHOTS_DIR}/frame_%04d.png',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-vf', 'scale=1920:1080',
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
            print(f"     Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print(f"     Duration: {duration:.1f}s")
            print(f"     Audio duration: 31.16s (target: 35s)")
        else:
            print(f"   ❌ Video file is empty or not found")
    else:
        print(f"   ❌ FFmpeg failed (exit code {result.returncode})")
        print(f"   Error: {result.stderr[-1000:]}")

except subprocess.TimeoutExpired:
    print("   ❌ FFmpeg timed out")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Cleanup
print("\n8. Cleaning up...")
subprocess.run(['rm', '-rf', SCREENSHOTS_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)
print()
print("Next step: Test the video in demo-player.html")
print()

#!/usr/bin/env python3
"""
Regenerate Slide 2 with Interactive Form Filling

BUSINESS PURPOSE:
Create a dynamic demo video showing actual form filling for organization creation.
This addresses user feedback: pauses too long, need actual form interaction, black screen at start.

TECHNICAL APPROACH:
1. Load organization registration page
2. Wait for full page load (eliminate black screen)
3. Fill in each form field with realistic typing delays
4. Capture screenshots at key moments
5. Generate video from screenshot sequence

IMPROVEMENTS:
- No black screen at start (proper page load wait)
- Actual form typing interactions
- Better timing synchronized with narration
- Smooth transitions between form sections
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Configuration
BASE_URL = 'https://localhost:3000'
OUTPUT_DIR = Path('frontend/static/demo/videos')
TEMP_DIR = Path('/tmp/slide2_frames')

# Form data to fill in - Simplified for clearer demo
FORM_DATA = {
    'orgName': 'TechEd Academy',
    'orgDomain': 'https://www.techedacademy.org',
    'orgDescription': 'Comprehensive tech education platform',
    'orgStreetAddress': '123 Innovation Drive',
    'orgCity': 'San Francisco',
    'adminUsername': 'admin',
    'adminEmail': 'admin@techedacademy.org',
    'adminPassword': 'SecurePass123!'
}


def setup_driver():
    """Initialize Chrome WebDriver with proper options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def dismiss_privacy_modal(driver, wait):
    """Dismiss privacy modal if present"""
    try:
        time.sleep(1)
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
            print("   ✓ Privacy modal dismissed")
    except Exception as e:
        print(f"   ℹ No privacy modal found (this is fine)")


def type_text_naturally(element, text, delay=0.05):
    """Type text with natural delays between characters"""
    for char in text:
        element.send_keys(char)
        time.sleep(delay)


def capture_frame(driver, temp_dir, frame_number, duration_frames=1):
    """Capture a frame and duplicate it for duration"""
    frame_path = temp_dir / f"frame_{frame_number:04d}.png"
    driver.save_screenshot(str(frame_path))

    for i in range(1, duration_frames):
        next_frame = frame_number + i
        subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{next_frame:04d}.png")],
                      capture_output=True, check=True)

    return frame_number + duration_frames


def main():
    print("=" * 80)
    print("🎬 REGENERATING SLIDE 2 - Organization Registration with Form Filling")
    print("=" * 80)
    print()

    # Create temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Temp directory: {TEMP_DIR}")
    print()

    # Initialize WebDriver
    print("🌐 Initializing Chrome WebDriver...")
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to organization registration page
        url = f'{BASE_URL}/html/organization-registration.html'
        print(f"📍 Navigating to: {url}")
        driver.get(url)

        # Wait for page to fully load (no black screen!)
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print("   ✓ Page loaded")

        # Dismiss privacy modal
        dismiss_privacy_modal(driver, wait)

        # Wait for form to be ready
        wait.until(EC.presence_of_element_located((By.ID, 'organizationRegistrationForm')))
        time.sleep(1)

        print()
        print("📹 Capturing frames...")
        frame_num = 0

        # Frame 1-210: Initial view (7 seconds at 30fps - during intro narration)
        print("   Frame 0000-0210: Initial page view")
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=210)

        # Scroll to ensure form is visible
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

        # Narration timing guide (45 seconds total, 30fps = 1350 frames):
        # "Every great learning program starts with a solid foundation" (0-5s, 150 frames)
        # "Watch as we create an organization" (5-7s, 60 frames)
        # "We'll enter the name, website, and a brief description" (7-12s, 150 frames)
        # "Then add contact details, like the business email and address" (12-17s, 150 frames)
        # "Finally, we'll set up the admin account" (17-20s, 90 frames)
        # "with username, email, and password" (20-24s, 120 frames)
        # "In under a minute, you've created a complete organizational structure" (24-29s, 150 frames)
        # "ready to host unlimited courses and manage hundreds of users" (29-34s, 150 frames)
        # "That's effortless setup" (34-36s, 60 frames)
        # Final hold (36-45s, 270 frames)

        # Phase 1: Organization Name (during "enter the name" - ~2s)
        print("   Typing: Organization Name")
        org_name_field = driver.find_element(By.ID, 'orgName')
        org_name_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=10)

        for i, char in enumerate(FORM_DATA['orgName']):
            org_name_field.send_keys(char)
            if i % 2 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.05)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=40)

        # Phase 2: Website (during "website" - ~2s)
        print("   Typing: Website")
        website_field = driver.find_element(By.ID, 'orgDomain')
        website_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['orgDomain']):
            website_field.send_keys(char)
            if i % 3 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.04)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=45)

        # Phase 3: Description (during "brief description" - ~3s)
        print("   Typing: Description")
        description_field = driver.find_element(By.ID, 'orgDescription')
        description_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['orgDescription']):
            description_field.send_keys(char)
            if i % 4 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.05)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=60)

        # Scroll down to contact details section
        driver.execute_script("window.scrollBy(0, 250);")
        time.sleep(0.3)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=15)

        # Phase 4: Street Address (during "contact details" - ~2s)
        print("   Typing: Street Address")
        address_field = driver.find_element(By.ID, 'orgStreetAddress')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_field)
        time.sleep(0.2)
        address_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['orgStreetAddress']):
            address_field.send_keys(char)
            if i % 3 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.05)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=35)

        # Phase 5: City (during "address" - ~1.5s)
        print("   Typing: City")
        city_field = driver.find_element(By.ID, 'orgCity')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_field)
        time.sleep(0.2)
        city_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['orgCity']):
            city_field.send_keys(char)
            if i % 2 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.05)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=45)

        # Scroll down to admin section
        driver.execute_script("window.scrollBy(0, 350);")
        time.sleep(0.3)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=20)

        # Phase 6: Admin Username (during "username" - ~1.5s)
        print("   Typing: Admin Username")
        admin_username_field = driver.find_element(By.ID, 'adminUsername')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", admin_username_field)
        time.sleep(0.2)
        admin_username_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['adminUsername']):
            admin_username_field.send_keys(char)
            if i % 2 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.06)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=30)

        # Phase 7: Admin Email (during "email" - ~2s)
        print("   Typing: Admin Email")
        admin_email_field = driver.find_element(By.ID, 'adminEmail')
        admin_email_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['adminEmail']):
            admin_email_field.send_keys(char)
            if i % 3 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.04)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=30)

        # Phase 8: Admin Password (during "password" - ~2s)
        print("   Typing: Admin Password")
        admin_password_field = driver.find_element(By.ID, 'adminPassword')
        admin_password_field.click()
        time.sleep(0.2)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=5)

        for i, char in enumerate(FORM_DATA['adminPassword']):
            admin_password_field.send_keys(char)
            if i % 2 == 0:
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=2)
            time.sleep(0.06)

        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=50)

        # Scroll back to top to show complete form (during "In under a minute...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.4)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=60)

        # Scroll down slowly to show middle section (during "ready to host unlimited courses...")
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(0.4)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=60)

        # Scroll to show bottom section (during "manage hundreds of users")
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(0.4)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=60)

        # Final scroll to middle for balanced view (during "That's effortless setup")
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(0.3)

        # Final hold (remaining time to reach 45s total)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=430)

        print(f"   ✓ Total frames captured: {frame_num}")
        print()

        # Generate video with FFmpeg
        print("🎞️  Generating video with FFmpeg...")
        output_path = OUTPUT_DIR / 'slide_02_org_admin.mp4'

        cmd = [
            'ffmpeg',
            '-r', '30',
            '-i', str(TEMP_DIR / 'frame_%04d.png'),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-vf', 'scale=1920:1080',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size_kb = output_path.stat().st_size / 1024
            duration = frame_num / 30
            print(f"   ✓ Video created: {output_path}")
            print(f"   ✓ Size: {size_kb:.1f}KB")
            print(f"   ✓ Duration: {duration:.1f}s ({frame_num} frames at 30fps)")
        else:
            print(f"   ✗ FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()
        print()
        print("🧹 Cleaning up temp files...")
        subprocess.run(['rm', '-rf', str(TEMP_DIR)], capture_output=True)

    print()
    print("=" * 80)
    print("✅ SLIDE 2 REGENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"📹 Video location: {output_path}")
    print(f"🎬 Ready for deployment")
    print()

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

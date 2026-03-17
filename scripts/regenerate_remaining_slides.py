#!/usr/bin/env python3
"""
Regenerate slides 3-13 using the proven screenshot sequence method

BUSINESS CONTEXT:
Uses the same approach that successfully created slide 2 (45s video, 929KB)
to regenerate remaining slides without privacy banner.
"""

import time
import os
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
VIDEO_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")

# Test credentials
INSTRUCTOR_EMAIL = "demo.instructor@example.com"
INSTRUCTOR_PASSWORD = "DemoPass123!"
STUDENT_EMAIL = "demo.student@example.com"
STUDENT_PASSWORD = "DemoPass123!"

print("=" * 70)
print("REGENERATING DEMO SLIDES 3-13")
print("=" * 70)

# Setup Chrome
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

def dismiss_privacy_modal():
    """Dismiss privacy modal if present"""
    try:
        time.sleep(1)
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
    except:
        pass

def login_instructor():
    """Login as instructor"""
    driver.get(f"{BASE_URL}/html/student-login.html")
    time.sleep(2)
    dismiss_privacy_modal()
    try:
        email = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email.send_keys(INSTRUCTOR_EMAIL)
        password = driver.find_element(By.ID, "password")
        password.send_keys(INSTRUCTOR_PASSWORD)
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        time.sleep(3)
    except Exception as e:
        print(f"   ⚠️  Login failed: {e}")

def login_student():
    """Login as student"""
    driver.get(f"{BASE_URL}/html/student-login.html")
    time.sleep(2)
    dismiss_privacy_modal()
    try:
        email = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email.send_keys(STUDENT_EMAIL)
        password = driver.find_element(By.ID, "password")
        password.send_keys(STUDENT_PASSWORD)
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        time.sleep(3)
    except Exception as e:
        print(f"   ⚠️  Login failed: {e}")

def capture(screenshot_count, temp_dir, duration_frames=30):
    """Capture screenshot and duplicate for duration"""
    frame_path = temp_dir / f"frame_{screenshot_count:04d}.png"
    driver.save_screenshot(str(frame_path))

    for i in range(1, duration_frames):
        screenshot_count += 1
        subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{screenshot_count:04d}.png")],
                       capture_output=True, check=True)
    return screenshot_count + 1

def slow_type(element, text):
    """Type text character by character"""
    for char in text:
        element.send_keys(char)
        time.sleep(0.03)

def create_video(slide_num, slide_name, url, duration, scroll_positions):
    """
    Create video from page with scrolling

    Args:
        slide_num: Slide number (e.g., 3)
        slide_name: Output filename stem (e.g., "projects_tracks")
        url: Page URL
        duration: Total duration in seconds
        scroll_positions: List of (scroll_y, hold_seconds) tuples
    """
    temp_dir = Path(f"/tmp/slide_{slide_num:02d}_frames")
    temp_dir.mkdir(exist_ok=True)

    try:
        print(f"\n📹 Slide {slide_num}: {slide_name} ({duration}s)")

        # Navigate and dismiss modal
        driver.get(url)
        time.sleep(2)
        dismiss_privacy_modal()
        time.sleep(1)

        screenshot_count = 0

        # Capture scrolling sequence
        for scroll_y, hold_time in scroll_positions:
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.5)
            screenshot_count = capture(screenshot_count, temp_dir, int(hold_time * 30))

        print(f"   Captured {screenshot_count} frames")

        # Create video
        output_path = VIDEO_DIR / f"slide_{slide_num:02d}_{slide_name}.mp4"

        cmd = [
            'ffmpeg',
            '-r', '30',
            '-i', str(temp_dir / 'frame_%04d.png'),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-vf', 'scale=1920:1080',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=120, text=True)

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            size = output_path.stat().st_size / 1024
            actual_duration = screenshot_count / 30.0
            print(f"   ✓ {size:.0f}KB, {actual_duration:.1f}s")
            return True
        else:
            print(f"   ❌ Failed")
            print(f"   FFmpeg error: {result.stderr[:300]}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        subprocess.run(['rm', '-rf', str(temp_dir)], capture_output=True)

# Regenerate all slides
success_count = 0

try:
    # Slide 3: Projects & Tracks (30s)
    login_instructor()
    if create_video(3, "projects_tracks", f"{BASE_URL}/html/org-admin-dashboard-modular.html", 30,
                   [(0, 15), (500, 15)]):
        success_count += 1

    # Slide 4: Adding Instructors (30s)
    if create_video(4, "add_instructors", f"{BASE_URL}/html/org-admin-dashboard-modular.html", 30,
                   [(0, 10), (800, 10), (1200, 10)]):
        success_count += 1

    # Slide 5: Instructor Dashboard (60s)
    if create_video(5, "instructor_dashboard", f"{BASE_URL}/html/instructor-dashboard-modular.html", 60,
                   [(0, 20), (500, 20), (1000, 20)]):
        success_count += 1

    # Slide 6: Course Content (45s)
    if create_video(6, "course_content", f"{BASE_URL}/html/course-content.html", 45,
                   [(0, 15), (400, 15), (800, 15)]):
        success_count += 1

    # Slide 7: Enroll Students (45s)
    if create_video(7, "enroll_students", f"{BASE_URL}/html/instructor-dashboard-modular.html", 45,
                   [(0, 15), (600, 15), (1000, 15)]):
        success_count += 1

    # Slide 8: Student Dashboard (30s)
    login_student()
    if create_video(8, "student_dashboard", f"{BASE_URL}/html/student-dashboard-modular.html", 30,
                   [(0, 15), (500, 15)]):
        success_count += 1

    # Slide 9: Course Browsing (75s)
    if create_video(9, "course_browsing", f"{BASE_URL}/html/courses.html", 75,
                   [(0, 25), (400, 25), (800, 25)]):
        success_count += 1

    # Slide 10: Taking Quiz (45s)
    if create_video(10, "taking_quiz", f"{BASE_URL}/html/quiz.html", 45,
                   [(0, 15), (300, 15), (600, 15)]):
        success_count += 1

    # Slide 11: Student Progress (30s)
    if create_video(11, "student_progress", f"{BASE_URL}/html/student-progress.html", 30,
                   [(0, 15), (500, 15)]):
        success_count += 1

    # Slide 12: Instructor Analytics (45s)
    login_instructor()
    if create_video(12, "instructor_analytics", f"{BASE_URL}/html/instructor-dashboard-modular.html", 45,
                   [(0, 15), (700, 15), (1200, 15)]):
        success_count += 1

    # Slide 13: Summary & CTA (15s)
    driver.get(f"{BASE_URL}/")
    time.sleep(2)
    dismiss_privacy_modal()
    if create_video(13, "summary_cta", f"{BASE_URL}/", 15,
                   [(0, 7), (1200, 8)]):
        success_count += 1

finally:
    driver.quit()

print("\n" + "=" * 70)
print(f"✅ COMPLETE: {success_count}/11 slides regenerated")
print(f"📁 Videos: {VIDEO_DIR}")
print("\n🔄 Next: Rebuild frontend")
print("   docker-compose build frontend && docker-compose up -d frontend")
print("=" * 70)

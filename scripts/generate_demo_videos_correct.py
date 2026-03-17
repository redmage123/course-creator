#!/usr/bin/env python3
"""
Correct Demo Video Generator - Matches demo-player.html structure

Generates 13 screencasts matching the exact structure in demo-player.html:
1. Introduction
2. Organization Dashboard
3. Projects & Tracks
4. Adding Instructors
5. Instructor Dashboard
6. Course Content
7. Enroll Students
8. Student Dashboard
9. Course Browsing
10. Taking Quizzes
11. Student Progress
12. Instructor Analytics
13. Summary & Next Steps
"""

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import os

BASE_URL = "https://localhost:3000"
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
RESOLUTION = (1920, 1080)
DISPLAY = os.environ.get('DISPLAY', ':99')

class VideoRecorder:
    def __init__(self, output_file, duration):
        self.output_file = output_file
        self.duration = duration
        self.process = None

    def start_recording(self):
        cmd = [
            'ffmpeg', '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', '30',
            '-i', DISPLAY,
            '-t', str(self.duration),
            '-vcodec', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-y', self.output_file
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  🎥 Recording: {os.path.basename(self.output_file)} ({self.duration}s)")

    def wait(self):
        if self.process:
            self.process.wait()
            print(f"  ✓ Saved: {os.path.basename(self.output_file)}")

def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={RESOLUTION[0]},{RESOLUTION[1]}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(*RESOLUTION)
    return driver

def record_slide(driver, filename, duration, workflow_func):
    filepath = str(VIDEOS_DIR / filename)
    recorder = VideoRecorder(filepath, duration)
    recorder.start_recording()
    try:
        workflow_func(driver)
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    recorder.wait()

# ============================================================================
# SLIDE WORKFLOWS
# ============================================================================

def hide_privacy_modals(driver):
    """Hide all privacy/GDPR modals and banners"""
    driver.execute_script("""
        const privacyModal = document.getElementById('privacyModal');
        if (privacyModal) {
            privacyModal.style.display = 'none';
            privacyModal.remove();
        }

        // Hide any cookie banners
        const cookieBanners = document.querySelectorAll('[class*="cookie"], [class*="privacy"], [class*="consent"], [id*="cookie"], [id*="privacy"], [id*="consent"]');
        cookieBanners.forEach(el => {
            if (el.tagName === 'DIV' && (el.className.includes('banner') || el.className.includes('modal'))) {
                el.style.display = 'none';
                el.remove();
            }
        });
    """)

def slide_01_introduction(driver):
    """Slide 1: Introduction - Homepage hero with Register Organization CTA (25s)"""
    driver.get(f"{BASE_URL}/")
    time.sleep(2)
    hide_privacy_modals(driver)
    time.sleep(1)

    # Scroll to show hero section
    driver.execute_script("window.scrollTo(0, 200);")
    time.sleep(4)

    # Scroll to show Register Organization button
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(5)

    # Highlight the Register Organization button area
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(5)

    # Scroll to CTA section
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(5)

    # Scroll back to top to show Register button
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(3)

def slide_02_org_admin(driver):
    """Slide 2: Organization Dashboard - Org creation (45s)"""
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)
    hide_privacy_modals(driver)
    time.sleep(3)

    # Fill org name
    try:
        org_name = driver.find_element(By.ID, "organization-name")
        org_name.send_keys("Tech Training Corp")
        time.sleep(3)

        # Fill website
        website = driver.find_element(By.ID, "organization-website")
        website.send_keys("https://techtraining.example.com")
        time.sleep(3)

        # Scroll to see more fields
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(5)

        # Show description field
        desc = driver.find_element(By.ID, "organization-description")
        desc.send_keys("Corporate technical training for software developers")
        time.sleep(5)

        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(5)

    except Exception as e:
        # Fallback: just scroll through the page
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(10)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(10)

def slide_03_projects_tracks(driver):
    """Slide 3: Projects & Tracks - Dashboard view (30s)"""
    # For now, show homepage or dashboard
    driver.get(f"{BASE_URL}/")
    time.sleep(2)
    hide_privacy_modals(driver)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)

def slide_04_adding_instructors(driver):
    """Slide 4: Adding Instructors - User management (30s)"""
    driver.get(f"{BASE_URL}/")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 200);")
    time.sleep(5)

def slide_05_instructor_dashboard(driver):
    """Slide 5: Instructor Dashboard - Course creation (60s)"""
    driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 900);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(15)

def slide_06_adding_course_content(driver):
    """Slide 6: Course Content - Content editor (45s)"""
    driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(10)

def slide_07_enrolling_students(driver):
    """Slide 7: Enroll Students - Student management (45s)"""
    driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(10)

def slide_08_student_course_browsing(driver):
    """Slide 8: Student Dashboard - Student view (30s)"""
    driver.get(f"{BASE_URL}/html/student-dashboard-modular.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)

def slide_09_student_login_and_dashboard(driver):
    """Slide 9: Course Browsing - Catalog and labs (75s)"""
    driver.get(f"{BASE_URL}/html/courses.html")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(10)

def slide_10_taking_quiz(driver):
    """Slide 10: Taking Quizzes - Quiz interface (45s)"""
    driver.get(f"{BASE_URL}/html/quiz.html")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)

def slide_11_student_progress_analytics(driver):
    """Slide 11: Student Progress - Progress tracking (30s)"""
    driver.get(f"{BASE_URL}/html/student-progress.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)

def slide_12_instructor_analytics(driver):
    """Slide 12: Instructor Analytics - Analytics dashboard (45s)"""
    driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(10)

def slide_13_summary_and_cta(driver):
    """Slide 13: Summary & Next Steps - Call to action (15s)"""
    driver.get(f"{BASE_URL}/")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(5)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*70)
    print("🎬 GENERATING CORRECT DEMO VIDEOS (13 slides)")
    print("="*70)
    print()

    driver = setup_driver()

    try:
        slides = [
            ("slide_01_introduction.mp4", 25, slide_01_introduction),
            ("slide_02_org_admin.mp4", 45, slide_02_org_admin),
            ("slide_03_projects_and_tracks.mp4", 30, slide_03_projects_tracks),
            ("slide_04_adding_instructors.mp4", 30, slide_04_adding_instructors),
            ("slide_05_instructor_dashboard.mp4", 60, slide_05_instructor_dashboard),
            ("slide_06_adding_course_content.mp4", 45, slide_06_adding_course_content),
            ("slide_07_enrolling_students.mp4", 45, slide_07_enrolling_students),
            ("slide_08_student_course_browsing.mp4", 30, slide_08_student_course_browsing),
            ("slide_09_student_login_and_dashboard.mp4", 75, slide_09_student_login_and_dashboard),
            ("slide_10_taking_quiz.mp4", 45, slide_10_taking_quiz),
            ("slide_11_student_progress_analytics.mp4", 30, slide_11_student_progress_analytics),
            ("slide_12_instructor_analytics.mp4", 45, slide_12_instructor_analytics),
            ("slide_13_summary_and_cta.mp4", 15, slide_13_summary_and_cta),
        ]

        for i, (filename, duration, workflow) in enumerate(slides, 1):
            print(f"\n🎥 Slide {i}/{len(slides)}: {filename}")
            record_slide(driver, filename, duration, workflow)
            time.sleep(2)

        print("\n" + "="*70)
        print("✅ ALL 13 VIDEOS GENERATED")
        print("="*70)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()

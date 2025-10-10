#!/usr/bin/env python3
"""
Demo Video Generator with Proper Interactions
- Mouse movements
- Button clicks
- Form filling
- No black screens
- No GDPR banners
"""

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import os

BASE_URL = "https://localhost:3000"
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
RESOLUTION = (1920, 1080)
DISPLAY = os.environ.get('DISPLAY', ':99')

def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={RESOLUTION[0]},{RESOLUTION[1]}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(*RESOLUTION)
    return driver

def remove_privacy_banners(driver):
    """Aggressively remove all privacy/GDPR elements"""
    driver.execute_script("""
        // Remove privacy modal
        const modal = document.getElementById('privacyModal');
        if (modal) modal.remove();

        // Remove ALL overlays and modals
        document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="backdrop"]').forEach(el => {
            if (el.style.display !== 'none') el.remove();
        });

        // Remove cookie/privacy/consent banners
        document.querySelectorAll('[id*="cookie"], [id*="privacy"], [id*="consent"], [class*="cookie"], [class*="privacy"], [class*="consent"]').forEach(el => {
            el.remove();
        });
    """)

def record_slide(driver, filename, duration, workflow_func):
    """Record slide - page loads BEFORE recording starts"""
    filepath = str(VIDEOS_DIR / filename)

    # Execute workflow to load page and prepare
    print(f"  ⏳ Loading page for {filename}...")
    workflow_func(driver, prepare_only=True)

    # Wait for page to be fully ready
    time.sleep(2)

    # Start recording NOW (page already loaded)
    print(f"  🎥 Recording {filename} ({duration}s)...")
    cmd = [
        'ffmpeg', '-f', 'x11grab',
        '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
        '-framerate', '30',
        '-i', DISPLAY,
        '-t', str(duration),
        '-vcodec', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        '-y', filepath
    ]
    recorder = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Now execute the actual interactions
    workflow_func(driver, prepare_only=False)

    # Wait for recording to finish
    recorder.wait()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# SLIDE WORKFLOWS - With Mouse Movements and Clicks
# ============================================================================

def slide_01_introduction(driver, prepare_only=False):
    """Slide 1: Show Register Organization button and call to action"""
    if prepare_only:
        driver.get(f"{BASE_URL}/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    # Recording started - now do interactions
    time.sleep(3)

    # Scroll to show Register Organization button
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(5)

    # Find and highlight Register Organization link
    try:
        register_btn = driver.find_element(By.LINK_TEXT, "Register Organization")
        actions = ActionChains(driver)
        actions.move_to_element(register_btn).perform()
        time.sleep(4)
    except:
        pass

    # Scroll to show features
    driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
    time.sleep(6)

    # Scroll back to show Get Started CTA
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(4)

    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(3)

def slide_02_org_admin(driver, prepare_only=False):
    """Slide 2: Organization registration with form filling"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/organization-registration.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(3)

    # Fill organization name with typing animation
    try:
        org_name_field = driver.find_element(By.ID, "organization-name")
        actions = ActionChains(driver)
        actions.move_to_element(org_name_field).click().perform()
        time.sleep(1)

        # Type slowly to show interaction
        for char in "Tech Training Corp":
            org_name_field.send_keys(char)
            time.sleep(0.1)
        time.sleep(3)

        # Fill website
        website_field = driver.find_element(By.ID, "organization-website")
        actions.move_to_element(website_field).click().perform()
        time.sleep(1)
        website_field.send_keys("https://techtraining.example.com")
        time.sleep(3)

        # Scroll to description
        driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
        time.sleep(3)

        # Fill description
        desc_field = driver.find_element(By.ID, "organization-description")
        actions.move_to_element(desc_field).click().perform()
        time.sleep(1)
        desc_field.send_keys("Corporate technical training for software developers")
        time.sleep(5)

        # Scroll to show submit button
        driver.execute_script("window.scrollTo({top: 700, behavior: 'smooth'});")
        time.sleep(5)

    except Exception as e:
        print(f"    Warning: {e}")
        # Fallback: just scroll
        driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
        time.sleep(10)
        driver.execute_script("window.scrollTo({top: 700, behavior: 'smooth'});")
        time.sleep(10)

def slide_03_projects_tracks(driver, prepare_only=False):
    """Slide 3: Projects and tracks management"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/org-admin-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(3)
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(7)

def slide_04_adding_instructors(driver, prepare_only=False):
    """Slide 4: Adding instructors to organization"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/org-admin-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(3)
    driver.execute_script("window.scrollTo({top: 500, behavior: 'smooth'});")
    time.sleep(12)
    driver.execute_script("window.scrollTo({top: 200, behavior: 'smooth'});")
    time.sleep(12)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(3)

def slide_05_instructor_dashboard(driver, prepare_only=False):
    """Slide 5: Instructor dashboard and course creation"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 300, behavior: 'smooth'});")
    time.sleep(12)
    driver.execute_script("window.scrollTo({top: 700, behavior: 'smooth'});")
    time.sleep(12)
    driver.execute_script("window.scrollTo({top: 1100, behavior: 'smooth'});")
    time.sleep(12)
    driver.execute_script("window.scrollTo({top: 500, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(9)

def slide_06_adding_course_content(driver, prepare_only=False):
    """Slide 6: Adding course content"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 1200, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 600, behavior: 'smooth'});")
    time.sleep(10)

def slide_07_enrolling_students(driver, prepare_only=False):
    """Slide 7: Organization enrolls employees in courses"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/org-admin-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 500, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 1000, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(10)

def slide_08_student_course_browsing(driver, prepare_only=False):
    """Slide 8: Student dashboard"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/student-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 300, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 600, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(5)

def slide_09_student_login_and_dashboard(driver, prepare_only=False):
    """Slide 9: Course content and labs"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/courses.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 1200, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 600, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(10)

def slide_10_taking_quiz(driver, prepare_only=False):
    """Slide 10: Quiz interface"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/quiz.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 300, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 600, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(5)

def slide_11_student_progress_analytics(driver, prepare_only=False):
    """Slide 11: Student progress tracking"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/student-progress.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 300, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 600, behavior: 'smooth'});")
    time.sleep(10)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(5)

def slide_12_instructor_analytics(driver, prepare_only=False):
    """Slide 12: Instructor analytics dashboard"""
    if prepare_only:
        driver.get(f"{BASE_URL}/html/instructor-dashboard-modular.html")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
    time.sleep(15)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(10)

def slide_13_summary_and_cta(driver, prepare_only=False):
    """Slide 13: Summary and call to action"""
    if prepare_only:
        driver.get(f"{BASE_URL}/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        remove_privacy_banners(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        return

    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
    time.sleep(5)
    driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
    time.sleep(5)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*70)
    print("🎬 GENERATING DEMO VIDEOS - Final Version")
    print("  ✓ No black screens (page loads before recording)")
    print("  ✓ Mouse movements and clicks")
    print("  ✓ Form filling animations")
    print("  ✓ GDPR banners removed")
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
            print(f"\n🎥 Slide {i}/13: {filename}")
            record_slide(driver, filename, duration, workflow)

        print("\n" + "="*70)
        print("✅ ALL 13 VIDEOS GENERATED")
        print("="*70)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

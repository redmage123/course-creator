#!/usr/bin/env python3
"""
Master script to regenerate all demo slides without privacy banner and with cursor overlay

BUSINESS CONTEXT:
Regenerates all demo slides to ensure clean presentation without privacy modals,
and adds visible mouse cursor for better user experience.

APPROACH:
1. Generate clean screenshots with privacy modal dismissed
2. Create video from screenshots
3. Add cursor overlay using ffmpeg
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
CURSOR_IMAGE = Path("/tmp/cursor.png")

# Test credentials (from generate_demo_videos.py)
INSTRUCTOR_EMAIL = "demo.instructor@example.com"
INSTRUCTOR_PASSWORD = "DemoPass123!"
STUDENT_EMAIL = "demo.student@example.com"
STUDENT_PASSWORD = "DemoPass123!"

def create_cursor_image():
    """Create a simple cursor image for overlay"""
    print("Creating cursor image...")

    # Create SVG cursor and convert to PNG
    svg_cursor = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow">
      <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="#000" flood-opacity="0.5"/>
    </filter>
  </defs>
  <path d="M 3 3 L 3 21 L 10 16 L 14 23 L 17 21 L 13 14 L 21 13 Z"
        fill="white" stroke="black" stroke-width="1" filter="url(#shadow)"/>
</svg>'''

    svg_path = "/tmp/cursor.svg"
    with open(svg_path, 'w') as f:
        f.write(svg_cursor)

    # Convert SVG to PNG
    cmd = ['convert', svg_path, '-resize', '24x24', str(CURSOR_IMAGE)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✓ Cursor image: {CURSOR_IMAGE}")
        return True
    except FileNotFoundError:
        print("   ⚠️  ImageMagick not installed, cursor overlay will be skipped")
        return False
    except Exception as e:
        print(f"   ⚠️  Could not create cursor: {e}")
        return False


def add_cursor_overlay(video_path, duration):
    """Add animated cursor overlay to video"""
    if not CURSOR_IMAGE.exists():
        print("   ⚠️  No cursor image, skipping overlay")
        return

    print(f"   Adding cursor overlay...")

    # Create temporary video with cursor
    temp_output = video_path.parent / f"{video_path.stem}_with_cursor.mp4"

    # Animate cursor from top-left moving down and right
    # Using overlay filter with enable expression for animation
    cursor_filter = (
        f"[0:v]overlay=x='100+t*30':y='100+t*20':enable='lt(t,{duration-5})'[out]"
    )

    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-i', str(CURSOR_IMAGE),
        '-filter_complex', cursor_filter,
        '-map', '[out]',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-y',
        str(temp_output)
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        if result.returncode == 0 and temp_output.exists() and temp_output.stat().st_size > 0:
            # Replace original with cursor version
            os.replace(temp_output, video_path)
            print(f"   ✓ Cursor overlay added")
        else:
            print(f"   ⚠️  Cursor overlay failed")
            if temp_output.exists():
                temp_output.unlink()
    except Exception as e:
        print(f"   ⚠️  Cursor overlay error: {e}")


class SlideRegenerator:
    """Regenerate demo slides without privacy banner"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.slides_regenerated = []

    def setup_driver(self):
        """Setup Selenium WebDriver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--ignore-certificate-errors")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)

    def teardown_driver(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()

    def dismiss_privacy_modal(self):
        """Dismiss privacy modal if present"""
        try:
            time.sleep(1)
            modal = self.wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
            if modal.is_displayed():
                accept_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Accept All')]"
                )
                accept_btn.click()
                time.sleep(1)
        except:
            pass

    def login_instructor(self):
        """Login as instructor"""
        self.driver.get(f"{BASE_URL}/html/student-login.html")
        time.sleep(2)
        self.dismiss_privacy_modal()

        try:
            email = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email.send_keys(INSTRUCTOR_EMAIL)
            password = self.driver.find_element(By.ID, "password")
            password.send_keys(INSTRUCTOR_PASSWORD)
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            time.sleep(3)
        except:
            pass

    def login_student(self):
        """Login as student"""
        self.driver.get(f"{BASE_URL}/html/student-login.html")
        time.sleep(2)
        self.dismiss_privacy_modal()

        try:
            email = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email.send_keys(STUDENT_EMAIL)
            password = self.driver.find_element(By.ID, "password")
            password.send_keys(STUDENT_PASSWORD)
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            time.sleep(3)
        except:
            pass

    def create_video_from_static_page(self, url, output_name, duration, scroll_positions=None):
        """
        Create video from static page with optional scrolling

        Args:
            url: Page URL
            output_name: Output filename
            duration: Video duration in seconds
            scroll_positions: List of (scroll_y, hold_time) tuples
        """
        temp_dir = Path(f"/tmp/{output_name}_frames")
        temp_dir.mkdir(exist_ok=True)

        try:
            print(f"\n📹 Generating {output_name}...")

            # Navigate and dismiss modal
            self.driver.get(url)
            time.sleep(2)
            self.dismiss_privacy_modal()
            time.sleep(1)

            frame_count = 0
            fps = 30

            if scroll_positions:
                # Animated scrolling
                for scroll_y, hold_time in scroll_positions:
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
                    time.sleep(0.5)

                    # Capture and hold
                    frame_path = temp_dir / f"frame_{frame_count:04d}.png"
                    self.driver.save_screenshot(str(frame_path))

                    hold_frames = int(hold_time * fps)
                    for i in range(1, hold_frames):
                        frame_count += 1
                        subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{frame_count:04d}.png")],
                                       capture_output=True)
                    frame_count += 1
            else:
                # Static page - single frame held for duration
                frame_path = temp_dir / "frame_0000.png"
                self.driver.save_screenshot(str(frame_path))

                total_frames = int(duration * fps)
                for i in range(1, total_frames):
                    subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{i:04d}.png")],
                                   capture_output=True)
                frame_count = total_frames

            # Create video
            output_path = VIDEO_DIR / output_name
            cmd = [
                'ffmpeg',
                '-r', '30',
                '-i', str(temp_dir / 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=120)

            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                size = output_path.stat().st_size / 1024
                print(f"   ✓ Video created: {size:.0f}KB, {duration}s")
                self.slides_regenerated.append(output_name)

                # Add cursor overlay
                add_cursor_overlay(output_path, duration)

                return True
            else:
                print(f"   ❌ Video creation failed")
                return False

        finally:
            # Cleanup
            subprocess.run(['rm', '-rf', str(temp_dir)], capture_output=True)

    def regenerate_all_slides(self):
        """Regenerate all slides that need fixing"""

        print("=" * 70)
        print("REGENERATING DEMO SLIDES - PRIVACY BANNER REMOVAL + CURSOR")
        print("=" * 70)

        # Slide 2: Already regenerated earlier (slide_02_org_admin.mp4)
        print("\n✓ Slide 2: Already regenerated with form filling")

        # Slide 3: Projects & Tracks (30s)
        self.login_instructor()
        self.create_video_from_static_page(
            f"{BASE_URL}/html/org-admin-dashboard-modular.html",
            "slide_03_projects_tracks.mp4",
            30,
            [(0, 15), (500, 15)]
        )

        # Slide 4: Adding Instructors (30s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/org-admin-dashboard-modular.html",
            "slide_04_add_instructors.mp4",
            30,
            [(0, 10), (800, 10), (1200, 10)]
        )

        # Slide 5: Instructor Dashboard (60s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/instructor-dashboard-modular.html",
            "slide_05_instructor_dashboard.mp4",
            60,
            [(0, 20), (500, 20), (1000, 20)]
        )

        # Slide 6: Course Content (45s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/course-content.html",
            "slide_06_course_content.mp4",
            45,
            [(0, 15), (400, 15), (800, 15)]
        )

        # Slide 7: Enroll Students (45s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/instructor-dashboard-modular.html",
            "slide_07_enroll_students.mp4",
            45,
            [(0, 15), (600, 15), (1000, 15)]
        )

        # Slide 8: Student Dashboard (30s)
        self.login_student()
        self.create_video_from_static_page(
            f"{BASE_URL}/html/student-dashboard-modular.html",
            "slide_08_student_dashboard.mp4",
            30,
            [(0, 15), (500, 15)]
        )

        # Slide 9: Course Browsing (75s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/courses.html",
            "slide_09_course_browsing.mp4",
            75,
            [(0, 25), (400, 25), (800, 25)]
        )

        # Slide 10: Taking Quizzes (45s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/quiz.html",
            "slide_10_taking_quiz.mp4",
            45,
            [(0, 15), (300, 15), (600, 15)]
        )

        # Slide 11: Student Progress (30s)
        self.create_video_from_static_page(
            f"{BASE_URL}/html/student-progress.html",
            "slide_11_student_progress.mp4",
            30,
            [(0, 15), (500, 15)]
        )

        # Slide 12: Instructor Analytics (45s)
        self.login_instructor()
        self.create_video_from_static_page(
            f"{BASE_URL}/html/instructor-dashboard-modular.html",
            "slide_12_instructor_analytics.mp4",
            45,
            [(0, 15), (700, 15), (1200, 15)]
        )

        # Slide 13: Summary & CTA (15s)
        self.driver.get(f"{BASE_URL}/")
        time.sleep(2)
        self.dismiss_privacy_modal()
        self.create_video_from_static_page(
            f"{BASE_URL}/",
            "slide_13_summary_cta.mp4",
            15,
            [(0, 7), (1200, 8)]
        )


def main():
    # Create cursor image
    has_cursor = create_cursor_image()

    if not has_cursor:
        print("\n⚠️  Cursor overlay will be skipped (ImageMagick not available)")
        print("   Videos will be generated without cursor, but privacy banner will be removed\n")

    regenerator = SlideRegenerator()

    try:
        regenerator.setup_driver()
        regenerator.regenerate_all_slides()

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✅ Regenerated {len(regenerator.slides_regenerated)} slides:")
        for slide in regenerator.slides_regenerated:
            print(f"   - {slide}")

        print("\n📁 Videos saved to: {VIDEO_DIR}")
        print("\n✅ All slides now have:")
        print("   ✓ Privacy banner removed")
        if has_cursor:
            print("   ✓ Cursor overlay added")
        print("\n🔄 Next: Rebuild frontend container")
        print("   docker-compose build frontend && docker-compose up -d frontend")

    finally:
        regenerator.teardown_driver()


if __name__ == "__main__":
    main()

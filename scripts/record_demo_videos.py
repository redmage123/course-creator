#!/usr/bin/env python3
"""
Demo Video Recording Script - Selenium + ffmpeg

BUSINESS PURPOSE:
Records screen captures of each demo slide workflow timed to match
the regenerated audio narration durations. Videos are recorded at
1920x1080 and encoded with H.264 for web compatibility.

TECHNICAL APPROACH:
- Uses Selenium WebDriver to automate browser interactions
- Uses ffmpeg to capture screen during the automation
- Each video is timed to match its corresponding audio file duration
- Videos are saved to frontend-legacy/static/demo/videos/

REQUIREMENTS:
    pip install selenium webdriver-manager
    # ffmpeg must be installed: sudo apt install ffmpeg

USAGE:
    # Record all slides
    python3 scripts/record_demo_videos.py

    # Record specific slide
    python3 scripts/record_demo_videos.py --slide 2

    # Test mode (no recording, just browser automation)
    python3 scripts/record_demo_videos.py --test

NOTES:
- Requires DISPLAY environment variable set (use Xvfb for headless)
- Requires demo data to be set up in the database
- Videos will be overwritten if they exist
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("ERROR: Selenium not installed")
    print("Run: pip install selenium webdriver-manager")
    sys.exit(1)

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
VIDEO_DIR = Path('frontend-legacy/static/demo/videos')
AUDIO_DIR = Path('frontend-legacy/static/demo/audio')

# Demo credentials
ORG_ADMIN_EMAIL = 'sarah@acmelearning.edu'
ORG_ADMIN_PASSWORD = 'SecurePass123!'
INSTRUCTOR_EMAIL = 'instructor@acmelearning.edu'
INSTRUCTOR_PASSWORD = 'SecurePass123!'
STUDENT_EMAIL = 'student@acmelearning.edu'
STUDENT_PASSWORD = 'SecurePass123!'

# Slide definitions with target durations from audio
SLIDES = [
    {
        'id': 1,
        'title': 'Platform Introduction',
        'filename': 'slide_01_platform_introduction.mp4',
        'duration': 16,
        'description': 'Homepage with hero section and features'
    },
    {
        'id': 2,
        'title': 'Organization Registration',
        'filename': 'slide_02_organization_registration.mp4',
        'duration': 26,
        'description': 'Fill out organization registration form'
    },
    {
        'id': 3,
        'title': 'Organization Admin Dashboard',
        'filename': 'slide_03_organization_admin_dashboard.mp4',
        'duration': 81,
        'description': 'Login as org admin, explore dashboard, create project'
    },
    {
        'id': 4,
        'title': 'Creating Training Tracks',
        'filename': 'slide_04_creating_training_tracks.mp4',
        'duration': 41,
        'description': 'Create a track from the Tracks tab'
    },
    {
        'id': 5,
        'title': 'AI Assistant',
        'filename': 'slide_05_ai_assistant.mp4',
        'duration': 47,
        'description': 'Use AI assistant to create track via natural language'
    },
    {
        'id': 6,
        'title': 'Adding Instructors',
        'filename': 'slide_06_adding_instructors.mp4',
        'duration': 19,
        'description': 'Add instructor to organization'
    },
    {
        'id': 7,
        'title': 'Instructor Dashboard',
        'filename': 'slide_07_instructor_dashboard.mp4',
        'duration': 32,
        'description': 'Show instructor dashboard and AI course generation'
    },
    {
        'id': 8,
        'title': 'Course Content Generation',
        'filename': 'slide_08_course_content.mp4',
        'duration': 36,
        'description': 'AI content generation, lesson creation, quiz generation'
    },
    {
        'id': 9,
        'title': 'Student Enrollment',
        'filename': 'slide_09_enroll_students.mp4',
        'duration': 22,
        'description': 'Bulk student enrollment via CSV upload'
    },
    {
        'id': 10,
        'title': 'Student Dashboard',
        'filename': 'slide_10_student_dashboard.mp4',
        'duration': 18,
        'description': 'Student dashboard with courses and progress'
    },
    {
        'id': 11,
        'title': 'Course Browsing & Labs',
        'filename': 'slide_11_course_browsing.mp4',
        'duration': 35,
        'description': 'Browse course catalog, show lab environment'
    },
    {
        'id': 12,
        'title': 'Quiz & Assessment',
        'filename': 'slide_12_quiz_assessment.mp4',
        'duration': 28,
        'description': 'Take a quiz, show feedback'
    },
    {
        'id': 13,
        'title': 'Student Progress',
        'filename': 'slide_13_student_progress.mp4',
        'duration': 20,
        'description': 'Student progress tracking and achievements'
    },
    {
        'id': 14,
        'title': 'Instructor Analytics',
        'filename': 'slide_14_instructor_analytics.mp4',
        'duration': 34,
        'description': 'Analytics dashboard with AI insights'
    },
    {
        'id': 15,
        'title': 'Summary & Next Steps',
        'filename': 'slide_15_summary.mp4',
        'duration': 26,
        'description': 'Platform summary and call to action'
    }
]


class DemoVideoRecorder:
    """Records demo videos using Selenium + ffmpeg"""

    def __init__(self, headless=False, test_mode=False):
        self.headless = headless
        self.test_mode = test_mode
        self.driver = None
        self.ffmpeg_process = None

    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        import tempfile

        options = Options()

        if self.headless:
            options.add_argument('--headless=new')

        # Use unique user data directory to avoid session conflicts
        user_data_dir = tempfile.mkdtemp(prefix='chrome-demo-')
        options.add_argument(f'--user-data-dir={user_data_dir}')

        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-gpu')
        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)

    def start_recording(self, output_path, duration):
        """Start ffmpeg screen recording"""
        if self.test_mode:
            print(f"   [TEST MODE] Would record {duration}s to {output_path}")
            return

        # Get display for ffmpeg
        display = os.getenv('DISPLAY', ':0')

        # ffmpeg command for screen recording
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-f', 'x11grab',
            '-video_size', '1920x1080',
            '-framerate', '30',
            '-i', display,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]

        print(f"   Starting recording: {duration}s -> {output_path.name}")
        self.ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_recording(self):
        """Stop ffmpeg recording"""
        if self.ffmpeg_process:
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None

    def wait_and_click(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for element and click it"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        element.click()
        return element

    def wait_for_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def type_slowly(self, element, text, delay=0.05):
        """Type text character by character for visual effect"""
        for char in text:
            element.send_keys(char)
            time.sleep(delay)

    def scroll_to_element(self, element):
        """Scroll element into view"""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(0.5)

    # =========================================================================
    # Slide Recording Functions
    # =========================================================================

    def record_slide_01_introduction(self, slide):
        """Slide 1: Platform Introduction (16s)"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Navigate to homepage
        self.driver.get(BASE_URL)
        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        # Show homepage hero section
        time.sleep(3)

        # Scroll down to features
        self.driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'});")
        time.sleep(3)

        # Continue scrolling through features
        self.driver.execute_script("window.scrollTo({top: 800, behavior: 'smooth'});")
        time.sleep(4)

        # Scroll to bottom
        self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
        time.sleep(4)

        # Wait for remaining duration
        remaining = slide['duration'] - 14
        if remaining > 0:
            time.sleep(remaining)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide_02_registration(self, slide):
        """Slide 2: Organization Registration (26s)"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Navigate to organization registration
        self.driver.get(f"{BASE_URL}/organization/register")
        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        # Show form and start filling
        time.sleep(2)

        try:
            # Organization Name
            org_name = self.wait_for_element('[name="organizationName"], #organizationName, input[placeholder*="organization"]')
            self.scroll_to_element(org_name)
            self.type_slowly(org_name, 'Acme Learning', delay=0.08)
            time.sleep(1)

            # Website (if field exists)
            try:
                website = self.driver.find_element(By.CSS_SELECTOR, '[name="website"], #website')
                self.type_slowly(website, 'https://acmelearning.edu', delay=0.06)
                time.sleep(0.5)
            except:
                pass

            # Description
            try:
                desc = self.driver.find_element(By.CSS_SELECTOR, '[name="description"], #description, textarea')
                self.scroll_to_element(desc)
                self.type_slowly(desc, 'Professional training organization', delay=0.05)
                time.sleep(1)
            except:
                pass

            # Email
            try:
                email = self.driver.find_element(By.CSS_SELECTOR, '[name="email"], #email, [type="email"]')
                self.scroll_to_element(email)
                self.type_slowly(email, 'sarah@acmelearning.edu', delay=0.06)
                time.sleep(0.5)
            except:
                pass

            # Show the filled form for remaining time
            time.sleep(max(0, slide['duration'] - 18))

        except Exception as e:
            print(f"   Warning: Form interaction failed: {e}")
            time.sleep(slide['duration'] - 4)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide_03_org_admin_dashboard(self, slide):
        """Slide 3: Organization Admin Dashboard (81s)"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Start at homepage
        self.driver.get(BASE_URL)
        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        # Click login button
        time.sleep(2)
        try:
            login_btn = self.wait_and_click('a[href*="login"], button:contains("Login"), .login-button')
        except:
            self.driver.get(f"{BASE_URL}/login")
        time.sleep(2)

        # Fill login form
        try:
            email_input = self.wait_for_element('[name="email"], #email, [type="email"]')
            self.type_slowly(email_input, ORG_ADMIN_EMAIL, delay=0.06)
            time.sleep(1)

            password_input = self.driver.find_element(By.CSS_SELECTOR, '[name="password"], #password, [type="password"]')
            self.type_slowly(password_input, ORG_ADMIN_PASSWORD, delay=0.08)
            time.sleep(1)

            # Submit login
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], .login-submit')
            submit_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"   Login form interaction failed: {e}")

        # Show dashboard
        time.sleep(5)

        # Explore different sections
        try:
            # Click on Projects tab if available
            projects_tab = self.wait_and_click('[data-tab="projects"], a[href*="projects"]', timeout=5)
            time.sleep(3)
        except:
            pass

        try:
            # Click on Tracks tab
            tracks_tab = self.wait_and_click('[data-tab="tracks"], a[href*="tracks"]', timeout=5)
            time.sleep(3)
        except:
            pass

        try:
            # Click on Members tab
            members_tab = self.wait_and_click('[data-tab="members"], a[href*="members"]', timeout=5)
            time.sleep(3)
        except:
            pass

        # Remaining time
        elapsed = 35  # Approximate elapsed time
        remaining = slide['duration'] - elapsed
        if remaining > 0:
            time.sleep(remaining)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide_04_creating_tracks(self, slide):
        """Slide 4: Creating Training Tracks (41s)"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Assume we're logged in as org admin, navigate to tracks
        self.driver.get(f"{BASE_URL}/org-admin")
        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        # Navigate to tracks tab
        time.sleep(2)
        try:
            tracks_tab = self.wait_and_click('[data-tab="tracks"], a[href*="tracks"]', timeout=5)
            time.sleep(2)
        except:
            pass

        # Click Create Track button
        try:
            create_btn = self.wait_and_click('button:contains("Create"), .create-track-btn', timeout=5)
            time.sleep(2)
        except:
            pass

        # Fill track form
        try:
            name_input = self.wait_for_element('[name="trackName"], #trackName, input[placeholder*="name"]')
            self.type_slowly(name_input, 'Python Fundamentals', delay=0.08)
            time.sleep(1)

            # Select project dropdown
            try:
                project_select = self.driver.find_element(By.CSS_SELECTOR, '[name="project"], #project, select')
                project_select.click()
                time.sleep(0.5)
                option = self.driver.find_element(By.CSS_SELECTOR, 'option:contains("Data Science")')
                option.click()
                time.sleep(1)
            except:
                pass

            # Select level
            try:
                level_select = self.driver.find_element(By.CSS_SELECTOR, '[name="level"], #level')
                level_select.click()
                time.sleep(0.5)
                option = self.driver.find_element(By.CSS_SELECTOR, 'option:contains("Beginner")')
                option.click()
                time.sleep(1)
            except:
                pass

            # Description
            try:
                desc = self.driver.find_element(By.CSS_SELECTOR, '[name="description"], textarea')
                self.type_slowly(desc, 'Learn Python basics for data science', delay=0.05)
                time.sleep(1)
            except:
                pass

        except Exception as e:
            print(f"   Track form interaction failed: {e}")

        # Wait remaining duration
        elapsed = 20
        remaining = slide['duration'] - elapsed
        if remaining > 0:
            time.sleep(remaining)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide_05_ai_assistant(self, slide):
        """Slide 5: AI Assistant (47s)"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Stay on org admin dashboard
        self.driver.get(f"{BASE_URL}/org-admin")
        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        time.sleep(3)

        # Click AI assistant button
        try:
            ai_btn = self.wait_and_click('.ai-assistant-btn, #ai-assistant, [aria-label*="AI"]', timeout=5)
            time.sleep(2)

            # Type in AI chat
            chat_input = self.wait_for_element('.ai-chat-input, #ai-input, textarea')
            ai_message = "Create an intermediate track called Machine Learning Basics for the Data Science project"
            self.type_slowly(chat_input, ai_message, delay=0.04)
            time.sleep(2)

            # Submit message
            chat_input.send_keys(Keys.RETURN)
            time.sleep(5)

        except Exception as e:
            print(f"   AI assistant interaction failed: {e}")

        # Wait remaining duration
        remaining = slide['duration'] - 15
        if remaining > 0:
            time.sleep(remaining)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide_generic(self, slide):
        """Generic slide recording for slides without specific automation"""
        print(f"Recording Slide {slide['id']}: {slide['title']}")

        output_path = VIDEO_DIR / slide['filename']

        # Navigate to a relevant page based on slide content
        if 'instructor' in slide['title'].lower():
            self.driver.get(f"{BASE_URL}/instructor")
        elif 'student' in slide['title'].lower():
            self.driver.get(f"{BASE_URL}/student")
        elif 'analytics' in slide['title'].lower():
            self.driver.get(f"{BASE_URL}/instructor")  # Analytics in instructor dashboard
        elif 'quiz' in slide['title'].lower():
            self.driver.get(f"{BASE_URL}/student")
        elif 'summary' in slide['title'].lower():
            self.driver.get(BASE_URL)
        else:
            self.driver.get(f"{BASE_URL}/org-admin")

        time.sleep(2)

        self.start_recording(output_path, slide['duration'])

        # Simple scrolling animation
        scroll_positions = [0, 300, 600, 900, 600, 300, 0]
        scroll_time = slide['duration'] / len(scroll_positions)

        for pos in scroll_positions:
            self.driver.execute_script(f"window.scrollTo({{top: {pos}, behavior: 'smooth'}});")
            time.sleep(scroll_time)

        self.stop_recording()
        print(f"   Completed slide {slide['id']}")

    def record_slide(self, slide):
        """Route to appropriate slide recording function"""
        slide_recorders = {
            1: self.record_slide_01_introduction,
            2: self.record_slide_02_registration,
            3: self.record_slide_03_org_admin_dashboard,
            4: self.record_slide_04_creating_tracks,
            5: self.record_slide_05_ai_assistant,
        }

        recorder = slide_recorders.get(slide['id'], self.record_slide_generic)
        recorder(slide)

    def run(self, slide_id=None):
        """Run the recording session"""
        print("=" * 70)
        print("DEMO VIDEO RECORDING SESSION")
        print("=" * 70)
        print()

        # Create output directory
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)

        # Setup browser
        print("Setting up Chrome WebDriver...")
        self.setup_driver()
        print(f"Browser window size: 1920x1080")
        print(f"Base URL: {BASE_URL}")
        print()

        # Determine which slides to record
        if slide_id:
            slides_to_record = [s for s in SLIDES if s['id'] == slide_id]
            if not slides_to_record:
                print(f"ERROR: Slide {slide_id} not found")
                return
        else:
            slides_to_record = SLIDES

        print(f"Recording {len(slides_to_record)} slide(s)...")
        print()

        # Record each slide
        for slide in slides_to_record:
            try:
                self.record_slide(slide)
                print()
            except Exception as e:
                print(f"   ERROR recording slide {slide['id']}: {e}")
                continue

        # Cleanup
        if self.driver:
            self.driver.quit()

        print("=" * 70)
        print("RECORDING SESSION COMPLETE")
        print("=" * 70)
        print()
        print(f"Videos saved to: {VIDEO_DIR.absolute()}")


def main():
    parser = argparse.ArgumentParser(description='Record demo videos')
    parser.add_argument('--slide', type=int, help='Record specific slide number')
    parser.add_argument('--test', action='store_true', help='Test mode (no recording)')
    parser.add_argument('--headless', action='store_true', help='Run browser headless')
    args = parser.parse_args()

    recorder = DemoVideoRecorder(
        headless=args.headless,
        test_mode=args.test
    )
    recorder.run(slide_id=args.slide)


if __name__ == '__main__':
    main()

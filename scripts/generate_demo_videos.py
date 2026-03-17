#!/usr/bin/env python3
"""
Demo Video Screencast Generator - Selenium + FFmpeg Automation

BUSINESS PURPOSE:
Automatically captures authentic platform video screencasts for the interactive demo
slideshow, showing live workflows that engage viewers more effectively than static images.

TECHNICAL APPROACH:
Uses Selenium WebDriver to navigate through real platform workflows while FFmpeg
records the browser window, creating high-quality video segments for each demo slide.

USAGE:
    python scripts/generate_demo_videos.py --all
    python scripts/generate_demo_videos.py --slide 3
    python scripts/generate_demo_videos.py --clean
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import signal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Demo configuration
BASE_URL = "https://localhost:3000"
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
RESOLUTION = (1920, 1080)
FRAMERATE = 30

# Test credentials
INSTRUCTOR_EMAIL = "demo.instructor@example.com"
INSTRUCTOR_PASSWORD = "DemoPass123!"
STUDENT_EMAIL = "demo.student@example.com"
STUDENT_PASSWORD = "DemoPass123!"


class VideoRecorder:
    """
    FFmpeg-based screen recorder for capturing browser automation

    BUSINESS CONTEXT:
    Records live platform workflows as video to create engaging,
    realistic demo presentations that show actual product functionality.
    """

    def __init__(self, output_file: str, duration: int, framerate: int = FRAMERATE):
        """
        Initialize video recorder

        Args:
            output_file: Path to save video file
            duration: Recording duration in seconds
            framerate: Video framerate (default 30fps)
        """
        self.output_file = output_file
        self.duration = duration
        self.framerate = framerate
        self.process = None

    def start_recording(self, display: str = ":99"):
        """
        Start FFmpeg screen recording

        Args:
            display: X display to record (for headless environments)
        """
        # FFmpeg command to record X display
        # Using x11grab for Linux screen capture
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', str(self.framerate),
            '-i', display,
            '-t', str(self.duration),
            '-vcodec', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-y',  # Overwrite output file
            self.output_file
        ]

        print(f"  🎥 Recording started: {os.path.basename(self.output_file)} ({self.duration}s)")

        # Start FFmpeg process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Give FFmpeg time to initialize
        time.sleep(1)

    def stop_recording(self):
        """Stop FFmpeg recording"""
        if self.process:
            # Send SIGINT to gracefully stop FFmpeg
            self.process.send_signal(signal.SIGINT)

            # Wait for process to finish
            try:
                self.process.wait(timeout=5)
                print(f"  ✓ Recording saved: {os.path.basename(self.output_file)}")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.process.kill()
                print(f"  ⚠️  Recording force-stopped: {os.path.basename(self.output_file)}")

            self.process = None

    def wait_for_completion(self):
        """Wait for recording to complete based on duration"""
        if self.process:
            # FFmpeg handles duration with -t flag, so we just wait
            time.sleep(self.duration + 1)
            self.stop_recording()


class DemoVideoGenerator:
    """
    Selenium automation for capturing demo video screencasts

    BUSINESS CONTEXT:
    Generates authentic platform video demonstrations showing real workflows
    for marketing demos, presentations, and sales materials.
    """

    def __init__(self, headless: bool = False):
        """
        Initialize Selenium WebDriver for video recording

        Args:
            headless: Run browser in headless mode (requires Xvfb)
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.video_counter = 0
        self.display = None

        # Ensure videos directory exists
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    def setup_display(self):
        """
        Set up virtual display for headless recording

        TECHNICAL NOTE:
        Uses Xvfb to create a virtual X server that FFmpeg can record.
        Required for headless environments (servers, containers).
        """
        if self.headless:
            # Start Xvfb on display :99
            self.display = ":99"

            # Check if Xvfb is already running
            result = subprocess.run(
                ['pgrep', '-f', 'Xvfb :99'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Start Xvfb
                subprocess.Popen([
                    'Xvfb',
                    self.display,
                    '-screen', '0', f'{RESOLUTION[0]}x{RESOLUTION[1]}x24'
                ])
                time.sleep(2)
                print(f"✓ Virtual display started: {self.display}")
            else:
                print(f"✓ Virtual display already running: {self.display}")

            # Set DISPLAY environment variable
            os.environ['DISPLAY'] = self.display
        else:
            # Use default display
            self.display = os.environ.get('DISPLAY', ':0')
            print(f"✓ Using display: {self.display}")

    def setup_driver(self):
        """Configure and initialize Chrome WebDriver"""
        chrome_options = Options()

        if self.headless:
            # For Xvfb, we don't use Chrome's headless mode
            # Chrome runs normally in the virtual X display
            pass

        # Try to use Google Chrome if available, fallback to Chromium
        import shutil
        if shutil.which('google-chrome'):
            chrome_options.binary_location = "/usr/bin/google-chrome"
        elif shutil.which('chromium'):
            chrome_options.binary_location = "/snap/bin/chromium"

        # Essential Chrome flags for headless/Xvfb compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument(f"--window-size={RESOLUTION[0]},{RESOLUTION[1]}")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")

        # Remote debugging for DevTools
        chrome_options.add_argument("--remote-debugging-port=9222")

        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Maximize browser window for clean recording
        chrome_options.add_argument("--start-maximized")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(*RESOLUTION)
        self.wait = WebDriverWait(self.driver, 30)

        print(f"✓ WebDriver initialized ({RESOLUTION[0]}x{RESOLUTION[1]})")

    def teardown_driver(self):
        """Close WebDriver and cleanup"""
        if self.driver:
            self.driver.quit()
            print("✓ WebDriver closed")

    def record_workflow(self, filename: str, duration: int, workflow_func):
        """
        Record a workflow as video

        Args:
            filename: Video filename (without path)
            duration: Recording duration in seconds
            workflow_func: Function that executes the workflow
        """
        filepath = str(VIDEOS_DIR / filename)

        # Create recorder
        recorder = VideoRecorder(filepath, duration)

        # Start recording
        recorder.start_recording(self.display)

        # Execute workflow
        try:
            workflow_func()
        except Exception as e:
            print(f"  ⚠️  Warning during workflow: {e}")

        # Wait for recording to complete
        recorder.wait_for_completion()

        self.video_counter += 1

    def login_as_instructor(self):
        """Login as demo instructor"""
        self.driver.get(f"{BASE_URL}/login")
        time.sleep(2)

        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.send_keys(INSTRUCTOR_EMAIL)

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(INSTRUCTOR_PASSWORD)

        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        time.sleep(3)  # Wait for dashboard load
        print("✓ Logged in as instructor")

    def login_as_student(self):
        """Login as demo student"""
        self.driver.get(f"{BASE_URL}/login")
        time.sleep(2)

        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.send_keys(STUDENT_EMAIL)

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(STUDENT_PASSWORD)

        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        time.sleep(3)  # Wait for dashboard load
        print("✓ Logged in as student")

    def logout(self):
        """Logout current user"""
        try:
            user_menu = self.driver.find_element(By.ID, "user-menu")
            user_menu.click()
            time.sleep(0.5)

            logout_btn = self.driver.find_element(By.ID, "logout-btn")
            logout_btn.click()
            time.sleep(2)
        except:
            self.driver.delete_all_cookies()
            time.sleep(1)

    # ========================================================================
    # SLIDE 1: Introduction (15 seconds)
    # ========================================================================

    def generate_slide_01_introduction(self):
        """
        Generate video for Slide 1: Introduction

        Duration: 15 seconds
        Narration: "Welcome to Course Creator Platform - the AI-powered solution
                   that transforms course development from weeks to minutes."
        Visual: Homepage with hero section and platform overview
        """
        print("\n🎥 Generating Slide 1: Introduction (15s)")

        def workflow():
            # Navigate to homepage
            self.driver.get(f"{BASE_URL}/")
            time.sleep(3)

            # Slow scroll through hero section
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {i * 200});")
                time.sleep(2)

        self.record_workflow("slide_01_introduction.mp4", 15, workflow)
        print("✓ Slide 1 complete")

    # ========================================================================
    # SLIDE 2: The Challenge (30 seconds)
    # ========================================================================

    def generate_slide_02_challenge(self):
        """
        Generate video for Slide 2: The Challenge

        Duration: 30 seconds
        Narration: "Traditional course creation is time-consuming. Instructors spend
                   40+ hours per course on content creation, assessment design, and
                   lab setup. Course Creator Platform changes everything."
        Visual: Split-screen showing traditional vs AI-powered course creation
        """
        print("\n🎥 Generating Slide 2: The Challenge (30s)")

        def workflow():
            self.login_as_instructor()
            self.driver.get(f"{BASE_URL}/dashboard")
            time.sleep(5)

            # Show dashboard features
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(5)

            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(5)

        self.record_workflow("slide_02_challenge.mp4", 30, workflow)
        self.logout()
        print("✓ Slide 2 complete")

    # ========================================================================
    # SLIDE 3: AI-Powered Course Generation (60 seconds)
    # ========================================================================

    def generate_slide_03_course_generation(self):
        """
        Generate video for Slide 3: AI-Powered Course Generation

        Duration: 60 seconds
        Narration: "Watch as our AI generates a complete Python programming course
                   in under 60 seconds - including syllabus, learning objectives,
                   and module structure."
        Workflow: Create Course → AI Generation → Course Structure
        """
        print("\n🎥 Generating Slide 3: AI-Powered Course Generation (60s)")

        def workflow():
            self.login_as_instructor()
            self.driver.get(f"{BASE_URL}/dashboard")
            time.sleep(10)

            # Demonstrate course creation workflow
            # Note: This may need adjustment based on actual UI
            try:
                # Look for create course button
                create_btn = self.driver.find_element(By.CSS_SELECTOR, "button.create-course-btn")
                create_btn.click()
                time.sleep(10)

                # Fill course form
                course_title = self.driver.find_element(By.ID, "courseTitle")
                for char in "Introduction to Python Programming":
                    course_title.send_keys(char)
                    time.sleep(0.1)

                time.sleep(5)

                # Submit
                generate_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                generate_btn.click()
                time.sleep(20)

            except Exception as e:
                # Fallback: show dashboard
                print(f"  Fallback workflow (button not found): {e}")
                time.sleep(30)

        self.record_workflow("slide_03_course_generation.mp4", 60, workflow)
        self.logout()
        print("✓ Slide 3 complete")

    # ========================================================================
    # SLIDE 4: Intelligent Content Generation (60 seconds)
    # ========================================================================

    def generate_slide_04_content_generation(self):
        """
        Generate video for Slide 4: Content Generation

        Duration: 60 seconds
        Narration: "Our RAG-enhanced AI creates engaging learning materials tailored
                   to your students' skill levels - from video scripts to interactive
                   exercises."
        Workflow: Generate Content → AI Creates Materials → Edit
        """
        print("\n🎥 Generating Slide 4: Intelligent Content Generation (60s)")

        def workflow():
            self.login_as_instructor()
            self.driver.get(f"{BASE_URL}/html/course-content.html")
            time.sleep(15)

            # Scroll through content
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {i * 400});")
                time.sleep(10)

        self.record_workflow("slide_04_content_generation.mp4", 60, workflow)
        self.logout()
        print("✓ Slide 4 complete")

    # ========================================================================
    # SLIDE 5: Multi-IDE Lab Environment (60 seconds)
    # ========================================================================

    def generate_slide_05_multi_ide_lab(self):
        """
        Generate video for Slide 5: Multi-IDE Lab Environment

        Duration: 60 seconds
        Narration: "Students get hands-on experience in professional coding
                   environments - VSCode, PyCharm, IntelliJ, JupyterLab, or
                   Terminal - all in their browser with no installation required."
        Workflow: Lab Selection → IDE Choice → Code Execution
        """
        print("\n🎥 Generating Slide 5: Multi-IDE Lab Environment (60s)")

        def workflow():
            self.login_as_student()
            self.driver.get(f"{BASE_URL}/lab")
            time.sleep(10)

            try:
                # Start lab
                start_btn = self.driver.find_element(By.ID, "start-lab-btn")
                start_btn.click()
                time.sleep(15)

                # Write code
                code_editor = self.driver.find_element(By.CLASS_NAME, "code-editor")
                code = "print('Hello from Course Creator!')"
                for char in code:
                    code_editor.send_keys(char)
                    time.sleep(0.1)

                time.sleep(5)

                # Run code
                run_btn = self.driver.find_element(By.ID, "run-code-btn")
                run_btn.click()
                time.sleep(15)

            except Exception as e:
                print(f"  Fallback: showing lab page ({e})")
                time.sleep(30)

        self.record_workflow("slide_05_multi_ide_lab.mp4", 60, workflow)
        self.logout()
        print("✓ Slide 5 complete")

    # ========================================================================
    # SLIDE 6: AI Lab Assistant Integration (45 seconds)
    # ========================================================================

    def generate_slide_06_ai_lab_assistant(self):
        """
        Generate video for Slide 6: AI Lab Assistant

        Duration: 45 seconds
        Narration: "Stuck on a problem? Our integrated AI assistant provides instant,
                   context-aware help - explaining concepts, debugging errors, and
                   suggesting improvements."
        Workflow: Open AI Chat → Ask Question → Get Help
        """
        print("\n🎥 Generating Slide 6: AI Lab Assistant Integration (45s)")

        def workflow():
            self.login_as_student()
            self.driver.get(f"{BASE_URL}/lab")
            time.sleep(5)

            try:
                start_btn = self.driver.find_element(By.ID, "start-lab-btn")
                start_btn.click()
                time.sleep(5)

                # Open AI chat
                ai_toggle = self.driver.find_element(By.ID, "ai-chat-toggle")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", ai_toggle)
                time.sleep(1)
                ai_toggle.click()
                time.sleep(3)

                # Type question
                ai_input = self.driver.find_element(By.ID, "ai-chat-input")
                question = "How do I fix a syntax error?"
                for char in question:
                    ai_input.send_keys(char)
                    time.sleep(0.1)

                time.sleep(2)

                # Send
                send_btn = self.driver.find_element(By.ID, "ai-chat-send")
                send_btn.click()
                time.sleep(15)

            except Exception as e:
                print(f"  Fallback: showing lab page ({e})")
                time.sleep(20)

        self.record_workflow("slide_06_ai_lab_assistant.mp4", 45, workflow)
        self.logout()
        print("✓ Slide 6 complete")

    # ========================================================================
    # SLIDE 7: Comprehensive Assessment System (45 seconds)
    # ========================================================================

    def generate_slide_07_assessment_system(self):
        """
        Generate video for Slide 7: Assessment System

        Duration: 45 seconds
        Narration: "Create sophisticated assessments with multiple question types,
                   automatic grading, and detailed analytics - all generated by AI
                   or customized by instructors."
        Workflow: Quiz Interface → Taking Quiz → Results
        """
        print("\n🎥 Generating Slide 7: Comprehensive Assessment System (45s)")

        def workflow():
            self.login_as_student()
            self.driver.get(f"{BASE_URL}/html/quiz.html")
            time.sleep(10)

            try:
                # Answer question
                first_option = self.driver.find_element(By.CSS_SELECTOR, "input[type='radio']")
                first_option.click()
                time.sleep(5)

                # Next question
                next_btn = self.driver.find_element(By.ID, "next-question-btn")
                next_btn.click()
                time.sleep(5)

                # Submit
                submit_btn = self.driver.find_element(By.ID, "submit-quiz-btn")
                submit_btn.click()
                time.sleep(15)

            except Exception as e:
                print(f"  Fallback: showing quiz page ({e})")
                time.sleep(20)

        self.record_workflow("slide_07_assessment_system.mp4", 45, workflow)
        self.logout()
        print("✓ Slide 7 complete")

    # ========================================================================
    # SLIDE 8: Real-Time Progress Tracking (30 seconds)
    # ========================================================================

    def generate_slide_08_progress_tracking(self):
        """
        Generate video for Slide 8: Progress Tracking

        Duration: 30 seconds
        Narration: "Both students and instructors get comprehensive analytics -
                   track completion rates, time spent, quiz scores, and learning
                   patterns in real-time."
        Visual: Student and Instructor Progress Dashboards
        """
        print("\n🎥 Generating Slide 8: Real-Time Progress Tracking (30s)")

        def workflow():
            self.login_as_student()
            self.driver.get(f"{BASE_URL}/student/progress")
            time.sleep(15)

            # Scroll through progress dashboard
            self.driver.execute_script("window.scrollTo(0, 400);")
            time.sleep(10)

        self.record_workflow("slide_08_progress_tracking.mp4", 30, workflow)
        self.logout()
        print("✓ Slide 8 complete")

    # ========================================================================
    # SLIDE 9: Multi-Tenant Organization Management (30 seconds)
    # ========================================================================

    def generate_slide_09_organization_management(self):
        """
        Generate video for Slide 9: Organization Management

        Duration: 30 seconds
        Narration: "Built for scale - manage multiple organizations, teams, and
                   learning tracks with enterprise-grade RBAC and compliance features."
        Visual: Organization admin dashboard
        """
        print("\n🎥 Generating Slide 9: Multi-Tenant Organization Management (30s)")

        def workflow():
            self.login_as_instructor()
            self.driver.get(f"{BASE_URL}/dashboard")
            time.sleep(15)

            # Show dashboard features
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(10)

        self.record_workflow("slide_09_organization_management.mp4", 30, workflow)
        self.logout()
        print("✓ Slide 9 complete")

    # ========================================================================
    # SLIDE 10: GDPR Privacy Compliance (30 seconds)
    # ========================================================================

    def generate_slide_10_privacy_compliance(self):
        """
        Generate video for Slide 10: Privacy Compliance

        Duration: 30 seconds
        Narration: "Full GDPR, CCPA, and PIPEDA compliance built-in - automated
                   consent management, data retention policies, and privacy-by-design
                   architecture."
        Workflow: Registration with Consent → Privacy Dashboard
        """
        print("\n🎥 Generating Slide 10: GDPR Privacy Compliance (30s)")

        def workflow():
            self.driver.get(f"{BASE_URL}/register")
            time.sleep(10)

            # Scroll through registration form
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(10)

            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(5)

        self.record_workflow("slide_10_privacy_compliance.mp4", 30, workflow)
        print("✓ Slide 10 complete")

    # ========================================================================
    # SLIDE 11: Call to Action (15 seconds)
    # ========================================================================

    def generate_slide_11_call_to_action(self):
        """
        Generate video for Slide 11: Summary & CTA

        Duration: 15 seconds
        Narration: "Transform your course creation process today. Start your free
                   trial or schedule a personalized demo with our team."
        Visual: Homepage with CTA and key metrics
        """
        print("\n🎥 Generating Slide 11: Call to Action (15s)")

        def workflow():
            self.driver.get(f"{BASE_URL}/")
            time.sleep(3)

            # Scroll to CTA
            self.driver.execute_script("window.scrollTo(0, 1200);")
            time.sleep(8)

        self.record_workflow("slide_11_call_to_action.mp4", 15, workflow)
        print("✓ Slide 11 complete")

    # ========================================================================
    # Main Generation Methods
    # ========================================================================

    def generate_all_slides(self):
        """Generate video screencasts for all slides"""
        print("=" * 60)
        print("DEMO VIDEO GENERATION - ALL SLIDES")
        print("=" * 60)

        start_time = time.time()

        try:
            self.setup_display()
            self.setup_driver()

            # Generate each slide
            self.generate_slide_01_introduction()
            self.generate_slide_02_challenge()
            self.generate_slide_03_course_generation()
            self.generate_slide_04_content_generation()
            self.generate_slide_05_multi_ide_lab()
            self.generate_slide_06_ai_lab_assistant()
            self.generate_slide_07_assessment_system()
            self.generate_slide_08_progress_tracking()
            self.generate_slide_09_organization_management()
            self.generate_slide_10_privacy_compliance()
            self.generate_slide_11_call_to_action()

        finally:
            self.teardown_driver()

        elapsed = time.time() - start_time

        print("\n" + "=" * 60)
        print(f"✅ COMPLETE: {self.video_counter} video screencasts generated")
        print(f"⏱️  Total duration: {elapsed:.1f} seconds")
        print(f"📁 Output directory: {VIDEOS_DIR}")
        print("=" * 60)

    def generate_single_slide(self, slide_number: int):
        """
        Generate video for a single slide

        Args:
            slide_number: Slide number (1-11)
        """
        print(f"\nGenerating Slide {slide_number}...")

        try:
            self.setup_display()
            self.setup_driver()

            # Map slide number to generator method
            generators = {
                1: self.generate_slide_01_introduction,
                2: self.generate_slide_02_challenge,
                3: self.generate_slide_03_course_generation,
                4: self.generate_slide_04_content_generation,
                5: self.generate_slide_05_multi_ide_lab,
                6: self.generate_slide_06_ai_lab_assistant,
                7: self.generate_slide_07_assessment_system,
                8: self.generate_slide_08_progress_tracking,
                9: self.generate_slide_09_organization_management,
                10: self.generate_slide_10_privacy_compliance,
                11: self.generate_slide_11_call_to_action,
            }

            if slide_number not in generators:
                print(f"❌ Error: Invalid slide number {slide_number}")
                return

            generators[slide_number]()

        finally:
            self.teardown_driver()

        print(f"\n✅ Slide {slide_number} complete")


def check_dependencies():
    """
    Check required dependencies are installed

    DEPENDENCIES:
    - FFmpeg: For video recording
    - Xvfb: For headless display (headless mode only)
    """
    print("Checking dependencies...")

    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFmpeg installed")
        else:
            print("❌ FFmpeg not found")
            print("   Install: sudo apt-get install ffmpeg")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found")
        print("   Install: sudo apt-get install ffmpeg")
        return False

    # Check Xvfb (optional, only for headless)
    try:
        result = subprocess.run(['Xvfb', '-help'], capture_output=True, text=True)
        if result.returncode == 0 or result.returncode == 1:  # Xvfb returns 1 for -help
            print("✓ Xvfb installed (headless mode available)")
    except FileNotFoundError:
        print("⚠️  Xvfb not found (headless mode will not work)")
        print("   Install: sudo apt-get install xvfb")

    return True


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate demo video screencasts using Selenium + FFmpeg"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all slides (1-11)"
    )
    parser.add_argument(
        "--slide",
        type=int,
        choices=range(1, 12),
        help="Generate specific slide number (1-11)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean videos directory before generating"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (requires Xvfb)"
    )

    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Clean if requested
    if args.clean:
        import shutil
        if VIDEOS_DIR.exists():
            shutil.rmtree(VIDEOS_DIR)
            print(f"✓ Cleaned {VIDEOS_DIR}")
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate videos
    generator = DemoVideoGenerator(headless=args.headless)

    if args.all:
        generator.generate_all_slides()
    elif args.slide:
        generator.generate_single_slide(args.slide)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

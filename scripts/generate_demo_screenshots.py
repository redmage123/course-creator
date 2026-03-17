#!/usr/bin/env python3
"""
Demo Screenshot Generator - Selenium Automation

BUSINESS PURPOSE:
Automatically captures authentic platform screenshots for the interactive demo
slideshow, ensuring consistency, quality, and easy updates when features change.

TECHNICAL APPROACH:
Uses Selenium WebDriver to navigate through real platform workflows, capturing
high-quality screenshots at key interaction points for demo presentation.

USAGE:
    python scripts/generate_demo_screenshots.py --all
    python scripts/generate_demo_screenshots.py --slide 3
    python scripts/generate_demo_screenshots.py --clean
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Demo configuration
BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/screenshots")
RESOLUTION = (1920, 1080)

# Test credentials
INSTRUCTOR_EMAIL = "demo.instructor@example.com"
INSTRUCTOR_PASSWORD = "DemoPass123!"
STUDENT_EMAIL = "demo.student@example.com"
STUDENT_PASSWORD = "DemoPass123!"


class DemoScreenshotGenerator:
    """
    Selenium automation for capturing demo screenshots

    BUSINESS CONTEXT:
    Generates authentic platform screenshots showing real workflows
    for marketing demos, presentations, and documentation.
    """

    def __init__(self, headless: bool = False):
        """
        Initialize Selenium WebDriver

        Args:
            headless: Run browser in headless mode for automation
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.screenshot_counter = 0

        # Ensure screenshots directory exists
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def setup_driver(self):
        """Configure and initialize Chrome WebDriver"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={RESOLUTION[0]},{RESOLUTION[1]}")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")

        # Use unique user data directory to avoid conflicts
        import tempfile
        user_data_dir = tempfile.mkdtemp(prefix="chrome_demo_")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        # High-quality screenshots
        chrome_options.add_argument("--force-device-scale-factor=1")
        chrome_options.add_argument("--high-dpi-support=1")

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

    def save_screenshot(self, filename: str, description: str = ""):
        """
        Save screenshot with metadata

        Args:
            filename: Screenshot filename (without path)
            description: Optional description for logging
        """
        filepath = SCREENSHOTS_DIR / filename
        self.driver.save_screenshot(str(filepath))
        self.screenshot_counter += 1

        print(f"  📸 Saved: {filename}")
        if description:
            print(f"     {description}")

        time.sleep(0.5)  # Pause for visual separation

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

    def dismiss_privacy_modal(self):
        """
        Dismiss the privacy consent modal if it appears

        BUSINESS CONTEXT:
        For demo screenshots, we want clean visuals without consent banners
        """
        try:
            # Wait briefly for modal to appear
            time.sleep(1)

            # Check if privacy modal is visible
            modal = self.driver.find_element(By.ID, 'privacyModal')
            if modal.is_displayed():
                # Click "Accept All" button
                accept_btn = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Accept All')]"
                )
                accept_btn.click()
                time.sleep(1)
                print("  ✓ Privacy modal dismissed")
        except Exception as e:
            # Modal not present or already dismissed - no action needed
            pass

    def logout(self):
        """Logout current user"""
        try:
            # Try to find and click logout button
            user_menu = self.driver.find_element(By.ID, "user-menu")
            user_menu.click()
            time.sleep(0.5)

            logout_btn = self.driver.find_element(By.ID, "logout-btn")
            logout_btn.click()
            time.sleep(2)
        except:
            # If logout fails, just clear cookies
            self.driver.delete_all_cookies()
            time.sleep(1)

    # ========================================================================
    # SLIDE 1: Introduction
    # ========================================================================

    def generate_slide_01_introduction(self):
        """
        Generate screenshots for Slide 1: Introduction

        Visual: Animated title card with platform logo
        """
        print("\n📸 Generating Slide 1: Introduction")

        # Navigate to home page
        self.driver.get(f"{BASE_URL}/")
        time.sleep(2)

        # Dismiss privacy modal if present
        self.dismiss_privacy_modal()
        time.sleep(1)

        # Capture homepage with hero section
        self.save_screenshot(
            "slide_01_01_hero.png",
            "Homepage hero section with platform overview"
        )

        # Scroll to features section
        self.driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)

        self.save_screenshot(
            "slide_01_02_features_overview.png",
            "Key features overview section"
        )

        print("✓ Slide 1 complete (2 screenshots)")

    # ========================================================================
    # SLIDE 2: The Challenge
    # ========================================================================

    def generate_slide_02_challenge(self):
        """
        Generate screenshots for Slide 2: The Challenge

        Visual: Traditional vs AI-powered course creation
        """
        print("\n📸 Generating Slide 2: The Challenge")

        # This will be a custom comparison graphic
        # For now, capture instructor dashboard showing time-saving metrics
        self.login_as_instructor()

        self.driver.get(f"{BASE_URL}/dashboard")
        time.sleep(3)

        self.save_screenshot(
            "slide_02_01_instructor_dashboard.png",
            "Instructor dashboard showing efficiency metrics"
        )

        self.logout()
        print("✓ Slide 2 complete (1 screenshot)")

    # ========================================================================
    # SLIDE 3: AI-Powered Course Generation
    # ========================================================================

    def generate_slide_03_course_generation(self):
        """
        Generate screenshots for Slide 3: AI-Powered Course Generation

        Workflow: Create Course → AI Generation → Course Structure
        """
        print("\n📸 Generating Slide 3: AI-Powered Course Generation")

        self.login_as_instructor()

        # 1. Instructor dashboard with Create Course button
        self.driver.get(f"{BASE_URL}/dashboard")
        time.sleep(2)

        self.save_screenshot(
            "slide_03_01_create_course_button.png",
            "Instructor dashboard with 'Create Course' highlighted"
        )

        # 2. Navigate to course creation (if page exists)
        # Note: This may need adjustment based on actual UI
        try:
            create_btn = self.driver.find_element(By.CSS_SELECTOR, "button.create-course-btn")
            create_btn.click()
            time.sleep(2)

            self.save_screenshot(
                "slide_03_02_course_input_form.png",
                "Course creation form"
            )

            # 3. Fill in course details
            course_title = self.driver.find_element(By.ID, "courseTitle")
            course_title.send_keys("Introduction to Python Programming")
            time.sleep(1)

            self.save_screenshot(
                "slide_03_03_ai_generating.png",
                "AI generating course structure"
            )

            # 4. Submit and wait for generation
            generate_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            generate_btn.click()
            time.sleep(5)  # Wait for AI generation

            self.save_screenshot(
                "slide_03_04_course_structure.png",
                "Generated course structure with modules"
            )

        except Exception as e:
            print(f"  ⚠️  Warning: Could not complete full workflow: {e}")
            print("  Using fallback screenshots from available pages")

        self.logout()
        print("✓ Slide 3 complete (4 screenshots)")

    # ========================================================================
    # SLIDE 4: Intelligent Content Generation
    # ========================================================================

    def generate_slide_04_content_generation(self):
        """
        Generate screenshots for Slide 4: Content Generation

        Workflow: Generate Content → AI Creates Materials → Edit
        """
        print("\n📸 Generating Slide 4: Intelligent Content Generation")

        self.login_as_instructor()

        # Navigate to a course (if exists)
        # For demo purposes, capture course content interface
        self.driver.get(f"{BASE_URL}/html/course-content.html")
        time.sleep(3)

        self.save_screenshot(
            "slide_04_01_content_generation_interface.png",
            "Content generation interface"
        )

        self.logout()
        print("✓ Slide 4 complete (1 screenshot)")

    # ========================================================================
    # SLIDE 5: Multi-IDE Lab Environment
    # ========================================================================

    def generate_slide_05_multi_ide_lab(self):
        """
        Generate screenshots for Slide 5: Multi-IDE Lab Environment

        Workflow: Lab Selection → IDE Choice → Code Execution
        """
        print("\n📸 Generating Slide 5: Multi-IDE Lab Environment")

        self.login_as_student()

        # 1. Navigate to lab environment
        self.driver.get(f"{BASE_URL}/lab")
        time.sleep(3)

        # 2. Capture IDE selection screen
        self.save_screenshot(
            "slide_05_01_ide_selection.png",
            "Lab environment with 5 IDE options"
        )

        # 3. Start lab environment
        try:
            start_btn = self.driver.find_element(By.ID, "start-lab-btn")
            start_btn.click()
            time.sleep(3)

            self.save_screenshot(
                "slide_05_02_lab_starting.png",
                "Lab environment starting up"
            )

            # 4. Code editor appears
            time.sleep(2)

            self.save_screenshot(
                "slide_05_03_code_editor.png",
                "Code editor with sample code"
            )

            # 5. Enter code and execute
            code_editor = self.driver.find_element(By.CLASS_NAME, "code-editor")
            code_editor.clear()
            code_editor.send_keys("print('Hello from Course Creator!')")
            time.sleep(1)

            self.save_screenshot(
                "slide_05_04_code_written.png",
                "Student code written in editor"
            )

            # 6. Run code
            run_btn = self.driver.find_element(By.ID, "run-code-btn")
            run_btn.click()
            time.sleep(2)

            self.save_screenshot(
                "slide_05_05_code_output.png",
                "Code execution output displayed"
            )

        except Exception as e:
            print(f"  ⚠️  Warning: {e}")

        self.logout()
        print("✓ Slide 5 complete (5 screenshots)")

    # ========================================================================
    # SLIDE 6: AI Lab Assistant Integration
    # ========================================================================

    def generate_slide_06_ai_lab_assistant(self):
        """
        Generate screenshots for Slide 6: AI Lab Assistant

        Workflow: Open AI Chat → Ask Question → Get Help
        """
        print("\n📸 Generating Slide 6: AI Lab Assistant Integration")

        self.login_as_student()

        # Navigate to lab
        self.driver.get(f"{BASE_URL}/lab")
        time.sleep(2)

        # Start lab
        try:
            start_btn = self.driver.find_element(By.ID, "start-lab-btn")
            start_btn.click()
            time.sleep(3)

            # 1. Show AI chat toggle
            self.save_screenshot(
                "slide_06_01_ai_chat_button.png",
                "AI assistant button in lab environment"
            )

            # 2. Click AI chat toggle
            ai_toggle = self.driver.find_element(By.ID, "ai-chat-toggle")

            # Scroll AI button into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", ai_toggle)
            time.sleep(0.5)

            ai_toggle.click()
            time.sleep(1)

            self.save_screenshot(
                "slide_06_02_ai_chat_opened.png",
                "AI chat panel opened with welcome message"
            )

            # 3. Type question
            ai_input = self.driver.find_element(By.ID, "ai-chat-input")
            ai_input.send_keys("How do I fix a syntax error?")
            time.sleep(1)

            self.save_screenshot(
                "slide_06_03_ai_question_typed.png",
                "Student asking AI for help"
            )

            # 4. Send question
            send_btn = self.driver.find_element(By.ID, "ai-chat-send")
            send_btn.click()
            time.sleep(5)  # Wait for AI response

            self.save_screenshot(
                "slide_06_04_ai_response.png",
                "AI assistant providing helpful response"
            )

        except Exception as e:
            print(f"  ⚠️  Warning: {e}")

        self.logout()
        print("✓ Slide 6 complete (4 screenshots)")

    # ========================================================================
    # SLIDE 7: Assessment System
    # ========================================================================

    def generate_slide_07_assessment_system(self):
        """
        Generate screenshots for Slide 7: Assessment System

        Workflow: Quiz Interface → Taking Quiz → Results
        """
        print("\n📸 Generating Slide 7: Comprehensive Assessment System")

        self.login_as_student()

        # Navigate to quiz page
        self.driver.get(f"{BASE_URL}/html/quiz.html")
        time.sleep(3)

        # 1. Quiz interface
        self.save_screenshot(
            "slide_07_01_quiz_interface.png",
            "Quiz interface with timer and questions"
        )

        # 2. Answer a question
        try:
            # Select first answer option
            first_option = self.driver.find_element(By.CSS_SELECTOR, "input[type='radio']")
            first_option.click()
            time.sleep(1)

            self.save_screenshot(
                "slide_07_02_quiz_in_progress.png",
                "Student answering quiz questions"
            )

            # 3. Submit quiz (if button exists)
            submit_btn = self.driver.find_element(By.ID, "submit-quiz-btn")
            submit_btn.click()
            time.sleep(2)

            self.save_screenshot(
                "slide_07_03_quiz_results.png",
                "Quiz results with score and feedback"
            )

        except Exception as e:
            print(f"  ⚠️  Warning: {e}")

        self.logout()
        print("✓ Slide 7 complete (3 screenshots)")

    # ========================================================================
    # SLIDE 8: Progress Tracking
    # ========================================================================

    def generate_slide_08_progress_tracking(self):
        """
        Generate screenshots for Slide 8: Progress Tracking

        Visual: Student and Instructor Progress Dashboards
        """
        print("\n📸 Generating Slide 8: Real-Time Progress Tracking")

        # 1. Student progress dashboard
        self.login_as_student()

        self.driver.get(f"{BASE_URL}/student/progress")
        time.sleep(3)

        self.save_screenshot(
            "slide_08_01_student_progress.png",
            "Student progress dashboard with completion metrics"
        )

        self.logout()

        # 2. Instructor analytics (if available)
        self.login_as_instructor()

        self.driver.get(f"{BASE_URL}/dashboard")
        time.sleep(3)

        self.save_screenshot(
            "slide_08_02_instructor_analytics.png",
            "Instructor viewing class analytics"
        )

        self.logout()
        print("✓ Slide 8 complete (2 screenshots)")

    # ========================================================================
    # SLIDE 9: Organization Management
    # ========================================================================

    def generate_slide_09_organization_management(self):
        """
        Generate screenshots for Slide 9: Multi-Tenant Organization

        Visual: Organization admin dashboard and RBAC
        """
        print("\n📸 Generating Slide 9: Multi-Tenant Organization Management")

        # This would require org admin credentials
        # For now, capture instructor dashboard showing organization context
        self.login_as_instructor()

        self.driver.get(f"{BASE_URL}/dashboard")
        time.sleep(3)

        self.save_screenshot(
            "slide_09_01_organization_dashboard.png",
            "Organization management dashboard"
        )

        self.logout()
        print("✓ Slide 9 complete (1 screenshot)")

    # ========================================================================
    # SLIDE 10: Privacy Compliance
    # ========================================================================

    def generate_slide_10_privacy_compliance(self):
        """
        Generate screenshots for Slide 10: GDPR Privacy Compliance

        Workflow: Registration with Consent → Privacy Dashboard
        """
        print("\n📸 Generating Slide 10: GDPR Privacy Compliance")

        # 1. Registration page with consent options
        self.driver.get(f"{BASE_URL}/register")
        time.sleep(3)

        self.save_screenshot(
            "slide_10_01_registration_consent.png",
            "Registration with GDPR consent options"
        )

        # 2. Student progress page (proxy for privacy dashboard)
        self.login_as_student()

        self.driver.get(f"{BASE_URL}/student/progress")
        time.sleep(2)

        self.save_screenshot(
            "slide_10_02_privacy_dashboard.png",
            "Privacy and data management dashboard"
        )

        self.logout()
        print("✓ Slide 10 complete (2 screenshots)")

    # ========================================================================
    # SLIDE 11: Call to Action
    # ========================================================================

    def generate_slide_11_call_to_action(self):
        """
        Generate screenshots for Slide 11: Summary & CTA

        Visual: Homepage with CTA and key metrics
        """
        print("\n📸 Generating Slide 11: Call to Action")

        # Navigate to homepage
        self.driver.get(f"{BASE_URL}/")
        time.sleep(3)

        # Scroll to CTA section
        self.driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(1)

        self.save_screenshot(
            "slide_11_01_call_to_action.png",
            "Homepage CTA with trial signup"
        )

        print("✓ Slide 11 complete (1 screenshot)")

    # ========================================================================
    # Main Generation Methods
    # ========================================================================

    def generate_all_slides(self):
        """Generate screenshots for all slides"""
        print("=" * 60)
        print("DEMO SCREENSHOT GENERATION - ALL SLIDES")
        print("=" * 60)

        start_time = time.time()

        try:
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
        print(f"✅ COMPLETE: {self.screenshot_counter} screenshots generated")
        print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
        print(f"📁 Output directory: {SCREENSHOTS_DIR}")
        print("=" * 60)

    def generate_single_slide(self, slide_number: int):
        """
        Generate screenshots for a single slide

        Args:
            slide_number: Slide number (1-11)
        """
        print(f"\nGenerating Slide {slide_number}...")

        try:
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


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate demo screenshots using Selenium automation"
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
        help="Clean screenshots directory before generating"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    args = parser.parse_args()

    # Clean if requested
    if args.clean:
        import shutil
        if SCREENSHOTS_DIR.exists():
            shutil.rmtree(SCREENSHOTS_DIR)
            print(f"✓ Cleaned {SCREENSHOTS_DIR}")
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate screenshots
    generator = DemoScreenshotGenerator(headless=args.headless)

    if args.all:
        generator.generate_all_slides()
    elif args.slide:
        generator.generate_single_slide(args.slide)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

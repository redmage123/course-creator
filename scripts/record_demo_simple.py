#!/usr/bin/env python3
"""
Simple Demo Video Recorder

Records longer demo videos by navigating slowly through workflows
and capturing frames at regular intervals.

USAGE:
    python3 scripts/record_demo_simple.py student_login
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Embedded VideoRecorder (simplified)
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
import os

class VideoRecorder:
    """Simple video recorder for demo capture"""

    def __init__(self, test_name, output_dir="frontend/static/demo/videos", fps=2, resolution=(1920, 1080)):
        self.test_name = test_name
        self.output_dir = output_dir
        self.fps = fps
        self.resolution = resolution

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename = f"{test_name}_{timestamp}.mp4"
        self.filepath = os.path.join(output_dir, self.filename)

        self.video_writer = None
        self.frame_count = 0
        self.is_recording = False

    def start(self):
        self.is_recording = True
        print(f"Started recording: {self.filename}")

    def add_frame(self, screenshot_data):
        if not self.is_recording:
            return

        try:
            image = Image.open(BytesIO(screenshot_data))
            if image.size != self.resolution:
                image = image.resize(self.resolution, Image.Resampling.LANCZOS)

            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            if self.video_writer is None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(
                    self.filepath, fourcc, self.fps, self.resolution
                )

            self.video_writer.write(frame)
            self.frame_count += 1

        except Exception as e:
            print(f"Error adding frame: {e}")

    def stop(self):
        if self.video_writer:
            self.video_writer.release()
        self.is_recording = False
        print(f"Saved {self.frame_count} frames to {self.filepath}")

# Configuration
BASE_URL = "https://localhost:3000"
VIDEO_DIR = "frontend/static/demo/videos"
VIDEO_FPS = 2  # 2 frames per second
FRAME_INTERVAL = 0.5  # Capture frame every 0.5 seconds


def setup_chrome():
    """Setup Chrome WebDriver"""
    import tempfile
    user_data_dir = tempfile.mkdtemp(prefix="chrome_demo_")

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument(f'--user-data-dir={user_data_dir}')  # Unique directory
    options.add_argument('--remote-debugging-port=9223')  # Unique port
    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)

    return driver


def capture_frames(driver, recorder, duration):
    """Capture frames for specified duration"""
    end_time = time.time() + duration
    while time.time() < end_time:
        screenshot = driver.get_screenshot_as_png()
        recorder.add_frame(screenshot)
        time.sleep(FRAME_INTERVAL)


def record_student_login(driver, recorder):
    """Record student login workflow"""
    print("Recording: Student Login")

    # Navigate to homepage
    driver.get(BASE_URL)
    time.sleep(2)
    capture_frames(driver, recorder, 3)

    # Navigate to login
    driver.get(f"{BASE_URL}/login")
    time.sleep(2)
    capture_frames(driver, recorder, 3)

    # Fill in login form
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    email_input.send_keys("demo.student@example.com")
    capture_frames(driver, recorder, 2)

    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("DemoPass123!")
    capture_frames(driver, recorder, 2)

    # Submit
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    capture_frames(driver, recorder, 5)

    # Dashboard loaded
    time.sleep(3)
    capture_frames(driver, recorder, 5)


def record_student_dashboard(driver, recorder):
    """Record student dashboard"""
    print("Recording: Student Dashboard")

    # Login first
    driver.get(f"{BASE_URL}/login")
    time.sleep(2)

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    email_input.send_keys("demo.student@example.com")

    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("DemoPass123!")

    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    time.sleep(3)

    # Capture dashboard
    capture_frames(driver, recorder, 10)

    # Scroll down
    driver.execute_script("window.scrollTo(0, 500);")
    capture_frames(driver, recorder, 5)

    driver.execute_script("window.scrollTo(0, 1000);")
    capture_frames(driver, recorder, 5)


def record_instructor_dashboard(driver, recorder):
    """Record instructor dashboard"""
    print("Recording: Instructor Dashboard")

    # Login as instructor
    driver.get(f"{BASE_URL}/login")
    time.sleep(2)

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    email_input.send_keys("demo.instructor@example.com")

    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys("DemoPass123!")

    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    time.sleep(3)

    # Capture dashboard
    capture_frames(driver, recorder, 15)

    # Scroll
    driver.execute_script("window.scrollTo(0, 800);")
    capture_frames(driver, recorder, 5)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 record_demo_simple.py <demo_name>")
        print("\nAvailable demos:")
        print("  student_login")
        print("  student_dashboard")
        print("  instructor_dashboard")
        sys.exit(1)

    demo_name = sys.argv[1]

    # Setup
    print(f"Setting up Chrome WebDriver...")
    driver = setup_chrome()

    # Create recorder
    print(f"Initializing video recorder...")
    recorder = VideoRecorder(
        test_name=demo_name,
        output_dir=VIDEO_DIR,
        fps=VIDEO_FPS,
        resolution=(1920, 1080)
    )
    recorder.start()

    try:
        # Record based on demo name
        if demo_name == "student_login":
            record_student_login(driver, recorder)
        elif demo_name == "student_dashboard":
            record_student_dashboard(driver, recorder)
        elif demo_name == "instructor_dashboard":
            record_instructor_dashboard(driver, recorder)
        else:
            print(f"Unknown demo: {demo_name}")
            sys.exit(1)

        # Stop recording
        recorder.stop()
        print(f"\n✅ Video recorded: {recorder.filepath}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

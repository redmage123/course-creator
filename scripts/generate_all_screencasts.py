#!/usr/bin/env python3
"""
Master Screencast Generator for All Demo Slides

Generates proper screencasts showing ACTUAL pages and interactions for each slide.

Usage:
    python3 generate_all_screencasts.py [slide_number]
    python3 generate_all_screencasts.py all
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

BASE_URL = 'https://localhost:3000'
OUTPUT_DIR = Path('frontend/static/demo/videos')
TEMP_DIR_BASE = Path('/tmp/demo_slides')


def setup_driver():
    """Initialize Chrome WebDriver with cursor support"""
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
        time.sleep(0.5)
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(0.5)
    except:
        pass


def add_cursor_to_element(driver, element):
    """Add visual cursor indicator to element"""
    driver.execute_script("""
        var elem = arguments[0];
        var cursor = document.createElement('div');
        cursor.id = 'demo-cursor';
        cursor.style.cssText = `
            position: fixed;
            width: 24px;
            height: 24px;
            background: rgba(255, 0, 0, 0.5);
            border: 2px solid red;
            border-radius: 50%;
            pointer-events: none;
            z-index: 99999;
            transition: all 0.1s ease;
        `;
        document.body.appendChild(cursor);
        var rect = elem.getBoundingClientRect();
        cursor.style.left = rect.left + rect.width/2 - 12 + 'px';
        cursor.style.top = rect.top + rect.height/2 - 12 + 'px';
    """, element)


def capture_frame(driver, temp_dir, frame_number, duration_frames=1):
    """Capture frame and duplicate"""
    frame_path = temp_dir / f"frame_{frame_number:04d}.png"
    driver.save_screenshot(str(frame_path))

    for i in range(1, duration_frames):
        next_frame = frame_number + i
        subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{next_frame:04d}.png")],
                      capture_output=True, check=True)

    return frame_number + duration_frames


def type_with_delay(element, text, delay=0.05):
    """Type text with natural delay"""
    for char in text:
        element.send_keys(char)
        time.sleep(delay)


def generate_video(temp_dir, output_path, slide_num):
    """Generate video from frames using FFmpeg"""
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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size_kb = output_path.stat().st_size / 1024
        return True, size_kb
    else:
        return False, result.stderr


# Slide generation functions

def generate_slide_01(driver, wait, temp_dir):
    """Slide 1: Introduction - Homepage (15s)"""
    print("📹 Generating Slide 1: Introduction")

    driver.get(f'{BASE_URL}/html/index.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    frame_num = 0

    # Show homepage (0-10s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Scroll to show CTA
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=90)

    # Highlight register button
    try:
        register_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'register') or contains(@href, 'organization-registration')]")
        add_cursor_to_element(driver, register_btn)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)

    return frame_num


def generate_slide_02(driver, wait, temp_dir):
    """Slide 2: Organization Registration with form filling (45s)"""
    print("📹 Generating Slide 2: Organization Registration")

    driver.get(f'{BASE_URL}/html/organization-registration.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    wait.until(EC.presence_of_element_located((By.ID, 'organizationRegistrationForm')))
    time.sleep(0.5)

    frame_num = 0

    # Initial view (0-7s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Fill org name (7-9s)
    org_name = driver.find_element(By.ID, 'orgName')
    org_name.click()
    add_cursor_to_element(driver, org_name)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=10)
    type_with_delay(org_name, 'TechEd Academy', 0.04)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)

    # Fill website (9-11s)
    website = driver.find_element(By.ID, 'orgDomain')
    website.click()
    add_cursor_to_element(driver, website)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=5)
    type_with_delay(website, 'https://techedacademy.org', 0.03)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=25)

    # Fill description (11-14s)
    desc = driver.find_element(By.ID, 'orgDescription')
    desc.click()
    add_cursor_to_element(driver, desc)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=5)
    type_with_delay(desc, 'Tech education platform', 0.04)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=50)

    # Scroll to contact section (14-16s)
    driver.execute_script("window.scrollBy(0, 250);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)

    # Fill address (16-18s)
    address = driver.find_element(By.ID, 'orgStreetAddress')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address)
    time.sleep(0.2)
    address.click()
    add_cursor_to_element(driver, address)
    type_with_delay(address, '123 Innovation Drive', 0.04)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=40)

    # Fill city (18-20s)
    city = driver.find_element(By.ID, 'orgCity')
    city.click()
    add_cursor_to_element(driver, city)
    type_with_delay(city, 'San Francisco', 0.04)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=45)

    # Scroll to admin section (20-22s)
    driver.execute_script("window.scrollBy(0, 350);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)

    # Fill admin username (22-24s)
    username = driver.find_element(By.ID, 'adminUsername')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username)
    time.sleep(0.2)
    username.click()
    add_cursor_to_element(driver, username)
    type_with_delay(username, 'admin', 0.06)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)

    # Fill admin email (24-26s)
    email = driver.find_element(By.ID, 'adminEmail')
    email.click()
    add_cursor_to_element(driver, email)
    type_with_delay(email, 'admin@techedacademy.org', 0.03)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=40)

    # Fill admin password (26-28s)
    password = driver.find_element(By.ID, 'adminPassword')
    password.click()
    add_cursor_to_element(driver, password)
    type_with_delay(password, 'SecurePass123!', 0.05)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=50)

    # Scroll through complete form (28-36s)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=80)

    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=80)

    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=80)

    # Final hold (36-45s)
    driver.execute_script("window.scrollTo(0, 300);")
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=270)

    return frame_num


def generate_slide_03(driver, wait, temp_dir):
    """Slide 3: Projects & Tracks - Org Admin Dashboard (30s)"""
    print("📹 Generating Slide 3: Projects & Tracks")

    driver.get(f'{BASE_URL}/html/org-admin-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Initial dashboard view (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Navigate to Projects tab
    try:
        projects_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Projects') or contains(@href, 'projects')]")
        add_cursor_to_element(driver, projects_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        projects_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Navigate to Tracks section
    try:
        tracks_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Tracks') or contains(@href, 'tracks')]")
        add_cursor_to_element(driver, tracks_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        tracks_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Final view (remaining to 30s)
    remaining = 900 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_04(driver, wait, temp_dir):
    """Slide 4: Adding Instructors - Org Admin Dashboard (30s)"""
    print("📹 Generating Slide 4: Adding Instructors")

    driver.get(f'{BASE_URL}/html/org-admin-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Initial view (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Navigate to Members/Instructors tab
    try:
        members_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Members') or contains(text(), 'Instructors')]")
        add_cursor_to_element(driver, members_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        members_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Show "Add Instructor" button
    try:
        add_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Instructor') or contains(text(), 'Invite')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        time.sleep(0.3)
        add_cursor_to_element(driver, add_btn)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=90)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=90)

    # Show instructor list
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Final hold
    remaining = 900 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_05(driver, wait, temp_dir):
    """Slide 5: Instructor Dashboard - Course Creation (60s)"""
    print("📹 Generating Slide 5: Instructor Dashboard")

    driver.get(f'{BASE_URL}/html/instructor-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Dashboard overview (0-10s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Navigate to "Create Course" section
    try:
        create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Course') or contains(text(), 'New Course')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", create_btn)
        time.sleep(0.3)
        add_cursor_to_element(driver, create_btn)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)
        create_btn.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Show course structure builder
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Show modules/objectives interface
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Final view
    remaining = 1800 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_06(driver, wait, temp_dir):
    """Slide 6: Course Content - Content Editor (45s)"""
    print("📹 Generating Slide 6: Course Content")

    driver.get(f'{BASE_URL}/html/instructor-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Initial view (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Navigate to course content editor
    try:
        content_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Content') or contains(text(), 'Course Content')]")
        add_cursor_to_element(driver, content_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        content_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Show content types (text, code, video)
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Display markdown editor
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Show resource upload
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Final hold
    remaining = 1350 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_07(driver, wait, temp_dir):
    """Slide 7: Enroll Students - Student Enrollment (45s)"""
    print("📹 Generating Slide 7: Enroll Students")

    driver.get(f'{BASE_URL}/html/instructor-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Initial view (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Navigate to student enrollment
    try:
        students_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Students') or contains(text(), 'Enrollment')]")
        add_cursor_to_element(driver, students_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        students_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Show "Add Student" button
    try:
        add_student_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Student') or contains(text(), 'Enroll')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_student_btn)
        time.sleep(0.3)
        add_cursor_to_element(driver, add_student_btn)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=120)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=120)

    # Display CSV upload interface
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Show student roster
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Final hold
    remaining = 1350 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_08(driver, wait, temp_dir):
    """Slide 8: Student Dashboard - Dashboard Overview (30s)"""
    print("📹 Generating Slide 8: Student Dashboard")

    driver.get(f'{BASE_URL}/html/student-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Show enrolled courses (0-10s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Display progress bars
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Show recent activity
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Highlight upcoming deadlines
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Final hold
    remaining = 900 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_09(driver, wait, temp_dir):
    """Slide 9: Course Browsing + Lab Environment (75s)"""
    print("📹 Generating Slide 9: Course Browsing + Lab")

    # Start with course catalog
    driver.get(f'{BASE_URL}/html/courses.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Show course catalog browsing (0-15s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Scroll through catalog
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Click on a course
    try:
        course_card = driver.find_element(By.CSS_SELECTOR, ".course-card, .card, a[href*='course']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", course_card)
        time.sleep(0.3)
        add_cursor_to_element(driver, course_card)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)
        course_card.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Navigate to lab environment
    driver.get(f'{BASE_URL}/html/lab-environment.html')
    time.sleep(2)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=300)

    # Show IDE selector (VSCode, PyCharm, Jupyter, Terminal)
    try:
        ide_selector = driver.find_element(By.CSS_SELECTOR, "#ide-selector, .ide-picker, select[name*='ide']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ide_selector)
        time.sleep(0.3)
        add_cursor_to_element(driver, ide_selector)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)

    # Display active coding environment
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=420)

    # Final hold
    remaining = 2250 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_10(driver, wait, temp_dir):
    """Slide 10: Taking Quizzes - Quiz Page (45s)"""
    print("📹 Generating Slide 10: Taking Quizzes")

    driver.get(f'{BASE_URL}/html/quiz.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Show quiz start screen (0-8s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Display question types (MC, code, short answer)
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Answer a question
    try:
        answer_option = driver.find_element(By.CSS_SELECTOR, "input[type='radio'], .quiz-option, .answer-choice")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", answer_option)
        time.sleep(0.3)
        add_cursor_to_element(driver, answer_option)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)
        answer_option.click()
        time.sleep(0.5)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Show instant feedback
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Display results
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Final hold
    remaining = 1350 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_11(driver, wait, temp_dir):
    """Slide 11: Student Progress - Progress Analytics (30s)"""
    print("📹 Generating Slide 11: Student Progress")

    driver.get(f'{BASE_URL}/html/student-progress.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Navigate to progress/analytics (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Show completion percentages
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Display quiz scores
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=240)

    # Show achievements/badges
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Final hold
    remaining = 900 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_12(driver, wait, temp_dir):
    """Slide 12: Instructor Analytics - Analytics Dashboard (45s)"""
    print("📹 Generating Slide 12: Instructor Analytics")

    driver.get(f'{BASE_URL}/html/instructor-dashboard-modular.html')
    time.sleep(2)
    dismiss_privacy_modal(driver, wait)
    time.sleep(0.5)

    frame_num = 0

    # Initial view (0-5s)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=150)

    # Navigate to analytics dashboard
    try:
        analytics_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Analytics') or contains(text(), 'Reports')]")
        add_cursor_to_element(driver, analytics_tab)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=30)
        analytics_tab.click()
        time.sleep(1)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=180)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=210)

    # Show engagement charts
    driver.execute_script("window.scrollBy(0, 200);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=270)

    # Display student performance metrics
    driver.execute_script("window.scrollBy(0, 300);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=270)

    # Show early warning indicators
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=270)

    # Final hold
    remaining = 1350 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def generate_slide_13(driver, wait, temp_dir):
    """Slide 13: Summary - Quick Montage (15s)"""
    print("📹 Generating Slide 13: Summary")

    frame_num = 0

    # Quick montage of key screens
    screens = [
        f'{BASE_URL}/html/index.html',
        f'{BASE_URL}/html/org-admin-dashboard-modular.html',
        f'{BASE_URL}/html/instructor-dashboard-modular.html',
        f'{BASE_URL}/html/student-dashboard-modular.html',
    ]

    for screen in screens:
        driver.get(screen)
        time.sleep(1)
        dismiss_privacy_modal(driver, wait)
        time.sleep(0.2)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)

    # End on homepage with CTA
    driver.get(f'{BASE_URL}/html/index.html')
    time.sleep(1)
    dismiss_privacy_modal(driver, wait)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)
    frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=90)

    # Highlight "Get Started" button
    try:
        cta_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Get Started') or contains(text(), 'Sign Up') or contains(@href, 'register')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cta_btn)
        time.sleep(0.2)
        add_cursor_to_element(driver, cta_btn)
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)
    except:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=60)

    # Final hold
    remaining = 450 - frame_num
    if remaining > 0:
        frame_num = capture_frame(driver, temp_dir, frame_num, duration_frames=remaining)

    return frame_num


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python3 generate_all_screencasts.py [slide_number|all]")
        sys.exit(1)

    slide_arg = sys.argv[1]

    if slide_arg == 'all':
        slides = list(range(1, 14))
    else:
        slides = [int(slide_arg)]

    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    try:
        for slide_num in slides:
            print(f"\n{'='*80}")
            print(f"GENERATING SLIDE {slide_num:02d}")
            print(f"{'='*80}\n")

            temp_dir = TEMP_DIR_BASE / f"slide_{slide_num:02d}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Descriptive names for each slide
            slide_names = {
                1: 'introduction',
                2: 'org_admin',
                3: 'projects_and_tracks',
                4: 'adding_instructors',
                5: 'instructor_dashboard',
                6: 'adding_course_content',
                7: 'enrolling_students',
                8: 'student_course_browsing',
                9: 'student_login_and_dashboard',
                10: 'taking_quiz',
                11: 'student_progress_analytics',
                12: 'instructor_analytics',
                13: 'summary_and_cta'
            }

            output_path = OUTPUT_DIR / f"slide_{slide_num:02d}_{slide_names[slide_num]}.mp4"

            # Generate frames
            if slide_num == 1:
                total_frames = generate_slide_01(driver, wait, temp_dir)
            elif slide_num == 2:
                total_frames = generate_slide_02(driver, wait, temp_dir)
            elif slide_num == 3:
                total_frames = generate_slide_03(driver, wait, temp_dir)
            elif slide_num == 4:
                total_frames = generate_slide_04(driver, wait, temp_dir)
            elif slide_num == 5:
                total_frames = generate_slide_05(driver, wait, temp_dir)
            elif slide_num == 6:
                total_frames = generate_slide_06(driver, wait, temp_dir)
            elif slide_num == 7:
                total_frames = generate_slide_07(driver, wait, temp_dir)
            elif slide_num == 8:
                total_frames = generate_slide_08(driver, wait, temp_dir)
            elif slide_num == 9:
                total_frames = generate_slide_09(driver, wait, temp_dir)
            elif slide_num == 10:
                total_frames = generate_slide_10(driver, wait, temp_dir)
            elif slide_num == 11:
                total_frames = generate_slide_11(driver, wait, temp_dir)
            elif slide_num == 12:
                total_frames = generate_slide_12(driver, wait, temp_dir)
            elif slide_num == 13:
                total_frames = generate_slide_13(driver, wait, temp_dir)
            else:
                print(f"⚠️  Slide {slide_num} not implemented")
                continue

            # Generate video
            print(f"\n🎞️  Generating video...")
            success, result = generate_video(temp_dir, output_path, slide_num)

            if success:
                duration = total_frames / 30
                print(f"✅ Video created: {output_path}")
                print(f"   Size: {result:.1f}KB")
                print(f"   Duration: {duration:.1f}s ({total_frames} frames)")
            else:
                print(f"❌ Video generation failed: {result}")

            # Cleanup
            subprocess.run(['rm', '-rf', str(temp_dir)], capture_output=True)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generate Slide 5 - Course Generation with AI

Duration: 30 seconds
Shows: Organization admin accessing Courses tab and using course generation UI
"""

import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = "/tmp/slide5_course_generation"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_05_course_generation.mp4"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70, flush=True)
print("SLIDE 5: COURSE GENERATION WITH AI", flush=True)
print("=" * 70, flush=True)

# Setup Chrome
print("Setting up Chrome options...", flush=True)
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

print("\nInitializing WebDriver...", flush=True)
chromedriver_path = "/home/bbrelin/.wdm/drivers/chromedriver/linux64/141.0.7390.76/chromedriver-linux64/chromedriver"
print(f"Using chromedriver: {chromedriver_path}", flush=True)
service = Service(chromedriver_path)
print("Creating Chrome driver...", flush=True)
driver = webdriver.Chrome(service=service, options=options)
print("Driver created! Setting window size...", flush=True)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)
print("WebDriver ready!", flush=True)

screenshot_count = 0

CURSOR_SCRIPT = """
const existingCursor = document.getElementById('demo-cursor');
if (existingCursor) existingCursor.remove();

const cursor = document.createElement('div');
cursor.id = 'demo-cursor';
cursor.style.position = 'fixed';
cursor.style.width = '24px';
cursor.style.height = '24px';
cursor.style.border = '3px solid #ff0000';
cursor.style.borderRadius = '50%';
cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
cursor.style.pointerEvents = 'none';
cursor.style.zIndex = '999999';
cursor.style.transition = 'all 0.1s ease';
cursor.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.5)';
document.body.appendChild(cursor);

window.moveCursor = function(x, y) {
    cursor.style.left = x + 'px';
    cursor.style.top = y + 'px';
};

window.moveCursor(window.innerWidth / 2, window.innerHeight / 2);
"""

def inject_cursor():
    driver.execute_script(CURSOR_SCRIPT)

def move_cursor_to_element(element):
    locations = element.locations
    size = element.size
    target_x = locations['x'] + size['width'] // 2
    target_y = locations['y'] + size['height'] // 2
    driver.execute_script(f"window.moveCursor({target_x}, {target_y});")

def capture(label, frames=30):
    global screenshot_count
    start_count = screenshot_count + 1
    for i in range(frames):
        screenshot_count += 1
        path = os.path.join(SCREENSHOTS_DIR, f"frame_{screenshot_count:05d}.png")
        driver.save_screenshot(path)
    print(f"{start_count:5d}. {label} ({frames} frames)")
    time.sleep(frames / 30)

try:
    print("\n1. Setting up authentication...")
    driver.get(f"{BASE_URL}/html/index.html")
    time.sleep(1)

    # Set up localStorage auth
    driver.execute_script("""
        localStorage.setItem('authToken', 'demo-org-admin-token');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 1,
            email: 'admin@example.com',
            role: 'organization_admin',
            organization_id: 1,
            name: 'Demo Admin'
        }));
    """)

    print("\n2. Loading org admin dashboard...")
    driver.get(f"{BASE_URL}/html/org-admin-dashboard.html?org_id=1")
    time.sleep(3)
    inject_cursor()
    capture("Dashboard loaded", 30)

    print("\n3. Clicking Courses tab...")
    courses_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='courses']")))
    move_cursor_to_element(courses_tab)
    capture("Cursor on Courses tab", 20)
    courses_tab.click()
    time.sleep(0.5)
    capture("Courses tab opened", 45)

    print("\n4. Clicking Generate Course button...")
    generate_btn = wait.until(EC.element_to_be_clickable((By.ID, "generateCourseBtn")))
    move_cursor_to_element(generate_btn)
    capture("Cursor on Generate Course button", 20)
    generate_btn.click()
    time.sleep(2)  # Wait for modal to fully render
    capture("Generate Course modal opened", 45)

    print("\n5. Filling course title...")
    # Wait for modal to be stable and find fresh element
    time.sleep(1)
    title_input = driver.find_element(By.ID, "generateCourseTitle")
    move_cursor_to_element(title_input)
    capture("Cursor on title field", 15)

    # Use JavaScript to interact with element
    driver.execute_script("arguments[0].value = '';", title_input)
    capture("Title field active", 10)

    # Type course title using JavaScript to avoid stale references
    course_title = "Machine Learning Fundamentals"
    for i, char in enumerate(course_title):
        driver.execute_script(f"document.getElementById('generateCourseTitle').value += '{char}';")
        capture(f"Typing: {char}", 2)
    capture("Course title entered", 30)

    print("\n6. Filling description...")
    description_field = driver.find_element(By.ID, "generateCourseDescription")
    move_cursor_to_element(description_field)
    capture("Cursor on description field", 15)

    # Use JavaScript to fill description
    driver.execute_script("""
        document.getElementById('generateCourseDescription').value =
            'Learn the fundamentals of machine learning including supervised and unsupervised learning';
    """)
    capture("Description entered", 45)

    print("\n7. Selecting category...")
    category_select = driver.find_element(By.ID, "generateCourseCategory")
    move_cursor_to_element(category_select)
    capture("Cursor on category dropdown", 15)

    # Select Data Science category
    driver.execute_script("""
        const select = document.getElementById('generateCourseCategory');
        select.value = 'Data Science';
        select.dispatchEvent(new Event('change'));
    """)
    capture("Category selected", 25)

    print("\n8. Selecting difficulty...")
    difficulty_select = driver.find_element(By.ID, "generateCourseDifficulty")
    move_cursor_to_element(difficulty_select)
    capture("Cursor on difficulty dropdown", 15)

    # Select Intermediate level
    driver.execute_script("""
        const select = document.getElementById('generateCourseDifficulty');
        select.value = 'intermediate';
        select.dispatchEvent(new Event('change'));
    """)
    capture("Difficulty selected", 25)

    print("\n9. Submitting form...")
    submit_btn = driver.find_element(By.ID, "submitGenerateCourse")
    move_cursor_to_element(submit_btn)
    capture("Cursor on Generate button", 20)
    submit_btn.click()
    time.sleep(1)
    capture("Course generation started", 60)

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count/30:.1f}s)")

    print("\n10. Creating video...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", os.path.join(SCREENSHOTS_DIR, "frame_%05d.png"),
        "-vf", "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-profile:v", "baseline",
        "-level", "3.0",
        VIDEO_OUTPUT
    ]

    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
    size = os.path.getsize(VIDEO_OUTPUT)
    print(f"✓ Video created: {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"  Duration: {screenshot_count/30:.1f}s")

finally:
    driver.quit()

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)

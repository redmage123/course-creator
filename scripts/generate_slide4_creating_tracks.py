#!/usr/bin/env python3
"""
Generate Slide 4 - Creating Tracks

Duration: 30 seconds
Shows: Organization admin creating a new learning track
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
SCREENSHOTS_DIR = "/tmp/slide4_creating_tracks"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_04_creating_tracks.mp4"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70, flush=True)
print("SLIDE 4: CREATING TRACKS", flush=True)
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
    print("\n1. Loading org admin dashboard...")
    driver.get(f"{BASE_URL}/html/org-admin-dashboard-demo.html")
    time.sleep(2)
    inject_cursor()
    capture("Dashboard loaded", 30)

    print("\n2. Clicking Tracks tab...")
    tracks_tab = wait.until(EC.element_to_be_clickable((By.ID, "nav-tracks")))
    move_cursor_to_element(tracks_tab)
    capture("Cursor on Tracks tab", 20)
    tracks_tab.click()
    time.sleep(0.3)
    capture("Tracks view opened", 30)

    print("\n3. Clicking Create New Track button...")
    create_track_btn = wait.until(EC.element_to_be_clickable((By.ID, "createTrackBtn")))
    move_cursor_to_element(create_track_btn)
    capture("Cursor on Create Track button", 20)
    create_track_btn.click()
    time.sleep(0.3)
    capture("Create Track modal opened", 30)

    print("\n4. Filling track name...")
    track_name_input = wait.until(EC.presence_of_element_located((By.ID, "trackName")))
    move_cursor_to_element(track_name_input)
    capture("Cursor on track name field", 15)
    track_name_input.click()
    capture("Name field active", 10)

    # Type track name character by character
    track_name = "Business Analytics"
    for char in track_name:
        track_name_input.send_keys(char)
        capture(f"Typing: {char}", 2)
    capture("Track name entered", 20)

    print("\n5. Selecting project...")
    project_select = driver.find_element(By.ID, "trackProject")
    move_cursor_to_element(project_select)
    capture("Cursor on project dropdown", 15)
    project_select.click()
    time.sleep(0.2)
    capture("Project dropdown opened", 15)

    # Select Data Science project
    driver.execute_script("""
        const select = document.getElementById('trackProject');
        select.value = 'data-science';
        select.dispatchEvent(new Event('change'));
    """)
    capture("Project selected", 20)

    print("\n6. Selecting level...")
    level_select = driver.find_element(By.ID, "trackLevel")
    move_cursor_to_element(level_select)
    capture("Cursor on level dropdown", 15)
    level_select.click()
    time.sleep(0.2)
    capture("Level dropdown opened", 15)

    # Select Intermediate level
    driver.execute_script("""
        const select = document.getElementById('trackLevel');
        select.value = 'intermediate';
        select.dispatchEvent(new Event('change'));
    """)
    capture("Level selected", 20)

    print("\n7. Adding description...")
    description_field = driver.find_element(By.ID, "trackDescription")
    move_cursor_to_element(description_field)
    capture("Cursor on description field", 15)
    description_field.click()
    description_field.send_keys("Learn data analysis, visualization, and business intelligence tools")
    capture("Description entered", 30)

    print("\n8. Submitting form...")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "#createTrackForm .btn-primary")
    move_cursor_to_element(submit_btn)
    capture("Cursor on Create Track button", 20)
    submit_btn.click()
    time.sleep(0.5)
    capture("Track created successfully", 60)

    print("\n9. Viewing new track in list...")
    capture("Track appears in tracks list", 60)

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

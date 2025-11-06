#!/usr/bin/env python3
"""
Generate Slide 4 - Adding Instructors

Duration: 30 seconds
Shows: Organization admin viewing instructor management interface
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
SCREENSHOTS_DIR = "/tmp/slide4_adding_instructors"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_04_adding_instructors.mp4"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70, flush=True)
print("SLIDE 4: ADDING INSTRUCTORS", flush=True)
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
    capture("Dashboard loaded", 45)

    print("\n2. Navigating to Members tab...")
    members_tab = wait.until(EC.element_to_be_clickable((By.ID, "nav-members")))
    move_cursor_to_element(members_tab)
    capture("Cursor on Members tab", 30)
    members_tab.click()
    time.sleep(0.5)
    capture("Members view opened", 60)

    print("\n3. Viewing instructor list...")
    capture("Showing instructors", 90)

    print("\n4. Highlighting instructor management...")
    # Scroll to show more instructors
    driver.execute_script("window.scrollTo(0, 200);")
    capture("Scrolled view", 60)

    print("\n5. Final overview...")
    capture("Complete instructor management interface", 90)

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count/30:.1f}s)")

    print("\n6. Creating video...")
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

#!/usr/bin/env python3
"""
Generate Slide 5 - AI Assistant Natural Language Management

Shows AI assistant creating a track via natural language
Duration: ~50 seconds to match audio
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
SCREENSHOTS_DIR = "/tmp/slide5_ai_assistant"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_05_ai_assistant.mp4"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("SLIDE 5: AI ASSISTANT - NATURAL LANGUAGE MANAGEMENT")
print("=" * 70)

# Setup Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

print("\nInitializing WebDriver...")
chromedriver_path = "/home/bbrelin/.wdm/drivers/chromedriver/linux64/141.0.7390.76/chromedriver-linux64/chromedriver"
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)
print("WebDriver ready!")

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
    print("\n1. Loading dashboard with AI button visible...")
    driver.get(f"{BASE_URL}/html/org-admin-dashboard-demo.html")
    time.sleep(2)
    inject_cursor()
    capture("Dashboard loaded with AI button", 60)

    print("\n2. Moving cursor to AI assistant button...")
    ai_button = wait.until(EC.element_to_be_clickable((By.ID, "aiAssistantBtn")))
    move_cursor_to_element(ai_button)
    capture("Cursor on AI assistant button", 30)

    print("\n3. Clicking AI assistant button...")
    ai_button.click()
    time.sleep(0.5)
    capture("AI panel sliding up", 60)

    print("\n4. Moving cursor to input field...")
    ai_input = wait.until(EC.element_to_be_clickable((By.ID, "aiInput")))
    move_cursor_to_element(ai_input)
    capture("Cursor on input field", 20)
    ai_input.click()
    capture("Input field focused", 15)

    print("\n5. Typing natural language request...")
    message = "Create an intermediate track called Machine Learning Basics for the Data Science project"
    for char in message:
        ai_input.send_keys(char)
        capture(f"Typing: {char}", 2)
    capture("Request typed", 30)

    print("\n6. Moving cursor to send button...")
    send_btn = driver.find_element(By.ID, "aiSendBtn")
    move_cursor_to_element(send_btn)
    capture("Cursor on send button", 20)

    print("\n7. Clicking send button...")
    send_btn.click()
    time.sleep(0.5)
    capture("Request sent", 30)

    print("\n8. AI response appearing...")
    capture("AI processing", 60)
    # Simulate AI response by injecting message
    driver.execute_script("""
        const messagesDiv = document.getElementById('aiMessages');
        const aiMsg = document.createElement('div');
        aiMsg.style.cssText = 'background: #f0f0f0; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;';
        aiMsg.innerHTML = '<strong style="color: #667eea;">AI Assistant:</strong><br>I\'ve created the intermediate track "Machine Learning Basics" in the Data Science Foundations project. The track is now available in your tracks list.';
        messagesDiv.appendChild(aiMsg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    """)
    capture("AI response shown", 90)

    print("\n9. Showing track in list...")
    # Close AI panel to show tracks
    driver.execute_script("""
        document.getElementById('aiAssistantPanel').classList.remove('open');
    """)
    time.sleep(0.5)
    # Click Tracks tab
    tracks_tab = driver.find_element(By.ID, "nav-tracks")
    tracks_tab.click()
    time.sleep(1)
    capture("Track appears in tracks list", 90)

    print("\n10. Final hold...")
    capture("Complete", 660)  # Adjusted to match ~50s audio

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count / 30:.1f}s)")

    print("\n11. Creating video...")
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
    print(f"✓ Video created: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
    print(f"  Duration: {screenshot_count / 30:.1f}s")

finally:
    driver.quit()

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)

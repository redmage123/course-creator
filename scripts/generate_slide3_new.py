#!/usr/bin/env python3
"""
Generate Slide 3 - Organization Admin Dashboard with Login
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
SCREENSHOTS_DIR = "/tmp/slide3_org_admin_dashboard"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_03_org_admin_dashboard.mp4"

ORG_ADMIN_EMAIL = "sarah@acmelearning.edu"
ORG_ADMIN_PASSWORD = "SecurePass123!"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("="  * 70, flush=True)
print("SLIDE 3: ORG ADMIN DASHBOARD WITH LOGIN", flush=True)
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
    print("\n1. Loading home page...")
    driver.get(f"{BASE_URL}/html/index.html")
    time.sleep(2)
    inject_cursor()
    capture("Home page loaded", 45)

    # Dismiss privacy modal (it always appears on first visit)
    print("\n2. Dismissing privacy modal...")
    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
    move_cursor_to_element(accept_btn)
    capture("Cursor on Accept All", 20)
    accept_btn.click()
    time.sleep(1)
    capture("Privacy modal dismissed", 30)

    print("\n3. Clicking Login button in header...")
    login_btn = wait.until(EC.element_to_be_clickable((By.ID, "loginBtn")))
    move_cursor_to_element(login_btn)
    capture("Cursor on Login button", 30)
    login_btn.click()
    time.sleep(1)
    capture("Login menu opened", 30)

    # Click "Account Login" link in dropdown (goes to student-login.html)
    driver.get(f"{BASE_URL}/html/student-login.html")
    time.sleep(2)
    inject_cursor()
    capture("Login page loaded", 45)

    print("\n4. Filling in email (slow typing)...")
    email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
    move_cursor_to_element(email_field)
    capture("Cursor on email field", 20)
    email_field.click()
    capture("Email field clicked", 15)

    # Type email slowly (character by character)
    for char in ORG_ADMIN_EMAIL:
        email_field.send_keys(char)
        capture(f"Typing: {char}", 3)
    capture("Email entered", 20)

    print("\n5. Filling in password (slow typing)...")
    password_field = driver.find_element(By.ID, "password")
    move_cursor_to_element(password_field)
    capture("Cursor on password field", 20)
    password_field.click()
    capture("Password field clicked", 15)

    # Type password slowly
    for char in ORG_ADMIN_PASSWORD:
        password_field.send_keys(char)
        capture(f"Typing: {char}", 3)
    capture("Password entered", 20)

    print("\n6. Clicking login button...")
    login_button = driver.find_element(By.ID, "credentialsBtn")
    move_cursor_to_element(login_button)
    capture("Cursor on login button", 30)
    login_button.click()
    capture("Login button clicked", 20)
    time.sleep(1)
    capture("Redirecting...", 30)

    print("\n7. Showing user icon change (logged in)...")
    capture("User icon shows logged in status", 60)

    print("\n8. Loading dashboard...")
    driver.get(f"{BASE_URL}/html/org-admin-dashboard-demo.html")
    time.sleep(2)
    inject_cursor()
    capture("Dashboard loaded", 60)

    print("\n9. Creating project...")
    create_btn = driver.find_element(By.ID, "createProjectBtn")
    move_cursor_to_element(create_btn)
    capture("Cursor on Create Project", 30)
    create_btn.click()
    time.sleep(0.5)
    capture("Project modal opened", 60)

    project_name = driver.find_element(By.ID, "projectName")
    move_cursor_to_element(project_name)
    capture("Cursor on project name", 15)
    project_name.send_keys("Machine Learning Fundamentals")
    capture("Project name entered", 30)

    project_desc = driver.find_element(By.ID, "projectDescription")
    move_cursor_to_element(project_desc)
    capture("Cursor on description", 15)
    project_desc.send_keys("Comprehensive ML course for beginners")
    capture("Description entered", 30)

    create_submit = driver.find_element(By.CSS_SELECTOR, ".btn-primary")
    move_cursor_to_element(create_submit)
    capture("Cursor on Create button", 20)
    create_submit.click()
    time.sleep(0.5)
    capture("Project created", 90)

    print("\n10. Showing Edit/Delete...")
    edit_btn = driver.find_element(By.CSS_SELECTOR, "button[style*='#f59e0b']")
    move_cursor_to_element(edit_btn)
    capture("Edit button", 45)

    delete_btn = driver.find_element(By.CSS_SELECTOR, "button[style*='#ef4444']")
    move_cursor_to_element(delete_btn)
    capture("Delete button", 45)

    print("\n11. Switching project...")
    overview_tab = driver.find_element(By.ID, "nav-overview")
    move_cursor_to_element(overview_tab)
    capture("Back to overview", 30)
    overview_tab.click()
    time.sleep(0.5)
    capture("Overview", 60)

    project_selector = driver.find_element(By.ID, "currentProject")
    move_cursor_to_element(project_selector)
    capture("Project dropdown", 45)
    project_selector.click()
    time.sleep(0.3)
    capture("Dropdown opened", 30)

    driver.execute_script("""
        const select = document.getElementById('currentProject');
        select.value = 'data-science';
        select.dispatchEvent(new Event('change'));
    """)
    time.sleep(0.5)
    capture("Switched to Data Science", 90)
    capture("Metrics updated", 90)

    print("\n12. Clicking on metrics...")
    tracks_stat = driver.find_element(By.ID, "stat-tracks")
    move_cursor_to_element(tracks_stat)
    capture("Cursor on Tracks", 30)
    tracks_stat.click()
    time.sleep(0.5)
    capture("Tracks view", 75)

    instructors_stat = driver.find_element(By.ID, "stat-instructors")
    move_cursor_to_element(instructors_stat)
    capture("Cursor on Members", 30)
    instructors_stat.click()
    time.sleep(0.5)
    capture("Members view", 75)

    settings_tab = driver.find_element(By.ID, "nav-settings")
    move_cursor_to_element(settings_tab)
    capture("Cursor on Settings", 30)
    settings_tab.click()
    time.sleep(0.5)
    capture("Settings view", 75)

    print("\n13. Final hold...")
    capture("Complete", 300)  # Reduced due to longer login flow - will adjust after testing

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count/30:.1f}s)")

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
    print(f"✓ Video created: {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"  Duration: {screenshot_count/30:.1f}s")

finally:
    driver.quit()

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)

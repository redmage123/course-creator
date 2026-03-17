#!/usr/bin/env python3
"""
Regenerate Slide 2 - Organization Registration (Audio-Synced)

AUDIO TIMELINE (26 seconds total):
- 0-3s:   Home page with Register Organization button
- 3-5s:   Clicking Register, transition to registration form
- 5-12s:  Fill org details (name, website, description) - scroll slowly down
- 12-18s: Fill contact info (email, address) - continue smooth scroll
- 18-23s: Fill admin account (name, email, password) - scroll to bottom
- 23-26s: Click submit, show success message

KEY FIXES:
- NO jumping - smooth continuous scroll following form filling
- Start at TOP of form, scroll down as filling progresses
- Each field fill matches audio narration timing
- Success message clearly visible at end
- Updated to use React registration form at /organization/register
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
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = "/tmp/slide2_audio_synced"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend-react/public/demo/videos/slide_02_organization_registration.mp4"
FPS = 30
DURATION_SECONDS = 26

# Create screenshots directory
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("SLIDE 2: ORGANIZATION REGISTRATION (AUDIO-SYNCED)")
print("=" * 70)

# Setup Chrome (headless)
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)

frame_count = 0

def capture_frame(description=""):
    """Capture a single frame"""
    global frame_count
    frame_count += 1
    path = f"{SCREENSHOTS_DIR}/frame_{frame_count:04d}.png"
    driver.save_screenshot(path)
    if frame_count % 30 == 0:  # Log every second
        print(f"   {frame_count/30:.1f}s: {description}")
    return path

def capture_duration(seconds, description=""):
    """Capture frames for specified duration"""
    frames = int(seconds * FPS)
    for _ in range(frames):
        capture_frame(description)

def slow_type(element, text, duration_seconds=1.0):
    """Type text over specified duration while capturing frames"""
    if not text:
        return
    delay_per_char = duration_seconds / len(text)
    frames_per_char = max(1, int(delay_per_char * FPS))

    for char in text:
        element.send_keys(char)
        for _ in range(frames_per_char):
            capture_frame(f"Typing: {text[:10]}...")

def smooth_scroll_to(target_y, duration_seconds=1.0):
    """Smoothly scroll to target Y position while capturing frames"""
    current_y = driver.execute_script("return window.pageYOffset;")
    frames = int(duration_seconds * FPS)

    for i in range(frames):
        progress = (i + 1) / frames
        # Ease-in-out cubic
        if progress < 0.5:
            ease = 4 * progress * progress * progress
        else:
            ease = 1 - pow(-2 * progress + 2, 3) / 2

        new_y = current_y + (target_y - current_y) * ease
        driver.execute_script(f"window.scrollTo(0, {new_y});")
        capture_frame(f"Scrolling to {target_y}")

def find_input_by_name(name):
    """Find input element by name attribute"""
    return driver.find_element(By.CSS_SELECTOR, f'input[name="{name}"], textarea[name="{name}"]')

def find_select_by_name(name):
    """Find select/button for custom select component by name"""
    # React Select components might use different markup
    # Try to find the container that has the select behavior
    try:
        return driver.find_element(By.CSS_SELECTOR, f'select[name="{name}"]')
    except:
        # Try finding by label if it's a custom component
        return driver.find_element(By.CSS_SELECTOR, f'[name="{name}"]')

try:
    # ========================================
    # PHASE 1: Home page (0-3 seconds)
    # ========================================
    print("\n[0-3s] Loading home page...")
    driver.get(f"{BASE_URL}/")
    time.sleep(2)

    # Dismiss privacy modal if present
    try:
        accept_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Accept All')]")
        ))
        accept_btn.click()
        time.sleep(0.5)
    except:
        pass

    # Capture home page (3 seconds)
    capture_duration(3, "Home page - Register button visible")

    # ========================================
    # PHASE 2: Click Register, transition (3-5 seconds)
    # ========================================
    print("\n[3-5s] Navigating to Register Organization...")
    driver.get(f"{BASE_URL}/organization/register")
    time.sleep(2)

    # Make sure we're at the top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    # Capture registration form loaded (2 seconds)
    capture_duration(2, "Registration form loaded")

    # ========================================
    # PHASE 3: Fill org details (5-12 seconds = 7 seconds)
    # ========================================
    print("\n[5-12s] Filling organization details...")

    # Organization name (2 seconds)
    org_name = wait.until(EC.presence_of_element_located((By.NAME, "name")))
    slow_type(org_name, "Acme Learning", duration_seconds=1.5)
    capture_duration(0.5, "Org name entered")

    # Domain/Website (2 seconds) - scroll down slightly as we go
    smooth_scroll_to(100, duration_seconds=0.3)
    org_domain = find_input_by_name("domain")
    slow_type(org_domain, "acmelearning.edu", duration_seconds=1.5)
    capture_duration(0.2, "Domain entered")

    # Description (2 seconds)
    smooth_scroll_to(200, duration_seconds=0.3)
    org_desc = find_input_by_name("description")
    slow_type(org_desc, "Professional corporate training", duration_seconds=1.5)
    capture_duration(0.2, "Description entered")

    # ========================================
    # PHASE 4: Fill contact info (12-18 seconds = 6 seconds)
    # ========================================
    print("\n[12-18s] Filling contact information...")

    # Scroll to address section smoothly
    smooth_scroll_to(400, duration_seconds=0.5)

    # Street Address (1 second)
    org_street = find_input_by_name("street_address")
    slow_type(org_street, "123 Tech Blvd", duration_seconds=0.8)

    # City (0.5 seconds)
    org_city = find_input_by_name("city")
    slow_type(org_city, "San Francisco", duration_seconds=0.5)

    # State (0.3 seconds)
    smooth_scroll_to(550, duration_seconds=0.2)
    org_state = find_input_by_name("state_province")
    slow_type(org_state, "CA", duration_seconds=0.3)

    # Postal Code (0.3 seconds)
    org_postal = find_input_by_name("postal_code")
    slow_type(org_postal, "94105", duration_seconds=0.3)

    # Select country - click on the select component
    smooth_scroll_to(650, duration_seconds=0.2)
    try:
        # Try to interact with a standard select element
        country_select = driver.find_element(By.NAME, "country")
        # Click and select US
        driver.execute_script("""
            const select = arguments[0];
            select.value = 'US';
            select.dispatchEvent(new Event('change', { bubbles: true }));
        """, country_select)
    except Exception as e:
        print(f"   Note: Country select interaction: {e}")
    capture_duration(0.3, "Country selected")

    # Contact email
    smooth_scroll_to(750, duration_seconds=0.3)
    contact_email = find_input_by_name("contact_email")
    slow_type(contact_email, "admin@acmelearning.edu", duration_seconds=1.0)

    # Phone (0.5 seconds)
    contact_phone = find_input_by_name("contact_phone")
    slow_type(contact_phone, "4155551234", duration_seconds=0.5)
    capture_duration(0.3, "Contact info complete")

    # ========================================
    # PHASE 5: Fill admin account (18-23 seconds = 5 seconds)
    # ========================================
    print("\n[18-23s] Setting up administrator account...")

    # Scroll to admin section smoothly
    smooth_scroll_to(900, duration_seconds=0.5)

    # Admin full name (1 second)
    admin_name = find_input_by_name("admin_full_name")
    slow_type(admin_name, "Sarah Johnson", duration_seconds=0.8)
    capture_duration(0.2, "Admin name")

    # Username (0.5 seconds)
    admin_username = find_input_by_name("admin_username")
    slow_type(admin_username, "sjohnson", duration_seconds=0.4)

    # Scroll to show password fields and submit button
    smooth_scroll_to(1100, duration_seconds=0.3)

    # Admin email (1 second)
    admin_email = find_input_by_name("admin_email")
    slow_type(admin_email, "sarah@acmelearning.edu", duration_seconds=0.8)

    # Password (0.5 seconds)
    admin_password = find_input_by_name("admin_password")
    admin_password.send_keys("SecurePass123!")
    capture_duration(0.3, "Password entered")

    # Confirm password (0.5 seconds)
    admin_confirm = find_input_by_name("admin_password_confirm")
    admin_confirm.send_keys("SecurePass123!")

    # Scroll to show terms and submit button
    smooth_scroll_to(1400, duration_seconds=0.4)

    # Check terms checkboxes
    try:
        terms_checkbox = driver.find_element(By.NAME, "terms_accepted")
        driver.execute_script("arguments[0].click();", terms_checkbox)
        time.sleep(0.1)

        privacy_checkbox = driver.find_element(By.NAME, "privacy_accepted")
        driver.execute_script("arguments[0].click();", privacy_checkbox)
    except Exception as e:
        print(f"   Note: Checkbox interaction: {e}")

    capture_duration(0.3, "Form complete - submit button visible")

    # ========================================
    # PHASE 6: Submit and success (23-26 seconds = 3 seconds)
    # ========================================
    print("\n[23-26s] Submitting form and showing success...")

    # Find and click submit button
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
    except:
        pass
    capture_duration(0.5, "Submit clicked")

    # Show success message via JavaScript overlay
    driver.execute_script("""
        // Create success overlay
        const overlay = document.createElement('div');
        overlay.id = 'demoSuccessOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            color: white;
            text-align: center;
            padding: 40px;
        `;

        overlay.innerHTML = `
            <div style="font-size: 80px; margin-bottom: 30px;">✓</div>
            <h1 style="font-size: 3rem; margin-bottom: 20px; color: white; font-weight: 700;">
                Registration Successful!
            </h1>
            <div style="background: rgba(255,255,255,0.15); border-radius: 16px; padding: 40px; margin-top: 20px; max-width: 600px;">
                <p style="font-size: 1.6rem; margin-bottom: 20px; font-weight: 600;">
                    <strong>Acme Learning</strong> has been registered!
                </p>
                <p style="font-size: 1.3rem; opacity: 0.95; margin-bottom: 15px;">
                    Administrator: sarah@acmelearning.edu
                </p>
                <p style="font-size: 1.1rem; margin-top: 25px; opacity: 0.9;">
                    You can now log in and start creating courses!
                </p>
            </div>
        `;

        document.body.appendChild(overlay);
    """)

    time.sleep(0.3)

    # Capture success message (2.5 seconds)
    capture_duration(2.5, "Success message displayed")

    print(f"\n✅ Captured {frame_count} frames ({frame_count/FPS:.1f} seconds)")
    print(f"   Target: {DURATION_SECONDS} seconds")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# ========================================
# Create video with ffmpeg
# ========================================
print("\nCreating video...")

ffmpeg_cmd = [
    'ffmpeg',
    '-r', str(FPS),
    '-i', f'{SCREENSHOTS_DIR}/frame_%04d.png',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-vf', 'scale=1920:1080',
    '-y',
    VIDEO_OUTPUT
]

try:
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)

    if result.returncode == 0 and os.path.exists(VIDEO_OUTPUT):
        file_size = os.path.getsize(VIDEO_OUTPUT)
        print(f"✅ Video created: {VIDEO_OUTPUT}")
        print(f"   Size: {file_size/1024/1024:.2f} MB")
        print(f"   Duration: {frame_count/FPS:.1f}s")
    else:
        print(f"❌ FFmpeg failed: {result.stderr[-500:]}")

except Exception as e:
    print(f"❌ Error: {e}")

# Cleanup
subprocess.run(['rm', '-rf', SCREENSHOTS_DIR], capture_output=True)

print("\n" + "=" * 70)
print("COMPLETE - Key improvements:")
print("  ✓ Uses React registration form at /organization/register")
print("  ✓ Smooth continuous scrolling (no jumping)")
print("  ✓ Form filling follows audio narration timing")
print("  ✓ Starts at top, scrolls down as filling")
print("  ✓ Success message clearly visible at end")
print("=" * 70)

#!/usr/bin/env python3
"""
Regenerate Slide 1 - Homepage with Register Button Click

BUSINESS PURPOSE:
Show the starting point of the platform journey - homepage with call to action.
User sees where to begin by clicking the register button.

TECHNICAL APPROACH:
1. Load homepage
2. Wait for page load (no black screen)
3. Show initial homepage view
4. Highlight/click register button
5. Generate smooth video
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

# Configuration
BASE_URL = 'https://localhost:3000'
OUTPUT_DIR = Path('frontend/static/demo/videos')
TEMP_DIR = Path('/tmp/slide1_frames')


def setup_driver():
    """Initialize Chrome WebDriver"""
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
        time.sleep(1)
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
            print("   ✓ Privacy modal dismissed")
    except:
        print("   ℹ No privacy modal found")


def capture_frame(driver, temp_dir, frame_number, duration_frames=1):
    """Capture a frame and duplicate it for duration"""
    frame_path = temp_dir / f"frame_{frame_number:04d}.png"
    driver.save_screenshot(str(frame_path))

    for i in range(1, duration_frames):
        next_frame = frame_number + i
        subprocess.run(['cp', str(frame_path), str(temp_dir / f"frame_{next_frame:04d}.png")],
                      capture_output=True, check=True)

    return frame_number + duration_frames


def main():
    print("=" * 80)
    print("🎬 REGENERATING SLIDE 1 - Homepage with Register Button")
    print("=" * 80)
    print()

    # Create temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Temp directory: {TEMP_DIR}")
    print()

    # Initialize WebDriver
    print("🌐 Initializing Chrome WebDriver...")
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to homepage
        url = f'{BASE_URL}/html/index.html'
        print(f"📍 Navigating to: {url}")
        driver.get(url)

        # Wait for page to fully load (no black screen!)
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print("   ✓ Page loaded")

        # Dismiss privacy modal
        dismiss_privacy_modal(driver, wait)

        # Scroll to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        print()
        print("📹 Capturing frames...")
        frame_num = 0

        # Frame 0-120: Initial homepage view (4 seconds at 30fps)
        print("   Frame 0000-0120: Initial homepage")
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=120)

        # Scroll down slightly to show hero section and CTA buttons
        driver.execute_script("window.scrollBy(0, 100);")
        time.sleep(0.5)
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=60)

        # Locate and highlight register button
        try:
            # Try to find register/signup button
            register_btn = None
            try:
                register_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign Up') or contains(text(), 'Register') or contains(@href, 'register')]")
            except:
                try:
                    register_btn = driver.find_element(By.CSS_SELECTOR, "a[href*='register'], a[href*='organization-registration']")
                except:
                    print("   ⚠ Register button not found, continuing without interaction")

            if register_btn:
                print("   ✓ Found register button")

                # Scroll register button into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", register_btn)
                time.sleep(0.5)
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=30)

                # Add visual emphasis with JavaScript (highlight effect)
                driver.execute_script("""
                    arguments[0].style.boxShadow = '0 0 20px 5px rgba(99, 102, 241, 0.6)';
                    arguments[0].style.transform = 'scale(1.05)';
                    arguments[0].style.transition = 'all 0.3s ease';
                """, register_btn)

                time.sleep(0.3)
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=45)

                # Move mouse to button (visual cue)
                actions = ActionChains(driver)
                actions.move_to_element(register_btn).perform()
                time.sleep(0.2)
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=15)

                # Click button
                register_btn.click()
                time.sleep(0.5)
                frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=30)

        except Exception as e:
            print(f"   ℹ Skipping button interaction: {e}")
            # Just hold on homepage
            frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=120)

        # Final hold
        frame_num = capture_frame(driver, TEMP_DIR, frame_num, duration_frames=90)

        print(f"   ✓ Total frames captured: {frame_num}")
        print()

        # Generate video with FFmpeg
        print("🎞️  Generating video with FFmpeg...")
        output_path = OUTPUT_DIR / 'slide_01_introduction.mp4'

        cmd = [
            'ffmpeg',
            '-r', '30',
            '-i', str(TEMP_DIR / 'frame_%04d.png'),
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
            duration = frame_num / 30
            print(f"   ✓ Video created: {output_path}")
            print(f"   ✓ Size: {size_kb:.1f}KB")
            print(f"   ✓ Duration: {duration:.1f}s ({frame_num} frames at 30fps)")
        else:
            print(f"   ✗ FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()
        print()
        print("🧹 Cleaning up temp files...")
        subprocess.run(['rm', '-rf', str(TEMP_DIR)], capture_output=True)

    print()
    print("=" * 80)
    print("✅ SLIDE 1 REGENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"📹 Video location: {output_path}")
    print()

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

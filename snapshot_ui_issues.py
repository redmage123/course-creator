#!/usr/bin/env python3
"""
Selenium script to take snapshots of UI issues:
1. Login button text in student-login.html
2. Slideshow text alignment on index.html
"""

import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup Chrome options
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
options.add_argument(f'--user-data-dir=/tmp/chrome-snapshot-{int(time.time())}')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

screenshot_dir = '/home/bbrelin/course-creator/tests/reports/screenshots'
os.makedirs(screenshot_dir, exist_ok=True)

try:
    print("=" * 70)
    print("UI ISSUE SNAPSHOT REPORT")
    print("=" * 70)

    # ========== ISSUE 1: Login Button Text ==========
    print("\n[1/2] Capturing student-login.html - Login mode buttons...")
    driver.get('https://localhost:3000/html/student-login.html')
    time.sleep(2)

    # Find the login mode toggle buttons
    try:
        credentials_btn = driver.find_element(By.ID, 'credentialsMode')
        token_btn = driver.find_element(By.ID, 'tokenMode')

        # Highlight the buttons
        driver.execute_script("arguments[0].style.border='3px solid red';", credentials_btn)
        driver.execute_script("arguments[0].style.border='3px solid blue';", token_btn)

        # Get button text
        cred_text = credentials_btn.text
        token_text = token_btn.text

        print(f"   Credentials Button Text: '{cred_text}'")
        print(f"   Token Button Text: '{token_text}'")

        # Take full page screenshot
        driver.save_screenshot(f'{screenshot_dir}/issue1_login_buttons_full.png')
        print(f"   ✓ Saved: issue1_login_buttons_full.png")

        # Take button-only screenshot
        credentials_btn.screenshot(f'{screenshot_dir}/issue1_credentials_btn.png')
        print(f"   ✓ Saved: issue1_credentials_btn.png")

    except Exception as e:
        print(f"   ✗ Error capturing login buttons: {e}")

    # ========== ISSUE 2: Slideshow Text Alignment ==========
    print("\n[2/2] Capturing index.html - Slideshow text alignment...")
    driver.get('https://localhost:3000/html/index.html')
    time.sleep(3)  # Wait for slideshow to load

    try:
        # Find slideshow container
        slideshow = driver.find_element(By.CLASS_NAME, 'hero-slideshow')

        # Scroll to slideshow
        driver.execute_script("arguments[0].scrollIntoView(true);", slideshow)
        time.sleep(1)

        # Highlight slideshow edges
        driver.execute_script("""
            arguments[0].style.border = '5px solid red';
            arguments[0].style.boxSizing = 'border-box';
        """, slideshow)

        # Take full page screenshot
        driver.save_screenshot(f'{screenshot_dir}/issue2_slideshow_full.png')
        print(f"   ✓ Saved: issue2_slideshow_full.png")

        # Take slideshow-only screenshot
        slideshow.screenshot(f'{screenshot_dir}/issue2_slideshow_only.png')
        print(f"   ✓ Saved: issue2_slideshow_only.png")

        # Get slide content elements
        slides = driver.find_elements(By.CLASS_NAME, 'slide')
        print(f"   Found {len(slides)} slides")

        # Capture first slide with text
        if slides:
            first_slide = slides[0]
            try:
                slide_content = first_slide.find_element(By.CLASS_NAME, 'slide-content')

                # Highlight the content area
                driver.execute_script("""
                    arguments[0].style.border = '3px solid yellow';
                    arguments[0].style.boxSizing = 'border-box';
                """, slide_content)

                # Get computed styles
                padding_left = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).paddingLeft;",
                    slide_content
                )
                margin_left = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).marginLeft;",
                    slide_content
                )
                left_position = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).left;",
                    slide_content
                )

                print(f"   Slide Content Padding-Left: {padding_left}")
                print(f"   Slide Content Margin-Left: {margin_left}")
                print(f"   Slide Content Left: {left_position}")

                time.sleep(0.5)
                slideshow.screenshot(f'{screenshot_dir}/issue2_slide_highlighted.png')
                print(f"   ✓ Saved: issue2_slide_highlighted.png")

            except Exception as e:
                print(f"   Warning: Could not find slide-content: {e}")

    except Exception as e:
        print(f"   ✗ Error capturing slideshow: {e}")

    print("\n" + "=" * 70)
    print("SNAPSHOT COMPLETE")
    print(f"Screenshots saved to: {screenshot_dir}")
    print("=" * 70)

except Exception as e:
    print(f"\n✗ Fatal Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    driver.quit()

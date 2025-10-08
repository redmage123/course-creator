#!/usr/bin/env python3
"""
Verify UI fixes with Selenium screenshots:
1. Login button text (Username<br>or Password)
2. Slideshow left edge text alignment
"""

import sys
import os
import time
import pytest

# Add tests directory to path
sys.path.insert(0, '/home/bbrelin/course-creator')
os.chdir('/home/bbrelin/course-creator')

from tests.e2e.selenium_base import BaseTest
from selenium.webdriver.common.by import By

class TestUIFixVerification(BaseTest):
    """Verify UI fixes with screenshots"""

    def test_verify_ui_fixes(self):
        """Capture screenshots to verify UI fixes"""
        screenshot_dir = '/home/bbrelin/course-creator/tests/reports/screenshots'
        os.makedirs(screenshot_dir, exist_ok=True)

        print("\n" + "=" * 70)
        print("UI FIX VERIFICATION")
        print("=" * 70)

        # ========== ISSUE 1: Login Button Text ==========
        print("\n[1/2] Verifying student-login.html - Login button text...")
        self.driver.get('https://localhost:3000/html/student-login.html')
        time.sleep(2)

        try:
            credentials_btn = self.driver.find_element(By.ID, 'credentialsMode')
            token_btn = self.driver.find_element(By.ID, 'tokenMode')

            # Highlight buttons
            self.driver.execute_script("arguments[0].style.border='3px solid red';", credentials_btn)
            self.driver.execute_script("arguments[0].style.border='3px solid blue';", token_btn)

            # Get button text
            cred_text = credentials_btn.text
            token_text = token_btn.text

            print(f"   Credentials Button Text: '{cred_text}'")
            print(f"   Token Button Text: '{token_text}'")

            # Take screenshots
            self.driver.save_screenshot(f'{screenshot_dir}/fix_verified_login_buttons.png')
            credentials_btn.screenshot(f'{screenshot_dir}/fix_verified_button_only.png')
            print(f"   ✓ Saved: fix_verified_login_buttons.png")
            print(f"   ✓ Saved: fix_verified_button_only.png")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            raise

        # ========== ISSUE 2: Slideshow Alignment ==========
        print("\n[2/2] Verifying index.html - Slideshow text alignment...")
        self.driver.get('https://localhost:3000/html/index.html')
        time.sleep(3)

        try:
            # Find slideshow
            slideshow = self.driver.find_element(By.CLASS_NAME, 'hero-slideshow')

            # Scroll to slideshow
            self.driver.execute_script("arguments[0].scrollIntoView(true);", slideshow)
            time.sleep(1)

            # Highlight slideshow
            self.driver.execute_script("""
                arguments[0].style.border = '5px solid red';
                arguments[0].style.boxSizing = 'border-box';
            """, slideshow)

            # Take screenshots
            self.driver.save_screenshot(f'{screenshot_dir}/fix_verified_slideshow.png')
            slideshow.screenshot(f'{screenshot_dir}/fix_verified_slideshow_only.png')
            print(f"   ✓ Saved: fix_verified_slideshow.png")
            print(f"   ✓ Saved: fix_verified_slideshow_only.png")

            # Check slide content
            slides = self.driver.find_elements(By.CLASS_NAME, 'slide')
            print(f"   Found {len(slides)} slides")

            if slides:
                first_slide = slides[0]
                try:
                    slide_content = first_slide.find_element(By.CLASS_NAME, 'slide-content')

                    # Get parent slide padding
                    parent_padding = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0].parentElement).paddingLeft;",
                        slide_content
                    )

                    # Get computed styles
                    padding_left = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).paddingLeft;",
                        slide_content
                    )
                    margin_left = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginLeft;",
                        slide_content
                    )

                    print(f"   Slide Padding-Left: {parent_padding}")
                    print(f"   Content Padding-Left: {padding_left}")
                    print(f"   Content Margin-Left: {margin_left}")

                except Exception as e:
                    print(f"   Warning: Could not analyze slide-content: {e}")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            raise

        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print(f"Screenshots saved to: {screenshot_dir}")
        print("=" * 70)

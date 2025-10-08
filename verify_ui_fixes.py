#!/usr/bin/env python3
"""
Verify UI fixes with Selenium screenshots:
1. Login button text (Username<br>or Password)
2. Slideshow left edge text alignment
"""

import sys
import os
import time

# Add tests directory to path to use selenium_base
sys.path.insert(0, '/home/bbrelin/course-creator')
os.chdir('/home/bbrelin/course-creator')

from tests.e2e.selenium_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class UIFixVerification(BaseTest):
    """Verify UI fixes with screenshots"""

    def setUp(self):
        """Initialize test"""
        super().setUp()
        self.screenshot_dir = '/home/bbrelin/course-creator/tests/reports/screenshots'
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def test_verify_ui_fixes(self):
        """Capture screenshots to verify UI fixes"""
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
            self.driver.save_screenshot(f'{self.screenshot_dir}/issue1_login_buttons.png')
            credentials_btn.screenshot(f'{self.screenshot_dir}/issue1_button_only.png')
            print(f"   ✓ Saved: issue1_login_buttons.png")
            print(f"   ✓ Saved: issue1_button_only.png")

        except Exception as e:
            print(f"   ✗ Error: {e}")

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
            self.driver.save_screenshot(f'{self.screenshot_dir}/issue2_slideshow.png')
            slideshow.screenshot(f'{self.screenshot_dir}/issue2_slideshow_only.png')
            print(f"   ✓ Saved: issue2_slideshow.png")
            print(f"   ✓ Saved: issue2_slideshow_only.png")

            # Check slide content
            slides = self.driver.find_elements(By.CLASS_NAME, 'slide')
            print(f"   Found {len(slides)} slides")

            if slides:
                first_slide = slides[0]
                try:
                    slide_content = first_slide.find_element(By.CLASS_NAME, 'slide-content')

                    # Get computed styles
                    padding_left = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).paddingLeft;",
                        slide_content
                    )
                    margin_left = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).marginLeft;",
                        slide_content
                    )

                    print(f"   Slide Content Padding-Left: {padding_left}")
                    print(f"   Slide Content Margin-Left: {margin_left}")

                except Exception as e:
                    print(f"   Warning: Could not analyze slide-content: {e}")

        except Exception as e:
            print(f"   ✗ Error: {e}")

        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print(f"Screenshots saved to: {self.screenshot_dir}")
        print("=" * 70)

if __name__ == '__main__':
    import unittest

    suite = unittest.TestLoader().loadTestsFromTestCase(UIFixVerification)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)

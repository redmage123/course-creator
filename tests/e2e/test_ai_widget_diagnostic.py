#!/usr/bin/env python3
"""
Diagnostic test for AI Assistant widget visibility
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def test_ai_widget_diagnostic():
    """Diagnose why AI widget is not appearing"""

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 20)

    try:
        print("\n" + "="*80)
        print("AI WIDGET DIAGNOSTIC TEST")
        print("="*80)

        # Login as org admin
        print("\n1. Logging in...")
        driver.get("https://localhost:3000")
        time.sleep(2)

        username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_input = driver.find_element(By.ID, "password")
        username_input.send_keys("orgadmin")
        password_input.send_keys("OrgAdmin123!")

        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        # Wait for dashboard
        wait.until(EC.url_contains("/org-admin-dashboard.html"))
        print("✅ Logged in successfully")
        time.sleep(3)

        # Get page HTML and check if widget HTML exists
        print("\n2. Checking HTML source...")
        page_source = driver.page_source

        if "ai-chat-toggle" in page_source:
            print("✅ Widget HTML found in page source")
        else:
            print("❌ Widget HTML NOT found in page source")

        if "ai-chat-panel" in page_source:
            print("✅ Panel HTML found in page source")
        else:
            print("❌ Panel HTML NOT found in page source")

        # Check if button exists in DOM
        print("\n3. Checking DOM elements...")
        try:
            button = driver.find_element(By.ID, "ai-chat-toggle")
            print("✅ Button element found in DOM")

            # Check if button is displayed
            is_displayed = button.is_displayed()
            print(f"   Button displayed: {is_displayed}")

            # Get button locations and size
            locations = button.locations
            size = button.size
            print(f"   Button locations: {locations}")
            print(f"   Button size: {size}")

            # Get computed styles
            button_bg = button.value_of_css_property('background')
            button_display = button.value_of_css_property('display')
            button_visibility = button.value_of_css_property('visibility')
            button_opacity = button.value_of_css_property('opacity')
            button_zindex = button.value_of_css_property('z-index')

            print(f"   CSS display: {button_display}")
            print(f"   CSS visibility: {button_visibility}")
            print(f"   CSS opacity: {button_opacity}")
            print(f"   CSS z-index: {button_zindex}")
            print(f"   CSS background: {button_bg[:50]}...")

        except Exception as e:
            print(f"❌ Button element NOT found in DOM: {e}")

        # Check if panel exists
        try:
            panel = driver.find_element(By.ID, "ai-chat-panel")
            print("✅ Panel element found in DOM")

            is_displayed = panel.is_displayed()
            print(f"   Panel displayed: {is_displayed}")

            panel_display = panel.value_of_css_property('display')
            print(f"   Panel CSS display: {panel_display}")

        except Exception as e:
            print(f"❌ Panel element NOT found in DOM: {e}")

        # Check for JavaScript console errors
        print("\n4. Checking browser console logs...")
        logs = driver.get_log('browser')

        if logs:
            print(f"   Found {len(logs)} console messages:")
            for log in logs[-10:]:  # Show last 10
                level = log.get('level')
                message = log.get('message', '')
                if 'SEVERE' in level or 'ERROR' in level:
                    print(f"   ❌ {level}: {message}")
                elif 'WARNING' in level:
                    print(f"   ⚠️  {level}: {message}")
                else:
                    print(f"   ℹ️  {level}: {message}")
        else:
            print("   ✅ No console errors")

        # Try to take a screenshot
        print("\n5. Taking screenshot...")
        screenshot_path = "/tmp/ai_widget_diagnostic.png"
        driver.save_screenshot(screenshot_path)
        print(f"   Screenshot saved: {screenshot_path}")

        # Summary
        print("\n" + "="*80)
        print("DIAGNOSTIC SUMMARY")
        print("="*80)
        print("Please review the output above to identify the issue.")
        print("Common issues:")
        print("  - If button NOT in DOM: JavaScript error preventing rendering")
        print("  - If button in DOM but not displayed: CSS issue (check display/visibility)")
        print("  - If button displayed=False: Element hidden or off-screen")
        print("  - Check console errors for module loading issues")
        print("="*80)

    finally:
        driver.quit()


if __name__ == '__main__':
    test_ai_widget_diagnostic()

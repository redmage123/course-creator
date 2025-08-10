#!/usr/bin/env python3
"""
Selenium Test for Registration Button
Captures exactly what the browser sees and does when clicking the registration button
"""

import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

def test_registration_button():
    print("🚀 Starting Selenium Registration Button Test...")
    
    # Set up Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--ignore-ssl-errors=yes")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = None
    
    try:
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        print("📄 Loading main page...")
        
        # Load the main page
        driver.get("https://176.9.99.103:3000/html/index.html")
        
        # Wait for page to load
        time.sleep(3)
        
        print("✅ Page loaded")
        print(f"📊 Page title: {driver.title}")
        print(f"🌐 Current URL: {driver.current_url}")
        
        # Capture initial page state
        print("\n🔍 INITIAL PAGE STATE:")
        
        # Check if register button exists
        try:
            register_btn = driver.find_element(By.ID, "registerBtn")
            print(f"✅ Register button found: {register_btn.text}")
            print(f"📍 Button location: {register_btn.location}")
            print(f"📐 Button size: {register_btn.size}")
            print(f"🎯 Button is displayed: {register_btn.is_displayed()}")
            print(f"🔘 Button is enabled: {register_btn.is_enabled()}")
        except Exception as e:
            print(f"❌ Register button not found: {e}")
            return
        
        # Check main content before click
        main_content = driver.find_element(By.ID, "main-content")
        initial_content_length = len(main_content.get_attribute('innerHTML'))
        print(f"📝 Initial main-content length: {initial_content_length}")
        print(f"📄 Initial content preview: {main_content.get_attribute('innerHTML')[:200]}...")
        
        # Take screenshot before click
        screenshot_before = driver.get_screenshot_as_base64()
        with open('/tmp/before_click.png', 'wb') as f:
            f.write(base64.b64decode(screenshot_before))
        print("📸 Screenshot saved: /tmp/before_click.png")
        
        # Enable browser console logging
        logs_before = driver.get_log('browser')
        print(f"\n📋 Console logs before click ({len(logs_before)} entries):")
        for log in logs_before[-5:]:  # Show last 5 logs
            print(f"   {log['level']}: {log['message']}")
        
        print(f"\n🖱️  CLICKING REGISTER BUTTON...")
        
        # Click the register button
        driver.execute_script("arguments[0].click();", register_btn)
        
        # Wait a moment for any async operations
        time.sleep(2)
        
        print("✅ Register button clicked")
        
        # Check page state after click
        print(f"\n🔍 PAGE STATE AFTER CLICK:")
        print(f"🌐 Current URL: {driver.current_url}")
        
        # Check main content after click
        main_content_after = driver.find_element(By.ID, "main-content")
        after_content_length = len(main_content_after.get_attribute('innerHTML'))
        print(f"📝 Main-content length after click: {after_content_length}")
        print(f"📊 Content length changed: {initial_content_length} → {after_content_length}")
        
        if after_content_length != initial_content_length:
            print("✅ Content was updated!")
            print(f"📄 New content preview: {main_content_after.get_attribute('innerHTML')[:300]}...")
            
            # Check for specific registration elements
            try:
                reg_section = driver.find_element(By.CLASS_NAME, "registration-options")
                print(f"✅ Registration section found!")
                print(f"📍 Registration section location: {reg_section.location}")
                print(f"📐 Registration section size: {reg_section.size}")
                print(f"🎯 Registration section displayed: {reg_section.is_displayed()}")
                print(f"📄 Registration section text: {reg_section.text[:200]}...")
            except Exception as e:
                print(f"❌ Registration section not found: {e}")
        else:
            print("❌ Content was NOT updated")
        
        # Get console logs after click
        logs_after = driver.get_log('browser')
        new_logs = logs_after[len(logs_before):]
        print(f"\n📋 New console logs after click ({len(new_logs)} entries):")
        for log in new_logs:
            print(f"   {log['level']}: {log['message']}")
        
        # Take screenshot after click
        screenshot_after = driver.get_screenshot_as_base64()
        with open('/tmp/after_click.png', 'wb') as f:
            f.write(base64.b64decode(screenshot_after))
        print("📸 Screenshot saved: /tmp/after_click.png")
        
        # Get full page HTML
        page_html = driver.page_source
        with open('/tmp/page_after_click.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        print("💾 Full page HTML saved: /tmp/page_after_click.html")
        
        # Test direct JavaScript execution
        print(f"\n🔬 TESTING DIRECT JAVASCRIPT:")
        
        # Test if Navigation object exists
        nav_exists = driver.execute_script("return typeof window.Navigation !== 'undefined';")
        print(f"📦 window.Navigation exists: {nav_exists}")
        
        if nav_exists:
            # Test calling showRegister directly
            try:
                result = driver.execute_script("window.Navigation.showRegister(); return 'success';")
                print(f"✅ Direct Navigation.showRegister() call: {result}")
                
                time.sleep(1)
                
                # Check content again after direct call
                main_after_direct = driver.find_element(By.ID, "main-content")
                direct_content_length = len(main_after_direct.get_attribute('innerHTML'))
                print(f"📝 Content length after direct call: {direct_content_length}")
                
            except Exception as e:
                print(f"❌ Error calling Navigation.showRegister() directly: {e}")
        
        # Final screenshot
        screenshot_final = driver.get_screenshot_as_base64()
        with open('/tmp/final_state.png', 'wb') as f:
            f.write(base64.b64decode(screenshot_final))
        print("📸 Final screenshot saved: /tmp/final_state.png")
        
        print(f"\n✅ Test completed successfully!")
        print(f"📁 Files saved:")
        print(f"   - /tmp/before_click.png")
        print(f"   - /tmp/after_click.png") 
        print(f"   - /tmp/final_state.png")
        print(f"   - /tmp/page_after_click.html")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("🔧 Browser closed")

if __name__ == "__main__":
    test_registration_button()
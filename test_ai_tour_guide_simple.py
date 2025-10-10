#!/usr/bin/env python3
"""
Simple AI Tour Guide Test - Manual Verification

Tests that AI tour guide can receive and display responses
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("🎬 Opening demo player...")
    driver.get('https://localhost:3000/html/demo-player.html')
    time.sleep(3)

    print("🤖 Opening AI Tour Guide...")
    trigger = driver.find_element(By.ID, "ai-tour-guide-trigger")
    trigger.click()
    time.sleep(2)

    print("📝 Sending question...")
    input_field = driver.find_element(By.CSS_SELECTOR, ".ai-guide-input")
    input_field.send_keys("Who is this platform for?")

    send_btn = driver.find_element(By.CSS_SELECTOR, ".ai-guide-send")
    send_btn.click()

    print("⏳ Waiting 15 seconds for response...")
    time.sleep(15)

    # Get all messages
    all_messages = driver.find_elements(By.CSS_SELECTOR, ".ai-guide-message")
    print(f"\n✅ Found {len(all_messages)} total messages")

    for i, msg in enumerate(all_messages, 1):
        classes = msg.get_attribute('class')
        text = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
        print(f"\n   Message {i}:")
        print(f"   Classes: {classes}")
        print(f"   Text: {text}")

    # Check for AI response specifically
    ai_messages = driver.find_elements(By.CSS_SELECTOR, ".ai-guide-message.ai")
    print(f"\n🤖 Found {len(ai_messages)} AI messages")

    if ai_messages:
        print("\n✅ SUCCESS - AI Tour Guide is working!")
        print(f"\nLatest AI Response:")
        print(ai_messages[-1].text[:500])
    else:
        print("\n⚠️  No AI responses found")

        # Check browser console for errors
        logs = driver.get_log('browser')
        if logs:
            print("\n🔍 Browser Console Errors:")
            for log in logs[-5:]:
                print(f"   {log}")

finally:
    driver.quit()

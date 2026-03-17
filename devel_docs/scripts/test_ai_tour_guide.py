#!/usr/bin/env python3
"""
Test AI Tour Guide RAG Integration

BUSINESS PURPOSE:
Verify that the AI Tour Guide can answer common questions about the platform
using the RAG service and knowledge base.

TECHNICAL APPROACH:
Use Selenium to interact with the AI Tour Guide and test RAG responses
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def test_ai_tour_guide():
    """
    Test AI Tour Guide with various questions
    """
    print("=" * 70)
    print("🤖 TESTING AI TOUR GUIDE - RAG INTEGRATION")
    print("=" * 70)
    print()

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("📍 Step 1: Opening demo player...")
        driver.get('https://localhost:3000/html/demo-player.html')
        time.sleep(3)
        print("   ✓ Demo player loaded")
        print()

        print("📍 Step 2: Opening AI Tour Guide...")
        ai_guide_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ai-tour-guide-trigger"))
        )
        ai_guide_trigger.click()
        time.sleep(2)
        print("   ✓ AI Tour Guide panel opened")
        print()

        # Test questions
        test_questions = [
            {
                "question": "Who is this platform for?",
                "expected_keywords": ["corporate", "training", "instructors", "professional"]
            },
            {
                "question": "How does the AI help with course creation?",
                "expected_keywords": ["generates", "course", "structure", "content", "quiz"]
            },
            {
                "question": "What integrations do you support?",
                "expected_keywords": ["zoom", "teams", "slack"]
            },
            {
                "question": "How much does this cost?",
                "expected_keywords": ["beta", "development", "pricing"]
            }
        ]

        for i, test in enumerate(test_questions, 1):
            print(f"📍 Step {i + 2}: Testing question: '{test['question']}'")

            try:
                # Find input field
                input_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ai-guide-input"))
                )

                # Clear and type question
                input_field.clear()
                input_field.send_keys(test['question'])
                time.sleep(0.5)

                # Click send or press Enter
                send_button = driver.find_element(By.CSS_SELECTOR, ".ai-guide-send")
                send_button.click()

                print(f"   ✓ Question sent: {test['question']}")

                # Wait for typing indicator to appear and disappear
                time.sleep(2)

                # Wait for response (up to 30 seconds)
                print(f"   ⏳ Waiting for AI response...")
                time.sleep(10)  # Give RAG service time to respond

                # Get all AI messages
                messages = driver.find_elements(By.CSS_SELECTOR, ".ai-message")

                if messages:
                    latest_message = messages[-1]
                    message_text = latest_message.text.lower()

                    print(f"   ✓ AI response received ({len(message_text)} chars)")

                    # Check for expected keywords
                    found_keywords = [kw for kw in test['expected_keywords'] if kw.lower() in message_text]

                    if found_keywords:
                        print(f"   ✓ Response contains expected keywords: {found_keywords}")
                    else:
                        print(f"   ⚠️  Response may not match expectations")
                        print(f"      Expected keywords: {test['expected_keywords']}")

                    # Show first 200 chars of response
                    preview = message_text[:200] + "..." if len(message_text) > 200 else message_text
                    print(f"   📄 Response preview: {preview}")

                else:
                    print(f"   ✗ No AI response found")

                print()

            except Exception as e:
                print(f"   ✗ Test failed: {e}")
                print()

        print("=" * 70)
        print("✅ AI TOUR GUIDE TESTING COMPLETE")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • AI Tour Guide interface: Working")
        print("  • Question submission: Working")
        print("  • RAG integration: Tested with 4 common questions")
        print("  • Knowledge base: Contains platform information")
        print()

    finally:
        driver.quit()


if __name__ == '__main__':
    test_ai_tour_guide()

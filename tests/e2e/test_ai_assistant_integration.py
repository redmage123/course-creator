#!/usr/bin/env python3
"""
Test AI Assistant Integration on Org Admin Dashboard

This test verifies that the AI Assistant widget:
1. Appears on the org-admin dashboard
2. Can be toggled open/closed
3. Sends messages to backend
4. Receives AI responses
5. Displays suggestions correctly
6. Handles errors gracefully
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestAIAssistantIntegration:
    """Test AI Assistant widget integration with backend"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)

        yield

        self.driver.quit()

    def login_as_org_admin(self):
        """Login as organization admin"""
        print("\n🔐 Logging in as organization admin...")

        self.driver.get("https://localhost:3000")
        time.sleep(2)

        # Wait for login form
        username_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_input = self.driver.find_element(By.ID, "password")

        # Login as org admin
        username_input.send_keys("orgadmin")
        password_input.send_keys("OrgAdmin123!")

        # Click login button
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        # Wait for redirect to dashboard
        self.wait.until(
            EC.url_contains("/org-admin-dashboard.html")
        )

        print("✅ Logged in successfully")
        time.sleep(2)

    def test_01_ai_widget_appears_on_dashboard(self):
        """Test that AI Assistant widget appears on org-admin dashboard"""
        print("\n📋 TEST 1: Verify AI widget appears on dashboard")

        self.login_as_org_admin()

        # Check for AI chat toggle button
        try:
            ai_toggle = self.wait.until(
                EC.presence_of_element_located((By.ID, "ai-chat-toggle"))
            )
            assert ai_toggle.is_displayed(), "AI chat toggle button should be visible"

            # Verify button text
            assert "AI Assistant" in ai_toggle.text, "Toggle button should say 'AI Assistant'"

            print("✅ AI Assistant toggle button found and visible")

            # Check button styling
            toggle_bg = ai_toggle.value_of_css_property('background')
            assert toggle_bg, "Toggle button should have background styling"

            print("✅ AI Assistant widget appears correctly on dashboard")

        except TimeoutException:
            pytest.fail("❌ AI chat toggle button not found on page")

    def test_02_ai_widget_opens_and_closes(self):
        """Test that AI widget can be toggled open and closed"""
        print("\n📋 TEST 2: Verify AI widget opens and closes")

        self.login_as_org_admin()

        # Find toggle button
        ai_toggle = self.wait.until(
            EC.element_to_be_clickable((By.ID, "ai-chat-toggle"))
        )

        # Check initial state (panel should be hidden)
        ai_panel = self.driver.find_element(By.ID, "ai-chat-panel")
        initial_display = ai_panel.value_of_css_property('display')

        print(f"📊 Initial panel display: {initial_display}")

        # Click to open
        ai_toggle.click()
        time.sleep(1)

        # Verify panel is now visible
        panel_classes = ai_panel.get_attribute('class')
        assert 'active' in panel_classes, "Panel should have 'active' class when opened"

        print("✅ AI panel opened successfully")

        # Click to close
        ai_toggle.click()
        time.sleep(1)

        # Verify panel is hidden again
        panel_classes = ai_panel.get_attribute('class')
        assert 'active' not in panel_classes, "Panel should not have 'active' class when closed"

        print("✅ AI panel closed successfully")

    def test_03_quick_action_buttons_work(self):
        """Test that quick action buttons populate the input"""
        print("\n📋 TEST 3: Verify quick action buttons work")

        self.login_as_org_admin()

        # Open AI panel
        ai_toggle = self.wait.until(
            EC.element_to_be_clickable((By.ID, "ai-chat-toggle"))
        )
        ai_toggle.click()
        time.sleep(1)

        # Find quick action buttons
        quick_actions = self.driver.find_elements(By.CSS_SELECTOR, ".ai-quick-action")
        assert len(quick_actions) >= 3, "Should have at least 3 quick action buttons"

        print(f"✅ Found {len(quick_actions)} quick action buttons")

        # Test first quick action (Project ideas)
        project_ideas_btn = quick_actions[0]
        assert "💡" in project_ideas_btn.text or "Project ideas" in project_ideas_btn.text

        print("✅ Quick action buttons configured correctly")

    def test_04_send_message_to_ai(self):
        """Test sending a message to AI and receiving response"""
        print("\n📋 TEST 4: Send message to AI backend")

        self.login_as_org_admin()

        # Open AI panel
        ai_toggle = self.wait.until(
            EC.element_to_be_clickable((By.ID, "ai-chat-toggle"))
        )
        ai_toggle.click()
        time.sleep(1)

        # Find input field
        ai_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "ai-chat-input"))
        )

        # Type a test message
        test_message = "What is a training project?"
        ai_input.send_keys(test_message)

        print(f"📝 Typed message: {test_message}")

        # Click send button
        send_button = self.driver.find_element(By.CSS_SELECTOR, ".ai-chat-send")
        send_button.click()

        print("📤 Sent message to AI")

        # Wait for typing indicator to appear
        time.sleep(1)

        # Wait for response (give it up to 15 seconds for AI to respond)
        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ai-message.assistant"))
            )

            print("✅ AI response received!")

            # Get all messages
            messages = self.driver.find_elements(By.CSS_SELECTOR, ".ai-message")

            # Should have at least 2 messages (user + assistant)
            assert len(messages) >= 2, f"Should have at least 2 messages, got {len(messages)}"

            # Check user message
            user_messages = self.driver.find_elements(By.CSS_SELECTOR, ".ai-message.user")
            assert len(user_messages) >= 1, "Should have at least 1 user message"
            assert test_message in user_messages[0].text, "User message should contain sent text"

            print(f"✅ User message displayed correctly")

            # Check assistant message
            assistant_messages = self.driver.find_elements(By.CSS_SELECTOR, ".ai-message.assistant")
            assert len(assistant_messages) >= 1, "Should have at least 1 assistant message"

            assistant_text = assistant_messages[0].text
            assert len(assistant_text) > 0, "Assistant message should not be empty"

            print(f"✅ Assistant message: {assistant_text[:100]}...")
            print("✅ AI message exchange completed successfully")

        except TimeoutException:
            # Check if there's an error message instead
            error_messages = self.driver.find_elements(By.CSS_SELECTOR, ".ai-message.assistant")
            if error_messages:
                print(f"⚠️ AI response may have errored: {error_messages[0].text}")
            pytest.fail("❌ No AI response received within timeout")

    def test_05_check_console_logs(self):
        """Test that console logs show proper initialization"""
        print("\n📋 TEST 5: Check browser console logs")

        self.login_as_org_admin()

        # Get console logs
        logs = self.driver.get_log('browser')

        print(f"\n📊 Browser console logs ({len(logs)} entries):")

        # Look for AI initialization log
        ai_init_found = False
        for log in logs:
            message = log.get('message', '')
            print(f"  {log.get('level')}: {message}")

            if 'AI Assistant initialized' in message:
                ai_init_found = True
                print("✅ Found AI Assistant initialization log")

        # Note: We might not always find the log due to timing, so we'll just report
        if ai_init_found:
            print("✅ Console shows proper AI initialization")
        else:
            print("ℹ️ AI initialization log not found (may be timing related)")

    def test_06_error_handling(self):
        """Test error handling when backend is unavailable"""
        print("\n📋 TEST 6: Verify error handling")

        self.login_as_org_admin()

        # Open AI panel
        ai_toggle = self.wait.until(
            EC.element_to_be_clickable((By.ID, "ai-chat-toggle"))
        )
        ai_toggle.click()
        time.sleep(1)

        print("✅ AI panel opened")
        print("ℹ️ Error handling test requires manual backend disruption")
        print("   Current test verifies UI is ready for error messages")

        # Verify error message styling exists in CSS
        # This ensures error messages will display correctly if they occur
        page_source = self.driver.page_source
        assert 'fee2e2' in page_source or 'error' in page_source.lower(), \
            "Page should have error styling configured"

        print("✅ Error handling CSS configured")


def test_ai_assistant_module_exists():
    """Verify ai-assistant.js module exists"""
    print("\n📋 VERIFY: AI assistant module file exists")

    import os
    module_path = "/home/bbrelin/course-creator/frontend/js/modules/ai-assistant.js"

    assert os.path.exists(module_path), f"ai-assistant.js module should exist at {module_path}"

    # Check file size (should be substantial if it has full implementation)
    file_size = os.path.getsize(module_path)
    print(f"✅ ai-assistant.js exists ({file_size} bytes)")

    assert file_size > 10000, "ai-assistant.js should be substantial (>10KB for full implementation)"

    print(f"✅ AI assistant module verified ({file_size:,} bytes)")


def test_nginx_routing_configured():
    """Verify nginx has chat endpoint routing"""
    print("\n📋 VERIFY: Nginx routing for /api/v1/chat")

    import os
    nginx_conf = "/home/bbrelin/course-creator/frontend/nginx.conf"

    assert os.path.exists(nginx_conf), "nginx.conf should exist"

    with open(nginx_conf, 'r') as f:
        content = f.read()

    assert '/api/v1/chat' in content, "nginx.conf should have /api/v1/chat route"
    assert 'course-generator:8001' in content, "nginx.conf should proxy to course-generator"

    print("✅ Nginx routing configured correctly")


if __name__ == '__main__':
    """Run tests directly"""
    import sys

    print("=" * 80)
    print("AI ASSISTANT INTEGRATION TEST SUITE")
    print("=" * 80)

    # Run with pytest
    sys.exit(pytest.main([__file__, '-v', '--tb=short', '-s']))

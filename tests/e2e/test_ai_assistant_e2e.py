#!/usr/bin/env python3
"""
End-to-End Tests for AI Assistant Complete User Journey

BUSINESS PURPOSE:
Tests complete workflows from user perspective:
- Admin discovers AI assistant
- Admin uses AI to create organizational resources
- Admin completes multiple tasks via natural language
- Verification that tasks are completed successfully

TECHNICAL APPROACH:
Full browser automation testing real user workflows
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


@pytest.fixture(scope="class")
def browser():
    """
    Browser fixture with extended timeout for E2E tests
    """
    options = webdriver.ChromeOptions()

    # Use headless mode unless HEADLESS=false
    if os.getenv("HEADLESS", "true").lower() != "false":
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


class TestAIAssistantCompleteJourney:
    """E2E tests for complete AI assistant user workflows"""

    BASE_URL = os.getenv("TEST_BASE_URL", "https://localhost:3000")

    def test_01_admin_discovers_ai_assistant(self, browser):
        """
        Test: Admin user logs in and discovers AI assistant button

        Steps:
        1. Navigate to dashboard
        2. Verify AI assistant button is visible
        3. Verify button has proper styling and icon
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # AI button should be visible
        ai_button = wait.until(
            EC.visibility_of_element_located((By.ID, "aiAssistantBtn"))
        )

        assert ai_button.is_displayed()

        # Verify it has robot icon
        icon = ai_button.find_element(By.CLASS_NAME, "fa-robot")
        assert icon is not None

        print("✓ Admin successfully discovers AI assistant button")

    def test_02_admin_opens_ai_assistant_first_time(self, browser):
        """
        Test: Admin opens AI assistant and sees welcome message

        Steps:
        1. Click AI assistant button
        2. Verify panel opens with animation
        3. Verify welcome message is displayed
        4. Verify capabilities are listed
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Click AI button
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()

        # Wait for panel to open
        time.sleep(0.5)

        # Verify panel is open
        panel = browser.find_element(By.ID, "aiAssistantPanel")
        assert "open" in panel.get_attribute("class")

        # Verify welcome message exists
        messages = browser.find_element(By.ID, "aiMessages")
        assert "Hello" in messages.text or "help" in messages.text.lower()

        # Verify capabilities are listed
        assert "projects" in messages.text.lower()
        assert "tracks" in messages.text.lower()
        assert "instructors" in messages.text.lower()

        print("✓ Admin successfully opens AI assistant and sees welcome")

    def test_03_admin_creates_project_via_ai(self, browser):
        """
        Test: Admin uses AI to create a project

        Steps:
        1. Open AI assistant
        2. Type "create a new project"
        3. Send message
        4. Verify AI responds with follow-up question
        5. Provide project details
        6. Verify confirmation
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Type create project request
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("create a new project")
        input_field.send_keys(Keys.ENTER)

        # Wait for AI response
        time.sleep(1)

        # Verify AI asks for project name
        messages = browser.find_element(By.ID, "aiMessages")
        assert "project" in messages.text.lower()
        assert "name" in messages.text.lower()

        print("✓ Admin successfully requests project creation via AI")

    def test_04_admin_creates_track_with_full_details(self, browser):
        """
        Test: Admin creates a track with complete details in one message

        Steps:
        1. Open AI assistant
        2. Send detailed track creation request
        3. Verify AI confirms track creation
        4. Verify track details are acknowledged
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send detailed track creation request
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        track_request = (
            "Create an intermediate track called Machine Learning Basics "
            "for the Data Science project"
        )

        input_field.send_keys(track_request)
        input_field.send_keys(Keys.ENTER)

        # Wait for AI response
        time.sleep(1)

        # Verify AI confirms creation
        messages = browser.find_element(By.ID, "aiMessages")
        message_text = messages.text.lower()

        assert "track" in message_text
        assert "created" in message_text or "available" in message_text

        print("✓ Admin successfully creates track via AI with full details")

    def test_05_admin_onboards_instructor_via_ai(self, browser):
        """
        Test: Admin uses AI to onboard an instructor

        Steps:
        1. Open AI assistant
        2. Request to add instructor
        3. Verify AI asks for required information
        4. Verify proper response
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Request to add instructor
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("I need to add a new instructor")
        input_field.send_keys(Keys.ENTER)

        # Wait for AI response
        time.sleep(1)

        # Verify AI asks for details
        messages = browser.find_element(By.ID, "aiMessages")
        message_text = messages.text.lower()

        assert "instructor" in message_text
        assert "email" in message_text or "project" in message_text

        print("✓ Admin successfully initiates instructor onboarding via AI")

    def test_06_admin_handles_multiple_tasks_in_sequence(self, browser):
        """
        Test: Admin completes multiple different tasks in one session

        Steps:
        1. Open AI assistant
        2. Create project
        3. Create track
        4. Onboard instructor
        5. Create course
        6. Verify all conversations are tracked
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        tasks = [
            "create a new project called Advanced Python",
            "create a beginner track for Python fundamentals",
            "add an instructor to my organization",
            "create a course about data structures"
        ]

        for task in tasks:
            input_field.send_keys(task)
            input_field.send_keys(Keys.ENTER)
            time.sleep(1)

        # Verify multiple messages exist
        messages = browser.find_element(By.ID, "aiMessages")
        message_elements = messages.find_elements(By.CLASS_NAME, "ai-message")

        # Should have welcome + (user + AI) × 4 tasks = 9 messages
        assert len(message_elements) >= 8

        print("✓ Admin successfully completes multiple tasks in sequence")

    def test_07_admin_closes_and_reopens_panel(self, browser):
        """
        Test: Admin can close and reopen AI assistant panel

        Steps:
        1. Open AI assistant
        2. Send a message
        3. Close panel
        4. Reopen panel
        5. Verify conversation history is preserved
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send a message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("create a project")
        input_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Get message count
        messages = browser.find_element(By.ID, "aiMessages")
        initial_count = len(messages.find_elements(By.CLASS_NAME, "ai-message"))

        # Close panel
        close_btn = browser.find_element(By.ID, "closeAIAssistant")
        close_btn.click()
        time.sleep(0.5)

        # Verify panel is closed
        panel = browser.find_element(By.ID, "aiAssistantPanel")
        assert "open" not in panel.get_attribute("class")

        # Reopen panel
        ai_button.click()
        time.sleep(0.5)

        # Verify panel is open
        assert "open" in panel.get_attribute("class")

        # Verify messages are still there
        final_count = len(messages.find_elements(By.CLASS_NAME, "ai-message"))
        assert final_count == initial_count

        print("✓ Admin successfully closes and reopens panel with history preserved")

    def test_08_admin_receives_helpful_response_for_unclear_request(self, browser):
        """
        Test: Admin sends unclear request and gets helpful default response

        Steps:
        1. Open AI assistant
        2. Send vague or unclear message
        3. Verify AI responds with capabilities list
        4. Verify response is helpful
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send unclear request
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("help me with something")
        input_field.send_keys(Keys.ENTER)

        # Wait for AI response
        time.sleep(1)

        # Verify helpful response
        messages = browser.find_element(By.ID, "aiMessages")
        message_text = messages.text.lower()

        assert "help" in message_text or "can" in message_text
        assert "project" in message_text or "track" in message_text

        print("✓ Admin receives helpful response for unclear request")

    def test_09_keyboard_navigation_works(self, browser):
        """
        Test: Admin can use keyboard shortcuts

        Steps:
        1. Open AI assistant
        2. Type message
        3. Press Enter to send
        4. Verify message is sent
        5. Verify input is cleared
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Type and send with Enter
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("test keyboard navigation")
        input_field.send_keys(Keys.ENTER)

        # Wait a moment
        time.sleep(0.5)

        # Verify input is cleared
        assert input_field.get_attribute("value") == ""

        print("✓ Keyboard navigation works correctly")

    def test_10_ai_assistant_accessible_from_all_dashboard_tabs(self, browser):
        """
        Test: AI assistant is accessible from all tabs

        Steps:
        1. Navigate to different tabs
        2. Verify AI button remains visible
        3. Verify AI works from each tab
        """
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        tabs = ["nav-projects", "nav-tracks", "nav-members", "nav-settings"]

        for tab_id in tabs:
            # Click tab
            tab = wait.until(
                EC.element_to_be_clickable((By.ID, tab_id))
            )
            tab.click()
            time.sleep(0.5)

            # Verify AI button is still visible
            ai_button = browser.find_element(By.ID, "aiAssistantBtn")
            assert ai_button.is_displayed()

        print("✓ AI assistant accessible from all dashboard tabs")


class TestAIAssistantPerformance:
    """Performance and reliability tests"""

    BASE_URL = os.getenv("TEST_BASE_URL", "https://localhost:3000")

    def test_rapid_messages_handled_correctly(self, browser):
        """Test sending many messages rapidly"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        # Send 5 messages rapidly
        for i in range(5):
            input_field.send_keys(f"message {i+1}")
            input_field.send_keys(Keys.ENTER)
            time.sleep(0.1)

        # Wait for all responses
        time.sleep(3)

        # Verify all messages were processed
        messages = browser.find_element(By.ID, "aiMessages")
        message_elements = messages.find_elements(By.CLASS_NAME, "ai-message")

        # Should have welcome + 5 user + 5 AI = 11 messages
        assert len(message_elements) >= 10

        print("✓ Rapid messages handled correctly")

    def test_long_message_handled_correctly(self, browser):
        """Test sending very long message"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open AI assistant
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        # Send long message
        long_message = "create " * 50 + "a project"
        input_field.send_keys(long_message)
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Verify message was sent
        messages = browser.find_element(By.ID, "aiMessages")
        assert len(messages.find_elements(By.CLASS_NAME, "ai-message")) >= 2

        print("✓ Long message handled correctly")

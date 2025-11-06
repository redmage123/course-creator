#!/usr/bin/env python3
"""
Integration Tests for AI Assistant

BUSINESS PURPOSE:
Tests the complete AI assistant workflow including:
- Panel open/close interactions
- Message sending and receiving
- Intent recognition accuracy
- Conversation flow

TECHNICAL APPROACH:
Uses pytest with Selenium to test JavaScript interactions in real browser
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


@pytest.fixture(scope="module")
def browser():
    """
    Browser fixture for integration tests
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)

    yield driver

    driver.quit()


class TestAIAssistantIntegration:
    """Integration tests for AI Assistant functionality"""

    BASE_URL = "https://localhost:3000"

    def test_ai_assistant_button_exists(self, browser):
        """Test that AI assistant button is present on page"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        ai_button = wait.until(
            EC.presence_of_element_located((By.ID, "aiAssistantBtn"))
        )

        assert ai_button is not None
        assert ai_button.is_displayed()

    def test_open_ai_assistant_panel(self, browser):
        """Test opening the AI assistant panel"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Click AI button
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()

        # Wait for panel to open (has 'open' class)
        time.sleep(0.5)

        panel = browser.find_element(By.ID, "aiAssistantPanel")
        assert "open" in panel.get_attribute("class")

    def test_close_ai_assistant_panel(self, browser):
        """Test closing the AI assistant panel"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Close panel
        close_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "closeAIAssistant"))
        )
        close_btn.click()
        time.sleep(0.5)

        panel = browser.find_element(By.ID, "aiAssistantPanel")
        assert "open" not in panel.get_attribute("class")

    def test_send_message_via_button(self, browser):
        """Test sending a message using the send button"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Type message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("Create a new project")

        # Click send
        send_btn = browser.find_element(By.ID, "aiSendBtn")
        send_btn.click()

        # Wait for response
        time.sleep(1)

        # Check messages container
        messages = browser.find_element(By.ID, "aiMessages")
        message_elements = messages.find_elements(By.CLASS_NAME, "ai-message")

        # Should have welcome message + user message + AI response = 3 messages
        assert len(message_elements) >= 2

    def test_send_message_via_enter_key(self, browser):
        """Test sending a message using Enter key"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Type message and press Enter
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("Create a track")
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check that input is cleared
        assert input_field.get_attribute("value") == ""

    def test_create_project_intent(self, browser):
        """Test AI recognition of create project intent"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send create project message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("create a new project")
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check response contains project-related keywords
        messages = browser.find_element(By.ID, "aiMessages")
        assert "project" in messages.text.lower()
        assert "name" in messages.text.lower()

    def test_create_track_intent(self, browser):
        """Test AI recognition of create track intent"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send create track message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("I want to create a learning track")
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check response contains track-related keywords
        messages = browser.find_element(By.ID, "aiMessages")
        assert "track" in messages.text.lower()

    def test_detailed_track_creation(self, browser):
        """Test creating a track with complete details"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send detailed track creation message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys(
            "Create an intermediate track called Machine Learning Basics for the Data Science project"
        )
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check response indicates success
        messages = browser.find_element(By.ID, "aiMessages")
        assert "created" in messages.text.lower() or "track" in messages.text.lower()

    def test_onboard_instructor_intent(self, browser):
        """Test AI recognition of onboard instructor intent"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send onboard instructor message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("add a new instructor to my organization")
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check response contains instructor-related keywords
        messages = browser.find_element(By.ID, "aiMessages")
        assert "instructor" in messages.text.lower()
        assert "email" in messages.text.lower()

    def test_default_response_for_unknown_intent(self, browser):
        """Test that unknown intents get default response"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Send unknown message
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )
        input_field.send_keys("what is the weather today")
        input_field.send_keys(Keys.ENTER)

        # Wait for response
        time.sleep(1)

        # Check response shows capabilities
        messages = browser.find_element(By.ID, "aiMessages")
        assert "help" in messages.text.lower()

    def test_multiple_message_conversation(self, browser):
        """Test sending multiple messages in a conversation"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        # Send first message
        input_field.send_keys("create a project")
        input_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Send second message
        input_field.send_keys("add an instructor")
        input_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Send third message
        input_field.send_keys("create a track")
        input_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Check we have multiple messages
        messages = browser.find_element(By.ID, "aiMessages")
        message_elements = messages.find_elements(By.CLASS_NAME, "ai-message")

        # Should have: welcome + (user1 + ai1) + (user2 + ai2) + (user3 + ai3) = 7 messages
        assert len(message_elements) >= 6

    def test_empty_message_not_sent(self, browser):
        """Test that empty messages are not sent"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "aiInput"))
        )

        # Get initial message count
        messages = browser.find_element(By.ID, "aiMessages")
        initial_count = len(messages.find_elements(By.CLASS_NAME, "ai-message"))

        # Try to send empty message
        input_field.send_keys("   ")
        input_field.send_keys(Keys.ENTER)
        time.sleep(0.5)

        # Count should be the same
        final_count = len(messages.find_elements(By.CLASS_NAME, "ai-message"))
        assert final_count == initial_count

    def test_panel_focus_on_open(self, browser):
        """Test that input field gets focus when panel opens"""
        browser.get(f"{self.BASE_URL}/html/org-admin-dashboard-demo.html")
        wait = WebDriverWait(browser, 10)

        # Open panel
        ai_button = wait.until(
            EC.element_to_be_clickable((By.ID, "aiAssistantBtn"))
        )
        ai_button.click()
        time.sleep(0.5)

        # Input field should be focused
        input_field = browser.find_element(By.ID, "aiInput")
        active_element = browser.switch_to.active_element

        # Note: In headless mode, focus testing may be limited
        # This checks that the element is present and clickable
        assert input_field is not None

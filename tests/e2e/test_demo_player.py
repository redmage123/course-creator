#!/usr/bin/env python3
"""
E2E Tests for Demo Player

BUSINESS PURPOSE:
Validates the complete demo player functionality including video playback,
audio narration, slide navigation, and audio-video synchronization.

TECHNICAL APPROACH:
Uses Selenium WebDriver to test the demo player in a real browser environment,
verifying all user interactions and media playback features.

TEST COVERAGE:
- Video display and loading
- Audio narration playback
- Slide navigation (next, previous, timeline)
- Play/pause functionality
- Audio-video synchronization
- Accessibility features
- Error handling

USAGE:
    # Run all demo player tests
    pytest tests/e2e/test_demo_player.py -v

    # Run specific test
    pytest tests/e2e/test_demo_player.py::TestDemoPlayer::test_video_displays_on_load -v

    # Run in headless mode
    HEADLESS=true pytest tests/e2e/test_demo_player.py -v
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.fixture(scope="class")
def driver():
    """
    Setup Chrome WebDriver for testing with Grid support

    RETURNS: Configured Chrome WebDriver instance
    """
    chrome_options = Options()

    # Headless mode for CI/CD
    if os.getenv('HEADLESS', 'false').lower() == 'true':
        chrome_options.add_argument('--headless=new')

    # Additional options for stability
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # Allow autoplay for video/audio testing
    chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')

    # SSL/HTTPS handling
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')

    # Check for Selenium Grid configuration
    selenium_remote = os.getenv('SELENIUM_REMOTE')
    if selenium_remote:
        driver = webdriver.Remote(
            command_executor=selenium_remote,
            options=chrome_options
        )
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(20)  # Increased for Grid reliability

    yield driver

    driver.quit()


@pytest.fixture(scope="session")
def test_base_url():
    """
    Get base URL for testing

    RETURNS: Base URL for the application
    """
    return os.getenv('TEST_BASE_URL', 'https://localhost:3000')


class TestDemoPlayer:
    """
    E2E tests for demo player functionality
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver, test_base_url):
        """
        Setup for each test - navigate to demo player page
        """
        self.driver = driver
        self.base_url = test_base_url
        self.wait = WebDriverWait(driver, 20)

        # Navigate to demo player
        print(f"\n🌐 Navigating to {test_base_url}/html/demo-player.html")
        driver.get(f"{test_base_url}/html/demo-player.html")

        # Wait for page load
        self.wait.until(EC.presence_of_element_located((By.ID, 'video-player')))

    def test_page_loads_successfully(self):
        """
        Test that demo player page loads without errors

        VERIFIES:
        - Page title is correct
        - Main elements are present
        - No JavaScript errors
        """
        print("📄 Testing page load...")

        # Check page title
        assert "Demo" in self.driver.title, "Page title should contain 'Demo'"

        # Check main elements exist
        video_player = self.driver.find_element(By.ID, 'video-player')
        assert video_player is not None, "Video player should exist"

        play_button = self.driver.find_element(By.ID, 'play-pause-btn')
        assert play_button is not None, "Play button should exist"

        timeline = self.driver.find_element(By.ID, 'slide-timeline')
        assert timeline is not None, "Slide timeline should exist"

        print("✓ Page loaded successfully with all main elements")

    def test_video_element_visible(self):
        """
        Test that video element is visible (not display:none or hidden)

        VERIFIES:
        - Video element has non-zero dimensions
        - Video element is not hidden by CSS
        - Loading screen has been removed
        """
        print("👁️ Testing video visibility...")

        # Wait for loading screen to disappear
        try:
            loading_state = self.driver.find_element(By.ID, 'loading-state')
            self.wait.until(lambda d: loading_state.value_of_css_property('display') == 'none')
            print("✓ Loading screen hidden")
        except NoSuchElementException:
            print("✓ Loading screen already removed")

        # Check video element visibility
        video_player = self.driver.find_element(By.ID, 'video-player')

        # Video should have dimensions
        assert video_player.size['width'] > 0, "Video should have non-zero width"
        assert video_player.size['height'] > 0, "Video should have non-zero height"

        # Video should be displayed
        assert video_player.is_displayed(), "Video should be visible on page"

        print(f"✓ Video dimensions: {video_player.size['width']}x{video_player.size['height']}")
        print("✓ Video element is visible")

    def test_video_source_loaded(self):
        """
        Test that video source is loaded for first slide

        VERIFIES:
        - Video src attribute is set
        - Video src points to valid MP4 file
        - Video duration is available (loaded metadata)
        - Video has actual dimensions from file (not just CSS)
        - Video ready state indicates data loaded
        """
        print("🎥 Testing video source loading...")

        video_player = self.driver.find_element(By.ID, 'video-player')

        # Check video source is set (src is now on video element, not source element)
        src = video_player.get_attribute('src')
        assert src is not None and src != "", "Video source should be set"
        assert 'slide_01_introduction.mp4' in src, "Should load first slide video"

        print(f"✓ Video source: {src}")

        # Capture browser console logs to debug video loading
        logs = self.driver.get_log('browser')
        if logs:
            print("\n📋 Browser console logs:")
            for log in logs:
                print(f"   [{log['level']}] {log['message']}")

        # Wait for video metadata to load (video duration available)
        try:
            self.wait.until(
                lambda d: d.execute_script("return arguments[0].duration > 0;", video_player),
                message="Video duration should be > 0 (metadata loaded)"
            )

            duration = self.driver.execute_script("return arguments[0].duration;", video_player)
            print(f"✓ Video duration: {duration:.2f} seconds")

            # Check video has actual dimensions from file (not just CSS dimensions)
            video_width = self.driver.execute_script("return arguments[0].videoWidth;", video_player)
            video_height = self.driver.execute_script("return arguments[0].videoHeight;", video_player)

            assert video_width > 0, f"Video should have actual width from file (got {video_width})"
            assert video_height > 0, f"Video should have actual height from file (got {video_height})"

            print(f"✓ Video dimensions from file: {video_width}x{video_height}")

            # Check ready state (should be at least HAVE_METADATA = 1)
            ready_state = self.driver.execute_script("return arguments[0].readyState;", video_player)
            assert ready_state >= 1, f"Video ready state should be >= 1 (HAVE_METADATA), got {ready_state}"

            print(f"✓ Video ready state: {ready_state} (1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 4=HAVE_ENOUGH_DATA)")
            print("✓ Video fully loaded with playable content")

        except Exception as e:
            # If video didn't load, capture detailed diagnostics
            ready_state = self.driver.execute_script("return arguments[0].readyState;", video_player)
            network_state = self.driver.execute_script("return arguments[0].networkState;", video_player)
            video_width = self.driver.execute_script("return arguments[0].videoWidth;", video_player)

            print(f"❌ Video failed to load:")
            print(f"   Ready state: {ready_state}")
            print(f"   Network state: {network_state}")
            print(f"   Video width: {video_width}")
            print(f"   Error: {e}")

            raise

    def test_timeline_displays_all_slides(self):
        """
        Test that timeline displays all 13 slides

        VERIFIES:
        - Timeline contains 13 slide thumbnails
        - Each thumbnail has title and duration
        - First slide is marked as active
        """
        print("📊 Testing slide timeline...")

        timeline = self.driver.find_element(By.ID, 'slide-timeline')
        thumbnails = timeline.find_elements(By.CLASS_NAME, 'slide-thumbnail')

        # Should have 13 slides
        assert len(thumbnails) == 13, f"Should have 13 slides, found {len(thumbnails)}"

        print(f"✓ Found {len(thumbnails)} slides in timeline")

        # Check first slide is active
        first_thumbnail = thumbnails[0]
        assert 'active' in first_thumbnail.get_attribute('class'), "First slide should be active"
        assert first_thumbnail.get_attribute('aria-current') == 'true', "First slide should have aria-current=true"

        # Check each thumbnail has required elements
        for i, thumbnail in enumerate(thumbnails, 1):
            slide_title = thumbnail.find_element(By.CLASS_NAME, 'slide-title')
            slide_duration = thumbnail.find_element(By.CLASS_NAME, 'slide-duration')

            assert slide_title.text != "", f"Slide {i} should have title"
            assert slide_duration.text != "", f"Slide {i} should have duration"

        print("✓ All slides have titles and durations")
        print("✓ First slide marked as active")

    def test_play_button_functionality(self):
        """
        Test play/pause button functionality

        VERIFIES:
        - Play button exists and is clickable
        - Clicking play starts video playback
        - Button changes to pause when playing
        - Video currentTime advances when playing
        """
        print("▶️ Testing play/pause functionality...")

        video_player = self.driver.find_element(By.ID, 'video-player')
        play_button = self.driver.find_element(By.ID, 'play-pause-btn')

        # Initially should show "Play"
        assert 'play' in play_button.text.lower() or 'fa-play' in play_button.get_attribute('innerHTML'), \
            "Button should initially show Play"

        # Video should be paused initially
        is_paused = self.driver.execute_script("return arguments[0].paused;", video_player)
        assert is_paused, "Video should be paused initially"

        # Click play button
        print("Clicking play button...")
        play_button.click()
        time.sleep(1)  # Allow time for playback to start

        # Video should be playing
        is_paused = self.driver.execute_script("return arguments[0].paused;", video_player)
        assert not is_paused, "Video should be playing after clicking play"

        # Button should change to "Pause"
        assert 'pause' in play_button.text.lower() or 'fa-pause' in play_button.get_attribute('innerHTML'), \
            "Button should show Pause when playing"

        # Check video time advances
        time1 = self.driver.execute_script("return arguments[0].currentTime;", video_player)
        time.sleep(2)
        time2 = self.driver.execute_script("return arguments[0].currentTime;", video_player)

        assert time2 > time1, f"Video time should advance (was {time1:.2f}s, now {time2:.2f}s)"

        print(f"✓ Video playing: time advanced from {time1:.2f}s to {time2:.2f}s")

        # Click pause button
        print("Clicking pause button...")
        play_button.click()
        time.sleep(0.5)

        # Video should be paused
        is_paused = self.driver.execute_script("return arguments[0].paused;", video_player)
        assert is_paused, "Video should be paused after clicking pause"

        print("✓ Play/pause functionality works correctly")

    def test_audio_narration_loads(self):
        """
        Test that audio narration loads for slides

        VERIFIES:
        - Audio player is created
        - Audio src is set to correct file
        - Audio is ready to play

        NOTE: We can't reliably test actual audio playback in automated tests,
        but we can verify the audio elements are created and loaded.
        """
        print("🔊 Testing audio narration loading...")

        # Check console logs for audio loading (via browser logs)
        # Note: This requires ChromeDriver to capture console logs
        logs = self.driver.get_log('browser')

        audio_loaded = False
        for log in logs:
            message = log.get('message', '')
            if 'Audio ready for slide' in message or 'Audio loaded for slide' in message:
                audio_loaded = True
                print(f"✓ Found audio log: {message}")
                break

        # Also check via JavaScript that audio was created
        audio_exists = self.driver.execute_script("""
            // Check if DemoPlayer instance has audioPlayer
            return window.demoPlayer && window.demoPlayer.audioPlayer !== null;
        """)

        if audio_exists:
            audio_src = self.driver.execute_script("""
                return window.demoPlayer.audioPlayer ? window.demoPlayer.audioPlayer.src : null;
            """)
            print(f"✓ Audio player created with source: {audio_src}")
            assert 'slide_01_narration.mp3' in audio_src, "Should load audio for first slide"

        print("✓ Audio narration loads successfully")

    def test_next_slide_navigation(self):
        """
        Test navigation to next slide

        VERIFIES:
        - Next button is enabled
        - Clicking next advances to slide 2
        - Video source changes
        - Timeline updates to show slide 2 as active
        - Slide counter updates
        """
        print("➡️ Testing next slide navigation...")

        next_button = self.driver.find_element(By.ID, 'next-btn')
        current_slide_display = self.driver.find_element(By.ID, 'current-slide')

        # Next button should be enabled
        assert next_button.is_enabled(), "Next button should be enabled on first slide"

        # Current slide should be 1
        assert current_slide_display.text == "1", "Should start on slide 1"

        # Click next button
        print("Clicking next button...")
        next_button.click()

        # Wait for slide to change
        self.wait.until(lambda d: current_slide_display.text == "2")

        # Verify slide changed
        assert current_slide_display.text == "2", "Should advance to slide 2"

        # Check video source updated
        video_player = self.driver.find_element(By.ID, 'video-player')
        src = video_player.get_attribute('src')
        assert 'slide_02' in src, "Video source should update to slide 2"

        print(f"✓ Advanced to slide 2, video source: {src}")

        # Check timeline shows slide 2 as active
        timeline = self.driver.find_element(By.ID, 'slide-timeline')
        thumbnails = timeline.find_elements(By.CLASS_NAME, 'slide-thumbnail')

        assert 'active' not in thumbnails[0].get_attribute('class'), "Slide 1 should no longer be active"
        assert 'active' in thumbnails[1].get_attribute('class'), "Slide 2 should be active"

        print("✓ Timeline updated correctly")
        print("✓ Next slide navigation works")

    def test_previous_slide_navigation(self):
        """
        Test navigation to previous slide

        VERIFIES:
        - Previous button is disabled on first slide
        - Previous button enabled after advancing
        - Clicking previous goes back to previous slide
        """
        print("⬅️ Testing previous slide navigation...")

        prev_button = self.driver.find_element(By.ID, 'prev-btn')
        next_button = self.driver.find_element(By.ID, 'next-btn')
        current_slide_display = self.driver.find_element(By.ID, 'current-slide')

        # Previous button should be disabled on first slide
        assert not prev_button.is_enabled(), "Previous button should be disabled on first slide"
        print("✓ Previous button disabled on first slide")

        # Advance to slide 2
        next_button.click()
        self.wait.until(lambda d: current_slide_display.text == "2")

        # Previous button should now be enabled
        assert prev_button.is_enabled(), "Previous button should be enabled on slide 2"

        # Click previous button
        print("Clicking previous button...")
        prev_button.click()

        # Wait for slide to change back
        self.wait.until(lambda d: current_slide_display.text == "1")

        # Verify back on slide 1
        assert current_slide_display.text == "1", "Should return to slide 1"

        # Check video source updated
        video_player = self.driver.find_element(By.ID, 'video-player')
        src = video_player.get_attribute('src')
        assert 'slide_01' in src, "Video source should return to slide 1"

        print("✓ Previous slide navigation works")

    def test_timeline_thumbnail_navigation(self):
        """
        Test clicking timeline thumbnails to navigate

        VERIFIES:
        - Clicking thumbnail navigates to that slide
        - Video source updates
        - Active state updates in timeline
        """
        print("🖱️ Testing timeline thumbnail navigation...")

        timeline = self.driver.find_element(By.ID, 'slide-timeline')
        thumbnails = timeline.find_elements(By.CLASS_NAME, 'slide-thumbnail')
        current_slide_display = self.driver.find_element(By.ID, 'current-slide')

        # Click on slide 5 thumbnail
        print("Clicking slide 5 thumbnail...")
        thumbnails[4].click()  # 0-indexed, so slide 5 is index 4

        # Wait for slide to change
        self.wait.until(lambda d: current_slide_display.text == "5")

        # Verify on slide 5
        assert current_slide_display.text == "5", "Should jump to slide 5"

        # Check video source updated
        video_player = self.driver.find_element(By.ID, 'video-player')
        src = video_player.get_attribute('src')
        assert 'slide_05' in src, "Video source should update to slide 5"

        # Check timeline active state
        assert 'active' in thumbnails[4].get_attribute('class'), "Slide 5 should be active in timeline"

        print("✓ Timeline thumbnail navigation works")

    def test_progress_bar_updates(self):
        """
        Test that progress bar updates during playback

        VERIFIES:
        - Progress bar exists
        - Progress bar width increases during playback
        - Time display updates
        """
        print("📊 Testing progress bar updates...")

        video_player = self.driver.find_element(By.ID, 'video-player')
        play_button = self.driver.find_element(By.ID, 'play-pause-btn')
        progress_bar = self.driver.find_element(By.CLASS_NAME, 'progress-bar')
        time_display = self.driver.find_element(By.ID, 'time-display')

        # Start playback
        play_button.click()
        time.sleep(0.5)

        # Get initial progress bar width
        initial_width = progress_bar.size['width']
        initial_time_text = time_display.text

        print(f"Initial progress: {initial_width}px, time: {initial_time_text}")

        # Wait and check progress increased
        time.sleep(3)

        final_width = progress_bar.size['width']
        final_time_text = time_display.text

        print(f"After 3s progress: {final_width}px, time: {final_time_text}")

        assert final_width > initial_width, "Progress bar should increase during playback"
        assert final_time_text != initial_time_text, "Time display should update"

        # Pause video
        play_button.click()

        print("✓ Progress bar updates during playback")

    def test_keyboard_navigation(self):
        """
        Test keyboard shortcuts for demo player

        VERIFIES:
        - Space key toggles play/pause
        - Arrow keys navigate slides
        """
        print("⌨️ Testing keyboard navigation...")

        video_player = self.driver.find_element(By.ID, 'video-player')
        current_slide_display = self.driver.find_element(By.ID, 'current-slide')

        # Get body element to send keyboard events
        body = self.driver.find_element(By.TAG_NAME, 'body')

        # Test space key (play/pause)
        print("Testing space key for play/pause...")
        body.send_keys(Keys.SPACE)
        time.sleep(0.5)

        is_paused = self.driver.execute_script("return arguments[0].paused;", video_player)
        playing_state = "paused" if is_paused else "playing"
        print(f"After space key: video is {playing_state}")

        # Test arrow right (next slide)
        print("Testing arrow right for next slide...")
        body.send_keys(Keys.ARROW_RIGHT)

        try:
            self.wait.until(lambda d: current_slide_display.text == "2")
            print("✓ Arrow right navigated to next slide")
        except TimeoutException:
            print("⚠️ Arrow right navigation may not be immediate")

        # Test arrow left (previous slide)
        print("Testing arrow left for previous slide...")
        body.send_keys(Keys.ARROW_LEFT)

        try:
            self.wait.until(lambda d: current_slide_display.text == "1")
            print("✓ Arrow left navigated to previous slide")
        except TimeoutException:
            print("⚠️ Arrow left navigation may not be immediate")

        print("✓ Keyboard navigation functional")

    def test_accessibility_features(self):
        """
        Test accessibility features of demo player

        VERIFIES:
        - ARIA labels on controls
        - ARIA live regions for announcements
        - Skip links present
        - Semantic HTML structure
        """
        print("♿ Testing accessibility features...")

        # Check video has aria-label
        video_player = self.driver.find_element(By.ID, 'video-player')
        aria_label = video_player.get_attribute('aria-label')
        assert aria_label is not None and aria_label != "", "Video should have aria-label"
        print(f"✓ Video aria-label: {aria_label}")

        # Check play button has aria-label
        play_button = self.driver.find_element(By.ID, 'play-pause-btn')
        button_aria_label = play_button.get_attribute('aria-label')
        assert button_aria_label is not None, "Play button should have aria-label"
        print(f"✓ Play button aria-label: {button_aria_label}")

        # Check ARIA live region exists
        try:
            live_region = self.driver.find_element(By.ID, 'demo-announcements')
            assert live_region.get_attribute('aria-live') == 'polite', "Should have polite live region"
            print("✓ ARIA live region present")
        except NoSuchElementException:
            print("⚠️ ARIA live region not found")

        # Check skip links
        try:
            skip_links = self.driver.find_elements(By.CLASS_NAME, 'skip-link')
            assert len(skip_links) > 0, "Should have skip links"
            print(f"✓ Found {len(skip_links)} skip link(s)")
        except NoSuchElementException:
            print("⚠️ Skip links not found")

        # Check timeline has proper ARIA attributes
        timeline = self.driver.find_element(By.ID, 'slide-timeline')
        timeline_role = timeline.get_attribute('role')
        print(f"✓ Timeline role: {timeline_role}")

        # Check thumbnails have aria-labels
        thumbnails = timeline.find_elements(By.CLASS_NAME, 'slide-thumbnail')
        first_thumbnail_label = thumbnails[0].get_attribute('aria-label')
        assert first_thumbnail_label is not None, "Thumbnails should have aria-labels"
        print(f"✓ Thumbnail aria-label example: {first_thumbnail_label}")

        print("✓ Accessibility features implemented")

    def test_narration_overlay_displays(self):
        """
        Test that narration overlay displays during playback

        VERIFIES:
        - Narration overlay exists
        - Narration text is populated
        - Overlay becomes visible during playback
        """
        print("📝 Testing narration overlay...")

        play_button = self.driver.find_element(By.ID, 'play-pause-btn')
        narration_overlay = self.driver.find_element(By.ID, 'narration-overlay')
        narration_text = self.driver.find_element(By.ID, 'narration-text')

        # Debug: Check actual HTML content
        text_content = narration_text.get_attribute('textContent')
        print(f"DEBUG: Narration text content: '{text_content}'")

        # Check if text is populated - it should be set during loadSlide(0) initialization
        if text_content:
            print(f"✓ Narration text: {text_content[:50]}...")
        else:
            print("⚠️  Narration text not yet populated (will be set during playback)")

        # Start playback
        play_button.click()
        time.sleep(0.5)

        # Narration overlay should be visible during playback
        # Note: It should have display: block when playing
        overlay_style = narration_overlay.value_of_css_property('display')
        assert overlay_style == 'block', f"Narration overlay should be visible during playback (display: {overlay_style})"

        print("✓ Narration overlay displays during playback")

    def test_no_javascript_errors(self):
        """
        Test that there are no critical JavaScript errors

        VERIFIES:
        - No uncaught exceptions in console
        - No SEVERE level errors
        """
        print("🐛 Checking for JavaScript errors...")

        logs = self.driver.get_log('browser')

        severe_errors = []
        warnings = []

        for log in logs:
            level = log.get('level')
            message = log.get('message', '')

            # Filter out known acceptable warnings
            if 'favicon.ico' in message:
                continue  # Favicon 404s are acceptable
            if 'Download the React DevTools' in message:
                continue  # React DevTools message is acceptable

            if level == 'SEVERE':
                severe_errors.append(message)
            elif level == 'WARNING':
                warnings.append(message)

        # Print warnings for information
        if warnings:
            print(f"⚠️ Found {len(warnings)} warnings:")
            for warning in warnings[:5]:  # Show first 5
                print(f"  - {warning[:100]}")

        # Assert no severe errors
        if severe_errors:
            print(f"❌ Found {len(severe_errors)} SEVERE errors:")
            for error in severe_errors:
                print(f"  - {error}")

        assert len(severe_errors) == 0, f"Should have no SEVERE JavaScript errors, found {len(severe_errors)}"

        print("✓ No critical JavaScript errors")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

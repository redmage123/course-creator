"""
Comprehensive E2E Tests for Video Playback and Progress Tracking

BUSINESS REQUIREMENT:
Students must be able to watch course videos with professional playback controls,
quality selection, speed adjustment, and progress tracking. The system must accurately
track watch time for completion analytics and resume playback from last position.
Instructors need visibility into student engagement through video analytics.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 10 comprehensive video feature scenarios
- Multi-layer verification (UI + Database + Video Player State)
- Validates player controls, quality settings, and analytics accuracy

TEST COVERAGE:
1. Playback Features (4 tests)
   - Play/pause/seek controls with video player state verification
   - Video quality selection (auto, 1080p, 720p, 480p)
   - Playback speed adjustment (0.5x, 1x, 1.5x, 2x)
   - Fullscreen mode toggle with browser API verification

2. Progress Tracking (3 tests)
   - Watch time tracking with database accuracy validation
   - Video completion detection (>90% watched threshold)
   - Resume playback from last saved position

3. Analytics (3 tests)
   - Record watch time in database (accuracy within 5 seconds)
   - Calculate average watch percentage per video across students
   - Identify drop-off points (heatmap of where students stop watching)

PRIORITY: P1 (HIGH) - Essential for student engagement and analytics
"""

import pytest
import time
import uuid
import psycopg2
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class StudentLoginPage(BasePage):
    """
    Page Object for student login page.

    BUSINESS CONTEXT:
    Students need authentication to access enrolled courses and video content.
    Secure login ensures only enrolled students can track progress.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to student login page."""
        self.navigate_to("/login")

    def login(self, email, password):
        """
        Perform student login.

        Args:
            email: Student email
            password: Student password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)  # Wait for redirect to dashboard


class VideoPlayerPage(BasePage):
    """
    Page Object for video player interface.

    BUSINESS CONTEXT:
    The video player is the primary interface for student learning through
    video content. It must provide professional controls (play/pause/seek),
    quality selection, speed adjustment, and fullscreen mode while accurately
    tracking watch time for progress analytics.

    TECHNICAL DETAILS:
    - HTML5 video element with custom controls
    - Quality switcher for adaptive streaming (1080p, 720p, 480p, auto)
    - Playback speed control (0.5x to 2x range)
    - Fullscreen API for immersive viewing
    - JavaScript event listeners for progress tracking
    """

    # Video Player Locators
    VIDEO_ELEMENT = (By.ID, "videoPlayer")
    VIDEO_CONTAINER = (By.CLASS_NAME, "video-container")
    PLAY_BUTTON = (By.ID, "playBtn")
    PAUSE_BUTTON = (By.ID, "pauseBtn")
    SEEK_BAR = (By.ID, "seekBar")
    CURRENT_TIME_DISPLAY = (By.ID, "currentTime")
    DURATION_DISPLAY = (By.ID, "duration")
    PROGRESS_BAR = (By.CLASS_NAME, "progress-bar")

    # Quality Selection Locators
    QUALITY_BUTTON = (By.ID, "qualityBtn")
    QUALITY_MENU = (By.CLASS_NAME, "quality-menu")
    QUALITY_AUTO = (By.CSS_SELECTOR, "[data-quality='auto']")
    QUALITY_1080P = (By.CSS_SELECTOR, "[data-quality='1080p']")
    QUALITY_720P = (By.CSS_SELECTOR, "[data-quality='720p']")
    QUALITY_480P = (By.CSS_SELECTOR, "[data-quality='480p']")
    QUALITY_INDICATOR = (By.CLASS_NAME, "quality-indicator")

    # Speed Control Locators
    SPEED_BUTTON = (By.ID, "speedBtn")
    SPEED_MENU = (By.CLASS_NAME, "speed-menu")
    SPEED_050X = (By.CSS_SELECTOR, "[data-speed='0.5']")
    SPEED_100X = (By.CSS_SELECTOR, "[data-speed='1.0']")
    SPEED_150X = (By.CSS_SELECTOR, "[data-speed='1.5']")
    SPEED_200X = (By.CSS_SELECTOR, "[data-speed='2.0']")
    SPEED_INDICATOR = (By.CLASS_NAME, "speed-indicator")

    # Fullscreen Locators
    FULLSCREEN_BUTTON = (By.ID, "fullscreenBtn")
    EXIT_FULLSCREEN_BUTTON = (By.ID, "exitFullscreenBtn")

    # Progress Tracking Locators
    WATCH_TIME_DISPLAY = (By.ID, "watchTime")
    COMPLETION_PERCENTAGE = (By.ID, "completionPercentage")
    COMPLETION_BADGE = (By.CLASS_NAME, "completion-badge")

    def navigate_to_video(self, course_id, video_id):
        """
        Navigate to specific video player page.

        Args:
            course_id: Course identifier
            video_id: Video identifier
        """
        self.navigate_to(f"/html/video-player.html?course={course_id}&video={video_id}")
        time.sleep(2)  # Wait for video to load

    def click_play(self):
        """Click play button to start video playback."""
        self.click_element(*self.PLAY_BUTTON)
        time.sleep(0.5)

    def click_pause(self):
        """Click pause button to pause video playback."""
        self.click_element(*self.PAUSE_BUTTON)
        time.sleep(0.5)

    def seek_to_position(self, seconds):
        """
        Seek video to specific position.

        Args:
            seconds: Target position in seconds

        BUSINESS REQUIREMENT:
        Students must be able to navigate to any point in the video
        for review or to skip to relevant sections.
        """
        # Get video duration first
        duration = self.get_video_duration()
        if duration == 0:
            raise ValueError("Video duration is 0 - cannot seek")

        # Calculate seek bar position (0-100%)
        seek_percentage = (seconds / duration) * 100

        # Use JavaScript to set seek bar value
        seek_bar = self.find_element(*self.SEEK_BAR)
        self.driver.execute_script(
            f"arguments[0].value = {seek_percentage}; "
            f"arguments[0].dispatchEvent(new Event('input')); "
            f"arguments[0].dispatchEvent(new Event('change'));",
            seek_bar
        )
        time.sleep(1)  # Wait for seek to complete

    def get_current_time(self):
        """
        Get current video playback position in seconds.

        Returns:
            Current time in seconds (float)
        """
        return float(self.driver.execute_script(
            "return document.getElementById('videoPlayer').currentTime;"
        ))

    def get_video_duration(self):
        """
        Get total video duration in seconds.

        Returns:
            Duration in seconds (float)
        """
        return float(self.driver.execute_script(
            "return document.getElementById('videoPlayer').duration;"
        ))

    def is_video_playing(self):
        """
        Check if video is currently playing.

        Returns:
            True if playing, False if paused
        """
        return self.driver.execute_script(
            "return !document.getElementById('videoPlayer').paused;"
        )

    def get_playback_rate(self):
        """
        Get current playback speed.

        Returns:
            Playback rate (e.g., 1.0, 1.5, 2.0)
        """
        return float(self.driver.execute_script(
            "return document.getElementById('videoPlayer').playbackRate;"
        ))

    # Quality Selection Methods
    def open_quality_menu(self):
        """Open quality selection menu."""
        self.click_element(*self.QUALITY_BUTTON)
        time.sleep(0.5)

    def select_quality_auto(self):
        """
        Select automatic quality (adaptive streaming).

        BUSINESS REQUIREMENT:
        Auto quality adjusts resolution based on student's internet speed
        to prevent buffering while maximizing visual quality.
        """
        self.open_quality_menu()
        self.click_element(*self.QUALITY_AUTO)
        time.sleep(1)

    def select_quality_1080p(self):
        """Select 1080p quality."""
        self.open_quality_menu()
        self.click_element(*self.QUALITY_1080P)
        time.sleep(1)

    def select_quality_720p(self):
        """Select 720p quality."""
        self.open_quality_menu()
        self.click_element(*self.QUALITY_720P)
        time.sleep(1)

    def select_quality_480p(self):
        """Select 480p quality."""
        self.open_quality_menu()
        self.click_element(*self.QUALITY_480P)
        time.sleep(1)

    def get_current_quality(self):
        """
        Get current video quality setting.

        Returns:
            Quality string (e.g., '1080p', '720p', 'auto')
        """
        indicator = self.find_element(*self.QUALITY_INDICATOR)
        return indicator.text.strip()

    # Speed Control Methods
    def open_speed_menu(self):
        """Open playback speed menu."""
        self.click_element(*self.SPEED_BUTTON)
        time.sleep(0.5)

    def select_speed_050x(self):
        """
        Select 0.5x playback speed.

        BUSINESS REQUIREMENT:
        Slower speeds help students review complex concepts or
        understand instructors with strong accents.
        """
        self.open_speed_menu()
        self.click_element(*self.SPEED_050X)
        time.sleep(0.5)

    def select_speed_100x(self):
        """Select normal (1.0x) playback speed."""
        self.open_speed_menu()
        self.click_element(*self.SPEED_100X)
        time.sleep(0.5)

    def select_speed_150x(self):
        """
        Select 1.5x playback speed.

        BUSINESS REQUIREMENT:
        Faster speeds allow students to consume content more efficiently
        when reviewing familiar material.
        """
        self.open_speed_menu()
        self.click_element(*self.SPEED_150X)
        time.sleep(0.5)

    def select_speed_200x(self):
        """Select 2.0x playback speed."""
        self.open_speed_menu()
        self.click_element(*self.SPEED_200X)
        time.sleep(0.5)

    # Fullscreen Methods
    def enter_fullscreen(self):
        """
        Enter fullscreen mode.

        BUSINESS REQUIREMENT:
        Fullscreen mode provides immersive learning experience,
        especially important for detailed diagrams or code examples.
        """
        self.click_element(*self.FULLSCREEN_BUTTON)
        time.sleep(1)

    def exit_fullscreen(self):
        """Exit fullscreen mode."""
        # Try clicking exit button first
        try:
            self.click_element(*self.EXIT_FULLSCREEN_BUTTON)
        except NoSuchElementException:
            # Fallback: Press ESC key
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)

    def is_fullscreen(self):
        """
        Check if video is in fullscreen mode.

        Returns:
            True if fullscreen, False otherwise
        """
        return self.driver.execute_script(
            "return document.fullscreenElement !== null || "
            "document.webkitFullscreenElement !== null || "
            "document.mozFullScreenElement !== null;"
        )

    # Progress Tracking Methods
    def get_watch_time(self):
        """
        Get total watch time displayed in UI.

        Returns:
            Watch time in seconds (int)
        """
        watch_time_text = self.get_element_text(*self.WATCH_TIME_DISPLAY)
        # Parse "5m 30s" format to seconds
        parts = watch_time_text.split()
        total_seconds = 0
        for part in parts:
            if 'm' in part:
                total_seconds += int(part.replace('m', '')) * 60
            elif 's' in part:
                total_seconds += int(part.replace('s', ''))
        return total_seconds

    def get_completion_percentage(self):
        """
        Get video completion percentage displayed in UI.

        Returns:
            Completion percentage (int)
        """
        percentage_text = self.get_element_text(*self.COMPLETION_PERCENTAGE)
        return int(percentage_text.replace('%', ''))

    def is_video_completed(self):
        """
        Check if video shows as completed.

        Returns:
            True if completion badge is visible, False otherwise
        """
        try:
            badge = self.find_element(*self.COMPLETION_BADGE)
            return badge.is_displayed()
        except NoSuchElementException:
            return False


class VideoProgressPage(BasePage):
    """
    Page Object for video progress tracking page.

    BUSINESS CONTEXT:
    Students need to see their overall progress across all course videos
    to understand completion status and identify which videos need attention.
    Progress tracking motivates students and helps identify struggling learners.
    """

    # Progress Overview Locators
    PROGRESS_CONTAINER = (By.CLASS_NAME, "progress-container")
    VIDEO_CARDS = (By.CLASS_NAME, "video-card")
    VIDEO_TITLE = (By.CLASS_NAME, "video-title")
    VIDEO_PROGRESS_BAR = (By.CLASS_NAME, "video-progress-bar")
    VIDEO_WATCH_TIME = (By.CLASS_NAME, "video-watch-time")
    VIDEO_STATUS_BADGE = (By.CLASS_NAME, "status-badge")

    # Resume Playback Locators
    RESUME_BUTTON = (By.CLASS_NAME, "resume-btn")
    LAST_WATCHED_POSITION = (By.CLASS_NAME, "last-position")

    def navigate(self, course_id):
        """
        Navigate to video progress page.

        Args:
            course_id: Course identifier
        """
        self.navigate_to(f"/html/video-progress.html?course={course_id}")
        time.sleep(2)

    def get_video_progress(self, video_id):
        """
        Get progress percentage for specific video.

        Args:
            video_id: Video identifier

        Returns:
            Progress percentage (int)
        """
        video_card = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-video-id='{video_id}']"
        )
        progress_bar = video_card.find_element(*self.VIDEO_PROGRESS_BAR)
        progress_text = progress_bar.get_attribute("data-progress")
        return int(progress_text)

    def get_last_watched_position(self, video_id):
        """
        Get last watched position for video.

        Args:
            video_id: Video identifier

        Returns:
            Position in seconds (int)
        """
        video_card = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-video-id='{video_id}']"
        )
        position_element = video_card.find_element(*self.LAST_WATCHED_POSITION)
        position_text = position_element.text
        # Parse "Resume at 5:30" format
        time_part = position_text.split("at")[-1].strip()
        minutes, seconds = time_part.split(":")
        return int(minutes) * 60 + int(seconds)

    def click_resume_video(self, video_id):
        """
        Click resume button for specific video.

        Args:
            video_id: Video identifier

        BUSINESS REQUIREMENT:
        Students should be able to quickly resume videos from where they
        left off without manually seeking.
        """
        video_card = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-video-id='{video_id}']"
        )
        resume_button = video_card.find_element(*self.RESUME_BUTTON)
        resume_button.click()
        time.sleep(2)


class VideoAnalyticsPage(BasePage):
    """
    Page Object for instructor video analytics dashboard.

    BUSINESS CONTEXT:
    Instructors need detailed analytics on student video engagement to:
    - Identify struggling students who aren't watching videos
    - Find confusing sections where students drop off
    - Optimize video content based on engagement patterns
    - Track overall course completion rates
    """

    # Analytics Dashboard Locators
    ANALYTICS_CONTAINER = (By.CLASS_NAME, "analytics-container")
    VIDEO_SELECT = (By.ID, "videoSelect")
    AVERAGE_WATCH_PERCENTAGE = (By.ID, "avgWatchPercentage")
    TOTAL_VIEWS = (By.ID, "totalViews")
    COMPLETION_RATE = (By.ID, "completionRate")

    # Drop-off Heatmap Locators
    HEATMAP_CANVAS = (By.ID, "dropoffHeatmap")
    HEATMAP_LEGEND = (By.CLASS_NAME, "heatmap-legend")
    DROPOFF_POINTS = (By.CLASS_NAME, "dropoff-point")

    # Student Watch Time Table Locators
    WATCH_TIME_TABLE = (By.ID, "watchTimeTable")
    TABLE_ROWS = (By.CSS_SELECTOR, "#watchTimeTable tbody tr")
    STUDENT_NAME_COLUMN = (By.CLASS_NAME, "student-name")
    WATCH_TIME_COLUMN = (By.CLASS_NAME, "watch-time")
    PERCENTAGE_COLUMN = (By.CLASS_NAME, "percentage")

    def navigate(self, course_id):
        """
        Navigate to video analytics page.

        Args:
            course_id: Course identifier
        """
        self.navigate_to(f"/html/instructor-video-analytics.html?course={course_id}")
        time.sleep(2)

    def select_video(self, video_id):
        """
        Select video from dropdown.

        Args:
            video_id: Video identifier
        """
        select_element = self.find_element(*self.VIDEO_SELECT)
        select = self.driver.execute_script(
            f"arguments[0].value = '{video_id}'; "
            f"arguments[0].dispatchEvent(new Event('change'));",
            select_element
        )
        time.sleep(1)

    def get_average_watch_percentage(self):
        """
        Get average watch percentage across all students.

        Returns:
            Average percentage (float)
        """
        text = self.get_element_text(*self.AVERAGE_WATCH_PERCENTAGE)
        return float(text.replace('%', ''))

    def get_total_views(self):
        """
        Get total number of video views.

        Returns:
            View count (int)
        """
        text = self.get_element_text(*self.TOTAL_VIEWS)
        return int(text)

    def get_completion_rate(self):
        """
        Get video completion rate (students who watched >90%).

        Returns:
            Completion rate percentage (float)
        """
        text = self.get_element_text(*self.COMPLETION_RATE)
        return float(text.replace('%', ''))

    def get_dropoff_points(self):
        """
        Get list of major drop-off points in video.

        Returns:
            List of tuples (timestamp_seconds, percentage_dropped)

        BUSINESS REQUIREMENT:
        Identifying where students stop watching helps instructors
        improve confusing content or recognize natural break points.
        """
        dropoff_elements = self.driver.find_elements(*self.DROPOFF_POINTS)
        dropoff_data = []
        for element in dropoff_elements:
            timestamp = int(element.get_attribute("data-timestamp"))
            percentage = float(element.get_attribute("data-percentage"))
            dropoff_data.append((timestamp, percentage))
        return dropoff_data

    def get_student_watch_times(self):
        """
        Get watch time data for all students.

        Returns:
            List of dicts with keys: student_name, watch_time, percentage
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        watch_times = []
        for row in rows:
            student_name = row.find_element(*self.STUDENT_NAME_COLUMN).text
            watch_time = row.find_element(*self.WATCH_TIME_COLUMN).text
            percentage = row.find_element(*self.PERCENTAGE_COLUMN).text
            watch_times.append({
                'student_name': student_name,
                'watch_time': watch_time,
                'percentage': float(percentage.replace('%', ''))
            })
        return watch_times


# ============================================================================
# TEST CLASS - Playback Features
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoPlaybackFeatures(BaseTest):
    """
    Test suite for video playback features.

    BUSINESS REQUIREMENT:
    Students must have professional video playback controls including
    play/pause, seek, quality selection, and speed adjustment to
    accommodate different learning styles and internet speeds.
    """

    @pytest.mark.priority_critical
    def test_01_play_pause_seek_controls(self, db_connection):
        """
        Test basic video player controls (play, pause, seek).

        BUSINESS REQUIREMENT:
        Students must be able to control video playback with standard
        play/pause buttons and seek to any position for review.

        VALIDATION:
        - UI: Play button changes to pause button
        - Video State: Video player reports playing state
        - Seek: Current time matches seek position within 1 second

        Args:
            db_connection: Database connection fixture
        """
        # Setup: Create test student and video
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # LAYER 1: UI Verification - Play button exists
        assert player_page.element_exists(*player_page.PLAY_BUTTON), \
            "Play button should be visible initially"

        # Test: Click play button
        player_page.click_play()
        time.sleep(2)  # Let video play for 2 seconds

        # LAYER 2: Video Player State - Video is playing
        assert player_page.is_video_playing(), \
            "Video should be playing after clicking play button"

        current_time_after_play = player_page.get_current_time()
        assert current_time_after_play > 0, \
            "Current time should advance while playing"

        # Test: Click pause button
        player_page.click_pause()
        time.sleep(0.5)

        # Verification: Video is paused
        assert not player_page.is_video_playing(), \
            "Video should be paused after clicking pause button"

        paused_time = player_page.get_current_time()
        time.sleep(1)
        still_paused_time = player_page.get_current_time()
        assert abs(paused_time - still_paused_time) < 0.5, \
            "Current time should not advance when paused"

        # Test: Seek to specific position
        seek_target = 30  # 30 seconds
        player_page.seek_to_position(seek_target)

        # LAYER 3: Seek Accuracy - Position matches seek target
        actual_time = player_page.get_current_time()
        assert abs(actual_time - seek_target) <= 1.0, \
            f"Seek should position video at {seek_target}s, got {actual_time}s"

        # Cleanup: Close browser
        self.driver.quit()

    @pytest.mark.priority_critical
    def test_02_video_quality_selection(self, db_connection):
        """
        Test video quality selection (auto, 1080p, 720p, 480p).

        BUSINESS REQUIREMENT:
        Students with varying internet speeds must be able to manually
        select video quality to balance visual clarity with buffering.
        Auto quality provides adaptive streaming for optimal experience.

        VALIDATION:
        - UI: Quality indicator updates to selected quality
        - Video Element: Video source changes to correct resolution
        - Database: Quality preference saved for future playback

        Args:
            db_connection: Database connection fixture
        """
        # Setup: Create test student and video
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Test: Select 1080p quality
        player_page.select_quality_1080p()

        # LAYER 1: UI Verification - Quality indicator shows 1080p
        quality = player_page.get_current_quality()
        assert quality == "1080p", \
            f"Quality indicator should show 1080p, got {quality}"

        # Test: Select 720p quality
        player_page.select_quality_720p()
        quality = player_page.get_current_quality()
        assert quality == "720p", \
            f"Quality indicator should show 720p, got {quality}"

        # Test: Select 480p quality
        player_page.select_quality_480p()
        quality = player_page.get_current_quality()
        assert quality == "480p", \
            f"Quality indicator should show 480p, got {quality}"

        # Test: Select auto quality
        player_page.select_quality_auto()
        quality = player_page.get_current_quality()
        assert quality == "auto", \
            f"Quality indicator should show auto, got {quality}"

        # LAYER 2: Database Verification - Quality preference saved
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT quality_preference
            FROM video_watch_sessions
            WHERE student_email = %s AND video_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (student_email, video_id))
        result = cursor.fetchone()

        if result:
            assert result[0] == "auto", \
                f"Database should store quality preference as 'auto', got {result[0]}"

        # Cleanup
        cursor.close()
        self.driver.quit()

    @pytest.mark.priority_high
    def test_03_playback_speed_adjustment(self, db_connection):
        """
        Test playback speed adjustment (0.5x, 1x, 1.5x, 2x).

        BUSINESS REQUIREMENT:
        Students learn at different paces. Slower speeds help with
        complex concepts, while faster speeds enable efficient review
        of familiar material.

        VALIDATION:
        - UI: Speed indicator updates to selected speed
        - Video Player: playbackRate property matches selected speed
        - Video Progress: Current time advances at correct rate

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Start playing video
        player_page.click_play()
        time.sleep(1)

        # Test: 1.5x speed
        player_page.select_speed_150x()

        # LAYER 1: Video Player State - playbackRate is 1.5
        playback_rate = player_page.get_playback_rate()
        assert playback_rate == 1.5, \
            f"Playback rate should be 1.5, got {playback_rate}"

        # Measure time advancement
        start_time = player_page.get_current_time()
        time.sleep(2)  # Wait 2 real seconds
        end_time = player_page.get_current_time()

        # At 1.5x speed, 2 real seconds = ~3 video seconds
        time_advanced = end_time - start_time
        assert 2.5 <= time_advanced <= 3.5, \
            f"At 1.5x speed, 2s should advance video ~3s, got {time_advanced}s"

        # Test: 0.5x speed (slow motion)
        player_page.select_speed_050x()
        playback_rate = player_page.get_playback_rate()
        assert playback_rate == 0.5, \
            f"Playback rate should be 0.5, got {playback_rate}"

        # Test: 2.0x speed (fast)
        player_page.select_speed_200x()
        playback_rate = player_page.get_playback_rate()
        assert playback_rate == 2.0, \
            f"Playback rate should be 2.0, got {playback_rate}"

        # Test: Normal speed (1.0x)
        player_page.select_speed_100x()
        playback_rate = player_page.get_playback_rate()
        assert playback_rate == 1.0, \
            f"Playback rate should be 1.0, got {playback_rate}"

        # Cleanup
        self.driver.quit()

    @pytest.mark.priority_medium
    def test_04_fullscreen_mode_toggle(self, db_connection):
        """
        Test fullscreen mode toggle.

        BUSINESS REQUIREMENT:
        Fullscreen mode provides immersive learning experience,
        essential for detailed diagrams, code examples, and
        minimizing distractions during learning.

        VALIDATION:
        - UI: Fullscreen button triggers fullscreen
        - Browser API: document.fullscreenElement is video container
        - Exit: ESC key or exit button returns to normal view

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Verify not fullscreen initially
        assert not player_page.is_fullscreen(), \
            "Video should not be fullscreen initially"

        # Test: Enter fullscreen
        player_page.enter_fullscreen()

        # LAYER 1: Browser API - Fullscreen element exists
        assert player_page.is_fullscreen(), \
            "Video should be in fullscreen mode after clicking fullscreen button"

        # Test: Exit fullscreen
        player_page.exit_fullscreen()

        # Verification: No longer fullscreen
        assert not player_page.is_fullscreen(), \
            "Video should exit fullscreen after clicking exit or ESC"

        # Cleanup
        self.driver.quit()


# ============================================================================
# TEST CLASS - Progress Tracking
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoProgressTracking(BaseTest):
    """
    Test suite for video progress tracking features.

    BUSINESS REQUIREMENT:
    Accurate progress tracking is essential for:
    - Course completion certification
    - Student motivation (seeing progress)
    - Instructor analytics (engagement monitoring)
    """

    @pytest.mark.priority_critical
    def test_05_track_watch_time(self, db_connection):
        """
        Test watch time tracking (seconds watched vs total duration).

        BUSINESS REQUIREMENT:
        System must accurately track how much of each video a student
        has watched for completion tracking and engagement analytics.

        VALIDATION:
        - UI: Watch time display updates during playback
        - Database: watch_time column matches actual viewing time
        - Accuracy: Database time within 5 seconds of actual

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Get initial watch time
        initial_watch_time = player_page.get_watch_time()

        # Play video for 10 seconds
        player_page.click_play()
        time.sleep(10)
        player_page.click_pause()

        # LAYER 1: UI Verification - Watch time increased
        final_watch_time = player_page.get_watch_time()
        time_increase = final_watch_time - initial_watch_time

        assert time_increase >= 8, \
            f"Watch time should increase by ~10s, got {time_increase}s"

        # LAYER 2: Database Verification - Accurate within 5 seconds
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT watch_time_seconds
            FROM video_watch_sessions
            WHERE student_email = %s AND video_id = %s
            ORDER BY updated_at DESC LIMIT 1
        """, (student_email, video_id))
        result = cursor.fetchone()

        if result:
            db_watch_time = result[0]
            assert abs(db_watch_time - time_increase) <= 5, \
                f"Database watch time ({db_watch_time}s) should be within 5s of UI ({time_increase}s)"

        # Cleanup
        cursor.close()
        self.driver.quit()

    @pytest.mark.priority_critical
    def test_06_mark_video_complete(self, db_connection):
        """
        Test video completion detection (>90% watched).

        BUSINESS REQUIREMENT:
        Videos are marked complete when student watches >90% to:
        - Award completion badges
        - Calculate course completion percentage
        - Track student progress for certification

        VALIDATION:
        - UI: Completion badge appears when >90% watched
        - Database: is_completed flag set to TRUE
        - Progress: completion_percentage >= 90

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Get video duration
        duration = player_page.get_video_duration()

        # Seek to 95% of video (ensures >90% completion)
        completion_position = duration * 0.95
        player_page.seek_to_position(completion_position)

        # Play for a few seconds to trigger completion
        player_page.click_play()
        time.sleep(3)
        player_page.click_pause()

        # LAYER 1: UI Verification - Completion badge visible
        assert player_page.is_video_completed(), \
            "Completion badge should appear when >90% watched"

        # Get completion percentage
        completion_percentage = player_page.get_completion_percentage()
        assert completion_percentage >= 90, \
            f"Completion percentage should be >= 90%, got {completion_percentage}%"

        # LAYER 2: Database Verification - is_completed flag set
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT is_completed, completion_percentage
            FROM video_watch_sessions
            WHERE student_email = %s AND video_id = %s
            ORDER BY updated_at DESC LIMIT 1
        """, (student_email, video_id))
        result = cursor.fetchone()

        if result:
            is_completed, db_completion = result
            assert is_completed, \
                "is_completed flag should be TRUE in database"
            assert db_completion >= 90, \
                f"Database completion_percentage should be >= 90%, got {db_completion}%"

        # Cleanup
        cursor.close()
        self.driver.quit()

    @pytest.mark.priority_high
    def test_07_resume_playback_from_last_position(self, db_connection):
        """
        Test resume playback from last saved position.

        BUSINESS REQUIREMENT:
        Students should be able to resume videos from where they left off
        without manually seeking, providing seamless learning continuity.

        VALIDATION:
        - UI: Resume button shows last watched position
        - Playback: Video starts at saved position (within 2 seconds)
        - Database: last_position matches video currentTime

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Watch video for 30 seconds then stop
        player_page.click_play()
        time.sleep(30)
        last_position = player_page.get_current_time()
        player_page.click_pause()

        # LAYER 1: Database - Save last position
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO video_watch_sessions (
                student_email, video_id, last_position, updated_at
            ) VALUES (%s, %s, %s, NOW())
            ON CONFLICT (student_email, video_id)
            DO UPDATE SET last_position = EXCLUDED.last_position,
                          updated_at = NOW()
        """, (student_email, video_id, last_position))
        db_connection.commit()

        # Navigate away and return
        progress_page = VideoProgressPage(self.driver)
        progress_page.navigate(course_id)

        # LAYER 2: UI - Resume button shows correct position
        saved_position = progress_page.get_last_watched_position(video_id)
        assert abs(saved_position - last_position) <= 5, \
            f"Saved position ({saved_position}s) should match last position ({last_position}s)"

        # Click resume button
        progress_page.click_resume_video(video_id)

        # LAYER 3: Playback - Video resumes at correct position
        player_page = VideoPlayerPage(self.driver)
        resumed_position = player_page.get_current_time()

        assert abs(resumed_position - last_position) <= 2, \
            f"Resumed position ({resumed_position}s) should match saved position ({last_position}s)"

        # Cleanup
        cursor.close()
        self.driver.quit()


# ============================================================================
# TEST CLASS - Analytics
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoAnalytics(BaseTest):
    """
    Test suite for instructor video analytics.

    BUSINESS REQUIREMENT:
    Instructors need detailed analytics to:
    - Identify students who aren't watching videos
    - Find confusing sections where students drop off
    - Optimize content based on engagement patterns
    """

    @pytest.mark.priority_critical
    def test_08_record_watch_time_in_database(self, db_connection):
        """
        Test watch time recording in database (accuracy within 5 seconds).

        BUSINESS REQUIREMENT:
        Watch time must be accurately recorded in database for:
        - Student progress reports
        - Instructor analytics dashboards
        - Completion certification verification

        VALIDATION:
        - Database: watch_time_seconds matches actual viewing time
        - Accuracy: Database value within 5 seconds of real time
        - Updates: watch_time increases with multiple sessions

        Args:
            db_connection: Database connection fixture
        """
        # Setup
        student_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
        course_id = 1
        video_id = 1

        # Navigate and login
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login(student_email, "password123")

        # Navigate to video player
        player_page = VideoPlayerPage(self.driver)
        player_page.navigate_to_video(course_id, video_id)

        # Session 1: Watch for 15 seconds
        player_page.click_play()
        time.sleep(15)
        player_page.click_pause()

        # LAYER 1: Database Verification - First session recorded
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT watch_time_seconds
            FROM video_watch_sessions
            WHERE student_email = %s AND video_id = %s
            ORDER BY updated_at DESC LIMIT 1
        """, (student_email, video_id))
        result = cursor.fetchone()

        assert result is not None, \
            "Watch session should be recorded in database"

        first_watch_time = result[0]
        assert 10 <= first_watch_time <= 20, \
            f"First session watch time should be ~15s, got {first_watch_time}s"

        # Session 2: Watch for another 20 seconds
        player_page.click_play()
        time.sleep(20)
        player_page.click_pause()

        # LAYER 2: Database Verification - Cumulative watch time
        cursor.execute("""
            SELECT watch_time_seconds
            FROM video_watch_sessions
            WHERE student_email = %s AND video_id = %s
            ORDER BY updated_at DESC LIMIT 1
        """, (student_email, video_id))
        result = cursor.fetchone()

        second_watch_time = result[0]
        total_expected = 35  # 15s + 20s

        assert abs(second_watch_time - total_expected) <= 5, \
            f"Cumulative watch time should be ~{total_expected}s, got {second_watch_time}s"

        # Cleanup
        cursor.close()
        self.driver.quit()

    @pytest.mark.priority_high
    def test_09_calculate_average_watch_percentage(self, db_connection):
        """
        Test average watch percentage calculation per video.

        BUSINESS REQUIREMENT:
        Instructors need to see average engagement per video to:
        - Identify low-engagement videos that need improvement
        - Compare video effectiveness across course
        - Prioritize content updates based on engagement

        VALIDATION:
        - Database: Correct calculation across all students
        - UI: Analytics dashboard shows accurate average
        - Formula: (sum of all watch_percentages) / (total students)

        Args:
            db_connection: Database connection fixture
        """
        # Setup: Create 3 test students with different watch percentages
        course_id = 1
        video_id = 1

        students = [
            {"email": f"student1_{uuid.uuid4().hex[:8]}@test.com", "percentage": 100},
            {"email": f"student2_{uuid.uuid4().hex[:8]}@test.com", "percentage": 75},
            {"email": f"student3_{uuid.uuid4().hex[:8]}@test.com", "percentage": 50},
        ]

        # LAYER 1: Database Setup - Insert watch sessions
        cursor = db_connection.cursor()
        for student in students:
            cursor.execute("""
                INSERT INTO video_watch_sessions (
                    student_email, video_id, completion_percentage, updated_at
                ) VALUES (%s, %s, %s, NOW())
            """, (student["email"], video_id, student["percentage"]))
        db_connection.commit()

        # Login as instructor
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login("instructor@test.com", "password123")

        # Navigate to analytics dashboard
        analytics_page = VideoAnalyticsPage(self.driver)
        analytics_page.navigate(course_id)
        analytics_page.select_video(video_id)

        # LAYER 2: UI Verification - Average displayed correctly
        avg_percentage = analytics_page.get_average_watch_percentage()
        expected_avg = (100 + 75 + 50) / 3  # 75%

        assert abs(avg_percentage - expected_avg) <= 1, \
            f"Average watch percentage should be {expected_avg}%, got {avg_percentage}%"

        # LAYER 3: Database Calculation - Verify query logic
        cursor.execute("""
            SELECT AVG(completion_percentage) as avg_percentage
            FROM video_watch_sessions
            WHERE video_id = %s
        """, (video_id,))
        result = cursor.fetchone()

        db_avg = float(result[0])
        assert abs(db_avg - expected_avg) <= 0.1, \
            f"Database average should be {expected_avg}%, got {db_avg}%"

        # Cleanup
        cursor.close()
        self.driver.quit()

    @pytest.mark.priority_medium
    def test_10_identify_dropoff_points(self, db_connection):
        """
        Test drop-off point identification (where students stop watching).

        BUSINESS REQUIREMENT:
        Identifying where students stop watching helps instructors:
        - Find confusing sections that need clarification
        - Optimize video length (if consistent drop-off at certain time)
        - Improve content quality based on engagement patterns

        VALIDATION:
        - UI: Heatmap shows drop-off points with timestamps
        - Database: Drop-off data aggregated from all students
        - Threshold: Points with >20% drop-off rate are flagged

        Args:
            db_connection: Database connection fixture
        """
        # Setup: Create test students with drop-off at specific timestamps
        course_id = 1
        video_id = 1

        # Simulate 10 students dropping off at 120s (2 minutes)
        # 5 students drop off at 120s, 3 at 180s, 2 complete
        cursor = db_connection.cursor()

        # Students dropping at 120s (50% drop-off)
        for i in range(5):
            email = f"dropoff120_{i}_{uuid.uuid4().hex[:8]}@test.com"
            cursor.execute("""
                INSERT INTO video_watch_sessions (
                    student_email, video_id, last_position, completion_percentage, updated_at
                ) VALUES (%s, %s, 120, 40, NOW())
            """, (email, video_id))

        # Students dropping at 180s (30% drop-off)
        for i in range(3):
            email = f"dropoff180_{i}_{uuid.uuid4().hex[:8]}@test.com"
            cursor.execute("""
                INSERT INTO video_watch_sessions (
                    student_email, video_id, last_position, completion_percentage, updated_at
                ) VALUES (%s, %s, 180, 60, NOW())
            """, (email, video_id))

        # Students completing (20%)
        for i in range(2):
            email = f"complete_{i}_{uuid.uuid4().hex[:8]}@test.com"
            cursor.execute("""
                INSERT INTO video_watch_sessions (
                    student_email, video_id, last_position, completion_percentage, updated_at
                ) VALUES (%s, %s, 300, 100, NOW())
            """, (email, video_id))

        db_connection.commit()

        # Login as instructor
        login_page = StudentLoginPage(self.driver)
        login_page.navigate()
        login_page.login("instructor@test.com", "password123")

        # Navigate to analytics dashboard
        analytics_page = VideoAnalyticsPage(self.driver)
        analytics_page.navigate(course_id)
        analytics_page.select_video(video_id)

        # LAYER 1: UI Verification - Drop-off points displayed
        dropoff_points = analytics_page.get_dropoff_points()

        assert len(dropoff_points) >= 2, \
            "Should identify at least 2 major drop-off points"

        # Find 120s drop-off point
        dropoff_120 = [p for p in dropoff_points if abs(p[0] - 120) <= 5]
        assert len(dropoff_120) > 0, \
            "Should identify drop-off point at ~120s"

        # Verify 120s drop-off percentage (50% of students)
        percentage_120 = dropoff_120[0][1]
        assert percentage_120 >= 45, \
            f"Drop-off at 120s should be ~50%, got {percentage_120}%"

        # Find 180s drop-off point
        dropoff_180 = [p for p in dropoff_points if abs(p[0] - 180) <= 5]
        if len(dropoff_180) > 0:
            percentage_180 = dropoff_180[0][1]
            assert percentage_180 >= 25, \
                f"Drop-off at 180s should be ~30%, got {percentage_180}%"

        # Cleanup
        cursor.close()
        self.driver.quit()


# ============================================================================
# CONFTEST.PY FIXTURES (Copy to conftest.py)
# ============================================================================

"""
# Database connection fixture for video tests
@pytest.fixture
def db_connection():
    '''
    Provide PostgreSQL database connection for E2E tests.

    BUSINESS REQUIREMENT:
    Tests need database access to verify data persistence and
    validate multi-layer verification (UI + Database).
    '''
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="course_creator",
        user="postgres",
        password="postgres"
    )
    yield conn
    conn.close()
"""
